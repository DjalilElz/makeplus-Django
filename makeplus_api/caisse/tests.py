import json
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
        # The mode is chosen by the cashier (Espèces by default), not guessed
        # from the receipt.
        response = self.client.post(
            reverse('caisse:process_transaction'),
            data={'participant_id': str(self.participant.id), 'items': [str(self.payable.id)], 'notes': '',
                  'payment_method': 'bank_transfer'},
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

    def test_reserved_and_walkup_combined_use_the_chosen_mode(self):
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
        # No longer 'mixed': one payment, under the mode the cashier chose
        # (Espèces by default).
        self.assertEqual(payload['payment_method'], 'cash')

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
                'payment_method': 'bank_transfer',
            },
            content_type='application/json',
        )
        payload = response.json()
        self.assertTrue(payload['success'], payload)
        self.assertEqual(payload['payment_method'], 'bank_transfer')
        # The reservation's discounted total is recorded in full, under
        # "Virement bancaire" -- so the stats' "Total virement" includes it
        # (it used to be recorded as 0, i.e. invisible in every total).
        self.assertEqual(Decimal(str(payload['total_amount'])), Decimal('1200.00'))

        txn = CaisseTransaction.objects.get(id=payload['transaction_id'])
        self.assertEqual(txn.total_amount, Decimal('1200.00'))
        self.assertIn('1200.00 DZD', txn.notes)

        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'approved')
        self.assertEqual(self.order.total_after_reduction, Decimal('1200.00'))

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

    def test_confirming_full_order_plus_walkup_item_recorded_in_full(self):
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
        # The whole 1400 is recorded, as two payments: the 1200 discounted
        # reservation already paid by transfer (receipt), and the 200
        # walk-up item paid now in Espèces (the counter's default).
        self.assertEqual(Decimal(str(payload['total_amount'])), Decimal('1400.00'))
        self.assertEqual(
            [(p['method'], p['amount']) for p in payload['payments']],
            [('bank_transfer', 1200.0), ('cash', 200.0)],
        )

        transfer, cash = CaisseTransaction.objects.filter(id__in=payload['transaction_ids']).order_by('id')
        self.assertIn('1200.00 DZD', transfer.notes)
        self.assertIn('Extra Snack', cash.notes)


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
                'payment_method': 'bank_transfer',
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


class PaymentModeTests(TestCase):
    """Payment status / mode / paying organisation: chosen at the caisse
    (Espèces by default) or on the dashboard, and split the same way on
    the caisse screen and the stats page."""

    def setUp(self):
        from dashboard.models_blocs import EventSponsor
        self.event = Event.objects.create(
            name="Congress", start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=2), location="Algiers",
        )
        EventBlocConfig.objects.create(event=self.event, show_status=True)
        self.status_item = BlocItem.objects.create(event=self.event, bloc='status', name='Adherent', price=Decimal('1000'))
        self.payable = PayableItem.objects.get(bloc_item=self.status_item)  # mirrored automatically
        self.hikma = EventSponsor.objects.create(event=self.event, name='Laboratoire Hikma')
        self.inactive = EventSponsor.objects.create(event=self.event, name='Ancien labo', is_active=False)
        self.caisse = Caisse.objects.create(name='Caisse 1', email='caisse@example.com', event=self.event)
        self.caisse.set_password('x')
        self.caisse.save()
        self.admin = User.objects.create_user(username='admin', password='x', is_staff=True, is_superuser=True)

    def _participant(self, name, receipt=False):
        user = User.objects.create_user(username=name, email=f'{name}@example.com', password='x')
        participant = create_participant_for_event(user, self.event)
        order = RegistrationOrder.objects.create(
            event=self.event, email=user.email, full_name=name, participant=participant, status='pending',
            items_snapshot=[{'bloc': 'status', 'type': 'item', 'id': self.status_item.id, 'name': 'Adherent', 'price': '1000.00'}],
            total_before_reduction=Decimal('1000'), total_after_reduction=Decimal('1000'),
            receipt_file=SimpleUploadedFile('r.pdf', b'x', content_type='application/pdf') if receipt else '',
        )
        return participant, order

    def _pay(self, participant, **payment):
        session = self.client.session
        session['caisse_id'] = str(self.caisse.id)
        session['caisse_name'] = self.caisse.name
        session.save()
        body = {'participant_id': participant.id, 'items': [str(self.payable.id)], 'action': 'process'}
        body.update(payment)
        return self.client.post(
            reverse('caisse:process_transaction'), json.dumps(body), content_type='application/json',
        ).json()

    def test_cash_by_default(self):
        participant, order = self._participant('a')
        result = self._pay(participant)
        self.assertTrue(result['success'])
        txn = CaisseTransaction.objects.get(participant=participant)
        self.assertEqual(txn.payment_method, 'cash')
        order.refresh_from_db()
        self.assertEqual((order.status, order.payment_mode), ('approved', 'cash'))
        self.assertIsNotNone(order.paid_at)

    def test_bank_transfer_recorded_with_its_full_amount(self):
        # A reservation with a bank receipt used to be left out of the
        # recorded amount; it now counts, under "Virement bancaire".
        participant, order = self._participant('b', receipt=True)
        result = self._pay(participant, payment_method='bank_transfer')
        self.assertTrue(result['success'])
        self.assertEqual(result['total_amount'], 1000.0)
        txn = CaisseTransaction.objects.get(participant=participant)
        self.assertEqual((txn.payment_method, txn.total_amount), ('bank_transfer', Decimal('1000.00')))
        self.assertEqual(txn.payment_display, 'Virement bancaire')

    def test_sponsoring_needs_an_active_organisation(self):
        participant, order = self._participant('c')
        self.assertFalse(self._pay(participant, payment_method='sponsoring')['success'])
        self.assertFalse(self._pay(participant, payment_method='sponsoring', sponsor_id=self.inactive.id)['success'])
        self.assertFalse(CaisseTransaction.objects.filter(participant=participant).exists())
        result = self._pay(participant, payment_method='sponsoring', sponsor_id=self.hikma.id)
        self.assertTrue(result['success'])
        self.assertEqual(result['payment_label'], 'Prise en charge · Laboratoire Hikma')
        order.refresh_from_db()
        self.assertEqual((order.payment_mode, order.sponsor_id), ('sponsoring', self.hikma.id))

    def test_unknown_mode_refused(self):
        participant, _ = self._participant('d')
        self.assertFalse(self._pay(participant, payment_method='cheque')['success'])

    def test_caisse_and_stats_show_the_same_breakdown(self):
        from caisse.services import payment_breakdown
        payments = (
            ('e', {}),
            ('f', {'payment_method': 'bank_transfer'}),
            ('g', {'payment_method': 'sponsoring', 'sponsor_id': self.hikma.id}),
        )
        for name, payment in payments:
            participant, _ = self._participant(name)
            self.assertTrue(self._pay(participant, **payment)['success'])
        totals = payment_breakdown(CaisseTransaction.objects.filter(caisse__event=self.event))
        self.assertEqual(totals['total']['amount'], Decimal('3000'))
        self.assertEqual(
            [totals[mode]['amount'] for mode in ('cash', 'bank_transfer', 'sponsoring')], [Decimal('1000')] * 3,
        )
        self.assertEqual(
            totals['sponsors'],
            [{'name': 'Laboratoire Hikma', 'amount': Decimal('1000.00'), 'count': 1, 'participants': 1}],
        )

        caisse_page = self.client.get(reverse('caisse:dashboard'))
        self.assertEqual(caisse_page.context['payment_totals']['total']['amount'], Decimal('3000'))
        self.assertContains(caisse_page, 'Prise en charge · Laboratoire Hikma')

        self.client.force_login(self.admin)
        stats = self.client.get(reverse('dashboard:event_stats', args=[self.event.id]))
        self.assertEqual(stats.context['payment_totals']['total']['amount'], Decimal('3000'))
        self.assertEqual(stats.context['payment_totals']['sponsoring']['amount'], Decimal('1000'))
        self.assertEqual(stats.context['money_stats']['total_amount'], Decimal('3000'))
        per_caisse = stats.context['per_caisse_stats'][0]
        self.assertEqual(
            (per_caisse['cash_amount'], per_caisse['bank_transfer_amount'], per_caisse['sponsoring_amount']),
            (Decimal('1000'), Decimal('1000'), Decimal('1000')),
        )

    def _pay_with_extra(self, participant, extra_price='2000', **payment):
        extra = PayableItem.objects.create(event=self.event, name='Dîner', price=Decimal(extra_price), item_type='other')
        return self._pay_items(participant, [self.payable.id, extra.id], **payment)

    def _pay_items(self, participant, item_ids, **payment):
        session = self.client.session
        session['caisse_id'] = str(self.caisse.id)
        session['caisse_name'] = self.caisse.name
        session.save()
        body = {'participant_id': participant.id, 'items': [str(i) for i in item_ids], 'action': 'process'}
        body.update(payment)
        return self.client.post(
            reverse('caisse:process_transaction'), json.dumps(body), content_type='application/json',
        ).json()

    def test_transfer_reservation_plus_cash_at_counter_is_split(self):
        # 1000 already paid by transfer (receipt) + 2000 paid in cash now:
        # two payments, so the cash total matches the drawer.
        participant, order = self._participant('s1', receipt=True)
        result = self._pay_with_extra(participant)
        self.assertTrue(result['success'])
        self.assertEqual(result['total_amount'], 3000.0)
        self.assertEqual(
            [(p['method'], p['amount']) for p in result['payments']],
            [('bank_transfer', 1000.0), ('cash', 2000.0)],
        )
        self.assertEqual(result['payment_label'], 'Virement bancaire + Espèces')
        txns = {t.payment_method: t for t in CaisseTransaction.objects.filter(participant=participant)}
        self.assertEqual(set(txns), {'bank_transfer', 'cash'})
        self.assertEqual(txns['bank_transfer'].total_amount, Decimal('1000'))
        self.assertEqual(list(txns['bank_transfer'].items.values_list('id', flat=True)), [self.payable.id])
        self.assertEqual(txns['cash'].total_amount, Decimal('2000'))
        self.assertEqual(list(txns['cash'].items.values_list('name', flat=True)), ['Dîner'])
        order.refresh_from_db()
        self.assertEqual((order.status, order.payment_mode), ('approved', 'bank_transfer'))

        from caisse.services import payment_breakdown
        totals = payment_breakdown(CaisseTransaction.objects.filter(caisse__event=self.event))
        self.assertEqual(
            (totals['cash']['amount'], totals['bank_transfer']['amount'], totals['total']['amount']),
            (Decimal('2000'), Decimal('1000'), Decimal('3000')),
        )
        self.assertEqual(totals['total']['participants'], 1)

    def test_split_reservation_mode_can_be_prise_en_charge(self):
        participant, order = self._participant('s2', receipt=True)
        refused = self._pay_with_extra(participant, reserved_payment_method='sponsoring')
        self.assertFalse(refused['success'])
        self.assertFalse(CaisseTransaction.objects.filter(participant=participant).exists())
        result = self._pay_with_extra(
            participant, reserved_payment_method='sponsoring', reserved_sponsor_id=self.hikma.id,
        )
        self.assertTrue(result['success'])
        self.assertEqual(
            [(p['label'], p['amount']) for p in result['payments']],
            [('Prise en charge · Laboratoire Hikma', 1000.0), ('Espèces', 2000.0)],
        )
        order.refresh_from_db()
        self.assertEqual((order.payment_mode, order.sponsor_id), ('sponsoring', self.hikma.id))

    def test_same_mode_for_both_parts_stays_one_payment(self):
        participant, _ = self._participant('s3', receipt=True)
        result = self._pay_with_extra(participant, payment_method='bank_transfer')
        self.assertTrue(result['success'])
        txn = CaisseTransaction.objects.get(participant=participant)
        self.assertEqual((txn.payment_method, txn.total_amount, txn.items.count()), ('bank_transfer', Decimal('3000'), 2))

    def test_free_extra_with_transfer_reservation_is_one_transfer_payment(self):
        # Nothing collected now: all of it is the reservation's money, under
        # the reservation's mode (not the counter's default Espèces).
        participant, _ = self._participant('s4', receipt=True)
        result = self._pay_with_extra(participant, extra_price='0')
        self.assertTrue(result['success'])
        txn = CaisseTransaction.objects.get(participant=participant)
        self.assertEqual((txn.payment_method, txn.total_amount, txn.items.count()), ('bank_transfer', Decimal('1000'), 2))

    def test_no_receipt_reservation_plus_extra_stays_one_payment(self):
        participant, order = self._participant('s5')
        result = self._pay_with_extra(participant)
        self.assertTrue(result['success'])
        txn = CaisseTransaction.objects.get(participant=participant)
        self.assertEqual((txn.payment_method, txn.total_amount), ('cash', Decimal('3000')))
        order.refresh_from_db()
        self.assertEqual(order.payment_mode, 'cash')

    def test_caisse_page_has_the_split_box(self):
        self._pay_items(self._participant('s6')[0], [])  # logs the caisse in
        page = self.client.get(reverse('caisse:dashboard'))
        self.assertContains(page, 'id="paymentSplitBox"')
        self.assertContains(page, 'name="reservedPaymentMode"')

    def test_dashboard_mark_paid_with_a_mode(self):
        participant, order = self._participant('h')
        self.client.force_login(self.admin)
        url = reverse('dashboard:registration_status_save', args=[order.id])
        # Prise en charge without an organisation is refused.
        self.client.post(url, {'status': 'approved', 'payment_method': 'sponsoring'})
        order.refresh_from_db()
        self.assertEqual(order.status, 'pending')
        self.client.post(url, {'status': 'approved', 'payment_method': 'sponsoring', 'sponsor_id': self.hikma.id})
        order.refresh_from_db()
        self.assertEqual((order.status, order.payment_mode, order.sponsor_id), ('approved', 'sponsoring', self.hikma.id))
        txn = order.caisse_transaction
        self.assertEqual((txn.payment_method, txn.sponsor_id), ('sponsoring', self.hikma.id))
        # Back to pending: the payment and its mode are undone.
        self.client.post(url, {'status': 'pending'})
        order.refresh_from_db()
        self.assertEqual((order.status, order.payment_mode, order.sponsor_id), ('pending', '', None))

    def test_list_filter_and_label(self):
        p1, o1 = self._participant('i')
        p2, o2 = self._participant('j')
        self._pay(p1, payment_method='bank_transfer')
        self.client.force_login(self.admin)
        url = reverse('dashboard:event_owner_submissions', args=[self.event.id])
        self.assertEqual([o.id for o in self.client.get(url + '?payment=bank_transfer').context['orders']], [o1.id])
        self.assertEqual([o.id for o in self.client.get(url + '?payment=pending').context['orders']], [o2.id])
        self.assertContains(self.client.get(url), 'Payé · Virement bancaire')

    def test_organisations_are_managed_on_the_blocs_page(self):
        from dashboard.models_blocs import EventSponsor
        self.client.force_login(self.admin)
        url = reverse('dashboard:sponsor_save', args=[self.event.id])
        self.client.post(url, {'name': 'Laboratoire Biopharm', 'order': 2})
        biopharm = EventSponsor.objects.get(event=self.event, name='Laboratoire Biopharm')
        # "Actif" left unchecked: deactivated.
        self.client.post(url, {'sponsor_id': biopharm.id, 'name': 'Biopharm', 'order': 2})
        biopharm.refresh_from_db()
        self.assertEqual((biopharm.name, biopharm.is_active), ('Biopharm', False))
        page = self.client.get(reverse('dashboard:blocs_config', args=[self.event.id]))
        self.assertContains(page, 'Organismes payeurs')

    def test_cashier_downloads_the_caisse_report(self):
        participant, _ = self._participant('k')
        self._pay(participant, payment_method='sponsoring', sponsor_id=self.hikma.id)
        response = self.client.get(reverse('caisse:caisse_report'))  # still logged in as the caisse
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertTrue(response.content.startswith(b'%PDF'))
        self.assertIn('remise-caisse_caisse-1_', response['Content-Disposition'])
        self.assertContains(self.client.get(reverse('caisse:dashboard')), 'Rapport de remise de caisse')

    def test_stats_pdf_is_the_caisse_report_with_filters(self):
        participant, _ = self._participant('l')
        self._pay(participant, payment_method='bank_transfer')
        self.client.force_login(self.admin)
        url = reverse('dashboard:event_stats_export_pdf', args=[self.event.id])
        for query in ('', f'?caisse_id={self.caisse.id}', '?date_from=2020-01-01T00:00&date_to=2099-12-31T23:59'):
            response = self.client.get(url + query)
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.content.startswith(b'%PDF'))
            self.assertIn('rapport-caisse_congress_', response['Content-Disposition'])



import shutil
import tempfile

from django.test import override_settings

_TEST_MEDIA = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=_TEST_MEDIA)
class PresenceAttestationAndBadgePrintTests(TestCase):
    """Auto-sent attestation on first presence, and the badge print log."""

    def setUp(self):
        from unittest import mock
        self.event = Event.objects.create(
            name="Congress", start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=2), location="Algiers",
        )
        self.user = User.objects.create_user(username='amina', email='amina@example.com', password='x',
                                             first_name='Amina', last_name='B')
        self.participant = create_participant_for_event(self.user, self.event)
        self.caisse = Caisse.objects.create(name='Caisse 1', email='c1@example.com', event=self.event)
        session = self.client.session
        session['caisse_id'] = str(self.caisse.id)
        session.save()
        # Run the background send inline and stub the e-mail itself.
        self.thread_patch = mock.patch('threading.Thread', side_effect=lambda target, args, daemon: mock.Mock(start=lambda: target(*args)))
        self.thread_patch.start()
        self.send_patch = mock.patch('dashboard.attestation_service.send_attestation_to_participant', return_value=(True, None))
        self.send_mock = self.send_patch.start()
        self.addCleanup(self.thread_patch.stop)
        self.addCleanup(self.send_patch.stop)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(_TEST_MEDIA, ignore_errors=True)

    def _template(self, auto):
        from dashboard.models_attestation import AttestationTemplate
        return AttestationTemplate.objects.create(
            event=self.event, auto_send_on_presence=auto,
            template_image=SimpleUploadedFile('t.png', b'x', content_type='image/png'),
        )

    def _mark_present(self):
        with self.captureOnCommitCallbacks(execute=True):
            return self.client.post(reverse('caisse:process_transaction'),
                                    data=json.dumps({'participant_id': self.participant.id, 'items': [], 'action': 'process'}),
                                    content_type='application/json')

    def test_marking_present_sends_attestation_once_when_enabled(self):
        from dashboard.models_attestation import AttestationSendLog
        self._template(auto=True)
        self.assertTrue(self._mark_present().json()['success'])
        self.assertEqual(self.send_mock.call_count, 1)
        self.assertEqual(AttestationSendLog.objects.get(participant=self.participant).status, 'sent')
        # A second visit to the counter does not send it again.
        self._mark_present()
        self.assertEqual(self.send_mock.call_count, 1)

    def test_not_sent_when_option_disabled(self):
        from dashboard.models_attestation import AttestationSendLog
        self._template(auto=False)
        self._mark_present()
        self.send_mock.assert_not_called()
        self.assertFalse(AttestationSendLog.objects.exists())

    def test_not_sent_again_if_already_received_from_dashboard(self):
        from dashboard.models_attestation import AttestationSendLog
        self._template(auto=True)
        AttestationSendLog.objects.create(event=self.event, participant=self.participant, status='sent')
        self._mark_present()
        self.send_mock.assert_not_called()

    def test_failed_send_is_recorded(self):
        from dashboard.models_attestation import AttestationSendLog
        self._template(auto=True)
        self.send_mock.return_value = (False, 'SMTP down')
        self._mark_present()
        log = AttestationSendLog.objects.get(participant=self.participant)
        self.assertEqual((log.status, log.error_message), ('failed', 'SMTP down'))

    def test_each_print_is_logged_and_listed_with_reprints(self):
        from .models import BadgePrint
        url = reverse('caisse:print_badge', args=[self.participant.id])
        self.client.get(url)
        self.client.get(url)
        self.assertEqual(BadgePrint.objects.filter(participant=self.participant, caisse=self.caisse).count(), 2)
        response = self.client.get(reverse('caisse:badge_prints'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['stats'], {'total': 2, 'participants': 1, 'reprints': 1})
        self.assertContains(response, '1re impression')
        self.assertContains(response, 'Réimpression n° 1')
        self.assertContains(self.client.get(reverse('caisse:badge_prints'), {'q': 'amina'}), 'Réimpression n° 1')
        self.assertNotContains(self.client.get(reverse('caisse:badge_prints'), {'q': 'nobody'}), 'Réimpression n°')
