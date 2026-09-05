"""
Views for Caisse (Cash Register) Operators
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import never_cache
from django.db.models import Q
from django.utils import timezone
import json
from decimal import Decimal
import qrcode
from io import BytesIO
import base64

from caisse.models import Caisse, PayableItem, CaisseTransaction
from events.models import Participant, Event
from dashboard.blocs_service import resolve_catalog_prices, _bloc_visible


def _reservation_data(event, payable_items):
    """
    Map registration-form reservations onto this event's PayableItems, so
    the caisse can pre-check what a participant already reserved and tally
    reserved-vs-confirmed counts. No admin review gates this: an order is
    reserved the moment it's submitted and email-verified.

    Deliberately NOT filtered to status='pending' here: orders approved
    under the since-removed admin-review flow (or otherwise carrying a
    stale 'approved' status) can still have items with no actual
    CaisseTransaction behind them -- nothing was really handed out. Only
    'rejected' orders are excluded; _pending_orders_with_payable_ids
    (which this feeds) does the real work of subtracting out whatever a
    completed CaisseTransaction already covers.

    Returns:
        key_to_payable_ids: {(kind, external_id): [payable_item_id, ...]}
        participant_reservations: {participant_id: {(kind, external_id), ...}}
        reservation_participants: {(kind, external_id): {participant_id, ...}}
    where kind is 'item' (BlocItem) or 'session' (paid workshop Session).
    """
    from dashboard.models_blocs import RegistrationOrder

    # Keys are always (kind, str(external_id)): BlocItem ids are ints,
    # Session ids are UUIDs, and items_snapshot JSON round-trips session
    # ids as strings -- casting everything to str keeps both sides
    # comparable (a bare int/UUID vs str mismatch meant session-based
    # workshop reservations, and their price coherence, silently never
    # matched anything).
    key_to_payable_ids = {}
    for item in payable_items:
        key = None
        if item.bloc_item_id:
            key = ('item', str(item.bloc_item_id))
        elif item.session_id:
            key = ('session', str(item.session_id))
        if key:
            key_to_payable_ids.setdefault(key, []).append(item.id)

    reserved_orders = RegistrationOrder.objects.exclude(status='rejected').filter(
        event=event, participant__isnull=False
    ).only('participant_id', 'items_snapshot')

    participant_reservations = {}
    reservation_participants = {}
    for order in reserved_orders:
        keys = set()
        for entry in order.items_snapshot or []:
            kind = entry.get('type')
            ext_id = entry.get('id')
            if kind in ('item', 'session') and ext_id is not None:
                key = (kind, str(ext_id))
                keys.add(key)
                reservation_participants.setdefault(key, set()).add(order.participant_id)
        if keys:
            participant_reservations.setdefault(order.participant_id, set()).update(keys)

    return key_to_payable_ids, participant_reservations, reservation_participants


def _pending_orders_with_payable_ids(participant, event, key_to_payable_ids=None):
    """
    This participant's MOST RECENT non-rejected RegistrationOrder for this
    event, with the set of mirrored PayableItem ids that haven't actually
    been confirmed (no completed CaisseTransaction covers them) yet. A bloc
    order's discount applies to the order as a whole, so it must be
    confirmed all at once -- see its use in process_transaction().

    Only the latest order is considered -- a participant can have several
    RegistrationOrders if they submitted the registration form more than
    once (a real, common occurrence, not blocked at submission time); the
    newest submission is treated as the authoritative one and older
    duplicates are ignored here, both for display and for what can be
    confirmed at the caisse.

    Whether an item still needs confirming is decided purely by the
    absence of a completed CaisseTransaction for it -- not by order.status,
    which can be stale 'approved' from the since-removed admin-review flow
    even though nothing was ever actually handed out at the counter.

    key_to_payable_ids: optional, from a caller's own _reservation_data()
    call. It only depends on `event` (not on `participant`), so a caller
    looping over many participants (caisse_dashboard) can compute it once
    and pass it in here instead of this function re-scanning every
    RegistrationOrder for the whole event on every single call -- that
    per-participant re-scan was the main cause of caisse dashboard/login
    slowness on events with many participants. Recomputed as before if
    omitted, so the other (single-participant) call sites are unaffected.

    Returns: [(RegistrationOrder, {payable_item_id, ...})] -- at most one
    entry (the latest order), omitted entirely if it has nothing pending.
    """
    from dashboard.models_blocs import RegistrationOrder

    if key_to_payable_ids is None:
        payable_items = PayableItem.objects.filter(event=event, is_active=True)
        key_to_payable_ids, _, _ = _reservation_data(event, payable_items)

    confirmed_ids = set()
    for txn in CaisseTransaction.objects.filter(
        participant=participant, status='completed'
    ).prefetch_related('items'):
        confirmed_ids.update(txn.items.values_list('id', flat=True))

    order = RegistrationOrder.objects.exclude(status='rejected').filter(
        event=event, participant=participant
    ).order_by('-created_at').first()

    result = []
    if order:
        keys = set()
        for entry in order.items_snapshot or []:
            kind = entry.get('type')
            ext_id = entry.get('id')
            if kind in ('item', 'session') and ext_id is not None:
                keys.add((kind, str(ext_id)))
        payable_ids = set()
        for key in keys:
            payable_ids.update(key_to_payable_ids.get(key, []))
        pending_ids = payable_ids - confirmed_ids
        if pending_ids:
            result.append((order, pending_ids))
    return result


def _pending_orders_with_payable_ids_bulk(participants, event, key_to_payable_ids, participant_paid_items):
    """
    Bulk version of _pending_orders_with_payable_ids() for caisse_dashboard's
    reserved-items summary panel, which needs this for every participant
    with a pending reservation -- calling the single-participant version in
    a loop still ran 2-3 queries *per participant* (a CaisseTransaction
    query + a per-transaction .items query that bypasses prefetch, plus a
    RegistrationOrder query), which was still enough to time out the whole
    dashboard/login request on events with many participants even after
    fixing the bigger _reservation_data() re-scan. This does the whole
    thing in exactly one query.

    Only the latest order per participant is considered -- same reasoning
    as _pending_orders_with_payable_ids(): a participant can have several
    RegistrationOrders if they submitted more than once, and the newest
    submission is treated as authoritative.

    participant_paid_items: {str(participant_id): [payable_item_id, ...]}
    -- caisse_dashboard already builds this correctly (from its own
    prefetch_related() on event_registrations), so it's reused here
    instead of re-querying CaisseTransaction per participant. Same
    semantics as _pending_orders_with_payable_ids()'s confirmed_ids
    (all of a participant's completed transactions, not event-scoped --
    harmless here since payable_ids is already scoped to this event via
    key_to_payable_ids).

    Returns: {participant_id: [(RegistrationOrder, {payable_item_id, ...})]}
    -- at most one entry (the latest order) per participant, participants
    with nothing pending are omitted.
    """
    from dashboard.models_blocs import RegistrationOrder

    participant_ids = [p.id for p in participants]
    latest_order_by_participant = {}
    for order in RegistrationOrder.objects.exclude(status='rejected').filter(
        event=event, participant_id__in=participant_ids
    ).order_by('-created_at'):
        # First order seen per participant, in -created_at order, is the
        # latest -- setdefault skips any older ones that follow.
        latest_order_by_participant.setdefault(order.participant_id, order)

    result = {}
    for participant in participants:
        order = latest_order_by_participant.get(participant.id)
        if order is None:
            continue
        confirmed_ids = set(participant_paid_items.get(str(participant.id), []))
        keys = set()
        for entry in order.items_snapshot or []:
            kind = entry.get('type')
            ext_id = entry.get('id')
            if kind in ('item', 'session') and ext_id is not None:
                keys.add((kind, str(ext_id)))
        payable_ids = set()
        for key in keys:
            payable_ids.update(key_to_payable_ids.get(key, []))
        pending_ids = payable_ids - confirmed_ids
        if pending_ids:
            result[participant.id] = [(order, pending_ids)]
    return result


def _participant_snapshot_prices_bulk(participants, event, key_to_payable_ids):
    """
    Each participant's PayableItem prices exactly as locked in on their own
    (latest, non-rejected) RegistrationOrder -- the frozen, status-correct
    amount the registration form itself charged. The catalog's generic
    live price (resolve_catalog_prices(), called once for the whole
    dashboard with no particular participant in mind) can't know which
    Status any given participant actually picked, so for an item whose
    price varies by Status it can show a different amount than what this
    participant's own order actually has -- reported as the caisse
    showing "Gratuit" for an item the event owner's dashboard shows was
    charged a real price. Used to override the catalog badge for exactly
    the currently-selected participant's own items; anything outside
    their order still falls back to the generic catalog price.

    Same "only the latest order" rule as _pending_orders_with_payable_ids
    -- a participant can have several RegistrationOrders if they
    submitted more than once, and the newest is authoritative.

    Also returns each participant's own Status BlocItem id (same
    resolution process_transaction already uses as existing_status_item_id
    when pricing a brand-new item added at the caisse today) -- the
    caller uses it to also correctly live-price items OUTSIDE this
    participant's own order under their actual Status, instead of the
    generic no-particular-participant catalog price.

    Returns ({str(participant_id): {payable_item_id: price_str}},
             {str(participant_id): status_bloc_item_id}).
    """
    from dashboard.models_blocs import RegistrationOrder

    participant_ids = [p.id for p in participants]
    latest_order_by_participant = {}
    for order in RegistrationOrder.objects.exclude(status='rejected').filter(
        event=event, participant_id__in=participant_ids
    ).order_by('-created_at').only('participant_id', 'items_snapshot'):
        latest_order_by_participant.setdefault(order.participant_id, order)

    prices_result = {}
    status_result = {}
    for participant_id, order in latest_order_by_participant.items():
        prices = {}
        status_item_id = None
        for entry in order.items_snapshot or []:
            kind = entry.get('type')
            ext_id = entry.get('id')
            price = entry.get('price')
            if entry.get('bloc') == 'status' and ext_id is not None:
                status_item_id = ext_id
            if kind not in ('item', 'session') or ext_id is None or price is None:
                continue
            for payable_id in key_to_payable_ids.get((kind, str(ext_id)), []):
                prices[payable_id] = price
        if prices:
            prices_result[str(participant_id)] = prices
        if status_item_id is not None:
            status_result[str(participant_id)] = status_item_id
    return prices_result, status_result


def _mark_participant_present(participant, event):
    """
    Set the same event-wide check-in flag/timestamp the event owner's own
    participant list already shows (events.models.ParticipantEventRegistration
    .is_checked_in/checked_in_at) -- this is deliberately the one shared
    signal for "has this person physically shown up", not a caisse-only
    concept, so a caisse action and a controller's badge scan both feed
    the same place. Only writes if not already checked in, so an earlier
    genuine arrival timestamp (e.g. from a badge scan at the door) is
    never overwritten by a later caisse visit.
    """
    from events.models import ParticipantEventRegistration
    ParticipantEventRegistration.objects.filter(
        participant=participant, event=event, is_checked_in=False
    ).update(is_checked_in=True, checked_in_at=timezone.now())


def caisse_required(view_func):
    """Decorator to check if caisse is logged in"""
    def wrapper(request, *args, **kwargs):
        caisse_id = request.session.get('caisse_id')
        if not caisse_id:
            messages.warning(request, 'Veuillez vous connecter pour continuer.')
            return redirect('caisse:login')
        
        try:
            caisse = Caisse.objects.select_related('event').get(id=caisse_id, is_active=True)
            request.caisse = caisse
        except Caisse.DoesNotExist:
            del request.session['caisse_id']
            messages.error(request, 'Votre session de caisse est invalide. Veuillez vous reconnecter.')
            return redirect('caisse:login')
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


# ==================== Authentication ====================

def caisse_login(request):
    """Login page for caisse operators"""
    if request.session.get('caisse_id'):
        return redirect('caisse:dashboard')
    
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        try:
            caisse = Caisse.objects.get(email=email, is_active=True)
            if caisse.check_password(password):
                request.session['caisse_id'] = caisse.id
                request.session['caisse_name'] = caisse.name
                messages.success(request, f'Bienvenue à {caisse.name} !')
                return redirect('caisse:dashboard')
            else:
                messages.error(request, 'E-mail ou mot de passe invalide.')
        except Caisse.DoesNotExist:
            messages.error(request, 'E-mail ou mot de passe invalide.')
    
    return render(request, 'caisse/login.html')


@caisse_required
def caisse_logout(request):
    """Logout caisse operator"""
    caisse_name = request.session.get('caisse_name', 'Caisse')
    del request.session['caisse_id']
    if 'caisse_name' in request.session:
        del request.session['caisse_name']
    messages.success(request, f'Déconnecté de {caisse_name}.')
    return redirect('caisse:login')


# ==================== Dashboard ====================

@never_cache
@caisse_required
def caisse_dashboard(request):
    """Main dashboard for caisse operators"""
    caisse = request.caisse
    event = caisse.event
    
    # Get payable items for this event
    payable_items = PayableItem.objects.filter(
        event=event,
        is_active=True
    ).select_related('session', 'bloc_item').order_by('item_type', 'name')

    # Reservations made via the (bloc-enabled) registration form -- who
    # reserved what, so it can be pre-checked/tallied at the caisse.
    key_to_payable_ids, participant_reservations, reservation_participants = _reservation_data(
        event, payable_items
    )

    # Live-current prices, resolved through BlocItemStatusRule exactly like
    # the registration form (dashboard.blocs_service.resolve_catalog_prices)
    # -- PayableItem.price is only a snapshot taken when the row was first
    # created and has no way to reflect a price override added/changed
    # afterward, so it drifts from what the registration page actually
    # charges. Applied below to keep the catalog display (and any item not
    # already covered by a frozen order/reservation amount) coherent with
    # the live pricing engine instead of that stale snapshot.
    from dashboard.models_blocs import EventBlocConfig
    try:
        bloc_config = event.bloc_config
    except EventBlocConfig.DoesNotExist:
        bloc_config = None
    live_prices = resolve_catalog_prices(event, bloc_config, timezone.now().date()) if bloc_config else {}

    # Precompute, in one query, which participants have a completed
    # CaisseTransaction covering each payable item -- both branches below
    # used to run their own "CaisseTransaction.objects.filter(items=item)"
    # query per item (2 queries x N payable items); this replaces that
    # with a single upfront query grouped by item.
    item_confirmed_participant_ids = {}
    for row in CaisseTransaction.objects.filter(
        status='completed', items__in=payable_items
    ).values('items__id', 'participant_id').distinct():
        item_confirmed_participant_ids.setdefault(row['items__id'], set()).add(row['participant_id'])

    # Calculate capacity info for each payable item linked to a session, and
    # reserved/confirmed counts for items that come from a registration bloc
    # (or a session that's also offered as a bloc workshop).
    payable_items_with_capacity = []
    for item in payable_items:
        data_bloc = None
        if item.bloc_item_id:
            data_bloc = item.bloc_item.bloc
            live = live_prices.get(('item', item.bloc_item_id))
        elif item.session_id:
            data_bloc = 'workshops'
            live = live_prices.get(('session', str(item.session_id)))
        else:
            live = None

        # An item some participant actually has locked into their own
        # registration order is never hidden, regardless of its current
        # visibility rule -- e.g. a Status like "Invité" that's normally
        # hidden from the public self-registration form (only assignable
        # by the event owner directly) but that a real participant's
        # order already includes. Hiding it entirely made that
        # participant's own reservation impossible to confirm at the
        # caisse: process_transaction requires every item bundled into
        # the same order to be confirmed together, but the operator had
        # no checkbox to confirm it with, since it never rendered here.
        reservation_key = None
        if item.bloc_item_id:
            reservation_key = ('item', str(item.bloc_item_id))
        elif item.session_id:
            reservation_key = ('session', str(item.session_id))
        is_reserved_by_someone = bool(reservation_key and reservation_participants.get(reservation_key))

        # Only offer items the registration form itself currently offers.
        # A PayableItem is a separately-maintained row that mirrors a
        # BlocItem/Session at the time someone created it -- if that
        # BlocItem/Session was later deactivated, hidden by a
        # BlocItemStatusRule, or its whole bloc got turned off
        # (EventBlocConfig.show_*), nothing here removes/deactivates the
        # PayableItem to match, so it kept showing up (and staying
        # payable) at the caisse after disappearing from registration. A
        # plain caisse-only item with no bloc_item/session link at all
        # never had a registration-page counterpart to begin with. Only
        # enforced when this event actually uses blocs (bloc_config set)
        # -- otherwise there is no registration-page catalog to compare
        # against, so every active PayableItem is left as-is.
        if bloc_config and not is_reserved_by_someone and (
            not data_bloc or live is None or not live['visible'] or not _bloc_visible(bloc_config, data_bloc)
        ):
            continue

        # In-memory only (never saved) -- makes every place that already
        # renders item.price (the catalog badge, the JS selection preview)
        # show the live, rule-resolved price instead of the stored
        # snapshot, with no template changes needed.
        if live is not None:
            item.price = live['price']

        item_data = {
            'item': item,
            'data_bloc': data_bloc,
            'has_capacity_limit': False,
            'max_participants': None,
            'registered_count': 0,
            'available_spots': None,
            'is_full': False,
            'capacity_percentage': 0,
            'is_reservable': False,
            'reserved_count': 0,
            'confirmed_count': 0,
        }

        if item.session:
            session = item.session
            if session.max_participants:
                # Count how many participants have paid for this session
                registered_count = len(item_confirmed_participant_ids.get(item.id, set()))

                available_spots = session.max_participants - registered_count
                is_full = available_spots <= 0
                capacity_percentage = int((registered_count / session.max_participants) * 100)

                item_data.update({
                    'has_capacity_limit': True,
                    'max_participants': session.max_participants,
                    'registered_count': registered_count,
                    'available_spots': max(0, available_spots),
                    'is_full': is_full,
                    'capacity_percentage': capacity_percentage
                })

        reservation_key = None
        if item.bloc_item_id:
            reservation_key = ('item', str(item.bloc_item_id))
        elif item.session_id:
            reservation_key = ('session', str(item.session_id))

        if reservation_key:
            reserved_participant_ids = reservation_participants.get(reservation_key, set())
            confirmed_participant_ids = item_confirmed_participant_ids.get(item.id, set())
            item_data.update({
                'is_reservable': True,
                'reserved_count': len(reserved_participant_ids - confirmed_participant_ids),
                'confirmed_count': len(confirmed_participant_ids),
            })

        payable_items_with_capacity.append(item_data)

    # Group items into blocs the same way the registration form does --
    # same order (status, restauration, social_event, then workshops last),
    # same select_mode (single = radio, multiple = checkbox) per bloc.
    # Anything outside the bloc system (plain dinner/access/other items, or
    # sessions when the event doesn't use blocs at all) falls into "Other".
    # (bloc_config already resolved above, for live_prices.)
    from dashboard.models_blocs import CUSTOM_BLOC_CHOICES

    bloc_groups = []
    grouped_item_ids = set()
    if bloc_config:
        for bloc_key, bloc_label in CUSTOM_BLOC_CHOICES:
            bloc_item_data = [d for d in payable_items_with_capacity if d['data_bloc'] == bloc_key]
            if bloc_item_data:
                select_mode = bloc_config.select_mode_for(bloc_key)
                bloc_groups.append({
                    'label': bloc_label,
                    'select_mode': select_mode,
                    'input_type': 'radio' if select_mode == 'single' else 'checkbox',
                    'radio_name': f'bloc_{bloc_key}',
                    'items': bloc_item_data,
                })
                grouped_item_ids.update(d['item'].id for d in bloc_item_data)

        if bloc_config.show_workshops:
            workshop_item_data = [d for d in payable_items_with_capacity if d['data_bloc'] == 'workshops']
            if workshop_item_data:
                bloc_groups.append({
                    'label': 'Workshops',
                    'select_mode': 'multiple',
                    'input_type': 'checkbox',
                    'radio_name': '',
                    'items': workshop_item_data,
                })
                grouped_item_ids.update(d['item'].id for d in workshop_item_data)

    other_items = [d for d in payable_items_with_capacity if d['item'].id not in grouped_item_ids]

    # Discount config for live client-side recompute of newly-added bloc
    # items -- bloc-count% only, matching compute_order()
    # (dashboard/blocs_service.py) exactly: period-based pricing is now
    # manual per-item (BlocItemStatusRule overrides), not a cart-wide
    # percentage, so compute_order always forces period_percent to 0.
    # This used to also add a period%, which no longer exists server-side
    # -- the preview showed a bigger discount than what actually got
    # charged. Removed rather than reintroduced, to stay coherent with
    # the real pricing engine instead of re-diverging from it again.
    blocs_enabled = bool(bloc_config and bloc_config.reduction_by_blocs_enabled)
    bloc_pct = {
        2: str(bloc_config.reduction_2_blocs) if bloc_config else '0',
        3: str(bloc_config.reduction_3_blocs) if bloc_config else '0',
        4: str(bloc_config.reduction_4_blocs) if bloc_config else '0',
    }

    # Statistics
    total_amount = caisse.get_total_amount()
    total_participants = caisse.get_total_participants()
    transaction_count = caisse.get_transaction_count()
    
    # Get only participants (users with role 'participant') for this event
    from events.models import UserEventAssignment, ParticipantEventRegistration
    participant_user_ids = UserEventAssignment.objects.filter(
        event=event,
        role='participant'
    ).values_list('user_id', flat=True)
    
    # Get participants registered for this event via ParticipantEventRegistration
    event_registrations = ParticipantEventRegistration.objects.filter(
        event=event,
        participant__user_id__in=participant_user_ids
    ).select_related('participant__user').prefetch_related(
        'participant__caisse_transactions__items',
        'participant__caisse_transactions__caisse'
    ).order_by('participant__user__first_name', 'participant__user__last_name')
    
    # Extract participants from registrations
    all_participants = [reg.participant for reg in event_registrations]
    
    # Build a dictionary of participant paid items for quick lookup.
    # .all() (not .filter()/.values_list(), which would each issue a fresh
    # query) so this reads from the prefetch_related() above instead of
    # re-querying per participant/transaction.
    participant_paid_items = {}
    for participant in all_participants:
        completed_transactions = [
            t for t in participant.caisse_transactions.all() if t.status == 'completed'
        ]
        paid_item_ids = set()
        for transaction in completed_transactions:
            paid_item_ids.update(item.id for item in transaction.items.all())
        participant_paid_items[str(participant.id)] = list(paid_item_ids)

    # Items reserved via the registration form (approved bloc orders) that
    # aren't confirmed yet -- these get pre-checked (but not disabled) so
    # the caisse operator can just confirm the transaction.
    participant_reserved_items = {}
    for participant in all_participants:
        reserved_keys = participant_reservations.get(participant.id, set())
        reserved_payable_ids = set()
        for key in reserved_keys:
            reserved_payable_ids.update(key_to_payable_ids.get(key, []))
        already_confirmed = set(participant_paid_items.get(str(participant.id), []))
        pending = reserved_payable_ids - already_confirmed
        if pending:
            participant_reserved_items[str(participant.id)] = list(pending)

    # Discount summary for participants with a pending bloc reservation, so
    # the operator sees the real (already paid) amount, not the raw catalog
    # sum -- e.g. "15000 DZD -25% -> already paid 11250 DZD".
    participants_with_pending = [
        p for p in all_participants if str(p.id) in participant_reserved_items
    ]
    pending_orders_by_participant = _pending_orders_with_payable_ids_bulk(
        participants_with_pending, event, key_to_payable_ids, participant_paid_items
    )
    participant_reserved_summary = {}
    for participant in participants_with_pending:
        pending_orders = pending_orders_by_participant.get(participant.id)
        if pending_orders:
            participant_reserved_summary[str(participant.id)] = [
                {
                    'total_before': str(order.total_before_reduction),
                    'period_discount_percent': str(order.period_discount_percent),
                    'blocs_discount_percent': str(order.blocs_discount_percent),
                    'discount_percent': str(order.total_discount_percent),
                    'total_after': str(order.total_after_reduction),
                    'payable_ids': list(pending_ids),
                    # Whether this reservation was ever actually paid for
                    # (a real bank receipt on file) -- if not, confirming
                    # it collects real cash right now and must say so
                    # instead of claiming it's "already paid by bank
                    # transfer" (see process_transaction's receipt_file
                    # check for the matching server-side fix).
                    'has_receipt': bool(order.receipt_file),
                }
                for order, pending_ids in pending_orders
            ]

    participant_item_prices, participant_status_ids = _participant_snapshot_prices_bulk(
        all_participants, event, key_to_payable_ids
    )

    # For every distinct Status actually present among these participants,
    # the live catalog price/visibility resolved AS that Status -- lets the
    # caisse show the correct price for an item outside a participant's own
    # order too (not just their already-reserved items, handled above via
    # their order's own snapshot), instead of the generic no-particular-
    # participant price, which can be hijacked by some OTHER Status's own
    # override (see resolve_catalog_prices's docstring).
    status_catalog = {}
    if bloc_config:
        for status_id in set(participant_status_ids.values()):
            live = resolve_catalog_prices(
                event, bloc_config, timezone.now().date(), context_status_item_id=status_id
            )
            prices_by_payable_id = {}
            for (kind, ext_id), data in live.items():
                for payable_id in key_to_payable_ids.get((kind, str(ext_id)), []):
                    prices_by_payable_id[payable_id] = str(data['price'])
            status_catalog[str(status_id)] = prices_by_payable_id

    # Recent transactions
    recent_transactions = caisse.transactions.filter(
        status='completed'
    ).select_related('participant__user').prefetch_related('items').order_by('-created_at')[:10]

    # Everyone checked in for this event -- from a completed transaction
    # here (any amount, including 0 DZD) or an explicit "Marquer comme
    # présent" click (see _mark_participant_present), same as a badge
    # controller's scan at the door would set. Event-wide, not scoped to
    # this one caisse station, since it's really "who has shown up",
    # not "who this specific counter processed".
    from events.models import ParticipantEventRegistration
    presence_list = ParticipantEventRegistration.objects.filter(
        event=event, is_checked_in=True
    ).select_related('participant__user').order_by('-checked_in_at')[:10]

    context = {
        'caisse': caisse,
        'event': event,
        'payable_items': payable_items,
        'payable_items_with_capacity': payable_items_with_capacity,
        'bloc_groups': bloc_groups,
        'other_items': other_items,
        'total_amount': total_amount,
        'total_participants': total_participants,
        'transaction_count': transaction_count,
        'all_participants': all_participants,
        'participant_paid_items_json': json.dumps(participant_paid_items),
        'participant_reserved_items_json': json.dumps(participant_reserved_items),
        'participant_reserved_summary_json': json.dumps(participant_reserved_summary),
        'participant_item_prices_json': json.dumps(participant_item_prices),
        'participant_status_ids_json': json.dumps(participant_status_ids),
        'status_catalog_json': json.dumps(status_catalog),
        'blocs_enabled_json': json.dumps(blocs_enabled),
        'bloc_pct_json': json.dumps(bloc_pct),
        'recent_transactions': recent_transactions,
        'presence_list': presence_list,
    }
    
    return render(request, 'caisse/dashboard.html', context)


# ==================== Participant Search ====================

@caisse_required
@require_http_methods(["GET"])
def search_participant(request):
    """Search for participant by name, email, or QR code"""
    query = request.GET.get('q', '').strip()
    caisse = request.caisse
    event = caisse.event
    
    if not query:
        return JsonResponse({'success': False, 'message': 'Please enter a search term'})
    
    # Get only users with 'participant' role
    from events.models import UserEventAssignment, ParticipantEventRegistration
    participant_user_ids = UserEventAssignment.objects.filter(
        event=event,
        role='participant'
    ).values_list('user_id', flat=True)
    
    # Search participants with participant role only - get via ParticipantEventRegistration
    event_registrations = ParticipantEventRegistration.objects.filter(
        event=event,
        participant__user_id__in=participant_user_ids
    ).filter(
        Q(participant__user__first_name__icontains=query) |
        Q(participant__user__last_name__icontains=query) |
        Q(participant__user__email__icontains=query) |
        Q(participant__user__username__icontains=query) |
        Q(participant__qr_code_data__icontains=query)
    ).select_related('participant__user').prefetch_related('participant__caisse_transactions')[:10]
    
    if not event_registrations.exists():
        return JsonResponse({'success': False, 'message': 'No participants found'})
    
    results = []
    for registration in event_registrations:
        participant = registration.participant
        # Check if already checked in
        has_transaction = participant.caisse_transactions.filter(
            caisse=caisse,
            status='completed'
        ).exists()
        
        # Get previous transactions
        transaction_count = participant.caisse_transactions.filter(
            status='completed'
        ).count()
        
        results.append({
            'id': participant.id,
            'name': participant.user.get_full_name() or participant.user.username,
            'email': participant.user.email,
            'qr_code': participant.qr_code_data,
            'checked_in': has_transaction,
            'transaction_count': transaction_count
        })
    
    return JsonResponse({'success': True, 'participants': results})


@caisse_required
@require_http_methods(["GET"])
def get_participant_paid_items(request, participant_id):
    """Get list of items already paid by a participant"""
    caisse = request.caisse
    
    try:
        participant = Participant.objects.get(id=participant_id)
        # Verify participant is registered for this event
        if not participant.is_registered_for_event(caisse.event):
            return JsonResponse({'success': False, 'message': 'Participant not registered for this event'})
    except Participant.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Participant not found'})
    
    # Get all completed transactions for this participant
    completed_transactions = CaisseTransaction.objects.filter(
        participant=participant,
        status='completed'
    ).prefetch_related('items')

    # Collect all paid item IDs
    paid_item_ids = set()
    for transaction in completed_transactions:
        paid_item_ids.update(transaction.items.values_list('id', flat=True))

    # Items reserved via the registration form (approved bloc orders) not
    # yet confirmed at the caisse.
    payable_items = PayableItem.objects.filter(event=caisse.event, is_active=True)
    key_to_payable_ids, participant_reservations, _ = _reservation_data(caisse.event, payable_items)
    reserved_keys = participant_reservations.get(participant.id, set())
    reserved_item_ids = set()
    for key in reserved_keys:
        reserved_item_ids.update(key_to_payable_ids.get(key, []))
    reserved_item_ids -= paid_item_ids

    return JsonResponse({
        'success': True,
        'paid_items': list(paid_item_ids),
        'reserved_items': list(reserved_item_ids)
    })


# ==================== Transaction Processing ====================

@caisse_required
@require_http_methods(["POST"])
def process_transaction(request):
    """Process a payment transaction"""
    import json
    
    caisse = request.caisse
    
    # Parse JSON body
    try:
        data = json.loads(request.body)
        participant_id = data.get('participant_id')
        item_ids = data.get('items', [])
        notes = data.get('notes', '')
        action = data.get('action', 'process_and_print')  # Default to process_and_print
    except json.JSONDecodeError:
        # Fallback to POST data
        participant_id = request.POST.get('participant_id')
        item_ids = request.POST.getlist('items[]')
        notes = request.POST.get('notes', '')
        action = request.POST.get('action', 'process_and_print')
    
    if not participant_id:
        return JsonResponse({'success': False, 'message': 'Participant ID required'})
    
    try:
        participant = Participant.objects.get(id=participant_id)
        # Verify participant is registered for this event
        if not participant.is_registered_for_event(caisse.event):
            return JsonResponse({'success': False, 'message': 'Participant not registered for this event'})
    except Participant.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Participant not found'})
    
    # For print_badge action, we don't need items
    if action == 'print_badge':
        return JsonResponse({
            'success': True,
            'message': 'Badge print initiated',
            'action': 'print_badge'
        })
    
    # For process and process_and_print, items are normally required -- but
    # a participant with nothing left to confirm (everything they
    # registered is already paid/confirmed, or they never selected
    # anything at all) isn't an error case, they're just here to be
    # marked present: no CaisseTransaction, just the same check-in
    # flag/timestamp the event owner's own participant list already
    # shows. If they actually DO still have something pending that
    # simply wasn't selected, refuse instead of silently skipping it --
    # this button never substitutes for a real confirmation.
    if not item_ids:
        pending = _pending_orders_with_payable_ids(participant, caisse.event)
        if pending:
            pending_payable_ids = set()
            for _, ids in pending:
                pending_payable_ids |= ids
            pending_names = list(
                PayableItem.objects.filter(id__in=pending_payable_ids).values_list('name', flat=True)
            )
            return JsonResponse({
                'success': False,
                'message': 'This participant still has a pending reservation to confirm: '
                + ', '.join(pending_names)
            })
        _mark_participant_present(participant, caisse.event)
        return JsonResponse({
            'success': True,
            'message': 'Participant marked present',
            'action': action,
            'marked_present_only': True,
        })
    
    # Get items and calculate total
    items = PayableItem.objects.filter(id__in=item_ids, event=caisse.event, is_active=True)
    if not items.exists():
        return JsonResponse({'success': False, 'message': 'Invalid items selected'})
    
    # Check capacity for each item linked to a session
    capacity_errors = []
    for item in items:
        if item.session and item.session.max_participants:
            # Count current registrations for this session
            registered_count = CaisseTransaction.objects.filter(
                status='completed',
                items=item
            ).values('participant').distinct().count()
            
            available_spots = item.session.max_participants - registered_count
            
            if available_spots <= 0:
                capacity_errors.append(f"{item.name} is full (0/{item.session.max_participants} spots available)")
    
    # If any capacity errors, return them
    if capacity_errors:
        return JsonResponse({
            'success': False,
            'message': 'Cannot process transaction:\n' + '\n'.join(capacity_errors)
        })

    # Enforce single-choice blocs the same way the registration form does --
    # reject if more than one item from a single-select bloc is chosen
    # together (whether reserved, newly added, or a mix of both).
    from dashboard.models_blocs import EventBlocConfig, CUSTOM_BLOC_CHOICES
    bloc_labels = dict(CUSTOM_BLOC_CHOICES)
    try:
        bloc_config_for_validation = caisse.event.bloc_config
    except EventBlocConfig.DoesNotExist:
        bloc_config_for_validation = None

    if bloc_config_for_validation:
        picked_by_bloc = {}
        for item in items:
            if item.bloc_item_id:
                picked_by_bloc.setdefault(item.bloc_item.bloc, []).append(item.name)

        select_mode_errors = []
        for bloc_key, names in picked_by_bloc.items():
            if bloc_config_for_validation.select_mode_for(bloc_key) == 'single' and len(names) > 1:
                select_mode_errors.append(
                    f"Please select only one option in {bloc_labels.get(bloc_key, bloc_key)}: {', '.join(names)}"
                )
        if select_mode_errors:
            return JsonResponse({
                'success': False,
                'message': 'Cannot process transaction:\n' + '\n'.join(select_mode_errors)
            })

    selected_ids = set(items.values_list('id', flat=True))

    # A bloc registration's discount is computed once, on the whole order --
    # so its reserved items must be confirmed together, at the exact amount
    # already paid by bank transfer (not re-summed from raw catalog prices).
    pending_orders = _pending_orders_with_payable_ids(participant, caisse.event)

    bank_transfer_amount = Decimal('0')
    bank_transfer_before = Decimal('0')
    bank_transfer_item_ids = set()
    # A reservation with no receipt_file was never actually paid for --
    # either this event doesn't require payment proof at all
    # (EventBlocConfig.require_payment_proof=False) or the item was free
    # when they registered. Confirming it here is the participant's FIRST
    # real payment, collected as cash right now -- it must NOT be treated
    # like a genuine bank-transfer reservation (money already received
    # elsewhere, excluded from what this transaction records), or a real
    # cash payment silently gets recorded as 0. Charged at the exact
    # amount already quoted to the operator/participant
    # (order.total_after_reduction) rather than a fresh live recompute
    # that could drift from what was promised (e.g. a pricing period
    # changing between registration and the caisse visit).
    unpaid_order_amount = Decimal('0')
    unpaid_order_before = Decimal('0')
    unpaid_order_item_ids = set()
    fully_confirmed_orders = []
    bank_transfer_breakdown_parts = []
    unpaid_order_breakdown_parts = []
    incomplete_order_errors = []
    for order, pending_ids in pending_orders:
        if not (pending_ids & selected_ids):
            continue  # this reservation isn't part of this transaction
        missing_ids = pending_ids - selected_ids
        if missing_ids:
            missing_names = list(
                PayableItem.objects.filter(id__in=missing_ids).values_list('name', flat=True)
            )
            incomplete_order_errors.append(
                f"Please also confirm: {', '.join(missing_names)} "
                "(reserved together in the same registration and discounted as one)."
            )
            continue
        fully_confirmed_orders.append(order)

        detail = f"{order.total_before_reduction} DZD"
        if order.total_discount_percent > 0:
            pieces = []
            if order.period_discount_percent > 0:
                pieces.append(f"period {order.period_discount_percent}%")
            if order.blocs_discount_percent > 0:
                pieces.append(f"blocs {order.blocs_discount_percent}%")
            reduction = f"-{order.total_discount_percent}%"
            if pieces:
                reduction += f" ({' + '.join(pieces)})"
            detail += f" {reduction}"
        detail += f" -> {order.total_after_reduction} DZD"

        if order.receipt_file:
            bank_transfer_amount += order.total_after_reduction
            bank_transfer_before += order.total_before_reduction
            bank_transfer_item_ids |= pending_ids
            bank_transfer_breakdown_parts.append(detail)
        else:
            unpaid_order_amount += order.total_after_reduction
            unpaid_order_before += order.total_before_reduction
            unpaid_order_item_ids |= pending_ids
            unpaid_order_breakdown_parts.append(detail)

    if incomplete_order_errors:
        return JsonResponse({
            'success': False,
            'message': 'Cannot process transaction:\n' + '\n'.join(incomplete_order_errors)
        })

    cash_items = [
        item for item in items
        if item.id not in bank_transfer_item_ids and item.id not in unpaid_order_item_ids
    ]
    bank_transfer_items = [item for item in items if item.id in bank_transfer_item_ids]
    unpaid_order_items = [item for item in items if item.id in unpaid_order_item_ids]

    # New bloc items the operator adds today (not part of any existing
    # reservation) are treated the same as if picked on the registration
    # form: recompute the bloc-count/period discount across just this new
    # selection, using the exact same engine the form uses.
    from dashboard.models_blocs import EventBlocConfig, RegistrationOrder
    from dashboard.blocs_service import compute_order

    # If this participant already has a Status locked in from an earlier
    # (non-rejected) reservation, status-dependent rules for it still apply
    # to brand-new items added today, even though they aren't re-picking
    # Status right now.
    existing_status_item_id = None
    for order in RegistrationOrder.objects.filter(
        event=caisse.event, participant=participant
    ).exclude(status='rejected').only('items_snapshot'):
        for entry in order.items_snapshot or []:
            if entry.get('bloc') == 'status':
                existing_status_item_id = entry.get('id')
                break
        if existing_status_item_id:
            break

    new_bloc_keys = {}
    plain_cash_items = []
    for item in cash_items:
        if item.bloc_item_id:
            key = ('item', str(item.bloc_item_id))
        elif item.session_id:
            key = ('session', str(item.session_id))
        else:
            plain_cash_items.append(item)
            continue
        new_bloc_keys[key] = item

    recomputed_bloc_amount = Decimal('0')
    recomputed_bloc_before = Decimal('0')
    recomputed_bloc_items = []
    recomputed_bloc_detail = ''
    if new_bloc_keys:
        try:
            config = caisse.event.bloc_config
        except EventBlocConfig.DoesNotExist:
            config = None

        if config:
            # Blocs the participant already has a paid selection in --
            # their own price stays exactly as already set (bank-transfer
            # orders keep their frozen total_after_reduction, untouched
            # below), but a NEW item added today should get the discount
            # tier their combined selection actually qualifies for, not
            # just what they're adding in isolation. Covers both an
            # existing reservation being confirmed in this same visit
            # (fully_confirmed_orders) and anything already paid for on
            # an earlier visit (a prior completed CaisseTransaction).
            existing_blocs_covered = set()
            for order in fully_confirmed_orders:
                for entry in order.items_snapshot or []:
                    if entry.get('bloc') in ('restauration', 'workshops', 'social_event'):
                        existing_blocs_covered.add(entry['bloc'])
            for txn in CaisseTransaction.objects.filter(
                participant=participant, status='completed'
            ).prefetch_related('items__bloc_item', 'items__session'):
                for paid_item in txn.items.all():
                    if paid_item.bloc_item_id:
                        existing_blocs_covered.add(paid_item.bloc_item.bloc)
                    elif paid_item.session_id:
                        existing_blocs_covered.add('workshops')

            new_item_ids = [ext_id for (kind, ext_id) in new_bloc_keys if kind == 'item']
            new_session_ids = [ext_id for (kind, ext_id) in new_bloc_keys if kind == 'session']
            result = compute_order(
                event=caisse.event, config=config,
                selected_item_ids=new_item_ids, selected_session_ids=new_session_ids,
                on_date=timezone.now().date(),
                context_status_item_id=existing_status_item_id,
                context_blocs_covered=existing_blocs_covered,
            )
            covered_keys = {(entry['type'], str(entry['id'])) for entry in result['snapshot']}
            recomputed_bloc_amount = result['total_after_reduction']
            recomputed_bloc_items = [new_bloc_keys[key] for key in covered_keys if key in new_bloc_keys]
            uncovered_items = [item for key, item in new_bloc_keys.items() if key not in covered_keys]
            # Not covered by compute_order (e.g. their bloc isn't shown in
            # this event's config) but still bloc_item/session-backed --
            # price them the same live, rule-resolved way rather than the
            # possibly-stale PayableItem.price snapshot.
            live_prices = resolve_catalog_prices(
                caisse.event, config, timezone.now().date(),
                context_status_item_id=existing_status_item_id,
            )
            for item in uncovered_items:
                if item.bloc_item_id:
                    live = live_prices.get(('item', item.bloc_item_id))
                elif item.session_id:
                    live = live_prices.get(('session', str(item.session_id)))
                else:
                    live = None
                if live is not None:
                    item.price = live['price']
            plain_cash_items.extend(uncovered_items)

            if recomputed_bloc_items:
                recomputed_bloc_before = result['total_before_reduction']
                recomputed_bloc_detail = f"{result['total_before_reduction']} DZD"
                if result['total_discount_percent'] > 0:
                    pieces = []
                    if result['period_discount_percent'] > 0:
                        pieces.append(f"period {result['period_discount_percent']}%")
                    if result['blocs_discount_percent'] > 0:
                        pieces.append(f"blocs {result['blocs_discount_percent']}%")
                    reduction = f"-{result['total_discount_percent']}%"
                    if pieces:
                        reduction += f" ({' + '.join(pieces)})"
                    recomputed_bloc_detail += f" {reduction}"
                recomputed_bloc_detail += f" -> {result['total_after_reduction']} DZD"
        else:
            # No bloc config at all for this event -- nothing to recompute against.
            plain_cash_items.extend(new_bloc_keys.values())

    plain_cash_amount = sum((item.price for item in plain_cash_items), Decimal('0'))
    # unpaid_order_amount is real cash being collected for the first time
    # right now (see the receipt_file check above) -- it belongs in the
    # recorded total exactly like plain_cash_amount, unlike a genuine
    # bank-transfer reservation (bank_transfer_amount), whose money was
    # already received before this visit.
    cash_amount = recomputed_bloc_amount + plain_cash_amount + unpaid_order_amount

    # What the caisse operator actually collects right now. Confirming an
    # existing bank-transfer reservation doesn't put any new money in the
    # cashier's hand -- that amount was already received before this visit
    # -- so it must not inflate this transaction's recorded amount, which
    # is exactly what get_total_amount()/"Transactions récentes" show as
    # revenue collected AT this caisse (e.g. a reservation confirmed for
    # 4000 plus 3000 of new items added at the counter must record 3000,
    # not 7000). The full picture (including the bank-transfer portion)
    # stays fully auditable in the transaction's own notes below.
    recorded_amount = cash_amount

    if bank_transfer_items and (cash_items or unpaid_order_items):
        payment_method = 'mixed'
    elif bank_transfer_items:
        payment_method = 'bank_transfer'
    else:
        payment_method = 'cash'

    method_note_parts = []
    if bank_transfer_items:
        method_note_parts.append(
            f"Paid via bank transfer (registration receipt): {'; '.join(bank_transfer_breakdown_parts)}. Items: "
            + ", ".join(i.name for i in bank_transfer_items)
        )
    if unpaid_order_items:
        method_note_parts.append(
            f"Reservation confirmed and paid in cash at the counter (no prior receipt), "
            f"{'; '.join(unpaid_order_breakdown_parts)}. Items: "
            + ", ".join(i.name for i in unpaid_order_items)
        )
    if recomputed_bloc_items:
        method_note_parts.append(
            f"New bloc items added at the counter (discount recomputed): {recomputed_bloc_detail}. Items: "
            + ", ".join(i.name for i in recomputed_bloc_items)
        )
    if plain_cash_items:
        method_note_parts.append(
            f"Paid in cash at the counter, {plain_cash_amount} DZD: "
            + ", ".join(i.name for i in plain_cash_items)
        )
    auto_note = "\n".join(method_note_parts)
    final_notes = f"{notes}\n{auto_note}" if notes else auto_note

    # Create transaction with explicit database transaction
    import logging
    from django.db import transaction as db_transaction
    logger = logging.getLogger(__name__)

    try:
        with db_transaction.atomic():
            # Create the transaction record
            transaction = CaisseTransaction.objects.create(
                caisse=caisse,
                participant=participant,
                total_amount=recorded_amount,
                payment_method=payment_method,
                status='completed',
                notes=final_notes,
                marked_present=True
            )
            
            # Link items to transaction using add() instead of set()
            # This ensures the many-to-many relationship is properly saved
            for item in items:
                transaction.items.add(item)
            
            # Explicitly save the transaction
            transaction.save()

            # Mark each fully-confirmed reservation as confirmed -- the
            # caisse operator's confirmation is the final validation, no
            # admin review involved.
            for order in fully_confirmed_orders:
                order.status = 'approved'
                order.reviewed_by_caisse = caisse
                order.reviewed_at = timezone.now()
                order.save(update_fields=['status', 'reviewed_by_caisse', 'reviewed_at'])

            # A completed transaction -- paid or 0 DZD, doesn't matter --
            # means this participant is physically at the counter right
            # now, same as clicking "Marquer comme présent" directly.
            _mark_participant_present(participant, caisse.event)

            logger.info(f"[CAISSE] ✅ Transaction {transaction.id} created successfully")
            logger.info(f"[CAISSE] Participant: {participant.user.email}")
            logger.info(f"[CAISSE] Items to link: {len(items)}")
            
    except Exception as e:
        logger.error(f"[CAISSE] ❌ Failed to create transaction: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Failed to create transaction: {str(e)}'
        })
    
    # Verify items were saved (outside the atomic block)
    transaction.refresh_from_db()
    items_count = transaction.items.count()
    
    logger.info(f"[CAISSE] Items actually linked: {items_count}")
    
    if items_count != len(items):
        logger.error(f"[CAISSE] ⚠️ MISMATCH! Expected {len(items)} items but only {items_count} were saved!")
        return JsonResponse({
            'success': False,
            'message': f'Transaction created but items not saved properly. Expected {len(items)}, got {items_count}'
        })
    
    # Log each item
    for item in transaction.items.all():
        logger.info(f"[CAISSE]   ✓ {item.name} ({item.item_type}) - {item.price} DA")
    
    # Grant access to the selected sessions/ateliers
    # Create SessionAccess records for paid sessions
    from events.models import Session, SessionAccess, UserProfile
    
    for item in items:
        if item.session:
            # Get the session
            session = item.session
            
            # Create or update SessionAccess record
            session_access, created = SessionAccess.objects.get_or_create(
                participant=participant,
                session=session,
                defaults={
                    'has_access': True,
                    'payment_status': 'paid',
                    'amount_paid': item.price
                }
            )
            
            # If already exists, update it
            if not created:
                session_access.has_access = True
                session_access.payment_status = 'paid'
                session_access.amount_paid = item.price
                session_access.save()
    
    # Regenerate QR code to include new paid sessions
    updated_qr_data = UserProfile.get_qr_for_user(participant.user)
    
    # Update participant's qr_code_data field (now a JSONField)
    participant.qr_code_data = updated_qr_data
    participant.save(update_fields=['qr_code_data'])
    
    # Mirrors recorded_amount above -- the confirmation the cashier sees
    # must show the same number that just got saved, not the combined
    # figure including whatever was already paid by bank transfer.
    total_before_reduction = recomputed_bloc_before + plain_cash_amount + unpaid_order_before
    return JsonResponse({
        'success': True,
        'message': 'Transaction processed successfully',
        'transaction_id': transaction.id,
        'total_amount': float(recorded_amount),
        'total_before_reduction': float(total_before_reduction),
        'total_discount_percent': float(
            (1 - (recorded_amount / total_before_reduction)) * 100
        ) if total_before_reduction > 0 else 0.0,
        'payment_method': payment_method,
        'action': action
    })


@caisse_required
@require_http_methods(["POST"])
def reject_reservation(request):
    """
    Reject a participant's still-reserved bloc registration(s) at the
    counter -- e.g. the bank receipt turns out to be invalid. No admin
    review happens before this; the caisse operator is the final check.
    Rejecting only affects the reserved items/discount -- it does not
    revoke the participant role itself, which was granted at email
    verification (same trust level as the free flow).
    """
    caisse = request.caisse

    try:
        data = json.loads(request.body)
        participant_id = data.get('participant_id')
        reason = (data.get('reason') or '').strip()
    except json.JSONDecodeError:
        participant_id = request.POST.get('participant_id')
        reason = (request.POST.get('reason') or '').strip()

    if not participant_id:
        return JsonResponse({'success': False, 'message': 'Participant ID required'})

    try:
        participant = Participant.objects.get(id=participant_id)
        if not participant.is_registered_for_event(caisse.event):
            return JsonResponse({'success': False, 'message': 'Participant not registered for this event'})
    except Participant.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Participant not found'})

    pending_orders = _pending_orders_with_payable_ids(participant, caisse.event)
    if not pending_orders:
        return JsonResponse({'success': False, 'message': 'No pending reservation to reject'})

    for order, _pending_ids in pending_orders:
        order.status = 'rejected'
        order.reviewed_by_caisse = caisse
        order.reviewed_at = timezone.now()
        if reason:
            order.admin_notes = reason
        order.save(update_fields=['status', 'reviewed_by_caisse', 'reviewed_at', 'admin_notes'])

    return JsonResponse({
        'success': True,
        'message': f'Rejected {len(pending_orders)} reservation(s).'
    })


@caisse_required
@require_http_methods(["POST"])
def modify_pending_order(request):
    """
    Let the caisse operator change what a NOT-YET-CONFIRMED participant
    actually reserved -- e.g. swap one workshop for another, add/remove
    a Social Event pack -- before processing/paying for it.
    process_transaction requires every item bundled into the same order
    to be confirmed together and has no way to change that bundle, so
    without this, a participant whose reservation no longer matches what
    they actually want (or what the caisse operator agrees to give them)
    could never be confirmed at all.

    Reuses the exact same compute_order() engine, cardinality rules
    (single-select blocs, Status mandatory), and save path
    (apply_compute_result_to_pending_order) as the event owner's own
    "Modifier les blocs" editor (dashboard.views_event_owner.
    registration_order_blocs_save) so pricing can never quietly drift
    between the two. Deliberately refuses once the order is 'approved'
    -- a confirmed order has real money/access effects (SessionAccess, a
    completed CaisseTransaction) that only the event owner's own editor
    is set up to safely resync; this is purely for a reservation that
    hasn't been paid for yet.
    """
    from dashboard.models_blocs import RegistrationOrder
    from dashboard.blocs_service import compute_order, apply_compute_result_to_pending_order
    from dashboard.views_blocs import get_public_bloc_context

    caisse = request.caisse

    try:
        data = json.loads(request.body)
        participant_id = data.get('participant_id')
        item_ids = data.get('items', [])
    except json.JSONDecodeError:
        participant_id = request.POST.get('participant_id')
        item_ids = request.POST.getlist('items[]')

    if not participant_id:
        return JsonResponse({'success': False, 'message': 'Participant ID required'})

    try:
        participant = Participant.objects.get(id=participant_id)
        if not participant.is_registered_for_event(caisse.event):
            return JsonResponse({'success': False, 'message': 'Participant not registered for this event'})
    except Participant.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Participant not found'})

    order = RegistrationOrder.objects.filter(
        event=caisse.event, participant=participant
    ).exclude(status__in=['rejected', 'approved']).order_by('-created_at').first()
    if not order:
        return JsonResponse({
            'success': False,
            'message': 'This participant has no pending reservation to modify.'
        })

    bloc_context = get_public_bloc_context(caisse.event, include_inactive=True)
    if not bloc_context:
        return JsonResponse({
            'success': False,
            'message': "This event's registration options are no longer available."
        })

    items = PayableItem.objects.filter(
        id__in=item_ids, event=caisse.event
    ).select_related('bloc_item', 'session')

    picked_by_bloc = {}
    selected_session_ids = []
    for item in items:
        if item.bloc_item_id:
            picked_by_bloc.setdefault(item.bloc_item.bloc, []).append(str(item.bloc_item_id))
        elif item.session_id:
            selected_session_ids.append(str(item.session_id))

    selected_item_ids = []
    errors = []
    for bloc in bloc_context['custom_blocs']:
        picked = picked_by_bloc.get(bloc['key'], [])
        if bloc['select_mode'] == 'single' and len(picked) > 1:
            errors.append(f"Veuillez sélectionner une seule option dans {bloc['label']}.")
        if bloc['key'] == 'status' and len(picked) == 0:
            errors.append(f"Veuillez sélectionner une option dans {bloc['label']}.")
        selected_item_ids.extend(picked)

    if errors:
        return JsonResponse({'success': False, 'message': ' '.join(errors)})

    result = compute_order(
        event=caisse.event, config=bloc_context['config'],
        selected_item_ids=selected_item_ids, selected_session_ids=selected_session_ids,
        on_date=timezone.now().date(), include_inactive=True, period=order.period,
        ignore_visibility_rules=True,
    )
    apply_compute_result_to_pending_order(order, result)

    return JsonResponse({
        'success': True,
        'message': 'Reservation updated.',
        'total_before_reduction': float(result['total_before_reduction']),
        'total_after_reduction': float(result['total_after_reduction']),
    })


# ==================== Transaction History ====================

@caisse_required
def transaction_history(request):
    """View transaction history for this caisse"""
    caisse = request.caisse
    
    status_filter = request.GET.get('status', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    transactions = caisse.transactions.select_related(
        'participant__user'
    ).prefetch_related('items').order_by('-created_at')
    
    # Apply filters
    if status_filter:
        transactions = transactions.filter(status=status_filter)
    
    if date_from:
        transactions = transactions.filter(created_at__date__gte=date_from)
    
    if date_to:
        transactions = transactions.filter(created_at__date__lte=date_to)
    
    context = {
        'caisse': caisse,
        'transactions': transactions[:100],  # Limit to 100
        'status_filter': status_filter,
        'date_from': date_from,
        'date_to': date_to
    }
    
    return render(request, 'caisse/transaction_history.html', context)


@caisse_required
@require_http_methods(["POST"])
def cancel_transaction(request, transaction_id):
    """Cancel a transaction and remove granted access"""
    import json
    from events.models import Session
    
    caisse = request.caisse
    
    try:
        transaction = CaisseTransaction.objects.get(id=transaction_id, caisse=caisse, status='completed')
    except CaisseTransaction.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Transaction not found or already cancelled'})
    
    # Parse JSON body
    try:
        data = json.loads(request.body)
        reason = data.get('reason', 'No reason provided')
    except json.JSONDecodeError:
        reason = request.POST.get('reason', 'No reason provided')
    
    # Get the participant before canceling
    participant = transaction.participant
    
    # Collect room IDs from the cancelled items that need to be removed
    rooms_to_remove = []
    for item in transaction.items.all():
        if item.session and item.session.room:
            rooms_to_remove.append(str(item.session.room.id))
    
    # Remove access to these rooms from participant's metadata
    if rooms_to_remove and participant.metadata and 'allowed_rooms' in participant.metadata:
        allowed_rooms = participant.metadata.get('allowed_rooms', [])
        if isinstance(allowed_rooms, list):
            # Check if any other completed transactions grant access to these rooms
            # Only remove if no other completed transaction provides access
            other_completed_transactions = CaisseTransaction.objects.filter(
                participant=participant,
                status='completed'
            ).exclude(id=transaction.id).prefetch_related('items__session__room')
            
            # Collect room IDs from other completed transactions
            rooms_from_other_transactions = set()
            for other_trans in other_completed_transactions:
                for item in other_trans.items.all():
                    if item.session and item.session.room:
                        rooms_from_other_transactions.add(str(item.session.room.id))
            
            # Remove only rooms not granted by other transactions
            new_allowed_rooms = [
                room_id for room_id in allowed_rooms 
                if room_id not in rooms_to_remove or room_id in rooms_from_other_transactions
            ]
            
            participant.metadata['allowed_rooms'] = new_allowed_rooms
            participant.save()
    
    # Cancel the transaction
    transaction.cancel(cancelled_by=caisse.name, reason=reason)
    
    # Verify transaction was cancelled
    transaction.refresh_from_db()
    
    # Regenerate QR code to remove cancelled items
    from events.models import UserProfile
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"[CAISSE CANCEL] ==========================================")
    logger.info(f"[CAISSE CANCEL] Transaction {transaction.id} cancelled for {participant.user.email}")
    logger.info(f"[CAISSE CANCEL] Transaction status: {transaction.status}")
    logger.info(f"[CAISSE CANCEL] Cancelled at: {transaction.cancelled_at}")
    logger.info(f"[CAISSE CANCEL] Regenerating QR code to remove cancelled items...")
    
    # Check how many completed transactions remain
    remaining_completed = CaisseTransaction.objects.filter(
        participant=participant,
        status='completed'
    ).count()
    logger.info(f"[CAISSE CANCEL] Remaining completed transactions: {remaining_completed}")
    
    updated_qr_data = UserProfile.get_qr_for_user(participant.user)
    
    # Update participant's qr_code_data field
    participant.qr_code_data = updated_qr_data
    participant.save(update_fields=['qr_code_data'])
    
    # Log the updated QR code data
    paid_items_count = len(updated_qr_data.get('paid_items', []))
    logger.info(f"[CAISSE CANCEL] ✅ QR code updated")
    logger.info(f"[CAISSE CANCEL] Paid items in QR code: {paid_items_count}")
    
    if paid_items_count > 0:
        logger.info(f"[CAISSE CANCEL] Items:")
        for item in updated_qr_data.get('paid_items', []):
            logger.info(f"[CAISSE CANCEL]   - {item.get('title')} ({item.get('type')}) - {item.get('amount_paid')} DA")
    else:
        logger.info(f"[CAISSE CANCEL] No paid items remaining")
    
    logger.info(f"[CAISSE CANCEL] ==========================================")
    
    return JsonResponse({
        'success': True,
        'message': 'Transaction cancelled successfully and access revoked'
    })


# ==================== Badge Printing ====================

@caisse_required
def print_badge(request, participant_id):
    """Generate printable badge with QR code"""
    caisse = request.caisse
    
    try:
        participant = Participant.objects.select_related('user').get(id=participant_id)
        # Verify participant is registered for this event
        if not participant.is_registered_for_event(caisse.event):
            messages.error(request, "Participant non inscrit à cet événement")
            return redirect('caisse:dashboard')
    except Participant.DoesNotExist:
        messages.error(request, 'Participant introuvable')
        return redirect('caisse:dashboard')
    
    # Generate QR code image -- must encode the plain user_id, not
    # badge_id: every real scan endpoint (events/views.py
    # ParticipantViewSet/ExposantScanViewSet scan_participant) and the
    # mobile app's own QR only ever accept that plain id and look
    # everything else (badge_id included) up fresh from the database.
    # Encoding badge_id here made every badge printed from the caisse
    # fail to scan with "Invalid QR code format" -- see
    # dashboard/views.py's _qr_display_payload for the canonical format
    # this must stay in sync with.
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(str(participant.user_id))
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()
    
    context = {
        'caisse': caisse,
        'participant': participant,
        'event': caisse.event,
        'name': participant.user.get_full_name() or participant.user.username,
        'first_name': participant.user.first_name or participant.user.username,
        'last_name': participant.user.last_name,
        'email': participant.user.email,
        'badge_id': participant.badge_id,
        'qr_code_base64': qr_code_base64
    }
    
    return render(request, 'caisse/print_badge.html', context)
