"""
Server-side pricing & discount calculation for the blocs registration cart.

All money math is authoritative here: prices are always re-read from the
database (never trusted from the client), and totals/discounts are recomputed
regardless of anything the browser submitted.
"""
from decimal import Decimal, ROUND_HALF_UP

from django.db.models import Q

from events.models import Session
from .models_blocs import BlocItem, BlocItemStatusRule


TWO_PLACES = Decimal('0.01')

# Sentinel distinguishing "caller didn't pass a period" (resolve live from
# on_date, the normal case) from "caller explicitly wants no period" (pass
# period=None) -- see compute_order's period arg.
_PERIOD_NOT_PASSED = object()

# All four blocs and which ones are item-based (custom) vs sessions (workshops).
ALL_BLOCS = ['status', 'restauration', 'workshops', 'social_event']
CUSTOM_BLOCS = ['status', 'restauration', 'social_event']


def _q(amount):
    """Quantize a Decimal to 2 places (DZD)."""
    return Decimal(amount).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


def _bloc_visible(config, bloc):
    return {
        'status': config.show_status,
        'restauration': config.show_restauration,
        'workshops': config.show_workshops,
        'social_event': config.show_social_event,
    }.get(bloc, False)


def get_active_period(event, on_date):
    """The ReductionPeriod (if any) covering on_date. If periods overlap,
    the one that starts latest wins (most specific/recent)."""
    return event.reduction_periods.filter(
        start_date__lte=on_date, end_date__gte=on_date
    ).order_by('-start_date').first()


def _resolve_rule(rules_by_target, key):
    """Most specific match wins: status+period > status-only > period-only.
    rules_by_target[key] only ever contains rules already filtered down to
    the relevant status ids / active period, so at most one candidate can
    exist per specificity tier."""
    candidates = rules_by_target.get(key)
    if not candidates:
        return None
    for r in candidates:
        if r.status_item_id and r.period_id:
            return r
    for r in candidates:
        if r.status_item_id and not r.period_id:
            return r
    for r in candidates:
        if not r.status_item_id and r.period_id:
            return r
    return None


def _rules_by_target(status_item_ids, active_period):
    """
    Build the {(kind, target_id): [rules]} lookup used to resolve per-item
    price/visibility overrides -- shared by compute_order() and
    resolve_catalog_prices() so there is exactly one place that decides
    which BlocItemStatusRule applies to a given item.
    """
    rules_qs = BlocItemStatusRule.objects.filter(
        Q(status_item_id__in=status_item_ids) | Q(status_item__isnull=True)
    ).filter(
        Q(period_id=active_period.id) | Q(period__isnull=True) if active_period else Q(period__isnull=True)
    )
    rules_by_target = {}
    for rule in rules_qs:
        key = ('item', rule.target_item_id) if rule.target_kind == 'item' else ('session', str(rule.target_session_id))
        rules_by_target.setdefault(key, []).append(rule)
    return rules_by_target


def resolve_catalog_prices(event, config, on_date, context_status_item_id=None):
    """
    Live-current effective price and visibility for every active BlocItem/
    Session in the event, resolved through BlocItemStatusRule exactly like
    compute_order() -- the one source of truth anything OTHER than the
    registration form's own cart (e.g. the caisse's item catalog) should
    read from, instead of a separately-stored price snapshot (like
    caisse.PayableItem.price) that has no way to know when a
    BlocItemStatusRule changes.

    Returns {('item', bloc_item_id): {'price': Decimal, 'visible': bool}, ...}
    with the same shape for ('session', str(session_id)) keys.

    status_item_ids passed to _rules_by_target is scoped to AT MOST
    context_status_item_id -- never every active Status BlocItem in the
    event (that used to be the default here, unlike compute_order(),
    whose own status_item_ids is always just whichever Status the caller
    is actually asking about). A Status-scoped rule outranks a
    status-less "any status" one in _resolve_rule's precedence, so
    pulling in every Status meant a caller with no particular
    participant in mind (e.g. the caisse's generic catalog preview)
    could have an item's baseline price silently hijacked by whichever
    OTHER status happened to have its own override for that item -- e.g.
    an item free only for "Non-membre" showing as free for everyone.
    """
    active_period = get_active_period(event, on_date) if config.reduction_by_period_enabled else None

    status_item_ids = [int(context_status_item_id)] if context_status_item_id else []

    rules_by_target = _rules_by_target(status_item_ids, active_period)

    result = {}
    for item in BlocItem.objects.filter(event=event, is_active=True):
        rule = _resolve_rule(rules_by_target, ('item', item.id))
        price = rule.override_price if (rule and rule.override_price is not None) else item.price
        visible = not (rule and not rule.is_visible)
        result[('item', item.id)] = {'price': price, 'visible': visible}

    for session in Session.objects.filter(event=event, is_paid=True, is_active=True):
        rule = _resolve_rule(rules_by_target, ('session', str(session.id)))
        price = rule.override_price if (rule and rule.override_price is not None) else session.price
        visible = not (rule and not rule.is_visible)
        result[('session', str(session.id))] = {'price': price, 'visible': visible}

    return result


def compute_order(
    event, config, selected_item_ids, selected_session_ids, on_date,
    context_status_item_id=None, context_blocs_covered=None, include_inactive=False,
    period=_PERIOD_NOT_PASSED, ignore_visibility_rules=False,
):
    """
    Compute a cart from the raw selections.

    Args:
        event: Event
        config: EventBlocConfig
        selected_item_ids: iterable of BlocItem ids (custom blocs)
        selected_session_ids: iterable of Session ids (workshops bloc)
        on_date: date used to resolve the active period (the submission date)
            -- ignored when period is explicitly passed (see below).
        period: pins pricing to a specific ReductionPeriod (or None for "no
            period") instead of resolving one live from on_date. Use this
            to re-price an EXISTING order against the period it was
            actually placed under (RegistrationOrder.period is a snapshot
            for exactly this reason -- see its model docstring), so editing
            an old registration doesn't silently reprice it at whatever
            period happens to be active today. Leave unset for a brand new
            selection (public form, caisse on-the-day add), where "today's
            active period" is what should apply.
        include_inactive: also resolve BlocItems/Sessions that have been
            deactivated since the participant picked them. Only the event
            owner's "Modifier les blocs" edit flow sets this -- the public
            form and the caisse must keep hiding deactivated items entirely.
        ignore_visibility_rules: don't drop an item/session just because a
            BlocItemStatusRule marks it not visible for the chosen Status
            (or the active period's baseline). That gating is meant to
            steer a PARTICIPANT's own choices on the public form; the
            event owner's edit flow sets this to True so they can still
            grant/remove an item a given status normally wouldn't see. A
            price override on the same rule still applies either way --
            only the visibility gate is bypassed.
        context_status_item_id: optional BlocItem id of a Status already
            chosen elsewhere (e.g. locked into an existing registration),
            used only to resolve status-dependent rules for THIS selection
            -- it does not get added to the cart/subtotal itself. Use this
            when pricing new items for someone who picked their Status at
            registration and isn't re-selecting it now (e.g. the caisse
            adding an extra item on event day).
        context_blocs_covered: optional iterable of bloc names ('restauration',
            'workshops', 'social_event') the person already has a paid
            selection in from elsewhere (e.g. an earlier, separately-priced
            reservation) -- counted toward THIS selection's multi-bloc
            discount tier without adding anything to its own subtotal/price.
            Use this so a new item added at the caisse gets the discount
            tier its combined selection actually qualifies for, while the
            earlier reservation's own already-set price stays untouched.

    Returns dict with subtotals, snapshot, distinct bloc count, discount
    percentages, and totals before/after reduction. Only items belonging to
    the event, active, and inside a *visible* bloc are counted.

    Pricing per item is resolved via BlocItemStatusRule: a rule can be
    scoped to a Status, to today's active registration Period, or both --
    the most specific match sets that item's effective price (which then
    still goes through the bloc-count% reduction below, same as any other
    item). No matching rule => the item's normal base price.
    """
    selected_item_ids = [str(i) for i in (selected_item_ids or [])]
    selected_session_ids = [str(i) for i in (selected_session_ids or [])]

    snapshot = []
    subtotals = {bloc: Decimal('0') for bloc in ALL_BLOCS}

    item_filters = {'id__in': selected_item_ids, 'event': event}
    if not include_inactive:
        item_filters['is_active'] = True
    items = list(BlocItem.objects.filter(**item_filters)) if selected_item_ids else []

    status_item_ids = [item.id for item in items if item.bloc == 'status']
    if context_status_item_id:
        status_item_ids.append(int(context_status_item_id))

    if period is not _PERIOD_NOT_PASSED:
        active_period = period
    else:
        active_period = get_active_period(event, on_date) if config.reduction_by_period_enabled else None
    rules_by_target = _rules_by_target(status_item_ids, active_period)

    # --- Custom bloc items ---
    for item in items:
        if item.bloc not in CUSTOM_BLOCS or not _bloc_visible(config, item.bloc):
            continue
        rule = _resolve_rule(rules_by_target, ('item', item.id))
        if rule and not rule.is_visible and not ignore_visibility_rules:
            continue
        price = rule.override_price if (rule and rule.override_price is not None) else item.price
        subtotals[item.bloc] += price
        snapshot.append({
            'bloc': item.bloc,
            'type': 'item',
            'id': item.id,
            'name': item.name,
            'price': str(_q(price)),
        })

    # --- Workshops (paid sessions) ---
    if selected_session_ids and _bloc_visible(config, 'workshops'):
        session_filters = {'id__in': selected_session_ids, 'event': event, 'is_paid': True}
        if not include_inactive:
            session_filters['is_active'] = True
        sessions = Session.objects.filter(**session_filters)
        for session in sessions:
            rule = _resolve_rule(rules_by_target, ('session', str(session.id)))
            if rule and not rule.is_visible and not ignore_visibility_rules:
                continue
            price = rule.override_price if (rule and rule.override_price is not None) else session.price
            subtotals['workshops'] += price
            snapshot.append({
                'bloc': 'workshops',
                'type': 'session',
                'id': str(session.id),
                'name': session.title,
                'price': str(_q(price)),
            })

    total_before = sum(subtotals.values(), Decimal('0'))
    # A bloc counts toward the multi-bloc discount only once its own
    # subtotal is > 0 -- a free item alone in a bloc doesn't unlock the
    # discount tier, the way a paid item in that bloc would. Status is
    # mandatory on every registration and never counts either way, so
    # the real maximum is 3 (Restauration + Workshops + Social Event).
    blocs_with_selection = {b for b in ('restauration', 'workshops', 'social_event') if subtotals[b] > 0}
    if context_blocs_covered:
        blocs_with_selection = blocs_with_selection | {b for b in context_blocs_covered if b in ('restauration', 'workshops', 'social_event')}
    distinct_blocs = len(blocs_with_selection)

    # --- Reductions (additive) ---
    # Period-based pricing is now manual per-item (resolved above via
    # rules), not a percentage -- kept at 0 so total_discount_percent
    # continues to reflect only the bloc-count discount.
    period_percent = Decimal('0')

    blocs_percent = Decimal('0')
    if config.reduction_by_blocs_enabled and total_before > 0:
        blocs_percent = config.blocs_reduction_percent(distinct_blocs)

    total_percent = period_percent + blocs_percent
    if total_percent > Decimal('100'):
        total_percent = Decimal('100')

    total_after = _q(total_before * (Decimal('1') - total_percent / Decimal('100')))

    return {
        'snapshot': snapshot,
        'subtotals': {bloc: str(_q(amount)) for bloc, amount in subtotals.items()},
        'distinct_blocs_count': distinct_blocs,
        'total_before_reduction': _q(total_before),
        'period_discount_percent': _q(period_percent),
        'blocs_discount_percent': _q(blocs_percent),
        'total_discount_percent': _q(total_percent),
        'total_after_reduction': total_after,
        'active_period_id': active_period.id if active_period else None,
    }


def apply_compute_result_to_pending_order(order, result):
    """
    Save a fresh compute_order() result onto a NOT-YET-APPROVED
    RegistrationOrder -- the same fields the event owner's "Modifier les
    blocs" editor writes for its non-approved branch
    (dashboard.views_event_owner.registration_order_blocs_save), factored
    out here so caisse's own "edit a still-pending reservation" action
    (caisse.views.modify_pending_order) saves through the exact same
    path instead of a second copy of this field list that could quietly
    drift from it. Never call this on an 'approved' order -- that case
    has real money/access effects and goes through
    caisse.services.resync_confirmed_registration_order instead.
    """
    order.period_id = result['active_period_id']
    order.items_snapshot = result['snapshot']
    order.subtotals = result['subtotals']
    order.distinct_blocs_count = result['distinct_blocs_count']
    order.total_before_reduction = result['total_before_reduction']
    order.period_discount_percent = result['period_discount_percent']
    order.blocs_discount_percent = result['blocs_discount_percent']
    order.total_discount_percent = result['total_discount_percent']
    order.total_after_reduction = result['total_after_reduction']
    order.save(update_fields=[
        'period', 'items_snapshot', 'subtotals', 'distinct_blocs_count',
        'total_before_reduction', 'period_discount_percent', 'blocs_discount_percent',
        'total_discount_percent', 'total_after_reduction',
    ])


def _target_key(rule):
    return f"item_{rule.target_item_id}" if rule.target_kind == 'item' else f"session_{rule.target_session_id}"


def serialize_period_baseline_rules(event, period):
    """
    Period-only (no status) rules for the given period -- the baseline
    price/visibility for every item (including Status items themselves),
    applied regardless of which Status is picked or before any is picked
    at all. Keyed by target key ('item_<id>'/'session_<id>'). Empty if
    period is None.
    """
    if not period:
        return {}
    result = {}
    for rule in BlocItemStatusRule.objects.filter(period=period, status_item__isnull=True):
        result[_target_key(rule)] = {
            'visible': rule.is_visible,
            'price': str(rule.override_price) if rule.override_price is not None else None,
        }
    return result


def serialize_status_rules_for_period(event, period):
    """
    Effective status-dependent rules for this event scoped to the given
    period (or None for "no period active"), keyed by status item id ->
    target key -> {'visible': bool, 'price': str or None}.

    Precedence, same as compute_order: a rule specific to (status, period)
    wins over a status-only rule that applies across all periods.
    """
    rules_qs = BlocItemStatusRule.objects.filter(status_item__event=event, status_item__isnull=False)
    if period:
        rules_qs = rules_qs.filter(Q(period=period) | Q(period__isnull=True))
    else:
        rules_qs = rules_qs.filter(period__isnull=True)

    grouped = {}
    for rule in rules_qs:
        grouped.setdefault((rule.status_item_id, _target_key(rule)), []).append(rule)

    result = {}
    for (status_id, target_key), candidates in grouped.items():
        chosen = next((r for r in candidates if r.period_id), candidates[0])
        result.setdefault(str(status_id), {})[target_key] = {
            'visible': chosen.is_visible,
            'price': str(chosen.override_price) if chosen.override_price is not None else None,
        }
    return result


def serialize_period_baseline_rules_for_event(event, on_date):
    """Period-only rules for TODAY's active period -- see serialize_period_baseline_rules."""
    try:
        config = event.bloc_config
    except Exception:
        return {}
    if not config.reduction_by_period_enabled:
        return {}
    return serialize_period_baseline_rules(event, get_active_period(event, on_date))


def serialize_status_rules_for_event(event, on_date):
    """Status-dependent rules resolved against TODAY's active period -- see serialize_status_rules_for_period."""
    try:
        config = event.bloc_config
        active_period = get_active_period(event, on_date) if config.reduction_by_period_enabled else None
    except Exception:
        active_period = None
    return serialize_status_rules_for_period(event, active_period)


def serialize_all_periods_preview(event):
    """
    For every configured ReductionPeriod, its baseline (any-status) and
    per-status rules -- lets the registration page preview any period's
    pricing client-side without a round trip. Keyed by period id (string):
    {"<period_id>": {"baseline": {...}, "status": {"<status_id>": {...}}}}.
    Only meaningful when reduction_by_period_enabled; callers should gate
    on that (and on there being at least one period) before using this.
    """
    result = {}
    for period in event.reduction_periods.all():
        result[str(period.id)] = {
            'baseline': serialize_period_baseline_rules(event, period),
            'status': serialize_status_rules_for_period(event, period),
        }
    return result
