"""
Admin management for registration blocs, items, reductions, and orders.
Staff-only. Lives as a tab on the event detail page.
"""
import json
import uuid
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.files.storage import default_storage
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from events.models import Event, Session
from .models_blocs import (
    EventBlocConfig, BlocItem, BlocItemStatusRule, ReductionPeriod, RegistrationOrder,
    CUSTOM_BLOC_CHOICES,
)
from .blocs_service import compute_order
from .views import is_staff_user


def _parse_decimal(raw, default='0'):
    try:
        return Decimal(str(raw).strip() or default)
    except (InvalidOperation, ValueError, TypeError):
        return Decimal(default)


def _get_config(event):
    config, _ = EventBlocConfig.objects.get_or_create(event=event)
    return config


@login_required
@user_passes_test(is_staff_user)
def blocs_config(request, event_id):
    """Main management page: visibility, select modes, reductions, items, periods."""
    event = get_object_or_404(Event, id=event_id)
    config = _get_config(event)

    blocs = []
    for bloc_key, bloc_label in CUSTOM_BLOC_CHOICES:
        blocs.append({
            'key': bloc_key,
            'label': bloc_label,
            'select_mode': config.select_mode_for(bloc_key),
            'items': list(BlocItem.objects.filter(event=event, bloc=bloc_key).order_by('order', 'name')),
        })

    paid_sessions = Session.objects.filter(event=event, is_paid=True).order_by('start_time')
    periods = ReductionPeriod.objects.filter(event=event).order_by('start_date')
    pending_orders = RegistrationOrder.objects.filter(event=event, status='pending').count()

    # Status-dependent rules matrix: rows = every item in the other blocs
    # (+ paid sessions for Workshops), columns = every Status item. A cell
    # holds whether that item is visible for that status, and an optional
    # overridden price -- see BlocItemStatusRule.
    status_items = list(BlocItem.objects.filter(event=event, bloc='status', is_active=True).order_by('order', 'name'))

    target_rows = []
    for bloc_key, bloc_label in CUSTOM_BLOC_CHOICES:
        if bloc_key == 'status':
            continue
        for item in BlocItem.objects.filter(event=event, bloc=bloc_key, is_active=True).order_by('order', 'name'):
            target_rows.append({'target_key': f'item_{item.id}', 'label': item.name, 'bloc_label': bloc_label})
    for session in paid_sessions:
        target_rows.append({'target_key': f'session_{session.id}', 'label': session.title, 'bloc_label': 'Workshops'})

    rules_lookup = {}
    for rule in BlocItemStatusRule.objects.filter(status_item__event=event):
        target_key = f'item_{rule.target_item_id}' if rule.target_kind == 'item' else f'session_{rule.target_session_id}'
        rules_lookup[(rule.status_item_id, target_key)] = rule

    for row in target_rows:
        row['cells'] = []
        for status_item in status_items:
            rule = rules_lookup.get((status_item.id, row['target_key']))
            row['cells'].append({
                'status_id': status_item.id,
                'target_key': row['target_key'],
                'visible': rule.is_visible if rule else True,
                'price': rule.override_price if rule else None,
            })

    context = {
        'event': event,
        'config': config,
        'blocs': blocs,
        'paid_sessions': paid_sessions,
        'periods': periods,
        'pending_orders': pending_orders,
        'select_mode_choices': [('single', 'Single choice (radio)'), ('multiple', 'Multiple choice (checkbox)')],
        'status_items': status_items,
        'target_rows': target_rows,
    }
    return render(request, 'dashboard/blocs/config.html', context)


@login_required
@user_passes_test(is_staff_user)
@require_POST
def blocs_config_save(request, event_id):
    """Save visibility toggles, per-bloc select modes, and reduction settings."""
    event = get_object_or_404(Event, id=event_id)
    config = _get_config(event)

    config.show_status = bool(request.POST.get('show_status'))
    config.show_restauration = bool(request.POST.get('show_restauration'))
    config.show_workshops = bool(request.POST.get('show_workshops'))
    config.show_social_event = bool(request.POST.get('show_social_event'))

    for bloc in ('status', 'restauration', 'social_event'):
        mode = request.POST.get(f'{bloc}_select_mode')
        if mode in ('single', 'multiple'):
            setattr(config, f'{bloc}_select_mode', mode)

    config.reduction_by_period_enabled = bool(request.POST.get('reduction_by_period_enabled'))
    config.reduction_by_blocs_enabled = bool(request.POST.get('reduction_by_blocs_enabled'))
    config.reduction_2_blocs = _parse_decimal(request.POST.get('reduction_2_blocs'))
    config.reduction_3_blocs = _parse_decimal(request.POST.get('reduction_3_blocs'))
    config.reduction_4_blocs = _parse_decimal(request.POST.get('reduction_4_blocs'))

    config.save()
    messages.success(request, 'Registration configuration saved.')
    return redirect('dashboard:blocs_config', event_id=event.id)


@login_required
@user_passes_test(is_staff_user)
@require_POST
def bloc_item_save(request, event_id):
    """Create or update a custom bloc item."""
    event = get_object_or_404(Event, id=event_id)

    item_id = request.POST.get('item_id')
    bloc = request.POST.get('bloc')
    name = (request.POST.get('name') or '').strip()
    price = _parse_decimal(request.POST.get('price'))
    order = request.POST.get('order') or 0

    valid_blocs = [b for b, _ in CUSTOM_BLOC_CHOICES]
    if bloc not in valid_blocs or not name:
        messages.error(request, 'A bloc and a name are required.')
        return redirect('dashboard:blocs_config', event_id=event.id)

    try:
        order = int(order)
    except (ValueError, TypeError):
        order = 0

    if item_id:
        item = get_object_or_404(BlocItem, id=item_id, event=event)
        item.bloc = bloc
        item.name = name
        item.price = price
        item.order = order
        item.save()
        messages.success(request, f'Item "{name}" updated.')
    else:
        BlocItem.objects.create(event=event, bloc=bloc, name=name, price=price, order=order)
        messages.success(request, f'Item "{name}" added.')

    return redirect('dashboard:blocs_config', event_id=event.id)


@login_required
@user_passes_test(is_staff_user)
@require_POST
def bloc_item_delete(request, item_id):
    """Delete a custom bloc item."""
    item = get_object_or_404(BlocItem, id=item_id)
    event_id = item.event_id
    name = item.name
    item.delete()
    messages.success(request, f'Item "{name}" deleted.')
    return redirect('dashboard:blocs_config', event_id=event_id)


@login_required
@user_passes_test(is_staff_user)
@require_POST
def bloc_status_rules_save(request, event_id):
    """
    Save the whole status-dependent visibility/price matrix in one submit.
    Expects visible_<status_id>_<target_key> (checkbox) and
    price_<status_id>_<target_key> (optional number) for every
    (status item, other-bloc item/session) pair on the page. A cell left
    at its default (visible, no price override) has its rule removed
    entirely, rather than storing a no-op row.
    """
    event = get_object_or_404(Event, id=event_id)
    status_item_ids = list(
        BlocItem.objects.filter(event=event, bloc='status', is_active=True).values_list('id', flat=True)
    )
    target_keys = [f'item_{i}' for i in BlocItem.objects.filter(
        event=event, is_active=True
    ).exclude(bloc='status').values_list('id', flat=True)]
    target_keys += [f'session_{s}' for s in Session.objects.filter(
        event=event, is_paid=True
    ).values_list('id', flat=True)]

    for status_id in status_item_ids:
        for target_key in target_keys:
            field_suffix = f'{status_id}_{target_key}'
            is_visible = bool(request.POST.get(f'visible_{field_suffix}'))
            raw_price = (request.POST.get(f'price_{field_suffix}') or '').strip()
            override_price = _parse_decimal(raw_price) if raw_price else None

            if is_visible and override_price is None:
                # Default state -- no rule needed.
                BlocItemStatusRule.objects.filter(
                    status_item_id=status_id, target_kind='item' if target_key.startswith('item_') else 'session',
                    **({'target_item_id': target_key[5:]} if target_key.startswith('item_') else {'target_session_id': target_key[8:]})
                ).delete()
                continue

            target_kind = 'item' if target_key.startswith('item_') else 'session'
            defaults = {'is_visible': is_visible, 'override_price': override_price}
            lookup = {'status_item_id': status_id, 'target_kind': target_kind}
            if target_kind == 'item':
                lookup['target_item_id'] = target_key[5:]
            else:
                lookup['target_session_id'] = target_key[8:]
            BlocItemStatusRule.objects.update_or_create(**lookup, defaults=defaults)

    messages.success(request, 'Status-dependent rules saved.')
    return redirect('dashboard:blocs_config', event_id=event.id)


@login_required
@user_passes_test(is_staff_user)
@require_POST
def reduction_period_save(request, event_id):
    """Add a reduction period."""
    event = get_object_or_404(Event, id=event_id)

    name = (request.POST.get('name') or '').strip()
    start_date = request.POST.get('start_date')
    end_date = request.POST.get('end_date')
    discount = _parse_decimal(request.POST.get('discount_percent'))

    if not start_date or not end_date:
        messages.error(request, 'Start and end dates are required for a period.')
        return redirect('dashboard:blocs_config', event_id=event.id)

    if end_date < start_date:
        messages.error(request, 'The period end date must be on or after the start date.')
        return redirect('dashboard:blocs_config', event_id=event.id)

    ReductionPeriod.objects.create(
        event=event, name=name, start_date=start_date, end_date=end_date, discount_percent=discount
    )
    messages.success(request, 'Reduction period added.')
    return redirect('dashboard:blocs_config', event_id=event.id)


@login_required
@user_passes_test(is_staff_user)
@require_POST
def reduction_period_delete(request, period_id):
    """Delete a reduction period."""
    period = get_object_or_404(ReductionPeriod, id=period_id)
    event_id = period.event_id
    period.delete()
    messages.success(request, 'Reduction period deleted.')
    return redirect('dashboard:blocs_config', event_id=event_id)


@login_required
@user_passes_test(is_staff_user)
def registration_orders(request, event_id):
    """
    Read-only list of submitted registration orders (paid registrations).
    Confirming or rejecting a reservation happens at the caisse on event
    day (see process_transaction / reject_reservation in caisse/views.py),
    not here -- admin no longer approves/rejects these.
    """
    event = get_object_or_404(Event, id=event_id)

    status = request.GET.get('status', '').strip()
    query = request.GET.get('q', '').strip()

    orders = RegistrationOrder.objects.filter(event=event).select_related('reviewed_by', 'reviewed_by_caisse')
    if status in ('pending', 'approved', 'rejected'):
        orders = orders.filter(status=status)
    if query:
        orders = orders.filter(Q(full_name__icontains=query) | Q(email__icontains=query))
    orders = orders.order_by('-created_at')

    context = {
        'event': event,
        'orders': orders,
        'status': status,
        'query': query,
    }
    return render(request, 'dashboard/blocs/orders.html', context)


# ---------------------------------------------------------------------------
# Public form integration (called from dashboard.views.public_form_view)
# ---------------------------------------------------------------------------

def get_public_bloc_context(event):
    """
    Build the blocs data for the public registration form.
    Returns None when the form has no event, no config, or no visible bloc
    (in which case the form stays a plain Informations-only form).
    """
    if not event:
        return None
    try:
        config = event.bloc_config
    except EventBlocConfig.DoesNotExist:
        return None
    if not config.any_bloc_visible():
        return None

    visibility = {
        'status': config.show_status,
        'restauration': config.show_restauration,
        'social_event': config.show_social_event,
    }
    custom_blocs = []
    for bloc_key, bloc_label in CUSTOM_BLOC_CHOICES:
        if not visibility.get(bloc_key):
            continue
        items = list(BlocItem.objects.filter(event=event, bloc=bloc_key, is_active=True).order_by('order', 'name'))
        if not items:
            continue
        custom_blocs.append({
            'key': bloc_key,
            'label': bloc_label,
            'select_mode': config.select_mode_for(bloc_key),
            'items': items,
        })

    paid_sessions = []
    if config.show_workshops:
        paid_sessions = list(Session.objects.filter(event=event, is_paid=True).order_by('start_time'))

    # Period discount applicable to *today* (fixed at page load), so the cart
    # can preview the reduced total client-side. The server still recomputes.
    period_percent_today = 0
    if config.reduction_by_period_enabled:
        today = timezone.now().date()
        period = event.reduction_periods.filter(
            start_date__lte=today, end_date__gte=today
        ).order_by('-discount_percent').first()
        if period:
            period_percent_today = float(period.discount_percent)

    active_bloc_keys = [b['key'] for b in custom_blocs]
    if config.show_workshops and paid_sessions:
        active_bloc_keys.append('workshops')

    from .blocs_service import serialize_status_rules_for_event

    return {
        'has_blocs': True,
        'config': config,
        'custom_blocs': custom_blocs,
        'workshops_visible': config.show_workshops,
        'paid_sessions': paid_sessions,
        'period_percent_today': period_percent_today,
        'active_bloc_keys': active_bloc_keys,
        'status_rules_json': json.dumps(serialize_status_rules_for_event(event)),
    }


def _client_ip(request):
    xff = request.META.get('HTTP_X_FORWARDED_FOR', '')
    return xff.split(',')[0].strip() if xff else request.META.get('REMOTE_ADDR')


def stage_paid_registration(request, form_config, form_data, email, full_name, bloc_context):
    """
    Validate a paid registration submission (blocs enabled) and stage it
    behind an email verification code -- the same code/expiry mechanism the
    free flow uses. The receipt is saved to storage right away (it can't
    ride along in the verification's JSON form_data like the other fields
    can); its path plus the bloc selections are bundled into form_data so
    finalize_paid_registration() can build the actual FormSubmission +
    RegistrationOrder once the code is confirmed.

    Returns (ok: bool, errors: list, wait_seconds: int or None).
    """
    config = bloc_context['config']
    errors = []

    # Gather selections, enforcing single-select cardinality per bloc.
    selected_item_ids = []
    for bloc in bloc_context['custom_blocs']:
        picked = [v for v in request.POST.getlist(f"items_{bloc['key']}") if v]
        if bloc['select_mode'] == 'single' and len(picked) > 1:
            errors.append(f"Please select only one option in {bloc['label']}.")
        selected_item_ids.extend(picked)

    selected_session_ids = [v for v in request.POST.getlist('sessions') if v]

    # Conditions + receipt are mandatory for paid registrations.
    if not request.POST.get('accept_conditions'):
        errors.append("You must accept the conditions.")
    receipt = request.FILES.get('receipt_file')
    if not receipt:
        errors.append("Please upload your bank receipt.")

    if not email:
        errors.append('Email is required.')

    if errors:
        return False, errors, None

    receipt_path = default_storage.save(
        f'registrations/receipts/{uuid.uuid4().hex}_{receipt.name}', receipt
    )

    staged_data = dict(form_data)
    staged_data['__paid_meta__'] = {
        'selected_item_ids': selected_item_ids,
        'selected_session_ids': selected_session_ids,
        'receipt_path': receipt_path,
        'full_name': full_name,
    }

    from events.form_validation_service import send_form_validation_code

    success, message, wait_seconds = send_form_validation_code(
        email=email,
        form_slug=form_config.slug,
        form_data=staged_data,
        ip_address=_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:1000],
    )
    if not success:
        return False, [message], wait_seconds
    return True, [], None


def finalize_paid_registration(verification, form_config, user):
    """
    Called once the email verification code staged by stage_paid_registration()
    has been confirmed. Builds the FormSubmission + RegistrationOrder from the
    data stashed on the verification row.

    The order starts out reserved (status='pending'/"Reserved"), and no
    admin review gates that -- the participant role is granted right away
    (same trust level as the free flow), while the caisse operator does the
    real payment validation on event day (see process_transaction /
    reject_reservation in caisse/views.py).

    Returns (ok: bool, message: str).
    """
    from .models_form import FormSubmission
    from events.form_validation_service import create_participant_for_event

    event = form_config.event
    bloc_context = get_public_bloc_context(event)
    if not bloc_context:
        return False, "This event's registration options are no longer available."

    meta = verification.form_data.get('__paid_meta__') or {}
    receipt_path = meta.get('receipt_path')
    if not receipt_path:
        return False, "Missing receipt file. Please submit your registration again."

    result = compute_order(
        event=event,
        config=bloc_context['config'],
        selected_item_ids=meta.get('selected_item_ids', []),
        selected_session_ids=meta.get('selected_session_ids', []),
        on_date=timezone.now().date(),
    )

    submission = FormSubmission.objects.create(
        form=form_config,
        data=verification.form_data,
        email=verification.email or '',
        ip_address=verification.ip_address,
        user_agent=verification.user_agent[:1000],
    )

    participant = create_participant_for_event(user, event)

    RegistrationOrder.objects.create(
        event=event,
        form_submission=submission,
        participant=participant,
        full_name=meta.get('full_name', ''),
        email=verification.email or '',
        items_snapshot=result['snapshot'],
        subtotals=result['subtotals'],
        distinct_blocs_count=result['distinct_blocs_count'],
        total_before_reduction=result['total_before_reduction'],
        period_discount_percent=result['period_discount_percent'],
        blocs_discount_percent=result['blocs_discount_percent'],
        total_discount_percent=result['total_discount_percent'],
        total_after_reduction=result['total_after_reduction'],
        receipt_file=receipt_path,
        ip_address=verification.ip_address,
        user_agent=verification.user_agent[:1000],
    )

    form_config.increment_submission_count()
    return True, (
        'Votre inscription a été enregistrée et est réservée. '
        'Présentez votre preuve de paiement à la caisse le jour de l\'événement pour la confirmer.'
    )
