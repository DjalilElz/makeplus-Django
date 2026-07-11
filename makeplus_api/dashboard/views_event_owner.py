"""
Registration submissions view for event owners.

Accessible by staff/superusers (any event) and by event-owner accounts
(events.UserEventAssignment role='event_owner') scoped to the event(s)
they're assigned to. Owners can view, search and filter, download
receipts, move a registration between its 4 statuses (Registered ->
Reserved -> Confirmed -> Cancelled -- see caisse.services for what
Confirmed/Cancelled actually do), and delete a registration.
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST

from caisse.services import cancel_registration_order, confirm_registration_order
from events.models import Event, ParticipantEventRegistration, UserEventAssignment
from .models_blocs import RegistrationOrder


def _can_access_event_orders(user, event):
    """Staff/superusers can access any event; event owners only their own."""
    if user.is_staff or user.is_superuser:
        return True
    return UserEventAssignment.objects.filter(
        user=user, event=event, role='event_owner', is_active=True
    ).exists()


@never_cache
@login_required
def event_owner_submissions_home(request):
    """
    Landing page for event owners after login. Redirects straight to
    their event if they own only one, otherwise shows a picker.
    """
    assignments = UserEventAssignment.objects.filter(
        user=request.user, role='event_owner', is_active=True
    ).select_related('event').order_by('-assigned_at')

    if not assignments.exists():
        if request.user.is_staff or request.user.is_superuser:
            return redirect('dashboard:home')
        messages.error(request, "You don't have access to any event as an event owner.")
        return redirect('dashboard:login')

    if assignments.count() == 1:
        return redirect('dashboard:event_owner_submissions', event_id=assignments.first().event_id)

    events = [a.event for a in assignments]
    return render(request, 'dashboard/event_owner/event_picker.html', {'events': events})


@never_cache
@login_required
def event_owner_submissions(request, event_id):
    """List registration submissions for one event, read-only."""
    event = get_object_or_404(Event, id=event_id)

    if not _can_access_event_orders(request.user, event):
        raise PermissionDenied("You do not have access to this event's submissions.")

    status = request.GET.get('status', '').strip()
    query = request.GET.get('q', '').strip()

    orders = RegistrationOrder.objects.filter(event=event).select_related('period')
    if status in ('pending', 'reserved', 'approved', 'rejected'):
        orders = orders.filter(status=status)
    if query:
        orders = orders.filter(Q(full_name__icontains=query) | Q(email__icontains=query))
    orders = list(orders.order_by('-created_at'))

    # The participant's chosen Status item lives inside items_snapshot
    # (a JSON list), not a direct field -- pull it out for display.
    for order in orders:
        status_entry = next((it for it in order.items_snapshot if it.get('bloc') == 'status'), None)
        order.participant_status = status_entry['name'] if status_entry else '—'
        order.other_items = [it for it in order.items_snapshot if it.get('bloc') != 'status']

    context = {
        'event': event,
        'orders': orders,
        'status': status,
        'query': query,
    }
    return render(request, 'dashboard/event_owner/submissions.html', context)


@never_cache
@login_required
@require_POST
def registration_status_save(request, order_id):
    """
    Move a registration between its 4 statuses. Confirmed/Cancelled
    trigger real effects (see caisse.services -- Confirmed creates a real
    paid CaisseTransaction + session access, Cancelled voids one if this
    flow created it); Registered/Reserved are plain bookkeeping.
    """
    order = get_object_or_404(RegistrationOrder, id=order_id)
    if not _can_access_event_orders(request.user, order.event):
        raise PermissionDenied("You do not have access to this event's submissions.")

    new_status = request.POST.get('status', '').strip()
    if new_status not in ('pending', 'reserved', 'approved', 'rejected'):
        messages.error(request, 'Invalid status.')
        return redirect('dashboard:event_owner_submissions', event_id=order.event_id)

    if new_status != order.status:
        if new_status == 'approved':
            try:
                confirm_registration_order(order, confirmed_by=request.user)
                messages.success(request, 'Registration confirmed -- the participant now has real paid access.')
            except ValueError as exc:
                messages.error(request, str(exc))
        elif new_status == 'rejected':
            cancel_registration_order(order, cancelled_by=request.user)
            messages.success(request, 'Registration cancelled.')
        elif order.status == 'approved':
            # Un-confirming isn't a plain label change -- it has to go
            # through cancel_registration_order to void the real
            # transaction, so route it through "Cancelled" instead.
            messages.error(
                request,
                'This registration is already Confirmed (real payment on file). '
                'Cancel it first if you need to revert it.',
            )
        else:
            order.status = new_status
            order.reviewed_by = request.user
            order.reviewed_at = timezone.now()
            order.save(update_fields=['status', 'reviewed_by', 'reviewed_at'])
            messages.success(request, 'Registration status updated.')

    return redirect('dashboard:event_owner_submissions', event_id=order.event_id)


@never_cache
@login_required
@require_POST
def registration_delete(request, order_id):
    """
    Delete a registration and revoke the participant's access to THIS
    event only -- their global participant profile, and any access to
    other events they're separately registered for, is untouched.

    If it was already Confirmed (a real caisse transaction is attached),
    requires the extra confirm_paid=1 flag: a plain delete on a paid
    registration would silently leave real collected money with nothing
    on record explaining it.
    """
    order = get_object_or_404(RegistrationOrder, id=order_id)
    if not _can_access_event_orders(request.user, order.event):
        raise PermissionDenied("You do not have access to this event's submissions.")

    if order.status == 'approved' and not request.POST.get('confirm_paid'):
        messages.error(
            request,
            'This registration was already Confirmed (real payment on file). '
            'Cancel it first, or explicitly confirm the delete if you understand this.',
        )
        return redirect('dashboard:event_owner_submissions', event_id=order.event_id)

    event_id = order.event_id
    participant = order.participant

    if order.caisse_transaction_id and order.caisse_transaction.status == 'completed':
        cancel_label = request.user.get_full_name() or request.user.email
        order.caisse_transaction.cancel(cancelled_by=cancel_label, reason='Registration deleted by event owner.')

    if participant:
        UserEventAssignment.objects.filter(
            user=participant.user, event_id=event_id, role='participant',
        ).update(is_active=False)
        ParticipantEventRegistration.objects.filter(participant=participant, event_id=event_id).delete()

    order.delete()
    messages.success(request, 'Registration deleted.')
    return redirect('dashboard:event_owner_submissions', event_id=event_id)
