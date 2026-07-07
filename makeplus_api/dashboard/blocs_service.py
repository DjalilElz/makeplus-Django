"""
Server-side pricing & discount calculation for the blocs registration cart.

All money math is authoritative here: prices are always re-read from the
database (never trusted from the client), and totals/discounts are recomputed
regardless of anything the browser submitted.
"""
from decimal import Decimal, ROUND_HALF_UP

from events.models import Session
from .models_blocs import BlocItem


TWO_PLACES = Decimal('0.01')

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


def compute_order(event, config, selected_item_ids, selected_session_ids, on_date):
    """
    Compute a cart from the raw selections.

    Args:
        event: Event
        config: EventBlocConfig
        selected_item_ids: iterable of BlocItem ids (custom blocs)
        selected_session_ids: iterable of Session ids (workshops bloc)
        on_date: date used to resolve the period reduction (the submission date)

    Returns dict with subtotals, snapshot, distinct bloc count, discount
    percentages, and totals before/after reduction. Only items belonging to
    the event, active, and inside a *visible* bloc are counted.
    """
    selected_item_ids = [str(i) for i in (selected_item_ids or [])]
    selected_session_ids = [str(i) for i in (selected_session_ids or [])]

    snapshot = []
    subtotals = {bloc: Decimal('0') for bloc in ALL_BLOCS}
    blocs_with_selection = set()

    # --- Custom bloc items ---
    if selected_item_ids:
        items = BlocItem.objects.filter(
            id__in=selected_item_ids, event=event, is_active=True
        )
        for item in items:
            if item.bloc not in CUSTOM_BLOCS or not _bloc_visible(config, item.bloc):
                continue
            subtotals[item.bloc] += item.price
            blocs_with_selection.add(item.bloc)
            snapshot.append({
                'bloc': item.bloc,
                'type': 'item',
                'id': item.id,
                'name': item.name,
                'price': str(_q(item.price)),
            })

    # --- Workshops (paid sessions) ---
    if selected_session_ids and _bloc_visible(config, 'workshops'):
        sessions = Session.objects.filter(
            id__in=selected_session_ids, event=event, is_paid=True
        )
        for session in sessions:
            subtotals['workshops'] += session.price
            blocs_with_selection.add('workshops')
            snapshot.append({
                'bloc': 'workshops',
                'type': 'session',
                'id': str(session.id),
                'name': session.title,
                'price': str(_q(session.price)),
            })

    total_before = sum(subtotals.values(), Decimal('0'))
    distinct_blocs = len(blocs_with_selection)

    # --- Reductions (additive) ---
    period_percent = Decimal('0')
    if config.reduction_by_period_enabled and total_before > 0:
        period = event.reduction_periods.filter(
            start_date__lte=on_date, end_date__gte=on_date
        ).order_by('-discount_percent').first()
        if period:
            period_percent = period.discount_percent

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
    }
