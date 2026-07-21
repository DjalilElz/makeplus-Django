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


def cancel_registration_order(order, cancelled_by=None, reason=''):
    """
    Cancel a RegistrationOrder.

    If it was confirmed via confirm_registration_order (the event-owner
    flow, order.caisse_transaction is set precisely to the transaction it
    created), void that transaction too via its own cancel() -- soft
    cancel, matching this codebase's existing convention -- so caisse
    stops treating the participant as having paid for those items.

    If it was instead confirmed by a real caisse station directly
    (order.caisse_transaction is null -- process_transaction doesn't set
    it, and can bundle several orders into one transaction), this only
    updates the registration record: an event owner shouldn't be able to
    silently reverse money a physical caisse already collected. Callers
    should surface that distinction to the user rather than imply the
    payment itself was undone.
    """
    if order.caisse_transaction_id and order.caisse_transaction.status == 'completed':
        cancelled_label = (cancelled_by.get_full_name() or cancelled_by.email) if cancelled_by else 'Event owner'
        order.caisse_transaction.cancel(
            cancelled_by=cancelled_label, reason=reason or 'Registration cancelled by event owner.',
        )

    order.status = 'rejected'
    order.reviewed_by = cancelled_by
    order.reviewed_at = timezone.now()
    if reason:
        order.admin_notes = f'{reason}\n{order.admin_notes}' if order.admin_notes else reason
    order.save(update_fields=['status', 'reviewed_by', 'reviewed_at', 'admin_notes'])
