"""
Registration-order confirmation/cancellation shared between caisse's own
POS flow (caisse/views.py, an interactive walk-up flow that also handles
new items added at the counter) and the event-owner submissions page
(dashboard/views_event_owner.py, which only ever confirms/cancels one
already-submitted order exactly as it stands).

Every one of caisse's own "is this paid" checks (dashboard totals,
capacity counts, search) reads CaisseTransaction(status='completed'),
never RegistrationOrder.status -- see caisse/views.py's
_pending_orders_with_payable_ids docstring. So confirming an order from
the event-owner page has to create a real CaisseTransaction, identical
in shape to what a physical caisse station would create, or caisse would
never recognize it as paid. Since CaisseTransaction.caisse is a required
FK to a real (login-capable) Caisse row, get_or_create_owner_caisse()
gives each event one dedicated, non-physical Caisse row to attribute
these confirmations to -- so caisse operators can see, in their own
transaction history, that a given payment was confirmed by the event
owner rather than at a physical station.
"""
import logging

from django.db import transaction as db_transaction
from django.utils import timezone
from django.utils.crypto import get_random_string

from caisse.models import Caisse, CaisseTransaction, PayableItem
from dashboard.email_sender import send_email
from dashboard.models_blocs import BlocItem, CUSTOM_BLOC_CHOICES

logger = logging.getLogger(__name__)

OWNER_CAISSE_EMAIL_TEMPLATE = 'owner-confirmations+{event_id}@makeplus.internal'
OWNER_CAISSE_NAME = "Confirmé par l'organisateur"


def get_or_create_owner_caisse(event):
    """One dedicated, non-physical Caisse per event for event-owner
    confirmations -- never used to log in (random unusable password)."""
    email = OWNER_CAISSE_EMAIL_TEMPLATE.format(event_id=event.id)
    caisse, created = Caisse.objects.get_or_create(
        email=email,
        defaults={'name': OWNER_CAISSE_NAME, 'event': event, 'is_active': True},
    )
    if created:
        caisse.set_password(get_random_string(40))
        caisse.save(update_fields=['password'])
    return caisse


def _payable_item_for_snapshot_entry(event, entry):
    """
    Find (or create, mirroring sync_paid_bloc_items/sync_paid_sessions) the
    PayableItem matching one items_snapshot entry, so a CaisseTransaction
    can link to it. Returns None if the underlying BlocItem/Session no
    longer exists (e.g. deleted since the order was placed).
    """
    if entry.get('type') == 'item':
        try:
            bloc_item = BlocItem.objects.get(id=entry['id'], event=event)
        except BlocItem.DoesNotExist:
            return None
        bloc_labels = dict(CUSTOM_BLOC_CHOICES)
        payable_item, _created = PayableItem.objects.get_or_create(
            event=event, bloc_item=bloc_item,
            defaults={
                'name': f"{bloc_labels.get(bloc_item.bloc, bloc_item.bloc)} - {bloc_item.name}",
                'price': bloc_item.price, 'item_type': 'bloc', 'is_active': True,
            },
        )
        return payable_item

    from events.models import Session
    try:
        session = Session.objects.get(id=entry['id'], event=event)
    except Session.DoesNotExist:
        return None
    payable_item, _created = PayableItem.objects.get_or_create(
        event=event, session=session,
        defaults={
            'name': f"{session.get_session_type_display()} - {session.title}",
            'price': session.price, 'item_type': 'session', 'is_active': True,
        },
    )
    return payable_item


def confirm_registration_order(order, confirmed_by=None):
    """
    Confirm a RegistrationOrder for real: creates a completed
    CaisseTransaction (same effect as caisse's own process_transaction
    confirming a bank-transfer reservation), grants SessionAccess for any
    workshop items, and regenerates the participant's QR code -- so
    caisse's own screens recognize it exactly as if a physical caisse
    station had confirmed it.

    confirmed_by is the dashboard User (event owner or staff) who did
    this from the submissions page -- recorded on the order separately
    from reviewed_by_caisse, which stays set to the virtual owner Caisse
    (consistent with how a real caisse confirmation sets it) so it's
    clear in caisse's own history that this wasn't a physical station.
    """
    from events.models import SessionAccess, UserProfile

    participant = order.participant
    if not participant:
        raise ValueError('Cannot confirm a registration with no linked participant.')

    caisse = get_or_create_owner_caisse(order.event)

    payable_items = []
    for entry in order.items_snapshot or []:
        payable_item = _payable_item_for_snapshot_entry(order.event, entry)
        if payable_item:
            payable_items.append(payable_item)
        else:
            logger.warning(
                '[OWNER CONFIRM] No matching BlocItem/Session for snapshot entry %s on order %s',
                entry, order.id,
            )

    with db_transaction.atomic():
        caisse_txn = CaisseTransaction.objects.create(
            caisse=caisse,
            participant=participant,
            total_amount=order.total_after_reduction,
            payment_method='bank_transfer',
            status='completed',
            notes=f'Confirmed by event owner for registration {order.id}.',
            marked_present=True,
        )
        for payable_item in payable_items:
            caisse_txn.items.add(payable_item)

        order.status = 'approved'
        order.reviewed_by_caisse = caisse
        order.reviewed_by = confirmed_by
        order.reviewed_at = timezone.now()
        order.caisse_transaction = caisse_txn
        order.save(update_fields=[
            'status', 'reviewed_by_caisse', 'reviewed_by', 'reviewed_at', 'caisse_transaction',
        ])

        for payable_item in payable_items:
            if payable_item.session_id:
                SessionAccess.objects.update_or_create(
                    participant=participant, session=payable_item.session,
                    defaults={
                        'has_access': True, 'payment_status': 'paid',
                        'amount_paid': payable_item.price,
                    },
                )

    updated_qr_data = UserProfile.get_qr_for_user(participant.user)
    participant.qr_code_data = updated_qr_data
    participant.save(update_fields=['qr_code_data'])

    _send_confirmation_email(order)

    return caisse_txn


def _send_confirmation_email(order):
    """
    Best-effort confirmation email to the participant. Failures are logged,
    never raised -- a Brevo/SMTP hiccup must not undo or block a real
    payment confirmation that already committed above.

    Uses the event admin's own 'order_confirmation' EventEmailTemplate if
    one exists (subject/body with {{participant_name}}/{{event_name}}
    substituted), same convention as events.views_registration's
    'registration_confirmation' template -- falls back to a fixed default
    message otherwise.
    """
    if not order.email:
        return

    from dashboard.models_email import get_event_email_template

    event = order.event
    template = get_event_email_template(event, 'order_confirmation')

    if template:
        subject = template.subject
        html_content = template.body_html or template.body
        replacements = {
            '{{participant_name}}': order.full_name or '',
            '{{event_name}}': event.name,
        }
        for key, value in replacements.items():
            subject = subject.replace(key, value)
            html_content = html_content.replace(key, value)
    else:
        subject = f"Votre inscription à {event.name} est confirmée"
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #1a1a1a; line-height: 1.5;">
            <p>Bonjour {order.full_name or ''},</p>
            <p>Nous vous confirmons que votre inscription à <strong>{event.name}</strong> est validée.</p>
            <p>Nous avons hâte de vous accueillir.</p>
            <p>Cordialement,<br>L'équipe {event.name}</p>
        </body>
        </html>
        """

    try:
        success, error, _ = send_email(
            to_email=order.email,
            subject=subject,
            html_content=html_content,
            to_name=order.full_name or None,
        )
        if not success:
            logger.warning(
                '[OWNER CONFIRM] Confirmation email to %s failed for order %s: %s',
                order.email, order.id, error,
            )
    except Exception:
        logger.exception(
            '[OWNER CONFIRM] Unexpected error sending confirmation email for order %s', order.id,
        )


def _revoke_session_access_for_order(order):
    """
    Revoke real SessionAccess for every paid-workshop session in this
    order's snapshot -- the mirror of what confirm_registration_order (and
    resync_confirmed_registration_order) grants, including a FREE (price 0)
    workshop: it still got real access when confirmed, so it must still
    lose that access when un-confirmed, same as a paid one. A no-op if the
    order was never confirmed (nothing was ever granted to revoke).
    """
    from events.models import SessionAccess

    if not order.participant_id:
        return
    session_ids = {
        entry['id'] for entry in (order.items_snapshot or []) if entry.get('type') == 'session'
    }
    if session_ids:
        SessionAccess.objects.filter(participant_id=order.participant_id, session_id__in=session_ids).update(
            has_access=False, payment_status='pending', amount_paid=0,
        )


def cancel_registration_order(order, cancelled_by=None, reason=''):
    """
    Cancel a RegistrationOrder.

    If it was confirmed via confirm_registration_order (the event-owner
    flow, order.caisse_transaction is set precisely to the transaction it
    created), void that transaction too via its own cancel() -- soft
    cancel, matching this codebase's existing convention -- so caisse
    stops treating the participant as having paid for those items. Also
    revokes any real SessionAccess granted for a paid workshop in this
    order (see _revoke_session_access_for_order) -- a no-op if it was
    never confirmed in the first place.

    If it was instead confirmed by a real caisse station directly
    (order.caisse_transaction is null -- process_transaction doesn't set
    it, and can bundle several orders into one transaction), the
    transaction itself is left untouched: an event owner shouldn't be
    able to silently reverse money a physical caisse already collected.
    Callers should surface that distinction to the user rather than imply
    the payment itself was undone. SessionAccess is still revoked either
    way -- it's tracked per participant, not shared across a bundled
    transaction, so there's nothing unsafe about un-granting THIS
    participant's own access to items on THIS order.
    """
    if order.caisse_transaction_id and order.caisse_transaction.status == 'completed':
        cancelled_label = (cancelled_by.get_full_name() or cancelled_by.email) if cancelled_by else 'Event owner'
        order.caisse_transaction.cancel(
            cancelled_by=cancelled_label, reason=reason or 'Registration cancelled by event owner.',
        )
    _revoke_session_access_for_order(order)

    order.status = 'rejected'
    order.reviewed_by = cancelled_by
    order.reviewed_at = timezone.now()
    if reason:
        order.admin_notes = f'{reason}\n{order.admin_notes}' if order.admin_notes else reason
    order.save(update_fields=['status', 'reviewed_by', 'reviewed_at', 'admin_notes'])


def unconfirm_registration_order(order, new_status, changed_by=None):
    """
    Move an already-CONFIRMED RegistrationOrder to a DIFFERENT status
    (Registered/Reserved/To Contact/To Recontact) rather than Cancelled --
    e.g. the owner realizes a confirmation was a mistake and wants it back
    in the pipeline, not marked Cancelled. Voids the real CaisseTransaction
    confirm_registration_order created (same soft-cancel as
    cancel_registration_order, just without also setting status='rejected')
    since the order is no longer being treated as paid, and revokes any
    SessionAccess it granted (see _revoke_session_access_for_order),
    including for a free workshop.

    Same physical-caisse-vs-owner-confirmed distinction as
    cancel_registration_order: if order.caisse_transaction is null
    (confirmed directly by a real caisse station, whose transaction can
    bundle several OTHER people's payments), the transaction itself is
    left untouched -- an event owner shouldn't be able to silently
    reverse money a physical caisse already collected. Callers must
    surface that distinction rather than imply the payment was undone.
    """
    if order.caisse_transaction_id and order.caisse_transaction.status == 'completed':
        changed_label = (changed_by.get_full_name() or changed_by.email) if changed_by else 'Event owner'
        order.caisse_transaction.cancel(
            cancelled_by=changed_label,
            reason=f'Status changed from Confirmed to {new_status} by event owner.',
        )
    _revoke_session_access_for_order(order)

    order.status = new_status
    order.reviewed_by = changed_by
    order.reviewed_at = timezone.now()
    order.save(update_fields=['status', 'reviewed_by', 'reviewed_at'])


def resync_confirmed_registration_order(order, result, edited_by=None):
    """
    Re-price an ALREADY-CONFIRMED RegistrationOrder after the event owner
    edited its blocs (dashboard's registration_order_blocs_save). Cancels
    the CaisseTransaction confirm_registration_order created and creates a
    brand new one for the updated total/items, rather than mutating the
    frozen total_amount in place -- this codebase never edits a completed
    transaction after the fact; cancel_registration_order voids-and-stops
    rather than un-recording it, and caisse's own on-the-day add-item flow
    always creates an additional transaction rather than touching an
    existing one. Same principle here: cancel + replace, full paper trail.

    Only valid for an order confirmed through confirm_registration_order
    (order.caisse_transaction is already set to the transaction it made).
    A registration confirmed by a real physical caisse station can be
    bundled into one transaction with several OTHER people's payments --
    there is no single transaction here that would be safe to touch, so
    callers must check order.caisse_transaction_id themselves and refuse
    before calling this (see registration_order_blocs_save).

    Grants/revokes real SessionAccess for any paid workshop added/removed
    by the edit, same as confirm_registration_order does on a first
    confirmation -- so a workshop added here is actually scannable, and
    one removed here actually stops being so.

    `result` is compute_order()'s return dict for the NEW selection
    (the caller resolves it against the order's own registration period,
    not today's -- see registration_order_blocs_save). Saves `order`
    itself (pricing fields + the new caisse_transaction) -- callers must
    not also save() those fields separately.

    Returns the new CaisseTransaction.
    """
    from events.models import SessionAccess

    participant = order.participant
    if not participant:
        raise ValueError('Cannot resync a registration with no linked participant.')
    if not order.caisse_transaction_id:
        raise ValueError('This order was not confirmed through the event-owner flow; nothing to resync.')

    old_txn = order.caisse_transaction
    old_session_ids = {
        str(entry['id']) for entry in (order.items_snapshot or []) if entry.get('type') == 'session'
    }
    new_session_ids = {
        str(entry['id']) for entry in result['snapshot'] if entry.get('type') == 'session'
    }

    caisse = get_or_create_owner_caisse(order.event)

    payable_items = []
    for entry in result['snapshot']:
        payable_item = _payable_item_for_snapshot_entry(order.event, entry)
        if payable_item:
            payable_items.append(payable_item)
        else:
            logger.warning(
                '[OWNER EDIT] No matching BlocItem/Session for snapshot entry %s on order %s',
                entry, order.id,
            )

    edited_label = (edited_by.get_full_name() or edited_by.email) if edited_by else 'Event owner'

    with db_transaction.atomic():
        old_txn.cancel(
            cancelled_by=edited_label,
            reason=f'Superseded: blocs modified by event owner for registration {order.id}.',
        )

        new_txn = CaisseTransaction.objects.create(
            caisse=caisse,
            participant=participant,
            total_amount=result['total_after_reduction'],
            payment_method='bank_transfer',
            status='completed',
            notes=f'Confirmed by event owner (blocs edit) for registration {order.id}. Replaces transaction {old_txn.id}.',
            marked_present=True,
        )
        for payable_item in payable_items:
            new_txn.items.add(payable_item)

        order.period_id = result['active_period_id']
        order.items_snapshot = result['snapshot']
        order.subtotals = result['subtotals']
        order.distinct_blocs_count = result['distinct_blocs_count']
        order.total_before_reduction = result['total_before_reduction']
        order.period_discount_percent = result['period_discount_percent']
        order.blocs_discount_percent = result['blocs_discount_percent']
        order.total_discount_percent = result['total_discount_percent']
        order.total_after_reduction = result['total_after_reduction']
        order.caisse_transaction = new_txn
        order.reviewed_by = edited_by
        order.reviewed_at = timezone.now()
        order.save(update_fields=[
            'period', 'items_snapshot', 'subtotals', 'distinct_blocs_count',
            'total_before_reduction', 'period_discount_percent', 'blocs_discount_percent',
            'total_discount_percent', 'total_after_reduction',
            'caisse_transaction', 'reviewed_by', 'reviewed_at',
        ])

        for session_id in (new_session_ids - old_session_ids):
            payable_item = next(
                (pi for pi in payable_items if pi.session_id and str(pi.session_id) == session_id), None,
            )
            if payable_item:
                SessionAccess.objects.update_or_create(
                    participant=participant, session_id=session_id,
                    defaults={
                        'has_access': True, 'payment_status': 'paid',
                        'amount_paid': payable_item.price,
                    },
                )
        for session_id in (old_session_ids - new_session_ids):
            SessionAccess.objects.filter(participant=participant, session_id=session_id).update(
                has_access=False, payment_status='pending', amount_paid=0,
            )

    return new_txn
