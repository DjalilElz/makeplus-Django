"""
Read-only registration submissions view for event owners.

Accessible by staff/superusers (any event) and by event-owner accounts
(events.UserEventAssignment role='event_owner') scoped to the event(s)
they're assigned to. Owners can view, search and filter, and download
receipts -- no approve/reject/edit actions live here (that stays a
caisse/admin action elsewhere).
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import never_cache

from events.models import Event, UserEventAssignment
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
    if status in ('pending', 'approved', 'rejected'):
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
