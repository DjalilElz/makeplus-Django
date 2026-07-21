"""
Registration submissions view for event owners.

Accessible by staff/superusers (any event) and by event-owner accounts
(events.UserEventAssignment role='event_owner') scoped to the event(s)
they're assigned to. Owners can view, search and filter (by registration
status, by bloc item, or by free text), edit a free-text note per
registration, move a registration between its 6 statuses (Registered /
Reserved / To Contact / To Recontact / Confirmed / Cancelled -- see
caisse.services for what Confirmed/Cancelled actually do), and delete a
registration.
"""
from collections import Counter
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST

from caisse.services import cancel_registration_order, confirm_registration_order
from dashboard.email_sender import send_email
from dashboard.models_email import get_event_email_template
from events.models import Event, ParticipantEventRegistration, UserEventAssignment
from .models_blocs import RegistrationOrder

BLOC_KEYS = ('status', 'restauration', 'workshops', 'social_event')


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


STATUS_LABELS = {
    'pending': 'Enregistré',
    'reserved': 'Réservé',
    'to_contact': 'Contacter',
    'to_recontact': 'À recontacter',
    'approved': 'Confirmé',
    'rejected': 'Annulé',
}


def _bloc_names(order):
    """Item name(s) picked in each bloc for this order, comma-joined
    (a bloc like workshops can have more than one)."""
    names = {b: [] for b in BLOC_KEYS}
    for it in order.items_snapshot:
        b = it.get('bloc')
        if b in names:
            names[b].append(it.get('name', ''))
    return {b: ', '.join(v) if v else '—' for b, v in names.items()}


def _bloc_item_ids(order, bloc):
    return {str(it.get('id')) for it in order.items_snapshot if it.get('bloc') == bloc}


@never_cache
@login_required
def event_owner_submissions(request, event_id):
    """List registration submissions for one event, read-only."""
    event = get_object_or_404(Event, id=event_id)

    if not _can_access_event_orders(request.user, event):
        raise PermissionDenied("You do not have access to this event's submissions.")

    status = request.GET.get('status', '').strip()
    query = request.GET.get('q', '').strip()
    item_filters = {
        'status': request.GET.get('item_status', '').strip(),
        'restauration': request.GET.get('item_restauration', '').strip(),
        'social_event': request.GET.get('item_social_event', '').strip(),
    }
    workshop_item_ids = [v for v in request.GET.getlist('item_workshops') if v]

    all_orders = list(
        RegistrationOrder.objects.filter(event=event).select_related(
            'period', 'form_submission__form',
        ).order_by('-created_at')
    )

    # Filter dropdown options are built from the event's full, unfiltered
    # order set so choosing a filter never makes other options disappear.
    bloc_item_options = {b: {} for b in BLOC_KEYS}
    for order in all_orders:
        for it in order.items_snapshot:
            b = it.get('bloc')
            if b in bloc_item_options:
                bloc_item_options[b][str(it.get('id'))] = it.get('name', '')
    for b in bloc_item_options:
        bloc_item_options[b] = sorted(bloc_item_options[b].items(), key=lambda pair: pair[1] or '')

    # items_snapshot is a JSON field, not a normalized relation -- item
    # filters are applied in Python rather than at the DB query level.
    orders = all_orders
    if status in STATUS_LABELS:
        orders = [o for o in orders if o.status == status]
    if query:
        ql = query.lower()
        orders = [o for o in orders if ql in (o.full_name or '').lower() or ql in (o.email or '').lower()]
    for bloc, item_id in item_filters.items():
        if item_id:
            orders = [o for o in orders if item_id in _bloc_item_ids(o, bloc)]
    if workshop_item_ids:
        # A person can pick several workshops -- "picked any of these",
        # not "picked all of these" (AND would too easily match nobody).
        wanted = set(workshop_item_ids)
        orders = [o for o in orders if _bloc_item_ids(o, 'workshops') & wanted]

    # A phone number, if the event's registration form has a "tel"-type
    # custom field, lives in FormSubmission.data under whatever name the
    # admin gave that field -- not a fixed column. Every order for this
    # event shares the same form, so resolve the field name once.
    phone_field_name = None
    form_config = event.custom_forms.first()
    if form_config:
        phone_field_name = next(
            (f.get('name') for f in form_config.fields_config if f.get('type') == 'tel'), None,
        )

    total_revenue = Decimal('0')
    status_counts = {code: 0 for code in STATUS_LABELS}
    item_counts = {b: {} for b in BLOC_KEYS}
    for order in orders:
        order.bloc_names = _bloc_names(order)
        order.participant_status = order.bloc_names['status']
        order.status_label = STATUS_LABELS.get(order.status, order.status)
        order.phone = (
            order.form_submission.data.get(phone_field_name, '')
            if order.form_submission and phone_field_name else ''
        )
        total_revenue += order.total_after_reduction
        status_counts[order.status] = status_counts.get(order.status, 0) + 1
        for it in order.items_snapshot:
            b = it.get('bloc')
            if b in item_counts:
                name = it.get('name') or '—'
                item_counts[b][name] = item_counts[b].get(name, 0) + 1

    item_counts = {b: sorted(counts.items(), key=lambda pair: -pair[1]) for b, counts in item_counts.items()}
    status_breakdown = [(code, STATUS_LABELS[code], count) for code, count in status_counts.items()]

    # Registration pace over time, for a trend chart -- one point per day
    # that had at least one submission, in chronological order.
    day_counts = Counter(order.created_at.date().isoformat() for order in orders)
    registrations_by_day = sorted(day_counts.items())

    context = {
        'event': event,
        'orders': orders,
        'status': status,
        'status_label': STATUS_LABELS.get(status, ''),
        'query': query,
        'submissions_count': len(orders),
        'total_revenue': total_revenue,
        'status_choices': STATUS_LABELS.items(),
        'status_breakdown': status_breakdown,
        'item_counts': item_counts,
        'bloc_item_options': bloc_item_options,
        'item_filters': item_filters,
        'workshop_item_ids': workshop_item_ids,
        'registrations_by_day': registrations_by_day,
    }
    return render(request, 'dashboard/event_owner/submissions.html', context)


@never_cache
@login_required
@require_POST
def registration_status_save(request, order_id):
    """
    Move a registration between its 6 statuses. Confirmed/Cancelled
    trigger real effects (see caisse.services -- Confirmed creates a real
    paid CaisseTransaction + session access, Cancelled voids one if this
    flow created it); Registered/Reserved/To Contact/To Recontact are
    plain bookkeeping.
    """
    order = get_object_or_404(RegistrationOrder, id=order_id)
    if not _can_access_event_orders(request.user, order.event):
        raise PermissionDenied("You do not have access to this event's submissions.")

    new_status = request.POST.get('status', '').strip()
    if new_status not in STATUS_LABELS:
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
def registration_notes_save(request, order_id):
    """Autosaved free-text note on a registration -- bookkeeping only,
    no side effects, so it responds with JSON instead of redirecting
    (avoids a full page reload/scroll-jump while someone is typing)."""
    order = get_object_or_404(RegistrationOrder, id=order_id)
    if not _can_access_event_orders(request.user, order.event):
        raise PermissionDenied("You do not have access to this event's submissions.")

    order.admin_notes = request.POST.get('admin_notes', '')
    order.save(update_fields=['admin_notes'])
    return JsonResponse({'ok': True})


@never_cache
@login_required
@require_POST
def send_payment_link_email(request, order_id):
    """
    Emails the participant a standard "préinscription" message: an itemized
    breakdown of what they selected and the total, so they know exactly how
    much to pay -- plus a "Procéder au paiement" button/link, but only if
    the event actually has one configured (Event.payment_link is optional;
    a préinscription can legitimately exist without a payment link yet).
    Responds with JSON (called from the submissions modal via fetch, no
    page reload) rather than redirecting.
    """
    order = get_object_or_404(RegistrationOrder, id=order_id)
    if not _can_access_event_orders(request.user, order.event):
        raise PermissionDenied("You do not have access to this event's submissions.")

    event = order.event
    if not order.email:
        return JsonResponse({'ok': False, 'error': "Cette inscription n'a pas d'adresse e-mail."}, status=400)

    items_html = ''.join(
        f"<li>{it.get('name', '')} — {it.get('price', 0)} DZD</li>"
        for it in (order.items_snapshot or [])
    )
    if not items_html:
        items_html = '<li>Aucun article</li>'
    items_value = f"<ul>{items_html}</ul>"
    total_value = f"{order.total_after_reduction} DZD"

    # The button/link paragraph only appears if the event actually has a
    # payment link configured -- items/total always appear regardless,
    # since that part of the requirement ("participant sees exactly what
    # they'd pay") doesn't depend on a link existing yet.
    payment_link_html = ''
    if event.payment_link:
        payment_link_html = f"""
        <p>
            <a href="{event.payment_link}"
               style="display:inline-block; padding:10px 20px; background:#2D1B6B; color:#ffffff; text-decoration:none; border-radius:6px;">
               Procéder au paiement
            </a>
        </p>
        <p>Si le bouton ne fonctionne pas, copiez ce lien dans votre navigateur :<br>{event.payment_link}</p>
        """

    template = get_event_email_template(event, 'payment_link')

    if template:
        subject = template.subject
        intro_html = template.body_html or template.body
        replacements = {
            '{{participant_name}}': order.full_name or '',
            '{{event_name}}': event.name,
            '{{payment_link}}': event.payment_link or '',
        }
        for key, value in replacements.items():
            subject = subject.replace(key, value)
            intro_html = intro_html.replace(key, value)
    else:
        subject = f"Préinscription — {event.name}"
        intro_html = f"""
        <p>Bonjour {order.full_name or ''},</p>
        <p>Voici les informations de votre préinscription à <strong>{event.name}</strong>.</p>
        """

    # {{items}}/{{total}} are insertable -- an admin can place them anywhere
    # in their own text. If a token is missing, that piece is auto-appended
    # afterwards instead, so it's repositionable but never silently dropped.
    used_items_token = '{{items}}' in intro_html
    used_total_token = '{{total}}' in intro_html
    intro_html = intro_html.replace('{{items}}', items_value).replace('{{total}}', total_value)

    fallback_html = ''
    if not used_items_token:
        fallback_html += f"<p><strong>Articles sélectionnés :</strong></p>{items_value}"
    if not used_total_token:
        fallback_html += f"<p><strong>Total à payer : {total_value}</strong></p>"

    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #1a1a1a; line-height: 1.5;">
        {intro_html}
        {fallback_html}
        {payment_link_html}
        <p>Cordialement,<br>L'équipe {event.name}</p>
    </body>
    </html>
    """

    success, error, _ = send_email(
        to_email=order.email,
        subject=subject,
        html_content=html_content,
        to_name=order.full_name or None,
    )
    if not success:
        return JsonResponse({'ok': False, 'error': error or "Échec de l'envoi."}, status=502)
    return JsonResponse({'ok': True})


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
