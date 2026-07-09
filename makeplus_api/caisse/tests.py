from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from events.models import Event, Room, Session
from events.form_validation_service import create_participant_for_event
from dashboard.models_blocs import BlocItem, BlocItemStatusRule, EventBlocConfig, RegistrationOrder
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

    def _make_order(self, status='pending'):
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

    def test_stale_approved_order_with_no_real_transaction_still_shows_as_reserved(self):
        # Regression: orders approved under the since-removed admin-review
        # flow can have status='approved' with no CaisseTransaction behind
        # them at all -- nothing was actually handed out. Whether an item
        # still needs confirming must be decided by CaisseTransaction data,
        # not the (possibly stale) status field.
        self._make_order(status='approved')
        self._login_caisse()
        response = self.client.get(reverse('caisse:dashboard'))
        reserved_json = response.context['participant_reserved_items_json']
        self.assertIn(str(self.participant.id), reserved_json)
        self.assertIn(str(self.payable.id), reserved_json)

    def test_order_with_completed_transaction_not_shown_as_reserved_again(self):
        self._make_order(status='approved')
        txn = CaisseTransaction.objects.create(
            caisse=self.caisse, participant=self.participant, total_amount=Decimal('1000'), status='completed',
        )
        txn.items.add(self.payable)

        self._login_caisse()
        response = self.client.get(reverse('caisse:dashboard'))
        self.assertEqual(response.context['participant_reserved_items_json'], '{}')

    def test_rejected_order_not_counted_as_reserved(self):
        self._make_order(status='rejected')
        self._login_caisse()
        response = self.client.get(reverse('caisse:dashboard'))
        self.assertEqual(response.context['participant_reserved_items_json'], '{}')

    def test_pending_order_pre_selects_item(self):
        # 'pending' = reserved on submission, no admin review needed.
        self._make_order(status='pending')
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

    def test_confirming_reserved_item_records_bank_transfer_and_flips_status(self):
        order = self._make_order(status='pending')
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

        order.refresh_from_db()
        self.assertEqual(order.status, 'approved')  # confirmed at caisse
        self.assertEqual(order.reviewed_by_caisse, self.caisse)

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
        self._make_order(status='pending')
        other_item = PayableItem.objects.create(
            event=self.event, name='Extra Snack', price=Decimal('300'), item_type='other'
        )
        self._login_caisse()
        response = self.client.post(
            reverse('caisse:process_transaction'),
            data={
                'participant_id': str(self.participant.id),
                'items': [str(self.payable.id), str(other_item.id)],
                'notes': '',
            },
            content_type='application/json',
        )
        payload = response.json()
        self.assertTrue(payload['success'], payload)
        self.assertEqual(payload['payment_method'], 'mixed')

    def test_reject_reservation_rejects_pending_order_without_revoking_role(self):
        self._make_order(status='pending')
        self._login_caisse()
        response = self.client.post(
            reverse('caisse:reject_reservation'),
            data={'participant_id': str(self.participant.id), 'reason': 'Fake receipt'},
            content_type='application/json',
        )
        payload = response.json()
        self.assertTrue(payload['success'], payload)

        order = RegistrationOrder.objects.get(participant=self.participant)
        self.assertEqual(order.status, 'rejected')
        self.assertEqual(order.reviewed_by_caisse, self.caisse)
        self.assertEqual(order.admin_notes, 'Fake receipt')
        # Participant role isn't revoked -- only the reservation is rejected.
        self.assertTrue(self.participant.pk)

        # No longer shown as reserved.
        response = self.client.get(reverse('caisse:dashboard'))
        self.assertEqual(response.context['participant_reserved_items_json'], '{}')

    def test_reject_reservation_with_no_pending_order_fails(self):
        self._login_caisse()
        response = self.client.post(
            reverse('caisse:reject_reservation'),
            data={'participant_id': str(self.participant.id), 'reason': ''},
            content_type='application/json',
        )
        payload = response.json()
        self.assertFalse(payload['success'])

    def test_new_bloc_item_added_at_counter_gets_combined_discount(self):
        # No reservation -- caisse adds two different bloc items fresh on
        # the day; the multi-bloc discount should apply just like it would
        # if picked together on the registration form.
        EventBlocConfig.objects.filter(event=self.event).update(
            show_restauration=True, reduction_by_blocs_enabled=True, reduction_2_blocs=Decimal('20'),
        )
        resto_item = BlocItem.objects.create(event=self.event, bloc='restauration', name='Dinner', price=Decimal('500'))
        call_command('sync_paid_bloc_items')
        resto_payable = PayableItem.objects.get(bloc_item=resto_item)

        self._login_caisse()
        response = self.client.post(
            reverse('caisse:process_transaction'),
            data={
                'participant_id': str(self.participant.id),
                'items': [str(self.payable.id), str(resto_payable.id)],
                'notes': '',
            },
            content_type='application/json',
        )
        payload = response.json()
        self.assertTrue(payload['success'], payload)
        self.assertEqual(payload['payment_method'], 'cash')
        # 1000 + 500 = 1500, 20% off (2 distinct blocs) -> 1200.
        self.assertEqual(Decimal(str(payload['total_amount'])), Decimal('1200.00'))


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
            participant=self.participant, status='pending',
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
        self.assertIn('1500.00', summary_json)  # before reduction
        self.assertIn('1200.00', summary_json)  # after reduction
        self.assertIn('20.00', summary_json)  # total discount %
        self.assertIn('blocs_discount_percent', summary_json)
        self.assertIn('period_discount_percent', summary_json)

    def test_confirm_response_includes_before_after_and_discount(self):
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
        self.assertEqual(payload['total_before_reduction'], 1500.0)
        self.assertEqual(payload['total_amount'], 1200.0)
        self.assertAlmostEqual(payload['total_discount_percent'], 20.0, places=1)

        txn = CaisseTransaction.objects.get(id=payload['transaction_id'])
        self.assertIn('1500.00 DZD', txn.notes)
        self.assertIn('20.00%', txn.notes)
        self.assertIn('1200.00 DZD', txn.notes)

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

        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'approved')

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


class CaisseBlocGroupingTests(TestCase):
    """
    The caisse item selection must be coherent with the registration form:
    items grouped by bloc, single-choice blocs rendered/enforced as
    single-select (radio), multiple-choice blocs stay multi-select
    (checkbox).
    """

    def setUp(self):
        self.event = Event.objects.create(
            name="Congress", start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=2), location="Algiers",
        )
        EventBlocConfig.objects.create(
            event=self.event, show_status=True, status_select_mode='single',
            show_restauration=True, restauration_select_mode='multiple',
        )
        self.status_item_a = BlocItem.objects.create(event=self.event, bloc='status', name='Adherent', price=Decimal('1000'))
        self.status_item_b = BlocItem.objects.create(event=self.event, bloc='status', name='Non-adherent', price=Decimal('2000'))
        self.resto_item_a = BlocItem.objects.create(event=self.event, bloc='restauration', name='Dinner 1', price=Decimal('500'))
        self.resto_item_b = BlocItem.objects.create(event=self.event, bloc='restauration', name='Dinner 2', price=Decimal('600'))
        call_command('sync_paid_bloc_items')
        self.status_payable_a = PayableItem.objects.get(bloc_item=self.status_item_a)
        self.status_payable_b = PayableItem.objects.get(bloc_item=self.status_item_b)
        self.resto_payable_a = PayableItem.objects.get(bloc_item=self.resto_item_a)
        self.resto_payable_b = PayableItem.objects.get(bloc_item=self.resto_item_b)

        self.user = User.objects.create_user(username='karim', email='k@example.com', password='x')
        self.participant = create_participant_for_event(self.user, self.event)

        self.caisse = Caisse.objects.create(name='Caisse 1', email='caisse4@example.com', event=self.event)
        self.caisse.set_password('x')
        self.caisse.save()

    def _login_caisse(self):
        session = self.client.session
        session['caisse_id'] = str(self.caisse.id)
        session['caisse_name'] = self.caisse.name
        session.save()

    def test_items_grouped_by_bloc_with_correct_input_type(self):
        self._login_caisse()
        response = self.client.get(reverse('caisse:dashboard'))
        groups = {g['label']: g for g in response.context['bloc_groups']}

        self.assertIn('Status', groups)
        self.assertEqual(groups['Status']['select_mode'], 'single')
        self.assertEqual(groups['Status']['input_type'], 'radio')
        self.assertEqual(
            {d['item'].id for d in groups['Status']['items']},
            {self.status_payable_a.id, self.status_payable_b.id},
        )

        self.assertIn('Restauration', groups)
        self.assertEqual(groups['Restauration']['select_mode'], 'multiple')
        self.assertEqual(groups['Restauration']['input_type'], 'checkbox')

    def test_selecting_two_single_choice_items_is_rejected(self):
        self._login_caisse()
        response = self.client.post(
            reverse('caisse:process_transaction'),
            data={
                'participant_id': str(self.participant.id),
                'items': [str(self.status_payable_a.id), str(self.status_payable_b.id)],
                'notes': '',
            },
            content_type='application/json',
        )
        payload = response.json()
        self.assertFalse(payload['success'])
        self.assertIn('only one option', payload['message'])
        self.assertFalse(CaisseTransaction.objects.filter(participant=self.participant).exists())

    def test_selecting_two_multiple_choice_items_is_allowed(self):
        self._login_caisse()
        response = self.client.post(
            reverse('caisse:process_transaction'),
            data={
                'participant_id': str(self.participant.id),
                'items': [str(self.resto_payable_a.id), str(self.resto_payable_b.id)],
                'notes': '',
            },
            content_type='application/json',
        )
        payload = response.json()
        self.assertTrue(payload['success'], payload)


class CaisseStatusDependentPricingTests(TestCase):
    """A participant's already-chosen Status (locked into a prior
    reservation) must still drive visibility/price for brand-new items
    added at the counter, even though they aren't re-picking Status now."""

    def setUp(self):
        self.event = Event.objects.create(
            name="Congress", start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=2), location="Algiers",
        )
        EventBlocConfig.objects.create(event=self.event, show_status=True, show_restauration=True)
        self.status_item = BlocItem.objects.create(event=self.event, bloc='status', name='Adherent', price=Decimal('0'))
        self.dinner = BlocItem.objects.create(event=self.event, bloc='restauration', name='Dinner', price=Decimal('1000'))
        BlocItemStatusRule.objects.create(
            status_item=self.status_item, target_kind='item', target_item=self.dinner,
            override_price=Decimal('400'),
        )
        call_command('sync_paid_bloc_items')
        self.dinner_payable = PayableItem.objects.get(bloc_item=self.dinner)

        self.user = User.objects.create_user(username='karim', email='k@example.com', password='x')
        self.participant = create_participant_for_event(self.user, self.event)

        # Already-approved reservation that only picked a Status (no
        # dinner) -- simulates them having chosen "Adherent" at
        # registration, now wanting to add Dinner fresh at the counter.
        RegistrationOrder.objects.create(
            event=self.event, email=self.user.email, full_name='Karim B',
            participant=self.participant, status='approved',
            items_snapshot=[{'bloc': 'status', 'type': 'item', 'id': self.status_item.id, 'name': 'Adherent', 'price': '0.00'}],
            total_before_reduction=Decimal('0'), total_after_reduction=Decimal('0'),
            receipt_file=SimpleUploadedFile('r.pdf', b'x', content_type='application/pdf'),
        )

        self.caisse = Caisse.objects.create(name='Caisse 1', email='caisse5@example.com', event=self.event)
        self.caisse.set_password('x')
        self.caisse.save()

    def _login_caisse(self):
        session = self.client.session
        session['caisse_id'] = str(self.caisse.id)
        session['caisse_name'] = self.caisse.name
        session.save()

    def test_new_item_uses_status_override_price_from_existing_reservation(self):
        self._login_caisse()
        response = self.client.post(
            reverse('caisse:process_transaction'),
            data={
                'participant_id': str(self.participant.id),
                'items': [str(self.dinner_payable.id)],
                'notes': '',
            },
            content_type='application/json',
        )
        payload = response.json()
        self.assertTrue(payload['success'], payload)
        # 400 (status-overridden price), not the normal 1000.
        self.assertEqual(Decimal(str(payload['total_amount'])), Decimal('400.00'))


class CaisseSessionReservationTests(TestCase):
    """
    Regression test: Session's PK is a UUID, but items_snapshot stores its
    id as a plain string (str(session.id)). Reservation-key matching must
    treat both sides as strings, or a workshop reserved via the bloc form
    never shows up as reserved at the caisse (silently broken before).
    """

    def setUp(self):
        self.event = Event.objects.create(
            name="Congress", start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=2), location="Algiers",
        )
        EventBlocConfig.objects.create(event=self.event, show_workshops=True)
        room = Room.objects.create(event=self.event, name='Hall A', capacity=100, location='1st floor')
        self.session = Session.objects.create(
            event=self.event, room=room, title='Machine Learning', session_type='conference',
            start_time=timezone.now(), end_time=timezone.now() + timedelta(hours=1),
            is_paid=True, price=Decimal('2000'),
        )
        # A post_save signal (events/signals.py) already mirrors any paid
        # Session into a PayableItem automatically -- fetch that one rather
        # than creating a second, duplicate PayableItem for the same session.
        self.session_payable = PayableItem.objects.get(session=self.session)

        self.user = User.objects.create_user(username='karim', email='k@example.com', password='x')
        self.participant = create_participant_for_event(self.user, self.event)

        self.caisse = Caisse.objects.create(name='Caisse 1', email='caisse3@example.com', event=self.event)
        self.caisse.set_password('x')
        self.caisse.save()

        self.order = RegistrationOrder.objects.create(
            event=self.event, email=self.user.email, full_name='Karim B',
            participant=self.participant, status='pending',
            items_snapshot=[
                {'bloc': 'workshops', 'type': 'session', 'id': str(self.session.id), 'name': 'Machine Learning', 'price': '2000.00'},
            ],
            total_before_reduction=Decimal('2000.00'),
            total_after_reduction=Decimal('2000.00'),
            receipt_file=SimpleUploadedFile('r.pdf', b'x', content_type='application/pdf'),
        )

    def _login_caisse(self):
        session = self.client.session
        session['caisse_id'] = str(self.caisse.id)
        session['caisse_name'] = self.caisse.name
        session.save()

    def test_reserved_session_shows_up_at_caisse(self):
        self._login_caisse()
        response = self.client.get(reverse('caisse:dashboard'))
        reserved_json = response.context['participant_reserved_items_json']
        self.assertIn(str(self.participant.id), reserved_json)
        self.assertIn(str(self.session_payable.id), reserved_json)

        item_data = next(
            d for d in response.context['payable_items_with_capacity']
            if d['item'].id == self.session_payable.id
        )
        self.assertTrue(item_data['is_reservable'])
        self.assertEqual(item_data['reserved_count'], 1)

    def test_confirming_reserved_session_is_bank_transfer(self):
        self._login_caisse()
        response = self.client.post(
            reverse('caisse:process_transaction'),
            data={
                'participant_id': str(self.participant.id),
                'items': [str(self.session_payable.id)],
                'notes': '',
            },
            content_type='application/json',
        )
        payload = response.json()
        self.assertTrue(payload['success'], payload)
        self.assertEqual(payload['payment_method'], 'bank_transfer')


class BackfillRegistrationOrderParticipantTests(TestCase):
    """Older orders approved before finalize_paid_registration set
    participant at creation time can be left with participant=None,
    making them invisible to the caisse. The backfill command fixes them."""

    def test_backfills_participant_when_account_exists(self):
        event = Event.objects.create(
            name="Congress", start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=2), location="Algiers",
        )
        user = User.objects.create_user(username='karim', email='k@example.com', password='x')
        order = RegistrationOrder.objects.create(
            event=event, email='k@example.com', full_name='Karim B', status='approved',
            receipt_file=SimpleUploadedFile('r.pdf', b'x', content_type='application/pdf'),
        )
        self.assertIsNone(order.participant)

        call_command('backfill_registration_order_participant')

        order.refresh_from_db()
        self.assertIsNotNone(order.participant)
        self.assertEqual(order.participant.user, user)

    def test_creates_placeholder_account_when_none_exists(self):
        # A reservation must show up at the caisse even if the person never
        # opened the mobile app -- so a missing account gets a placeholder
        # (unusable password) instead of being left orphaned.
        event = Event.objects.create(
            name="Congress", start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=2), location="Algiers",
        )
        order = RegistrationOrder.objects.create(
            event=event, email='ghost@example.com', full_name='Ghost Writer', status='approved',
            receipt_file=SimpleUploadedFile('r.pdf', b'x', content_type='application/pdf'),
        )
        call_command('backfill_registration_order_participant')
        order.refresh_from_db()
        self.assertIsNotNone(order.participant)
        self.assertEqual(order.participant.user.email, 'ghost@example.com')
        self.assertFalse(order.participant.user.has_usable_password())
