from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from events.models import Event
from events.form_validation_service import create_participant_for_event
from dashboard.models_blocs import BlocItem, EventBlocConfig, RegistrationOrder
from .models import Caisse, CaisseTransaction, PayableItem


class BlocItemSyncTests(TestCase):
    def setUp(self):
        self.event = Event.objects.create(
            name="Congress", start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=2), location="Algiers",
        )
        EventBlocConfig.objects.create(event=self.event, show_status=True, show_restauration=True)
        self.status_item = BlocItem.objects.create(event=self.event, bloc='status', name='Adherent', price=Decimal('1000'))
        self.resto_item = BlocItem.objects.create(event=self.event, bloc='restauration', name='Dinner', price=Decimal('500'))

    def test_sync_creates_payable_items(self):
        call_command('sync_paid_bloc_items')
        self.assertEqual(PayableItem.objects.filter(event=self.event, item_type='bloc').count(), 2)
        payable = PayableItem.objects.get(bloc_item=self.status_item)
        self.assertEqual(payable.price, Decimal('1000'))
        self.assertIn('Adherent', payable.name)

    def test_sync_updates_price_change(self):
        call_command('sync_paid_bloc_items')
        self.status_item.price = Decimal('1200')
        self.status_item.save()
        call_command('sync_paid_bloc_items')
        payable = PayableItem.objects.get(bloc_item=self.status_item)
        self.assertEqual(payable.price, Decimal('1200'))

    def test_sync_deactivates_orphaned_items(self):
        call_command('sync_paid_bloc_items')
        self.resto_item.is_active = False
        self.resto_item.save()
        call_command('sync_paid_bloc_items')
        payable = PayableItem.objects.get(bloc_item=self.resto_item)
        self.assertFalse(payable.is_active)


class CaisseBlocReservationTests(TestCase):
    def setUp(self):
        self.event = Event.objects.create(
            name="Congress", start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=2), location="Algiers",
        )
        EventBlocConfig.objects.create(event=self.event, show_status=True)
        self.status_item = BlocItem.objects.create(event=self.event, bloc='status', name='Adherent', price=Decimal('1000'))
        call_command('sync_paid_bloc_items')
        self.payable = PayableItem.objects.get(bloc_item=self.status_item)

        self.user = User.objects.create_user(username='karim', email='k@example.com', password='x')
        self.participant = create_participant_for_event(self.user, self.event)

        self.caisse = Caisse.objects.create(name='Caisse 1', email='caisse@example.com', event=self.event)
        self.caisse.set_password('x')
        self.caisse.save()

    def _login_caisse(self):
        session = self.client.session
        session['caisse_id'] = str(self.caisse.id)
        session['caisse_name'] = self.caisse.name
        session.save()

    def _make_order(self, status='approved'):
        return RegistrationOrder.objects.create(
            event=self.event, email=self.user.email, full_name='Karim B',
            participant=self.participant, status=status,
            items_snapshot=[{'bloc': 'status', 'type': 'item', 'id': self.status_item.id, 'name': 'Adherent', 'price': '1000.00'}],
            receipt_file=SimpleUploadedFile('r.pdf', b'x', content_type='application/pdf'),
        )

    def test_no_reservation_nothing_pre_selected(self):
        self._login_caisse()
        response = self.client.get(reverse('caisse:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['participant_reserved_items_json'], '{}')

    def test_pending_order_not_counted_as_reserved(self):
        self._make_order(status='pending')
        self._login_caisse()
        response = self.client.get(reverse('caisse:dashboard'))
        self.assertEqual(response.context['participant_reserved_items_json'], '{}')

    def test_approved_order_pre_selects_item(self):
        self._make_order(status='approved')
        self._login_caisse()
        response = self.client.get(reverse('caisse:dashboard'))
        reserved_json = response.context['participant_reserved_items_json']
        self.assertIn(str(self.participant.id), reserved_json)
        self.assertIn(str(self.payable.id), reserved_json)

        item_data = next(
            d for d in response.context['payable_items_with_capacity'] if d['item'].id == self.payable.id
        )
        self.assertTrue(item_data['is_reservable'])
        self.assertEqual(item_data['reserved_count'], 1)
        self.assertEqual(item_data['confirmed_count'], 0)

    def test_confirming_reserved_item_records_bank_transfer(self):
        self._make_order(status='approved')
        self._login_caisse()
        response = self.client.post(
            reverse('caisse:process_transaction'),
            data={'participant_id': str(self.participant.id), 'items': [str(self.payable.id)], 'notes': ''},
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['success'], payload)
        self.assertEqual(payload['payment_method'], 'bank_transfer')

        txn = CaisseTransaction.objects.get(id=payload['transaction_id'])
        self.assertEqual(txn.payment_method, 'bank_transfer')
        self.assertIn('bank transfer', txn.notes.lower())

        # Reserved count drops to 0, confirmed count rises to 1 once processed.
        response = self.client.get(reverse('caisse:dashboard'))
        item_data = next(
            d for d in response.context['payable_items_with_capacity'] if d['item'].id == self.payable.id
        )
        self.assertEqual(item_data['reserved_count'], 0)
        self.assertEqual(item_data['confirmed_count'], 1)

    def test_walkup_purchase_records_cash(self):
        # No reservation at all -- a fresh walk-up sale of the same catalog item.
        self._login_caisse()
        response = self.client.post(
            reverse('caisse:process_transaction'),
            data={'participant_id': str(self.participant.id), 'items': [str(self.payable.id)], 'notes': ''},
            content_type='application/json',
        )
        payload = response.json()
        self.assertTrue(payload['success'], payload)
        self.assertEqual(payload['payment_method'], 'cash')

    def test_mixed_payment_when_reserved_and_walkup_combined(self):
        self._make_order(status='approved')
        session_item = PayableItem.objects.create(
            event=self.event, name='Extra Workshop', price=Decimal('300'), item_type='other'
        )
        self._login_caisse()
        response = self.client.post(
            reverse('caisse:process_transaction'),
            data={
                'participant_id': str(self.participant.id),
                'items': [str(self.payable.id), str(session_item.id)],
                'notes': '',
            },
            content_type='application/json',
        )
        payload = response.json()
        self.assertTrue(payload['success'], payload)
        self.assertEqual(payload['payment_method'], 'mixed')

    def test_registration_order_update_sets_participant_on_approve(self):
        order = RegistrationOrder.objects.create(
            event=self.event, email='new@example.com', full_name='New Person',
            status='pending',
            receipt_file=SimpleUploadedFile('r.pdf', b'x', content_type='application/pdf'),
        )
        new_user = User.objects.create_user(username='newperson', email='new@example.com', password='x')
        admin = User.objects.create_user(username='admin', password='x', is_staff=True)
        self.client.force_login(admin)
        self.client.post(reverse('dashboard:registration_order_update', args=[order.id]), {
            'action': 'approve', 'admin_notes': '',
        })
        order.refresh_from_db()
        self.assertEqual(order.status, 'approved')
        self.assertIsNotNone(order.participant)
        self.assertEqual(order.participant.user, new_user)


class CaisseDiscountedReservationTests(TestCase):
    """A bloc order's discount is computed once for the whole order -- the
    caisse must charge/show that real (post-discount) amount, and must
    confirm all of an order's reserved items together, not piecemeal."""

    def setUp(self):
        self.event = Event.objects.create(
            name="Congress", start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=2), location="Algiers",
        )
        EventBlocConfig.objects.create(
            event=self.event, show_status=True, show_restauration=True,
            reduction_by_blocs_enabled=True, reduction_2_blocs=Decimal('20'),
        )
        self.status_item = BlocItem.objects.create(event=self.event, bloc='status', name='Adherent', price=Decimal('1000'))
        self.resto_item = BlocItem.objects.create(event=self.event, bloc='restauration', name='Dinner', price=Decimal('500'))
        call_command('sync_paid_bloc_items')
        self.status_payable = PayableItem.objects.get(bloc_item=self.status_item)
        self.resto_payable = PayableItem.objects.get(bloc_item=self.resto_item)

        self.user = User.objects.create_user(username='karim', email='k@example.com', password='x')
        self.participant = create_participant_for_event(self.user, self.event)

        self.caisse = Caisse.objects.create(name='Caisse 1', email='caisse2@example.com', event=self.event)
        self.caisse.set_password('x')
        self.caisse.save()

        # 1000 + 500 = 1500 subtotal, 20% off (2 distinct blocs) -> 1200 after reduction.
        self.order = RegistrationOrder.objects.create(
            event=self.event, email=self.user.email, full_name='Karim B',
            participant=self.participant, status='approved',
            items_snapshot=[
                {'bloc': 'status', 'type': 'item', 'id': self.status_item.id, 'name': 'Adherent', 'price': '1000.00'},
                {'bloc': 'restauration', 'type': 'item', 'id': self.resto_item.id, 'name': 'Dinner', 'price': '500.00'},
            ],
            distinct_blocs_count=2,
            total_before_reduction=Decimal('1500.00'),
            total_discount_percent=Decimal('20.00'),
            blocs_discount_percent=Decimal('20.00'),
            total_after_reduction=Decimal('1200.00'),
            receipt_file=SimpleUploadedFile('r.pdf', b'x', content_type='application/pdf'),
        )

    def _login_caisse(self):
        session = self.client.session
        session['caisse_id'] = str(self.caisse.id)
        session['caisse_name'] = self.caisse.name
        session.save()

    def test_dashboard_shows_discounted_summary(self):
        self._login_caisse()
        response = self.client.get(reverse('caisse:dashboard'))
        summary_json = response.context['participant_reserved_summary_json']
        self.assertIn('1200.00', summary_json)
        self.assertIn('20.00', summary_json)

    def test_confirming_full_order_charges_discounted_total(self):
        self._login_caisse()
        response = self.client.post(
            reverse('caisse:process_transaction'),
            data={
                'participant_id': str(self.participant.id),
                'items': [str(self.status_payable.id), str(self.resto_payable.id)],
                'notes': '',
            },
            content_type='application/json',
        )
        payload = response.json()
        self.assertTrue(payload['success'], payload)
        self.assertEqual(payload['payment_method'], 'bank_transfer')
        self.assertEqual(Decimal(str(payload['total_amount'])), Decimal('1200.00'))

        txn = CaisseTransaction.objects.get(id=payload['transaction_id'])
        self.assertEqual(txn.total_amount, Decimal('1200.00'))

    def test_confirming_partial_order_is_rejected(self):
        self._login_caisse()
        response = self.client.post(
            reverse('caisse:process_transaction'),
            data={
                'participant_id': str(self.participant.id),
                'items': [str(self.status_payable.id)],  # only one of the two reserved items
                'notes': '',
            },
            content_type='application/json',
        )
        payload = response.json()
        self.assertFalse(payload['success'])
        self.assertIn('Dinner', payload['message'])
        self.assertFalse(CaisseTransaction.objects.filter(participant=self.participant).exists())

    def test_confirming_full_order_plus_walkup_item_is_mixed(self):
        walkup_item = PayableItem.objects.create(
            event=self.event, name='Extra Snack', price=Decimal('200'), item_type='other'
        )
        self._login_caisse()
        response = self.client.post(
            reverse('caisse:process_transaction'),
            data={
                'participant_id': str(self.participant.id),
                'items': [str(self.status_payable.id), str(self.resto_payable.id), str(walkup_item.id)],
                'notes': '',
            },
            content_type='application/json',
        )
        payload = response.json()
        self.assertTrue(payload['success'], payload)
        self.assertEqual(payload['payment_method'], 'mixed')
        # 1200 (discounted reservation) + 200 (walk-up) = 1400
        self.assertEqual(Decimal(str(payload['total_amount'])), Decimal('1400.00'))
