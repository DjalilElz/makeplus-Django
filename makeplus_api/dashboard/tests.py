from datetime import timedelta

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from unittest.mock import patch

from events.models import (
    Event, UserEventAssignment, FormRegistrationVerification, Participant, ParticipantEventRegistration,
)
from .models_eposter import (
    ScientificContributionFinalSubmission, ScientificContributionSubmission, EPosterCommitteeMember,
)


class PublicEposterGalleryTests(TestCase):
    def setUp(self):
        self.event = Event.objects.create(
            name="Test Congress",
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=2),
            location="Algiers",
        )

        self.eposter_sub = self._make_submission(
            'e_poster', 'Deep Learning in Radiology', 'Ben Ali', 'Karim',
            'karim@example.com', 'EPOSTER-TEST-001'
        )
        self.comm_sub = self._make_submission(
            'communication_orale', 'Surgical Advances', 'Haddad', 'Sara',
            'sara@example.com', 'COMORAL-TEST-001'
        )

        self.eposter_final = ScientificContributionFinalSubmission.objects.create(
            original_submission=self.eposter_sub,
            event=self.event,
            nom="Ben Ali",
            email="karim@example.com",
            telephone="0000000000",
            contribution_number="EPOSTER-TEST-001",
            titre="Deep Learning in Radiology",
            auteurs="Karim Ben Ali",
            abstract_file=SimpleUploadedFile("abstract.pdf", b"%PDF-1.4 fake", content_type="application/pdf"),
        )
        self.comm_final = ScientificContributionFinalSubmission.objects.create(
            original_submission=self.comm_sub,
            event=self.event,
            nom="Haddad",
            email="sara@example.com",
            telephone="0000000000",
            contribution_number="COMORAL-TEST-001",
            titre="Surgical Advances",
            auteurs="Sara Haddad",
            abstract_file=SimpleUploadedFile("abstract2.pdf", b"%PDF-1.4 fake", content_type="application/pdf"),
        )

    def _make_submission(self, type_participation, titre, nom, prenom, email, code):
        return ScientificContributionSubmission.objects.create(
            event=self.event,
            nom=nom,
            prenom=prenom,
            email=email,
            telephone="0000000000",
            grade="professeur",
            service="Cardiology",
            etablissement="CHU",
            wilaya="Alger",
            type_participation=type_participation,
            theme="Theme",
            titre_travail=titre,
            introduction="i",
            materiels_methodes="m",
            resultats="r",
            conclusion="c",
            status="accepted",
            contribution_code=code,
        )

    def test_gallery_is_public_and_returns_200(self):
        url = reverse('public_eposter_gallery', args=[self.event.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_gallery_shows_only_eposter_type(self):
        url = reverse('public_eposter_gallery', args=[self.event.id])
        response = self.client.get(url)
        self.assertContains(response, "Deep Learning in Radiology")
        self.assertNotContains(response, "Surgical Advances")

    def test_gallery_search_by_title(self):
        url = reverse('public_eposter_gallery', args=[self.event.id])
        response = self.client.get(url, {'q': 'Deep Learning'})
        self.assertContains(response, "Deep Learning in Radiology")

    def test_gallery_search_by_author_name(self):
        url = reverse('public_eposter_gallery', args=[self.event.id])
        response = self.client.get(url, {'q': 'Karim Ben Ali'})
        self.assertContains(response, "Deep Learning in Radiology")

    def test_gallery_search_no_match_shows_empty_state(self):
        url = reverse('public_eposter_gallery', args=[self.event.id])
        response = self.client.get(url, {'q': 'Nonexistent Title XYZ'})
        self.assertContains(response, "Aucun résultat")


class EventDetailGalleryLinkTests(TestCase):
    def setUp(self):
        self.event = Event.objects.create(
            name="Test Congress",
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=2),
            location="Algiers",
        )
        self.staff_user = User.objects.create_user(
            username="staffuser", password="testpass123", is_staff=True
        )
        self.client.force_login(self.staff_user)

    def test_event_detail_links_to_public_gallery(self):
        url = reverse('dashboard:event_detail', args=[self.event.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        gallery_url = reverse('public_eposter_gallery', args=[self.event.id])
        self.assertContains(response, gallery_url)

    def test_event_detail_links_to_final_communications(self):
        url = reverse('dashboard:event_detail', args=[self.event.id])
        response = self.client.get(url)
        comms_url = reverse('dashboard:final_communications', args=[self.event.id])
        self.assertContains(response, comms_url)


class RoomManagerLoginTests(TestCase):
    def setUp(self):
        self.event = Event.objects.create(
            name="Test Congress",
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=2),
            location="Algiers",
        )
        self.room_manager = User.objects.create_user(
            username="roommanager", email="rm@example.com", password="testpass123"
        )
        UserEventAssignment.objects.create(
            user=self.room_manager, event=self.event, role='gestionnaire_des_salles', is_active=True
        )
        self.plain_participant = User.objects.create_user(
            username="plainuser", email="plain@example.com", password="testpass123"
        )

    def test_room_manager_can_log_in_and_is_redirected_to_communications(self):
        response = self.client.post(reverse('dashboard:login'), {
            'email': 'rm@example.com', 'password': 'testpass123'
        })
        # Don't follow through: my_final_communications_home itself redirects
        # again (straight to the event) when there's only one assignment.
        self.assertRedirects(
            response, reverse('dashboard:my_final_communications_home'),
            fetch_redirect_response=False
        )

    def test_plain_user_without_assignment_is_rejected(self):
        response = self.client.post(reverse('dashboard:login'), {
            'email': 'plain@example.com', 'password': 'testpass123'
        })
        # Rejected: re-renders the login page, not redirected anywhere
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)


class FinalCommunicationsTests(TestCase):
    def setUp(self):
        self.event = Event.objects.create(
            name="Test Congress",
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=2),
            location="Algiers",
        )
        self.other_event = Event.objects.create(
            name="Other Congress",
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=2),
            location="Oran",
        )

        self.room_manager = User.objects.create_user(
            username="roommanager", email="rm@example.com", password="testpass123"
        )
        UserEventAssignment.objects.create(
            user=self.room_manager, event=self.event, role='gestionnaire_des_salles', is_active=True
        )

        self.staff_user = User.objects.create_user(
            username="staffuser", password="testpass123", is_staff=True
        )

        comm_sub = ScientificContributionSubmission.objects.create(
            event=self.event, nom="Haddad", prenom="Sara", email="sara@example.com",
            telephone="0000000000", grade="professeur", service="Cardiology",
            etablissement="CHU", wilaya="Alger", type_participation='communication_orale',
            theme="Theme", titre_travail="Surgical Advances", introduction="i",
            materiels_methodes="m", resultats="r", conclusion="c", status="accepted",
            contribution_code="COMORAL-TEST-001",
        )
        eposter_sub = ScientificContributionSubmission.objects.create(
            event=self.event, nom="Ben Ali", prenom="Karim", email="karim@example.com",
            telephone="0000000000", grade="professeur", service="Cardiology",
            etablissement="CHU", wilaya="Alger", type_participation='e_poster',
            theme="Theme", titre_travail="Deep Learning in Radiology", introduction="i",
            materiels_methodes="m", resultats="r", conclusion="c", status="accepted",
            contribution_code="EPOSTER-TEST-001",
        )

        self.comm_final = ScientificContributionFinalSubmission.objects.create(
            original_submission=comm_sub, event=self.event, nom="Haddad",
            email="sara@example.com", telephone="0000000000",
            contribution_number="COMORAL-TEST-001", titre="Surgical Advances",
            auteurs="Sara Haddad",
            abstract_file=SimpleUploadedFile("comm.pdf", b"%PDF-1.4 fake", content_type="application/pdf"),
        )
        self.eposter_final = ScientificContributionFinalSubmission.objects.create(
            original_submission=eposter_sub, event=self.event, nom="Ben Ali",
            email="karim@example.com", telephone="0000000000",
            contribution_number="EPOSTER-TEST-001", titre="Deep Learning in Radiology",
            auteurs="Karim Ben Ali",
            abstract_file=SimpleUploadedFile("eposter.pdf", b"%PDF-1.4 fake", content_type="application/pdf"),
        )

    def test_room_manager_with_single_assignment_redirects_to_event(self):
        self.client.force_login(self.room_manager)
        response = self.client.get(reverse('dashboard:my_final_communications_home'))
        self.assertRedirects(response, reverse('dashboard:final_communications', args=[self.event.id]))

    def test_room_manager_with_multiple_assignments_sees_picker(self):
        UserEventAssignment.objects.create(
            user=self.room_manager, event=self.other_event, role='gestionnaire_des_salles', is_active=True
        )
        self.client.force_login(self.room_manager)
        response = self.client.get(reverse('dashboard:my_final_communications_home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.event.name)
        self.assertContains(response, self.other_event.name)

    def test_room_manager_can_access_own_event(self):
        self.client.force_login(self.room_manager)
        response = self.client.get(reverse('dashboard:final_communications', args=[self.event.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Surgical Advances")

    def test_room_manager_denied_for_other_event(self):
        self.client.force_login(self.room_manager)
        response = self.client.get(reverse('dashboard:final_communications', args=[self.other_event.id]))
        self.assertEqual(response.status_code, 403)

    def test_only_communication_orale_type_is_shown(self):
        self.client.force_login(self.staff_user)
        response = self.client.get(reverse('dashboard:final_communications', args=[self.event.id]))
        self.assertContains(response, "Surgical Advances")
        self.assertNotContains(response, "Deep Learning in Radiology")

    def test_search_by_title(self):
        self.client.force_login(self.staff_user)
        response = self.client.get(
            reverse('dashboard:final_communications', args=[self.event.id]), {'q': 'Surgical'}
        )
        self.assertContains(response, "Surgical Advances")

    def test_search_by_author_name(self):
        self.client.force_login(self.staff_user)
        response = self.client.get(
            reverse('dashboard:final_communications', args=[self.event.id]), {'q': 'Sara Haddad'}
        )
        self.assertContains(response, "Surgical Advances")

    def test_download_forces_attachment(self):
        self.client.force_login(self.staff_user)
        response = self.client.get(
            reverse('dashboard:download_final_communication', args=[self.comm_final.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('attachment', response['Content-Disposition'])

    def test_download_denied_for_room_manager_of_other_event(self):
        self.client.force_login(self.room_manager)
        response = self.client.get(
            reverse('dashboard:download_final_communication', args=[self.eposter_final.id])
        )
        # eposter_final is not communication_orale type -> 404 (excluded from queryset)
        self.assertEqual(response.status_code, 404)


# ===========================================================================
# Registration Blocs / Paid Registration
# ===========================================================================
from decimal import Decimal

from django.core.files.uploadedfile import SimpleUploadedFile as _Upload

from events.models import Room, Session
from .models_blocs import EventBlocConfig, BlocItem, BlocItemStatusRule, ReductionPeriod, RegistrationOrder
from .models_form import FormConfiguration, FormSubmission
from .blocs_service import compute_order


class BlocsComputeOrderTests(TestCase):
    def setUp(self):
        self.event = Event.objects.create(
            name="Congress", start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=2), location="Algiers",
        )
        self.config = EventBlocConfig.objects.create(
            event=self.event, show_status=True, show_restauration=True,
            show_workshops=True, show_social_event=True,
        )
        self.status_item = BlocItem.objects.create(event=self.event, bloc='status', name='Adherent', price=Decimal('1000'))
        self.resto_item = BlocItem.objects.create(event=self.event, bloc='restauration', name='Lunch', price=Decimal('500'))
        self.social_item = BlocItem.objects.create(event=self.event, bloc='social_event', name='Gala', price=Decimal('2000'))

        room = Room.objects.create(event=self.event, name='R1', capacity=50, location='Hall')
        self.paid_session = Session.objects.create(
            event=self.event, room=room, title='Workshop A',
            start_time=timezone.now(), end_time=timezone.now() + timedelta(hours=1),
            is_paid=True, price=Decimal('300'),
        )
        self.free_session = Session.objects.create(
            event=self.event, room=room, title='Free talk',
            start_time=timezone.now(), end_time=timezone.now() + timedelta(hours=1),
            is_paid=False, price=Decimal('0'),
        )
        self.today = timezone.now().date()

    def _compute(self, item_ids=None, session_ids=None):
        return compute_order(self.event, self.config, item_ids or [], session_ids or [], self.today)

    def test_subtotals_and_total_no_reduction(self):
        r = self._compute(item_ids=[self.status_item.id, self.resto_item.id])
        self.assertEqual(r['subtotals']['status'], '1000.00')
        self.assertEqual(r['subtotals']['restauration'], '500.00')
        self.assertEqual(r['total_before_reduction'], Decimal('1500.00'))
        self.assertEqual(r['total_after_reduction'], Decimal('1500.00'))
        # Status is mandatory on every registration, so it never counts
        # toward the multi-bloc discount -- only restauration does here.
        self.assertEqual(r['distinct_blocs_count'], 1)

    def test_status_never_counts_toward_bloc_discount(self):
        # Status + Restauration is only 1 *countable* bloc (restauration) --
        # not enough to trigger the 2-bloc discount tier.
        self.config.reduction_by_blocs_enabled = True
        self.config.reduction_2_blocs = Decimal('20')
        self.config.save()
        r = self._compute(item_ids=[self.status_item.id, self.resto_item.id])
        self.assertEqual(r['distinct_blocs_count'], 1)
        self.assertEqual(r['blocs_discount_percent'], Decimal('0'))
        self.assertEqual(r['total_after_reduction'], r['total_before_reduction'])

        # Adding a second *real* bloc (workshops) makes it 2 countable blocs.
        r2 = self._compute(
            item_ids=[self.status_item.id, self.resto_item.id], session_ids=[self.paid_session.id],
        )
        self.assertEqual(r2['distinct_blocs_count'], 2)
        self.assertEqual(r2['blocs_discount_percent'], Decimal('20.00'))

    def test_workshops_counts_as_a_bloc(self):
        r = self._compute(item_ids=[self.status_item.id], session_ids=[self.paid_session.id])
        # status doesn't count -- only workshops does.
        self.assertEqual(r['distinct_blocs_count'], 1)
        self.assertEqual(r['total_before_reduction'], Decimal('1300.00'))

    def test_free_session_not_charged(self):
        r = self._compute(session_ids=[self.free_session.id])
        # free session is not is_paid -> excluded entirely
        self.assertEqual(r['total_before_reduction'], Decimal('0.00'))
        self.assertEqual(r['distinct_blocs_count'], 0)

    def test_period_pricing_applies_by_date(self):
        # Period pricing is manual per-item (BlocItemStatusRule scoped to a
        # period, no status) rather than a % off the cart.
        period = ReductionPeriod.objects.create(
            event=self.event, name='Early bird',
            start_date=self.today - timedelta(days=1), end_date=self.today + timedelta(days=1),
        )
        self.config.reduction_by_period_enabled = True
        self.config.save()
        BlocItemStatusRule.objects.create(
            period=period, target_kind='item', target_item=self.status_item, override_price=Decimal('700'),
        )
        r = self._compute(item_ids=[self.status_item.id])  # normally 1000
        self.assertEqual(r['total_before_reduction'], Decimal('700.00'))
        self.assertEqual(r['total_after_reduction'], Decimal('700.00'))

    def test_period_pricing_outside_range_uses_normal_price(self):
        period = ReductionPeriod.objects.create(
            event=self.event, start_date=self.today + timedelta(days=5), end_date=self.today + timedelta(days=10),
        )
        self.config.reduction_by_period_enabled = True
        self.config.save()
        BlocItemStatusRule.objects.create(
            period=period, target_kind='item', target_item=self.status_item, override_price=Decimal('700'),
        )
        r = self._compute(item_ids=[self.status_item.id])
        self.assertEqual(r['total_before_reduction'], Decimal('1000.00'))

    def test_free_item_alone_in_bloc_does_not_count(self):
        free_resto = BlocItem.objects.create(event=self.event, bloc='restauration', name='Free snack', price=Decimal('0'))
        self.config.reduction_by_blocs_enabled = True
        self.config.reduction_2_blocs = Decimal('20')
        self.config.save()
        # A free item alone in restauration keeps that bloc's subtotal at
        # 0, so it doesn't count -- only social_event does here (1 real
        # bloc), not enough for the 2-blocs discount.
        r = self._compute(item_ids=[self.status_item.id, free_resto.id, self.social_item.id])
        self.assertEqual(r['subtotals']['restauration'], '0.00')
        self.assertEqual(r['distinct_blocs_count'], 1)
        self.assertEqual(r['blocs_discount_percent'], Decimal('0'))

        # Adding a paid item alongside the free one makes restauration's
        # subtotal > 0, so it counts too -- now 2 blocs, discount applies.
        r2 = self._compute(
            item_ids=[self.status_item.id, free_resto.id, self.resto_item.id, self.social_item.id],
        )
        self.assertEqual(r2['distinct_blocs_count'], 2)
        self.assertEqual(r2['blocs_discount_percent'], Decimal('20.00'))

    def test_blocs_reduction_by_count(self):
        self.config.reduction_by_blocs_enabled = True
        self.config.reduction_2_blocs = Decimal('20')
        self.config.save()
        # 2 *countable* blocs: restauration + social_event (status doesn't count).
        r = self._compute(item_ids=[self.status_item.id, self.resto_item.id, self.social_item.id])  # 3500, 2 blocs
        self.assertEqual(r['distinct_blocs_count'], 2)
        self.assertEqual(r['blocs_discount_percent'], Decimal('20.00'))
        self.assertEqual(r['total_after_reduction'], Decimal('2800.00'))

    def test_reduction_4_blocs_is_ignored(self):
        # Status doesn't count, so 3 (Restauration + Social Event +
        # Workshops) is the real, and only, maximum -- reduction_4_blocs
        # is unreachable and must be ignored outright, not folded into the
        # 3-blocs tier as a fallback (that produced a discount the admin
        # never actually configured for 3 blocs -- reverted).
        self.config.reduction_by_blocs_enabled = True
        self.config.reduction_3_blocs = Decimal('5')
        self.config.reduction_4_blocs = Decimal('30')
        self.config.save()
        r = self._compute(
            item_ids=[self.status_item.id, self.resto_item.id, self.social_item.id],
            session_ids=[self.paid_session.id],
        )
        self.assertEqual(r['distinct_blocs_count'], 3)
        self.assertEqual(r['blocs_discount_percent'], Decimal('5'))

    def test_period_price_and_blocs_reduction_are_additive(self):
        period = ReductionPeriod.objects.create(
            event=self.event, start_date=self.today - timedelta(days=1), end_date=self.today + timedelta(days=1),
        )
        self.config.reduction_by_period_enabled = True
        self.config.reduction_by_blocs_enabled = True
        self.config.reduction_2_blocs = Decimal('20')
        self.config.save()
        BlocItemStatusRule.objects.create(
            period=period, target_kind='item', target_item=self.status_item, override_price=Decimal('700'),
        )
        # status (period price 700) + restauration (500) + social_event (2000)
        # = 3200 before reduction; 2 countable blocs (status doesn't count).
        r = self._compute(item_ids=[self.status_item.id, self.resto_item.id, self.social_item.id])
        self.assertEqual(r['distinct_blocs_count'], 2)
        self.assertEqual(r['total_before_reduction'], Decimal('3200.00'))
        self.assertEqual(r['blocs_discount_percent'], Decimal('20.00'))
        # 3200 - 20% = 2560
        self.assertEqual(r['total_after_reduction'], Decimal('2560.00'))

    def test_item_from_hidden_bloc_is_ignored(self):
        self.config.show_social_event = False
        self.config.save()
        r = self._compute(item_ids=[self.status_item.id, self.social_item.id])
        # social_event hidden -> its item excluded; status doesn't count
        # toward the bloc discount either -> 0 countable blocs.
        self.assertEqual(r['total_before_reduction'], Decimal('1000.00'))
        self.assertEqual(r['distinct_blocs_count'], 0)

    def test_item_from_other_event_is_ignored(self):
        other = Event.objects.create(name="Other", start_date=timezone.now(),
                                     end_date=timezone.now() + timedelta(days=1), location="X")
        foreign = BlocItem.objects.create(event=other, bloc='status', name='X', price=Decimal('999'))
        r = self._compute(item_ids=[self.status_item.id, foreign.id])
        self.assertEqual(r['total_before_reduction'], Decimal('1000.00'))


class BlocsPublicFormTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username='admin', password='x', is_staff=True)
        self.event = Event.objects.create(
            name="Congress", start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=2), location="Algiers",
        )
        self.form = FormConfiguration.objects.create(
            name="Reg", slug="reg", event=self.event, created_by=self.admin,
            fields_config=[
                {'name': 'first_name', 'label': 'First', 'type': 'text', 'required': True},
                {'name': 'last_name', 'label': 'Last', 'type': 'text', 'required': True},
                {'name': 'email', 'label': 'Email', 'type': 'email', 'required': True},
            ],
        )
        self.item = BlocItem.objects.create(event=self.event, bloc='status', name='Adherent', price=Decimal('1000'))
        self.registrant = User.objects.create_user(username='karim', email='k@example.com', password='x')

    def _enable_blocs(self):
        EventBlocConfig.objects.create(event=self.event, show_status=True)

    def test_no_blocs_shows_plain_form(self):
        response = self.client.get(reverse('public_form', args=[self.form.slug]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Envoyer le formulaire')
        self.assertNotContains(response, 'Confirmer')
        self.assertNotContains(response, 'quittance de banque')

    def test_blocs_visible_shows_cart_and_receipt(self):
        self._enable_blocs()
        response = self.client.get(reverse('public_form', args=[self.form.slug]))
        self.assertContains(response, 'Votre panier')
        self.assertContains(response, 'quittance de banque')
        self.assertContains(response, "Confirmer l'inscription")
        self.assertContains(response, 'Adherent')

    def test_item_description_shown_only_when_present(self):
        self._enable_blocs()
        self.item.description = 'Full access to all conference sessions.'
        self.item.save()
        no_desc_item = BlocItem.objects.create(event=self.event, bloc='status', name='Etudiant', price=Decimal('0'))

        response = self.client.get(reverse('public_form', args=[self.form.slug]))
        self.assertContains(response, 'Full access to all conference sessions.')
        # No description set on no_desc_item -- its product card has no
        # product-description span at all, but the page as a whole still
        # has one (from self.item), so just check the item still renders.
        self.assertContains(response, no_desc_item.name)

    @patch.object(FormRegistrationVerification, 'generate_code', return_value='777888')
    def test_paid_submission_without_existing_account_creates_placeholder(self, _mock_code):
        self._enable_blocs()
        receipt = _Upload('receipt.pdf', b'%PDF-1.4 fake', content_type='application/pdf')
        response = self.client.post(reverse('public_form', args=[self.form.slug]), {
            'first_name': 'Nobody', 'last_name': 'X', 'email': 'no-account@example.com',
            'items_status': str(self.item.id),
            'accept_conditions': '1',
            'receipt_file': receipt,
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Vérifiez votre e-mail')
        self.assertTrue(FormRegistrationVerification.objects.filter(email='no-account@example.com').exists())

        response = self.client.post(reverse('public_form', args=[self.form.slug]), {
            'email': 'no-account@example.com', 'verification_code': '777888',
        })
        self.assertEqual(response.status_code, 200)
        order = RegistrationOrder.objects.get(event=self.event, email='no-account@example.com')
        placeholder = User.objects.get(email='no-account@example.com')
        self.assertFalse(placeholder.has_usable_password())
        # Reserved immediately, no admin review -- participant role granted
        # right away too (same trust level as the free flow).
        self.assertEqual(order.status, 'pending')
        self.assertIsNotNone(order.participant)
        self.assertEqual(order.participant.user, placeholder)
        self.assertTrue(Participant.objects.filter(user=placeholder, role='participant').exists())

    @patch.object(FormRegistrationVerification, 'generate_code', return_value='654321')
    def test_paid_submission_stages_code_then_verify_creates_pending_order(self, _mock_code):
        self._enable_blocs()
        receipt = _Upload('receipt.pdf', b'%PDF-1.4 fake', content_type='application/pdf')
        response = self.client.post(reverse('public_form', args=[self.form.slug]), {
            'first_name': 'Karim', 'last_name': 'B', 'email': 'k@example.com',
            'items_status': str(self.item.id),
            'accept_conditions': '1',
            'receipt_file': receipt,
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Vérifiez votre e-mail')
        # Nothing is created yet -- only staged behind the verification code.
        self.assertFalse(RegistrationOrder.objects.filter(event=self.event).exists())

        response = self.client.post(reverse('public_form', args=[self.form.slug]), {
            'email': 'k@example.com', 'verification_code': '654321',
        })
        self.assertEqual(response.status_code, 200)
        order = RegistrationOrder.objects.get(event=self.event)
        self.assertEqual(order.status, 'pending')
        self.assertEqual(order.total_after_reduction, Decimal('1000.00'))
        self.assertEqual(order.email, 'k@example.com')
        self.assertTrue(order.receipt_file)
        self.assertTrue(FormSubmission.objects.filter(form=self.form).exists())
        # Reserved immediately -- no admin review gates it. The participant
        # role is granted right away too (same trust level as the free
        # flow); the caisse operator validates the actual payment on the day.
        self.assertEqual(order.participant.user, self.registrant)
        self.assertTrue(Participant.objects.filter(user=self.registrant, role='participant').exists())

    def test_free_item_shown_as_free_on_registration_page(self):
        self._enable_blocs()
        free_item = BlocItem.objects.create(event=self.event, bloc='status', name='Etudiant', price=Decimal('0'))
        response = self.client.get(reverse('public_form', args=[self.form.slug]))
        self.assertContains(response, 'Free')
        self.assertContains(response, free_item.name)

    @patch.object(FormRegistrationVerification, 'generate_code', return_value='111222')
    def test_free_selection_skips_receipt_and_conditions(self, _mock_code):
        self._enable_blocs()
        free_item = BlocItem.objects.create(event=self.event, bloc='status', name='Etudiant', price=Decimal('0'))
        self.item.delete()  # only the free item is selectable for this test

        # No accept_conditions, no receipt_file -- must not be rejected.
        response = self.client.post(reverse('public_form', args=[self.form.slug]), {
            'first_name': 'Karim', 'last_name': 'B', 'email': 'k@example.com',
            'items_status': str(free_item.id),
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Vérifiez votre e-mail')

        response = self.client.post(reverse('public_form', args=[self.form.slug]), {
            'email': 'k@example.com', 'verification_code': '111222',
        })
        self.assertEqual(response.status_code, 200)
        order = RegistrationOrder.objects.get(event=self.event)
        self.assertEqual(order.total_after_reduction, Decimal('0.00'))
        self.assertFalse(order.receipt_file)
        self.assertEqual(order.participant.user, self.registrant)

    @patch.object(FormRegistrationVerification, 'generate_code', return_value='222333')
    def test_require_payment_proof_off_skips_receipt_even_when_not_free(self, _mock_code):
        self._enable_blocs()
        config = self.event.bloc_config
        config.require_payment_proof = False
        config.save()

        # self.item is priced at 1000 (not free) -- still no receipt/conditions needed.
        response = self.client.post(reverse('public_form', args=[self.form.slug]), {
            'first_name': 'Karim', 'last_name': 'B', 'email': 'k@example.com',
            'items_status': str(self.item.id),
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Vérifiez votre e-mail')

        response = self.client.post(reverse('public_form', args=[self.form.slug]), {
            'email': 'k@example.com', 'verification_code': '222333',
        })
        self.assertEqual(response.status_code, 200)
        order = RegistrationOrder.objects.get(event=self.event)
        self.assertEqual(order.total_after_reduction, Decimal('1000.00'))
        self.assertFalse(order.receipt_file)

    def test_paid_submission_requires_receipt(self):
        self._enable_blocs()
        response = self.client.post(reverse('public_form', args=[self.form.slug]), {
            'first_name': 'Karim', 'last_name': 'B', 'email': 'k@example.com',
            'items_status': str(self.item.id), 'accept_conditions': '1',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(RegistrationOrder.objects.filter(event=self.event).exists())
        self.assertContains(response, 'quittance de banque')

    def test_paid_submission_requires_conditions(self):
        self._enable_blocs()
        receipt = _Upload('receipt.pdf', b'%PDF-1.4 fake', content_type='application/pdf')
        response = self.client.post(reverse('public_form', args=[self.form.slug]), {
            'first_name': 'Karim', 'last_name': 'B', 'email': 'k@example.com',
            'items_status': str(self.item.id), 'receipt_file': receipt,
        })
        self.assertFalse(RegistrationOrder.objects.filter(event=self.event).exists())
        self.assertContains(response, 'accepter les conditions')

    def test_single_select_rejects_multiple(self):
        EventBlocConfig.objects.create(event=self.event, show_status=True, status_select_mode='single')
        item2 = BlocItem.objects.create(event=self.event, bloc='status', name='Student', price=Decimal('500'))
        receipt = _Upload('receipt.pdf', b'%PDF-1.4 fake', content_type='application/pdf')
        response = self.client.post(reverse('public_form', args=[self.form.slug]), {
            'first_name': 'Karim', 'last_name': 'B', 'email': 'k@example.com',
            'items_status': [str(self.item.id), str(item2.id)],
            'accept_conditions': '1', 'receipt_file': receipt,
        })
        self.assertFalse(RegistrationOrder.objects.filter(event=self.event).exists())
        self.assertContains(response, 'une seule option')

    def test_status_selection_is_required(self):
        self._enable_blocs()
        receipt = _Upload('receipt.pdf', b'%PDF-1.4 fake', content_type='application/pdf')
        response = self.client.post(reverse('public_form', args=[self.form.slug]), {
            'first_name': 'Karim', 'last_name': 'B', 'email': 'k@example.com',
            # items_status omitted entirely -- no status picked.
            'accept_conditions': '1', 'receipt_file': receipt,
        })
        self.assertFalse(RegistrationOrder.objects.filter(event=self.event).exists())
        self.assertContains(response, 'Veuillez sélectionner une option')

    def test_no_period_switcher_without_periods(self):
        self._enable_blocs()
        response = self.client.get(reverse('public_form', args=[self.form.slug]))
        # The CSS rule always exists in <style>; the actual switcher element
        # (with this id) is only rendered when periods exist.
        self.assertNotContains(response, 'id="period-switcher"')

    def test_period_switcher_shows_one_button_per_period(self):
        self._enable_blocs()
        config = self.event.bloc_config
        config.reduction_by_period_enabled = True
        config.save()
        today = timezone.now().date()
        self.event.reduction_periods.create(
            name='Early Bird', start_date=today - timedelta(days=1), end_date=today + timedelta(days=1),
        )
        self.event.reduction_periods.create(
            name='Regular', start_date=today + timedelta(days=10), end_date=today + timedelta(days=20),
        )
        response = self.client.get(reverse('public_form', args=[self.form.slug]))
        self.assertContains(response, 'id="period-switcher"')
        self.assertContains(response, 'Early Bird')
        self.assertContains(response, 'Regular')
        self.assertContains(response, 'class="period-btn active"')

    def test_period_switcher_bakes_preview_prices_for_every_period(self):
        self._enable_blocs()
        config = self.event.bloc_config
        config.reduction_by_period_enabled = True
        config.save()
        today = timezone.now().date()
        early = self.event.reduction_periods.create(
            name='Early Bird', start_date=today - timedelta(days=1), end_date=today + timedelta(days=1),
        )
        BlocItemStatusRule.objects.create(period=early, target_kind='item', target_item=self.item, override_price=Decimal('300'))

        response = self.client.get(reverse('public_form', args=[self.form.slug]))
        self.assertContains(response, f'"{early.id}"')
        self.assertContains(response, '300.00')


class PublicFormNeverCachedTests(TestCase):
    """
    public_form_view sits behind the site-wide page cache
    (UpdateCacheMiddleware, CACHE_MIDDLEWARE_SECONDS=300 in settings.py).
    Its GET response embeds a fresh CSRF token on every render via
    {% csrf_token %} -- if that response were ever cached, every visitor
    hitting the cache within the window would submit against a frozen
    token from someone else's page load and get a 403 "CSRF token from
    POST incorrect", silently dropping real registrations. This actually
    happened in production (reported directly against
    /forms/ASCO-2026-registrations/).

    Django's page-cache middleware decides whether to cache purely by
    looking for a numeric max-age token (django.utils.cache.get_max_age)
    -- it does NOT honor a bare 'no-cache, no-store, must-revalidate'
    Cache-Control string the way a browser would. Only @never_cache
    (which sets max-age=0) actually stops it, which is why this asserts
    the header directly rather than just checking the page renders.
    """

    def setUp(self):
        self.admin = User.objects.create_user(username='admin2', password='x', is_staff=True)
        self.event = Event.objects.create(
            name="Congress", start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=2), location="Algiers",
        )
        self.form = FormConfiguration.objects.create(
            name="Reg", slug="reg2", event=self.event, created_by=self.admin,
            fields_config=[{'name': 'email', 'label': 'Email', 'type': 'email', 'required': True}],
        )

    def test_response_carries_max_age_zero(self):
        from django.utils.cache import get_max_age

        response = self.client.get(reverse('public_form', args=[self.form.slug]))
        self.assertEqual(get_max_age(response), 0)

    def test_closed_form_response_also_carries_max_age_zero(self):
        from django.utils.cache import get_max_age

        self.form.is_active = False
        self.form.save(update_fields=['is_active'])

        response = self.client.get(reverse('public_form', args=[self.form.slug]))
        self.assertEqual(get_max_age(response), 0)


class BlocsAdminTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username='admin', password='x', is_staff=True)
        self.plain = User.objects.create_user(username='plain', password='x')
        self.event = Event.objects.create(
            name="Congress", start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=2), location="Algiers",
        )

    def test_config_page_requires_staff(self):
        self.client.force_login(self.plain)
        response = self.client.get(reverse('dashboard:blocs_config', args=[self.event.id]))
        self.assertNotEqual(response.status_code, 200)  # redirected to login

    def test_staff_can_open_config(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse('dashboard:blocs_config', args=[self.event.id]))
        self.assertEqual(response.status_code, 200)

    def test_save_config_toggles(self):
        self.client.force_login(self.admin)
        self.client.post(reverse('dashboard:blocs_config_save', args=[self.event.id]), {
            'show_status': 'on', 'reduction_by_blocs_enabled': 'on',
            'reduction_2_blocs': '15', 'reduction_3_blocs': '25', 'reduction_4_blocs': '30',
            'status_select_mode': 'single',
        })
        config = EventBlocConfig.objects.get(event=self.event)
        self.assertTrue(config.show_status)
        self.assertFalse(config.show_restauration)
        self.assertTrue(config.reduction_by_blocs_enabled)
        self.assertEqual(config.reduction_2_blocs, Decimal('15'))

    def test_require_payment_proof_defaults_true_and_is_toggleable(self):
        config = EventBlocConfig.objects.create(event=self.event)
        self.assertTrue(config.require_payment_proof)

        self.client.force_login(self.admin)
        self.client.post(reverse('dashboard:blocs_config_save', args=[self.event.id]), {
            'status_select_mode': 'single',
            # require_payment_proof omitted -> unchecked
        })
        config.refresh_from_db()
        self.assertFalse(config.require_payment_proof)

        self.client.post(reverse('dashboard:blocs_config_save', args=[self.event.id]), {
            'status_select_mode': 'single', 'require_payment_proof': 'on',
        })
        config.refresh_from_db()
        self.assertTrue(config.require_payment_proof)

    def test_create_and_delete_item(self):
        self.client.force_login(self.admin)
        self.client.post(reverse('dashboard:bloc_item_save', args=[self.event.id]), {
            'bloc': 'restauration', 'name': 'Dinner', 'price': '800', 'order': '0',
        })
        item = BlocItem.objects.get(event=self.event, name='Dinner')
        self.assertEqual(item.price, Decimal('800'))
        self.assertEqual(item.description, '')
        self.client.post(reverse('dashboard:bloc_item_delete', args=[item.id]))
        self.assertFalse(BlocItem.objects.filter(id=item.id).exists())

    def test_item_description_is_optional_and_editable(self):
        self.client.force_login(self.admin)
        self.client.post(reverse('dashboard:bloc_item_save', args=[self.event.id]), {
            'bloc': 'restauration', 'name': 'Dinner', 'price': '800', 'order': '0',
            'description': 'Includes 3 courses and a drink.',
        })
        item = BlocItem.objects.get(event=self.event, name='Dinner')
        self.assertEqual(item.description, 'Includes 3 courses and a drink.')

        self.client.post(reverse('dashboard:bloc_item_save', args=[self.event.id]), {
            'item_id': item.id, 'bloc': 'restauration', 'name': 'Dinner', 'price': '800', 'order': '0',
            'description': 'Updated description.',
        })
        item.refresh_from_db()
        self.assertEqual(item.description, 'Updated description.')

    def test_create_and_edit_reduction_period(self):
        self.client.force_login(self.admin)
        self.client.post(reverse('dashboard:reduction_period_save', args=[self.event.id]), {
            'name': 'Early bird', 'start_date': '2026-01-01', 'end_date': '2026-01-31',
        })
        period = ReductionPeriod.objects.get(event=self.event, name='Early bird')
        self.assertEqual(str(period.start_date), '2026-01-01')
        self.assertEqual(str(period.end_date), '2026-01-31')

        self.client.post(reverse('dashboard:reduction_period_save', args=[self.event.id]), {
            'period_id': period.id, 'name': 'Early bird', 'start_date': '2026-02-01', 'end_date': '2026-02-15',
        })
        period.refresh_from_db()
        self.assertEqual(str(period.start_date), '2026-02-01')
        self.assertEqual(str(period.end_date), '2026-02-15')
        # Editing must not create a second row.
        self.assertEqual(ReductionPeriod.objects.filter(event=self.event).count(), 1)

    def test_workshop_order_save_and_public_page_respects_it(self):
        room = Room.objects.create(event=self.event, name='R1', capacity=50, location='Hall')
        session_a = Session.objects.create(
            event=self.event, room=room, title='Workshop A',
            start_time=timezone.now(), end_time=timezone.now() + timedelta(hours=1),
            is_paid=True, price=Decimal('300'),
        )
        session_b = Session.objects.create(
            event=self.event, room=room, title='Workshop B',
            start_time=timezone.now() + timedelta(hours=2), end_time=timezone.now() + timedelta(hours=3),
            is_paid=True, price=Decimal('300'),
        )

        self.client.force_login(self.admin)
        self.client.post(reverse('dashboard:workshop_order_save', args=[self.event.id]), {
            f'order_{session_a.id}': '2',
            f'order_{session_b.id}': '1',
        })
        session_a.refresh_from_db()
        session_b.refresh_from_db()
        self.assertEqual(session_a.order, 2)
        self.assertEqual(session_b.order, 1)

        from .views_blocs import get_public_bloc_context
        EventBlocConfig.objects.create(event=self.event, show_workshops=True)
        bloc_context = get_public_bloc_context(self.event)
        self.assertEqual(
            [s.title for s in bloc_context['paid_sessions']], ['Workshop B', 'Workshop A'],
        )

    def test_orders_list_is_read_only(self):
        # Admin can view submitted orders, but confirming/rejecting them now
        # only happens at the caisse (see caisse.tests) -- no admin action.
        self.client.force_login(self.admin)
        order = RegistrationOrder.objects.create(
            event=self.event, email='k@example.com', full_name='K',
            receipt_file=_Upload('r.pdf', b'x', content_type='application/pdf'),
        )
        response = self.client.get(reverse('dashboard:registration_orders', args=[self.event.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, order.email)
        self.assertNotContains(response, 'name="action" value="approve"')
        self.assertNotContains(response, 'name="action" value="reject"')


class BlocItemStatusRuleComputeOrderTests(TestCase):
    """compute_order() must respect status-dependent visibility/price
    overrides: hidden items are excluded from the cart, overridden prices
    replace the normal price (and the period/bloc-count reduction still
    applies on top of it)."""

    def setUp(self):
        self.event = Event.objects.create(
            name="Congress", start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=2), location="Algiers",
        )
        self.config = EventBlocConfig.objects.create(
            event=self.event, show_status=True, show_restauration=True,
        )
        self.status_a = BlocItem.objects.create(event=self.event, bloc='status', name='Student', price=Decimal('0'))
        self.status_b = BlocItem.objects.create(event=self.event, bloc='status', name='Adherent', price=Decimal('0'))
        self.dinner = BlocItem.objects.create(event=self.event, bloc='restauration', name='Dinner', price=Decimal('1000'))

    def _compute(self, status_id, item_ids=()):
        return compute_order(
            event=self.event, config=self.config,
            selected_item_ids=[status_id, *item_ids], selected_session_ids=[],
            on_date=timezone.now().date(),
        )

    def test_no_rule_means_visible_at_normal_price(self):
        result = self._compute(self.status_a.id, [self.dinner.id])
        self.assertEqual(result['total_before_reduction'], Decimal('1000.00'))
        self.assertEqual(len(result['snapshot']), 2)  # status + dinner

    def test_hidden_item_excluded_from_cart(self):
        BlocItemStatusRule.objects.create(
            status_item=self.status_a, target_kind='item', target_item=self.dinner, is_visible=False,
        )
        result = self._compute(self.status_a.id, [self.dinner.id])
        self.assertEqual(result['total_before_reduction'], Decimal('0.00'))
        self.assertEqual(len(result['snapshot']), 1)  # only status, dinner excluded

    def test_hidden_for_one_status_but_visible_for_another(self):
        BlocItemStatusRule.objects.create(
            status_item=self.status_a, target_kind='item', target_item=self.dinner, is_visible=False,
        )
        result = self._compute(self.status_b.id, [self.dinner.id])
        self.assertEqual(result['total_before_reduction'], Decimal('1000.00'))

    def test_price_override_applies_and_stacks_with_blocs_reduction(self):
        self.config.reduction_by_blocs_enabled = True
        self.config.reduction_2_blocs = Decimal('10')
        self.config.save()
        BlocItemStatusRule.objects.create(
            status_item=self.status_b, target_kind='item', target_item=self.dinner, override_price=Decimal('500'),
        )
        result = self._compute(self.status_b.id, [self.dinner.id])
        self.assertEqual(result['total_before_reduction'], Decimal('500.00'))
        self.assertEqual(result['blocs_discount_percent'], Decimal('10.00'))
        # 500 - 10% = 450
        self.assertEqual(result['total_after_reduction'], Decimal('450.00'))

    def test_period_price_takes_precedence_and_status_layers_per_period(self):
        # "period price is the base; status overrides must be set per
        # period" -- a rule scoped to (status, period) beats a status-only
        # rule that applies across all periods.
        period = ReductionPeriod.objects.create(
            event=self.event, start_date=timezone.now().date() - timedelta(days=1),
            end_date=timezone.now().date() + timedelta(days=1),
        )
        self.config.reduction_by_period_enabled = True
        self.config.save()
        # Status-only rule (any period): Dinner costs 800 for Adherent.
        BlocItemStatusRule.objects.create(
            status_item=self.status_b, target_kind='item', target_item=self.dinner, override_price=Decimal('800'),
        )
        # More specific: during THIS period, Adherent's Dinner costs 300 instead.
        BlocItemStatusRule.objects.create(
            status_item=self.status_b, period=period, target_kind='item', target_item=self.dinner,
            override_price=Decimal('300'),
        )
        result = self._compute(self.status_b.id, [self.dinner.id])
        self.assertEqual(result['total_before_reduction'], Decimal('300.00'))


class BlocStatusRulesAdminTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username='admin', password='x', is_staff=True)
        self.event = Event.objects.create(
            name="Congress", start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=2), location="Algiers",
        )
        EventBlocConfig.objects.create(event=self.event, show_status=True, show_restauration=True)
        self.status_a = BlocItem.objects.create(event=self.event, bloc='status', name='Student', price=Decimal('0'))
        self.dinner = BlocItem.objects.create(event=self.event, bloc='restauration', name='Dinner', price=Decimal('1000'))

    def test_config_page_shows_matrix(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse('dashboard:blocs_config', args=[self.event.id]))
        self.assertContains(response, 'Status-dependent rules')
        self.assertContains(response, 'Student')
        self.assertContains(response, 'Dinner')

    def test_save_view_get_redirects_instead_of_405(self):
        # A stray GET (refresh, back/forward nav, a stale bookmark) on this
        # save-only endpoint should bounce back to the config page, not
        # show a raw 405 error.
        self.client.force_login(self.admin)
        response = self.client.get(reverse('dashboard:bloc_status_rules_save', args=[self.event.id]))
        self.assertRedirects(response, reverse('dashboard:blocs_config', args=[self.event.id]))

    def test_save_hides_item_and_sets_price(self):
        self.client.force_login(self.admin)
        self.client.post(reverse('dashboard:bloc_status_rules_save', args=[self.event.id]), {
            f'price_{self.status_a.id}_any_item_{self.dinner.id}': '750',
            # visible checkbox omitted -> hidden
        })
        rule = BlocItemStatusRule.objects.get(status_item=self.status_a, period__isnull=True, target_item=self.dinner)
        self.assertFalse(rule.is_visible)
        self.assertEqual(rule.override_price, Decimal('750.00'))

    def test_save_default_state_removes_rule(self):
        BlocItemStatusRule.objects.create(
            status_item=self.status_a, target_kind='item', target_item=self.dinner, is_visible=False,
        )
        self.client.force_login(self.admin)
        self.client.post(reverse('dashboard:bloc_status_rules_save', args=[self.event.id]), {
            f'visible_{self.status_a.id}_any_item_{self.dinner.id}': 'on',
        })
        self.assertFalse(
            BlocItemStatusRule.objects.filter(status_item=self.status_a, target_item=self.dinner).exists()
        )

    def test_save_period_pricing_matrix(self):
        period = self.event.reduction_periods.create(
            name='Early bird', start_date=timezone.now().date(), end_date=timezone.now().date() + timedelta(days=1),
        )
        config = self.event.bloc_config
        config.reduction_by_period_enabled = True
        config.save()

        self.client.force_login(self.admin)
        response = self.client.get(reverse('dashboard:blocs_config', args=[self.event.id]))
        self.assertContains(response, 'Period pricing')
        self.assertContains(response, 'Any status')

        self.client.post(reverse('dashboard:bloc_status_rules_save', args=[self.event.id]), {
            f'visible_any_{period.id}_item_{self.status_a.id}': 'on',
            f'price_any_{period.id}_item_{self.status_a.id}': '2000',
            f'visible_any_{period.id}_item_{self.dinner.id}': 'on',
            f'price_any_{period.id}_item_{self.dinner.id}': '300',
        })
        status_rule = BlocItemStatusRule.objects.get(
            status_item__isnull=True, period=period, target_item=self.status_a,
        )
        self.assertTrue(status_rule.is_visible)
        self.assertEqual(status_rule.override_price, Decimal('2000.00'))
        dinner_rule = BlocItemStatusRule.objects.get(
            status_item__isnull=True, period=period, target_item=self.dinner,
        )
        self.assertEqual(dinner_rule.override_price, Decimal('300.00'))


class EventOwnerSubmissionsTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username='admin', password='x', is_staff=True)
        self.owner = User.objects.create_user(username='owner', email='owner@example.com', password='x')
        self.stranger = User.objects.create_user(username='stranger', password='x')
        self.event = Event.objects.create(
            name="Congress", start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=2), location="Algiers",
        )
        self.other_event = Event.objects.create(
            name="Other Congress", start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=2), location="Oran",
        )
        UserEventAssignment.objects.create(
            user=self.owner, event=self.event, role='event_owner', is_active=True,
        )
        status_item = BlocItem.objects.create(event=self.event, bloc='status', name='Membre', price=Decimal('0'))
        receipt = _Upload('receipt.pdf', b'%PDF-1.4 fake', content_type='application/pdf')
        self.order = RegistrationOrder.objects.create(
            event=self.event, full_name='Karim B', email='k@example.com',
            items_snapshot=[
                {'bloc': 'status', 'type': 'item', 'id': status_item.id, 'name': 'Membre', 'price': '0'},
                {'bloc': 'restauration', 'type': 'item', 'id': 99, 'name': 'Dinner', 'price': '800'},
            ],
            total_before_reduction=Decimal('800'), total_after_reduction=Decimal('800'),
            receipt_file=receipt,
        )

    def test_owner_sees_only_their_own_event(self):
        self.client.force_login(self.owner)
        response = self.client.get(reverse('dashboard:event_owner_submissions', args=[self.event.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Karim B')
        self.assertContains(response, 'Membre')
        self.assertContains(response, 'Dinner')

    def test_owner_cannot_view_a_different_event(self):
        self.client.force_login(self.owner)
        response = self.client.get(reverse('dashboard:event_owner_submissions', args=[self.other_event.id]))
        self.assertEqual(response.status_code, 403)

    def test_stranger_without_assignment_is_forbidden(self):
        self.client.force_login(self.stranger)
        response = self.client.get(reverse('dashboard:event_owner_submissions', args=[self.event.id]))
        self.assertEqual(response.status_code, 403)

    def test_staff_can_view_any_event(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse('dashboard:event_owner_submissions', args=[self.event.id]))
        self.assertEqual(response.status_code, 200)

    def test_home_redirects_straight_to_the_only_owned_event(self):
        self.client.force_login(self.owner)
        response = self.client.get(reverse('dashboard:event_owner_submissions_home'))
        self.assertRedirects(response, reverse('dashboard:event_owner_submissions', args=[self.event.id]))

    def test_home_shows_picker_for_multiple_events(self):
        UserEventAssignment.objects.create(
            user=self.owner, event=self.other_event, role='event_owner', is_active=True,
        )
        self.client.force_login(self.owner)
        response = self.client.get(reverse('dashboard:event_owner_submissions_home'))
        self.assertContains(response, self.event.name)
        self.assertContains(response, self.other_event.name)

    def test_login_allows_event_owner_and_redirects_to_submissions(self):
        response = self.client.post(reverse('dashboard:login'), {
            'email': 'owner@example.com', 'password': 'x',
        })
        self.assertRedirects(response, reverse('dashboard:event_owner_submissions_home'))

    def _create_order_with_participant(self):
        """A registration order with a real participant + workshop session,
        for exercising confirm/cancel/delete's real side effects."""
        participant_user = User.objects.create_user(username='participant1', email='p1@example.com', password='x')
        participant = Participant.objects.create(user=participant_user, badge_id='BADGE-1')
        UserEventAssignment.objects.create(
            user=participant_user, event=self.event, role='participant', is_active=True,
        )
        ParticipantEventRegistration.objects.create(participant=participant, event=self.event)

        status_item = BlocItem.objects.create(event=self.event, bloc='status', name='Adherent', price=Decimal('0'))
        room = Room.objects.create(event=self.event, name='R1', capacity=50, location='Hall')
        session = Session.objects.create(
            event=self.event, room=room, title='Workshop A',
            start_time=timezone.now(), end_time=timezone.now() + timedelta(hours=1),
            is_paid=True, price=Decimal('300'),
        )
        order = RegistrationOrder.objects.create(
            event=self.event, participant=participant, full_name='Real Participant', email='p1@example.com',
            items_snapshot=[
                {'bloc': 'status', 'type': 'item', 'id': status_item.id, 'name': 'Adherent', 'price': '0'},
                {'bloc': 'workshops', 'type': 'session', 'id': str(session.id), 'name': 'Workshop A', 'price': '300'},
            ],
            total_before_reduction=Decimal('300'), total_after_reduction=Decimal('300'),
            receipt_file=_Upload('receipt.pdf', b'%PDF-1.4 fake', content_type='application/pdf'),
        )
        return order, participant, participant_user, session

    def test_confirm_creates_real_transaction_and_grants_session_access(self):
        from caisse.models import CaisseTransaction
        from events.models import SessionAccess

        order, participant, _user, session = self._create_order_with_participant()
        self.client.force_login(self.owner)
        self.client.post(reverse('dashboard:registration_status_save', args=[order.id]), {'status': 'approved'})

        order.refresh_from_db()
        self.assertEqual(order.status, 'approved')
        self.assertEqual(order.reviewed_by, self.owner)
        self.assertIsNotNone(order.caisse_transaction)
        self.assertEqual(order.caisse_transaction.status, 'completed')
        self.assertEqual(order.caisse_transaction.participant, participant)

        access = SessionAccess.objects.get(participant=participant, session=session)
        self.assertTrue(access.has_access)
        self.assertEqual(access.payment_status, 'paid')

    def test_reserved_is_bookkeeping_only(self):
        from caisse.models import CaisseTransaction

        order, _participant, _user, _session = self._create_order_with_participant()
        self.client.force_login(self.owner)
        self.client.post(reverse('dashboard:registration_status_save', args=[order.id]), {'status': 'reserved'})

        order.refresh_from_db()
        self.assertEqual(order.status, 'reserved')
        self.assertIsNone(order.caisse_transaction)
        self.assertFalse(CaisseTransaction.objects.exists())

    def test_cancel_after_confirm_voids_the_transaction(self):
        order, _participant, _user, _session = self._create_order_with_participant()
        self.client.force_login(self.owner)
        self.client.post(reverse('dashboard:registration_status_save', args=[order.id]), {'status': 'approved'})
        order.refresh_from_db()
        txn = order.caisse_transaction

        self.client.post(reverse('dashboard:registration_status_save', args=[order.id]), {'status': 'rejected'})
        order.refresh_from_db()
        txn.refresh_from_db()
        self.assertEqual(order.status, 'rejected')
        self.assertEqual(txn.status, 'cancelled')

    def test_cancel_after_confirm_revokes_session_access_including_free_workshops(self):
        """
        A FREE (price 0) workshop still gets real SessionAccess on confirm
        (it's still added to the transaction's items, just at 0 DZD) --
        cancelling must revoke that access too, same as a paid workshop's,
        not skip it just because nothing was charged for it.
        """
        from events.models import SessionAccess

        order, participant, _user, paid_session = self._create_order_with_participant()
        free_session = Session.objects.create(
            event=self.event, room=paid_session.room, title='Free Workshop',
            start_time=timezone.now(), end_time=timezone.now() + timedelta(hours=1),
            is_paid=True, price=Decimal('0'),
        )
        order.items_snapshot = order.items_snapshot + [
            {'bloc': 'workshops', 'type': 'session', 'id': str(free_session.id), 'name': 'Free Workshop', 'price': '0'},
        ]
        order.save(update_fields=['items_snapshot'])

        self.client.force_login(self.owner)
        self.client.post(reverse('dashboard:registration_status_save', args=[order.id]), {'status': 'approved'})
        self.assertTrue(SessionAccess.objects.get(participant=participant, session=paid_session).has_access)
        self.assertTrue(SessionAccess.objects.get(participant=participant, session=free_session).has_access)

        self.client.post(reverse('dashboard:registration_status_save', args=[order.id]), {'status': 'rejected'})
        self.assertFalse(SessionAccess.objects.get(participant=participant, session=paid_session).has_access)
        self.assertFalse(SessionAccess.objects.get(participant=participant, session=free_session).has_access)

    def test_reverting_confirmed_order_to_another_status_voids_its_transaction(self):
        order, _participant, _user, _session = self._create_order_with_participant()
        self.client.force_login(self.owner)
        self.client.post(reverse('dashboard:registration_status_save', args=[order.id]), {'status': 'approved'})
        order.refresh_from_db()
        txn = order.caisse_transaction
        self.assertEqual(txn.status, 'completed')

        self.client.post(reverse('dashboard:registration_status_save', args=[order.id]), {'status': 'pending'})
        order.refresh_from_db()
        txn.refresh_from_db()
        self.assertEqual(order.status, 'pending')
        self.assertEqual(txn.status, 'cancelled')

    def test_reverting_confirmed_order_revokes_session_access_including_free_workshops(self):
        from events.models import SessionAccess

        order, participant, _user, paid_session = self._create_order_with_participant()
        free_session = Session.objects.create(
            event=self.event, room=paid_session.room, title='Free Workshop',
            start_time=timezone.now(), end_time=timezone.now() + timedelta(hours=1),
            is_paid=True, price=Decimal('0'),
        )
        order.items_snapshot = order.items_snapshot + [
            {'bloc': 'workshops', 'type': 'session', 'id': str(free_session.id), 'name': 'Free Workshop', 'price': '0'},
        ]
        order.save(update_fields=['items_snapshot'])

        self.client.force_login(self.owner)
        self.client.post(reverse('dashboard:registration_status_save', args=[order.id]), {'status': 'approved'})
        self.client.post(reverse('dashboard:registration_status_save', args=[order.id]), {'status': 'pending'})

        self.assertFalse(SessionAccess.objects.get(participant=participant, session=paid_session).has_access)
        self.assertFalse(SessionAccess.objects.get(participant=participant, session=free_session).has_access)

    def test_reverting_caisse_confirmed_order_to_another_status_leaves_no_transaction_to_void(self):
        """No order.caisse_transaction means it was confirmed by a real
        physical caisse station (whose transaction can bundle several
        OTHER people's payments) -- the status change still goes through,
        same as the Cancelled path already does, there's just nothing
        here that's safe to touch."""
        order, _participant, _user, _session = self._create_order_with_participant()
        order.status = 'approved'
        order.save(update_fields=['status'])
        self.assertIsNone(order.caisse_transaction_id)

        self.client.force_login(self.owner)
        self.client.post(reverse('dashboard:registration_status_save', args=[order.id]), {'status': 'pending'})
        order.refresh_from_db()
        self.assertEqual(order.status, 'pending')

    def test_delete_revokes_only_this_events_access(self):
        order, participant, participant_user, _session = self._create_order_with_participant()
        # Same participant also registered for a second event -- must survive.
        UserEventAssignment.objects.create(
            user=participant_user, event=self.other_event, role='participant', is_active=True,
        )
        ParticipantEventRegistration.objects.create(participant=participant, event=self.other_event)

        self.client.force_login(self.owner)
        self.client.post(reverse('dashboard:registration_delete', args=[order.id]))

        self.assertFalse(RegistrationOrder.objects.filter(id=order.id).exists())
        self.assertFalse(
            UserEventAssignment.objects.filter(user=participant_user, event=self.event, is_active=True).exists()
        )
        self.assertFalse(
            ParticipantEventRegistration.objects.filter(participant=participant, event=self.event).exists()
        )
        # Other event's access untouched.
        self.assertTrue(
            UserEventAssignment.objects.filter(user=participant_user, event=self.other_event, is_active=True).exists()
        )
        self.assertTrue(
            ParticipantEventRegistration.objects.filter(participant=participant, event=self.other_event).exists()
        )
        # Global participant profile untouched.
        self.assertTrue(Participant.objects.filter(id=participant.id).exists())

    def test_delete_confirmed_requires_explicit_flag(self):
        order, _participant, _user, _session = self._create_order_with_participant()
        self.client.force_login(self.owner)
        self.client.post(reverse('dashboard:registration_status_save', args=[order.id]), {'status': 'approved'})

        self.client.post(reverse('dashboard:registration_delete', args=[order.id]))
        self.assertTrue(RegistrationOrder.objects.filter(id=order.id).exists())

        self.client.post(reverse('dashboard:registration_delete', args=[order.id]), {'confirm_paid': '1'})
        self.assertFalse(RegistrationOrder.objects.filter(id=order.id).exists())

    def test_stranger_cannot_change_status_or_delete(self):
        order, _participant, _user, _session = self._create_order_with_participant()
        self.client.force_login(self.stranger)
        response = self.client.post(
            reverse('dashboard:registration_status_save', args=[order.id]), {'status': 'approved'},
        )
        self.assertEqual(response.status_code, 403)
        response = self.client.post(reverse('dashboard:registration_delete', args=[order.id]))
        self.assertEqual(response.status_code, 403)
        self.assertTrue(RegistrationOrder.objects.filter(id=order.id).exists())

    @patch('dashboard.views_event_owner.send_email')
    def test_send_payment_link_is_remembered_across_page_loads(self, mock_send_email):
        """
        The green "already sent" confirmation must survive a reload, not
        just live in the popup's own JS for as long as it stays open --
        payment_link_sent_at is what makes that durable.
        """
        mock_send_email.return_value = (True, None, None)
        self.client.force_login(self.owner)

        self.assertIsNone(self.order.payment_link_sent_at)
        response = self.client.post(reverse('dashboard:send_payment_link_email', args=[self.order.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['ok'])

        self.order.refresh_from_db()
        self.assertIsNotNone(self.order.payment_link_sent_at)

        page = self.client.get(reverse('dashboard:event_owner_submissions', args=[self.event.id]))
        self.assertContains(page, 'Mail de préinscription envoyé le')

    @patch('dashboard.views_event_owner.send_email')
    def test_failed_payment_link_send_does_not_record_anything(self, mock_send_email):
        mock_send_email.return_value = (False, 'SMTP down', None)
        self.client.force_login(self.owner)

        response = self.client.post(reverse('dashboard:send_payment_link_email', args=[self.order.id]))
        self.assertEqual(response.status_code, 502)
        self.order.refresh_from_db()
        self.assertIsNone(self.order.payment_link_sent_at)

    def test_status_change_redirect_preserves_active_filters(self):
        """
        A plain redirect() drops whatever status/search filters were
        active, silently resetting the owner's filtered view on top of
        losing their scroll position -- the query string must survive
        the round trip.
        """
        self.client.force_login(self.owner)
        url = reverse('dashboard:registration_status_save', args=[self.order.id]) + '?status=pending&q=Karim'
        response = self.client.post(url, {'status': 'reserved'})
        expected = reverse('dashboard:event_owner_submissions', args=[self.event.id]) + '?status=pending&q=Karim'
        self.assertRedirects(response, expected)

    def test_delete_redirect_preserves_active_filters(self):
        self.client.force_login(self.owner)
        url = reverse('dashboard:registration_delete', args=[self.order.id]) + '?status=pending&q=Karim'
        response = self.client.post(url)
        expected = reverse('dashboard:event_owner_submissions', args=[self.event.id]) + '?status=pending&q=Karim'
        self.assertRedirects(response, expected)


class RegistrationOrderBlocsEditTests(TestCase):
    """
    The event owner submissions page's "edit blocs" popup -- lets an owner
    change what an already-submitted (not-yet-confirmed) registration
    picked, recomputed through the exact same compute_order() the public
    registration form itself uses.
    """

    def setUp(self):
        self.owner = User.objects.create_user(username='owner2', email='owner2@example.com', password='x')
        self.stranger = User.objects.create_user(username='stranger2', password='x')
        self.event = Event.objects.create(
            name="Bloc Congress", start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=2), location="Algiers",
        )
        UserEventAssignment.objects.create(
            user=self.owner, event=self.event, role='event_owner', is_active=True,
        )
        self.config = EventBlocConfig.objects.create(
            event=self.event, show_status=True, show_restauration=True,
            status_select_mode='single', restauration_select_mode='single',
            reduction_by_blocs_enabled=True, reduction_2_blocs=Decimal('10'), reduction_3_blocs=Decimal('20'),
        )
        self.status_a = BlocItem.objects.create(event=self.event, bloc='status', name='Membre', price=Decimal('0'))
        self.dinner = BlocItem.objects.create(event=self.event, bloc='restauration', name='Dinner', price=Decimal('1000'))
        self.lunch = BlocItem.objects.create(event=self.event, bloc='restauration', name='Lunch', price=Decimal('500'))
        self.order = RegistrationOrder.objects.create(
            event=self.event, full_name='Karim B', email='k2@example.com',
            items_snapshot=[
                {'bloc': 'status', 'type': 'item', 'id': self.status_a.id, 'name': 'Membre', 'price': '0'},
            ],
            total_before_reduction=Decimal('0'), total_after_reduction=Decimal('0'),
        )

    def _save(self, user, order, data):
        self.client.force_login(user)
        return self.client.post(reverse('dashboard:registration_order_blocs_save', args=[order.id]), data)

    def test_page_renders_editor_button_and_shared_modal(self):
        self.client.force_login(self.owner)
        response = self.client.get(reverse('dashboard:event_owner_submissions', args=[self.event.id]))
        self.assertContains(response, 'blocs-editor-modal')
        self.assertContains(response, 'openBlocsEditor')
        self.assertContains(response, 'Dinner')

    def test_owner_can_add_a_bloc_item_and_total_recomputes(self):
        response = self._save(self.owner, self.order, {
            'items_status': [str(self.status_a.id)],
            'items_restauration': [str(self.dinner.id)],
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['ok'])

        self.order.refresh_from_db()
        self.assertEqual(self.order.total_before_reduction, Decimal('1000.00'))
        # Only Restauration is a real second bloc here (Status never counts) --
        # not enough for the 2-bloc discount tier, matches compute_order.
        self.assertEqual(self.order.total_after_reduction, Decimal('1000.00'))
        item_ids = {it['id'] for it in self.order.items_snapshot}
        self.assertEqual(item_ids, {self.status_a.id, self.dinner.id})

    def test_matches_compute_order_directly(self):
        """
        The view's math must be compute_order()'s math, not a
        reimplementation of it -- assert the two agree exactly rather than
        hardcoding an expected total that could silently drift from
        whatever compute_order actually does.
        """
        self._save(self.owner, self.order, {
            'items_status': [str(self.status_a.id)],
            'items_restauration': [str(self.lunch.id)],
        })
        self.order.refresh_from_db()

        expected = compute_order(
            event=self.event, config=self.config,
            selected_item_ids=[str(self.status_a.id), str(self.lunch.id)],
            selected_session_ids=[],
            on_date=timezone.now().date(),
        )
        self.assertEqual(self.order.total_after_reduction, expected['total_after_reduction'])
        self.assertEqual(self.order.total_before_reduction, expected['total_before_reduction'])

    def test_status_is_mandatory(self):
        response = self._save(self.owner, self.order, {
            'items_restauration': [str(self.dinner.id)],
        })
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()['ok'])
        self.order.refresh_from_db()
        self.assertEqual(self.order.total_after_reduction, Decimal('0'))  # unchanged

    def test_single_select_bloc_rejects_multiple_picks(self):
        response = self._save(self.owner, self.order, {
            'items_status': [str(self.status_a.id)],
            'items_restauration': [str(self.dinner.id), str(self.lunch.id)],
        })
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()['ok'])

    def test_cannot_edit_an_already_confirmed_order(self):
        self.order.status = 'approved'
        self.order.save(update_fields=['status'])

        response = self._save(self.owner, self.order, {
            'items_status': [str(self.status_a.id)],
            'items_restauration': [str(self.dinner.id)],
        })
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()['ok'])
        self.order.refresh_from_db()
        self.assertEqual(self.order.total_after_reduction, Decimal('0'))  # unchanged

    def test_stranger_cannot_edit_blocs(self):
        response = self._save(self.stranger, self.order, {
            'items_status': [str(self.status_a.id)],
        })
        self.assertEqual(response.status_code, 403)

    def test_deactivated_item_still_shown_selectable_in_editor(self):
        """
        Unlike the public form, the owner's edit popup must keep listing
        an item after it's deactivated, so they can still add/remove it
        on an existing registration (e.g. one picked before it was
        discontinued).
        """
        self.lunch.is_active = False
        self.lunch.save(update_fields=['is_active'])

        self.client.force_login(self.owner)
        response = self.client.get(reverse('dashboard:event_owner_submissions', args=[self.event.id]))
        self.assertContains(response, 'Lunch')
        self.assertContains(response, 'Désactivé')

    def test_public_form_context_still_hides_deactivated_items(self):
        """include_inactive is opt-in -- the public form's own context call
        (no flag) must keep excluding a deactivated item even though the
        owner's editor now shows it, otherwise this would leak into
        participant-facing registration."""
        from .views_blocs import get_public_bloc_context
        self.lunch.is_active = False
        self.lunch.save(update_fields=['is_active'])

        context = get_public_bloc_context(self.event)
        names = {item.name for bloc in context['custom_blocs'] for item in bloc['items']}
        self.assertNotIn('Lunch', names)

    def test_owner_can_select_a_deactivated_item_and_price_applies(self):
        self.lunch.is_active = False
        self.lunch.save(update_fields=['is_active'])

        response = self._save(self.owner, self.order, {
            'items_status': [str(self.status_a.id)],
            'items_restauration': [str(self.lunch.id)],
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['ok'])
        self.order.refresh_from_db()
        self.assertEqual(self.order.total_before_reduction, Decimal('500.00'))
        item_ids = {it['id'] for it in self.order.items_snapshot}
        self.assertIn(self.lunch.id, item_ids)

    def test_edit_prices_against_the_orders_own_period_not_todays(self):
        """
        RegistrationOrder.period is a snapshot of whichever period was
        active when the order was placed. Editing it must keep pricing
        against THAT period, not whatever period happens to be active
        today -- otherwise an old registration would silently get
        repriced at today's rates just by touching its blocs.
        """
        self.config.reduction_by_period_enabled = True
        self.config.save(update_fields=['reduction_by_period_enabled'])
        today = timezone.now().date()
        old_period = ReductionPeriod.objects.create(
            event=self.event, name='Early bird',
            start_date=today - timedelta(days=30), end_date=today - timedelta(days=20),
        )
        current_period = ReductionPeriod.objects.create(
            event=self.event, name='Standard',
            start_date=today - timedelta(days=1), end_date=today + timedelta(days=1),
        )
        BlocItemStatusRule.objects.create(
            period=old_period, target_kind='item', target_item=self.lunch, override_price=Decimal('200'),
        )
        BlocItemStatusRule.objects.create(
            period=current_period, target_kind='item', target_item=self.lunch, override_price=Decimal('900'),
        )
        self.order.period = old_period
        self.order.save(update_fields=['period'])

        response = self._save(self.owner, self.order, {
            'items_status': [str(self.status_a.id)],
            'items_restauration': [str(self.lunch.id)],
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['ok'])
        self.order.refresh_from_db()
        self.assertEqual(self.order.total_before_reduction, Decimal('200.00'))
        self.assertEqual(self.order.period_id, old_period.id)

    def test_period_rules_payload_is_keyed_by_each_orders_own_period(self):
        """
        The blocs-editor popup needs each row's OWN period's rules, not one
        shared 'today' ruleset -- otherwise the live price preview couldn't
        match what registration_order_blocs_save() actually saves once it's
        pinned to the order's period.
        """
        import json
        from .views_event_owner import _period_rules_by_period_json

        self.config.reduction_by_period_enabled = True
        self.config.save(update_fields=['reduction_by_period_enabled'])
        today = timezone.now().date()
        old_period = ReductionPeriod.objects.create(
            event=self.event, name='Early bird',
            start_date=today - timedelta(days=30), end_date=today - timedelta(days=20),
        )
        BlocItemStatusRule.objects.create(
            period=old_period, target_kind='item', target_item=self.lunch, override_price=Decimal('200'),
        )
        self.order.period = old_period
        self.order.save(update_fields=['period'])

        payload = json.loads(_period_rules_by_period_json(self.event, [self.order]))
        self.assertIn(str(old_period.id), payload)
        rule = payload[str(old_period.id)]['period'][f'item_{self.lunch.id}']
        self.assertEqual(rule['price'], '200.00')

    def test_owner_can_select_an_item_hidden_by_a_status_visibility_rule(self):
        """
        A BlocItemStatusRule.is_visible=False rule is meant to steer what
        a PARTICIPANT sees for their chosen status (e.g. "students can't
        pick the VIP dinner") -- it must not also stop the owner from
        manually granting that same item on an existing registration.
        """
        BlocItemStatusRule.objects.create(
            status_item=self.status_a, target_kind='item', target_item=self.dinner, is_visible=False,
        )
        # Control: compute_order() itself (participant-facing default,
        # ignore_visibility_rules=False) still drops it -- this isn't a
        # bug in the gate, only a deliberate bypass for the owner's edit
        # endpoint below.
        participant_result = compute_order(
            event=self.event, config=self.config,
            selected_item_ids=[str(self.status_a.id), str(self.dinner.id)],
            selected_session_ids=[], on_date=timezone.now().date(),
        )
        self.assertEqual(participant_result['total_before_reduction'], Decimal('0.00'))

        response = self._save(self.owner, self.order, {
            'items_status': [str(self.status_a.id)],
            'items_restauration': [str(self.dinner.id)],
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['ok'])
        self.order.refresh_from_db()
        self.assertEqual(self.order.total_before_reduction, Decimal('1000.00'))
        item_ids = {it['id'] for it in self.order.items_snapshot}
        self.assertIn(self.dinner.id, item_ids)

    def _confirm_order_for_real(self):
        """
        Link self.order to a real Participant and confirm it through
        confirm_registration_order() directly, exactly like the "Confirmé"
        status transition does -- gives a real CaisseTransaction + (via a
        paid session) real SessionAccess to edit against below.
        """
        from caisse.services import confirm_registration_order

        participant_user = User.objects.create_user(username='participant2', email='p2@example.com', password='x')
        participant = Participant.objects.create(user=participant_user, badge_id='BADGE-2')
        UserEventAssignment.objects.create(
            user=participant_user, event=self.event, role='participant', is_active=True,
        )
        ParticipantEventRegistration.objects.create(participant=participant, event=self.event)

        self.config.show_workshops = True
        self.config.save(update_fields=['show_workshops'])
        room = Room.objects.create(event=self.event, name='R1', capacity=50, location='Hall')
        session = Session.objects.create(
            event=self.event, room=room, title='Workshop A',
            start_time=timezone.now(), end_time=timezone.now() + timedelta(hours=1),
            is_paid=True, price=Decimal('300'),
        )

        self.order.participant = participant
        self.order.save(update_fields=['participant'])
        confirm_registration_order(self.order, confirmed_by=self.owner)
        self.order.refresh_from_db()
        return participant, session

    def test_confirmed_order_shows_edit_button_not_lock(self):
        self._confirm_order_for_real()
        self.client.force_login(self.owner)
        response = self.client.get(reverse('dashboard:event_owner_submissions', args=[self.event.id]))
        self.assertContains(response, 'openBlocsEditor')
        self.assertNotContains(response, 'Confirmée directement à la caisse')

    def test_editing_a_confirmed_order_replaces_its_transaction(self):
        from caisse.models import CaisseTransaction

        participant, session = self._confirm_order_for_real()
        old_txn = self.order.caisse_transaction
        self.assertIsNotNone(old_txn)
        self.assertEqual(old_txn.status, 'completed')

        response = self._save(self.owner, self.order, {
            'items_status': [str(self.status_a.id)],
            'items_restauration': [str(self.dinner.id)],
            'sessions': [str(session.id)],
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['ok'])

        old_txn.refresh_from_db()
        self.assertEqual(old_txn.status, 'cancelled')

        self.order.refresh_from_db()
        new_txn = self.order.caisse_transaction
        self.assertNotEqual(new_txn.id, old_txn.id)
        self.assertEqual(new_txn.status, 'completed')
        # dinner (1000) + workshop (300) = 1300 before reduction, but that's
        # now 2 distinct blocs (restauration + workshops) -- the config's
        # reduction_2_blocs=10% applies, same math as any other edit.
        self.assertEqual(self.order.total_before_reduction, Decimal('1300.00'))
        self.assertEqual(new_txn.total_amount, Decimal('1170.00'))
        self.assertEqual(self.order.total_after_reduction, Decimal('1170.00'))
        self.assertEqual(CaisseTransaction.objects.filter(status='completed', participant=participant).count(), 1)

    def test_editing_a_confirmed_order_grants_and_revokes_session_access(self):
        from events.models import SessionAccess

        participant, session = self._confirm_order_for_real()
        # Not part of the order yet -- add it.
        self._save(self.owner, self.order, {
            'items_status': [str(self.status_a.id)],
            'sessions': [str(session.id)],
        })
        access = SessionAccess.objects.get(participant=participant, session=session)
        self.assertTrue(access.has_access)
        self.assertEqual(access.payment_status, 'paid')

        # Now remove it again.
        self._save(self.owner, self.order, {
            'items_status': [str(self.status_a.id)],
        })
        access.refresh_from_db()
        self.assertFalse(access.has_access)

    def test_caisse_confirmed_order_without_transaction_stays_locked(self):
        """
        An order confirmed by a real physical caisse station never sets
        RegistrationOrder.caisse_transaction (that transaction can bundle
        several OTHER people's payments) -- editing must stay blocked for
        those, unlike an owner-confirmed order.
        """
        self.order.status = 'approved'
        self.order.save(update_fields=['status'])
        self.assertIsNone(self.order.caisse_transaction_id)

        response = self._save(self.owner, self.order, {
            'items_status': [str(self.status_a.id)],
            'items_restauration': [str(self.dinner.id)],
        })
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()['ok'])

    def test_owner_can_deselect_a_now_deactivated_item(self):
        """The participant originally picked Lunch; it's since been
        deactivated; the owner should still be able to remove it."""
        self.lunch.is_active = False
        self.lunch.save(update_fields=['is_active'])
        self.order.items_snapshot = [
            {'bloc': 'status', 'type': 'item', 'id': self.status_a.id, 'name': 'Membre', 'price': '0'},
            {'bloc': 'restauration', 'type': 'item', 'id': self.lunch.id, 'name': 'Lunch', 'price': '500'},
        ]
        self.order.save(update_fields=['items_snapshot'])

        response = self._save(self.owner, self.order, {
            'items_status': [str(self.status_a.id)],
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['ok'])
        self.order.refresh_from_db()
        item_ids = {it['id'] for it in self.order.items_snapshot}
        self.assertNotIn(self.lunch.id, item_ids)


class CampaignImportFormSubmissionsTests(TestCase):
    """
    campaign_import_form_submissions used to filter on
    FormSubmission.status='approved' -- a field the real (bloc/paid)
    registration flow never sets, so it always found zero rows regardless
    of how many people had actually registered. See views_email.py.
    """

    def setUp(self):
        self.admin = User.objects.create_user(
            username='admin', email='admin@example.com', password='x', is_staff=True,
        )
        self.event = Event.objects.create(
            name="Congress", start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=2), location="Algiers",
        )
        self.form = FormConfiguration.objects.create(
            name="Reg", slug="campaign-import-reg", event=self.event, created_by=self.admin,
            fields_config=[{'name': 'email', 'label': 'Email', 'type': 'email', 'required': True}],
        )

        from .models_email import EmailCampaign, EmailRecipient
        self.EmailRecipient = EmailRecipient
        self.campaign = EmailCampaign.objects.create(
            name="Reminder", event=self.event, subject="Hello",
            from_email="noreply@example.com", body_html="<p>Hi</p>",
        )
        self.client.force_login(self.admin)

    def _submission(self, email, days_ago, status='pending', data=None):
        submission = FormSubmission.objects.create(
            form=self.form, email=email, data=data or {},
        )
        if status != 'pending':
            submission.status = status
            submission.save(update_fields=['status'])
        FormSubmission.objects.filter(pk=submission.pk).update(
            submitted_at=timezone.now() - timedelta(days=days_ago)
        )
        return submission

    def _import(self):
        return self.client.post(
            reverse('dashboard:campaign_import_form_submissions', args=[self.campaign.id])
        )

    def test_query_count_does_not_scale_with_submission_count(self):
        """Regression guard for the production incident: the import used
        to run an exists() check plus a create() per submission, so 600+
        submissions meant 1200+ round trips to Postgres -- slow enough to
        blow past gunicorn's worker timeout and 500 mid-request. Must stay
        flat regardless of how many submissions there are."""
        for i in range(50):
            self._submission(f'user{i}@example.com', days_ago=1)

        with self.assertNumQueries(11):
            self._import()
        self.assertEqual(self.EmailRecipient.objects.filter(campaign=self.campaign).count(), 50)

    def test_imports_pending_submissions_not_just_approved(self):
        """This is the exact bug report: real submissions sit at the
        default 'pending' status forever, and must still be importable."""
        self._submission('a@example.com', days_ago=1)
        self._submission('b@example.com', days_ago=2)

        response = self._import()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.EmailRecipient.objects.filter(campaign=self.campaign).count(), 2)

    def test_dedupes_by_email_keeping_the_most_recent_submission(self):
        self._submission(
            'dup@example.com', days_ago=5,
            data={'first_name': 'Old', 'last_name': 'Name'},
        )
        self._submission(
            'dup@example.com', days_ago=1,
            data={'first_name': 'New', 'last_name': 'Name'},
        )

        self._import()

        recipients = self.EmailRecipient.objects.filter(campaign=self.campaign, email='dup@example.com')
        self.assertEqual(recipients.count(), 1)
        self.assertEqual(recipients.first().name, 'New Name')

    def test_excludes_rejected_and_spam_submissions(self):
        self._submission('rejected@example.com', days_ago=1, status='rejected')
        self._submission('spam@example.com', days_ago=1, status='spam')
        self._submission('good@example.com', days_ago=1)

        self._import()

        emails = set(
            self.EmailRecipient.objects.filter(campaign=self.campaign).values_list('email', flat=True)
        )
        self.assertEqual(emails, {'good@example.com'})


class CampaignSendTotalFailureTests(TestCase):
    """
    campaign_send (transactional path) used to mark the campaign 'sent'
    even when every single recipient failed -- misreporting a total
    outage as success, and leaving no way to retry since the "Envoyer"
    button only shows for status='draft'. See views_email.py.
    """

    def setUp(self):
        self.admin = User.objects.create_user(
            username='admin2', email='admin2@example.com', password='x', is_staff=True,
        )
        self.event = Event.objects.create(
            name="Congress", start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=2), location="Algiers",
        )
        from .models_email import EmailCampaign, EmailRecipient
        self.EmailCampaign = EmailCampaign
        self.EmailRecipient = EmailRecipient
        self.campaign = EmailCampaign.objects.create(
            name="Reminder", event=self.event, subject="Hello",
            from_email="noreply@example.com", body_html="<p>Hi</p>", status='draft',
        )
        self.r1 = EmailRecipient.objects.create(
            campaign=self.campaign, email='a@example.com', tracking_token='tok-a',
        )
        self.r2 = EmailRecipient.objects.create(
            campaign=self.campaign, email='b@example.com', tracking_token='tok-b',
        )

    def _send(self):
        self.client.force_login(self.admin)
        return self.client.post(
            reverse('dashboard:campaign_send', args=[self.campaign.id]),
            {'use_campaign_api': 'false'},
        )

    @patch('dashboard.brevo_client.get_brevo_client')
    def test_total_failure_reverts_to_draft_instead_of_sent(self, mock_get_client):
        mock_client = mock_get_client.return_value
        mock_client.send_transactional_email.side_effect = Exception('SMTP down')

        self._send()

        self.campaign.refresh_from_db()
        self.assertEqual(self.campaign.status, 'draft')
        self.assertEqual(self.campaign.total_sent, 0)

        statuses = set(
            self.EmailRecipient.objects.filter(campaign=self.campaign).values_list('status', flat=True)
        )
        self.assertEqual(statuses, {'pending'})

    @patch('dashboard.brevo_client.get_brevo_client')
    def test_partial_failure_still_marks_sent(self, mock_get_client):
        mock_client = mock_get_client.return_value
        mock_client.send_transactional_email.side_effect = [
            {'messageId': 'ok-1'}, Exception('SMTP down'),
        ]

        self._send()

        self.campaign.refresh_from_db()
        self.assertEqual(self.campaign.status, 'sent')
        self.assertEqual(self.campaign.total_sent, 1)

    @patch('dashboard.brevo_client.get_brevo_client')
    def test_large_list_is_sent_in_batches_of_ten(self, mock_get_client):
        """This is the production incident: a single request trying to
        send to everyone at once (600+ recipients) took long enough to
        hit gunicorn's worker timeout and 500 mid-send. Each request must
        now only process one batch, reporting back so the confirm page's
        JS can call again -- driving it exactly like that loop would."""
        mock_client = mock_get_client.return_value
        mock_client.send_transactional_email.return_value = {'messageId': 'ok'}

        for i in range(23):
            self.EmailRecipient.objects.create(
                campaign=self.campaign, email=f'batch{i}@example.com', tracking_token=f'tok-batch-{i}',
            )
        # 2 (from setUp) + 23 = 25 recipients total -> 3 batches of 10/10/5

        responses = []
        for _ in range(3):
            self.campaign.refresh_from_db()
            self.assertEqual(self.campaign.status, 'draft')
            responses.append(self._send())

        bodies = [r.json() for r in responses]
        self.assertEqual([b['done'] for b in bodies], [False, False, True])
        self.assertEqual([b['sent_this_batch'] for b in bodies], [10, 10, 5])
        self.assertEqual(mock_client.send_transactional_email.call_count, 25)

        self.campaign.refresh_from_db()
        self.assertEqual(self.campaign.status, 'sent')
        self.assertEqual(self.campaign.total_sent, 25)
        self.assertEqual(
            self.EmailRecipient.objects.filter(campaign=self.campaign, status='sent').count(), 25
        )


class EventOwnerNewRegistrationTests(TestCase):
    """
    event_owner_new_registration lets an owner create a real registration
    using the full catalog -- including BlocItems/Sessions that have since
    been deactivated on the public form (get_public_bloc_context's
    include_inactive=True). The whole point of the feature is that a
    deactivated item must still end up in the created order, so that's
    what these tests actually assert -- not just that the page loads.
    """

    def setUp(self):
        self.admin = User.objects.create_user(username='admin', password='x', is_staff=True)
        self.owner = User.objects.create_user(username='owner', email='owner@example.com', password='x')
        self.stranger = User.objects.create_user(username='stranger', password='x')
        self.event = Event.objects.create(
            name="Congress", start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=2), location="Algiers",
        )
        UserEventAssignment.objects.create(
            user=self.owner, event=self.event, role='event_owner', is_active=True,
        )
        EventBlocConfig.objects.create(
            event=self.event, show_status=True, show_restauration=True,
        )
        self.status_item = BlocItem.objects.create(event=self.event, bloc='status', name='Membre', price=Decimal('0'))
        self.discontinued_item = BlocItem.objects.create(
            event=self.event, bloc='restauration', name='Dîner de gala 2024',
            price=Decimal('1500'), is_active=False,
        )
        self.form_config = FormConfiguration.objects.create(
            name="Reg", slug="owner-new-reg", event=self.event, created_by=self.admin,
            fields_config=[
                {'name': 'first_name', 'label': 'Prénom', 'type': 'text', 'required': True},
                {'name': 'last_name', 'label': 'Nom', 'type': 'text', 'required': True},
                {'name': 'email', 'label': 'Email', 'type': 'email', 'required': True},
            ],
        )

    def _url(self, event=None):
        return reverse('dashboard:event_owner_new_registration', args=[(event or self.event).id])

    def _post(self, user, **extra_items):
        self.client.force_login(user)
        data = {
            'first_name': 'Amina', 'last_name': 'K', 'email': 'amina@example.com',
            'items_status': str(self.status_item.id),
        }
        data.update(extra_items)
        return self.client.post(self._url(), data)

    def test_get_shows_the_deactivated_item(self):
        self.client.force_login(self.owner)
        response = self.client.get(self._url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Dîner de gala 2024')
        self.assertContains(response, 'Désactivé')

    def test_stranger_without_assignment_is_forbidden(self):
        self.client.force_login(self.stranger)
        response = self.client.get(self._url())
        self.assertEqual(response.status_code, 403)

    def test_creating_a_registration_with_a_deactivated_item_keeps_it(self):
        response = self._post(self.owner, items_restauration=str(self.discontinued_item.id))

        self.assertEqual(response.status_code, 302)
        order = RegistrationOrder.objects.get(event=self.event, email='amina@example.com')
        item_ids = {it['id'] for it in order.items_snapshot}
        self.assertIn(self.discontinued_item.id, item_ids)
        self.assertEqual(order.total_after_reduction, Decimal('1500'))
        self.assertEqual(order.status, 'pending')

        user = User.objects.get(email='amina@example.com')
        self.assertTrue(
            ParticipantEventRegistration.objects.filter(participant__user=user, event=self.event).exists()
        )
        self.assertTrue(
            UserEventAssignment.objects.filter(user=user, event=self.event, role='participant').exists()
        )

    def test_missing_status_selection_is_rejected(self):
        self.client.force_login(self.owner)
        response = self.client.post(self._url(), {
            'first_name': 'Amina', 'last_name': 'K', 'email': 'amina@example.com',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(RegistrationOrder.objects.filter(email='amina@example.com').exists())


class LoginViewNoRedirectLoopTests(TestCase):
    """
    Regression coverage for ERR_TOO_MANY_REDIRECTS on /dashboard/login/.

    login_view's "already authenticated" early-return used to send EVERY
    authenticated user to 'dashboard:home' unconditionally. dashboard_home
    is gated by @user_passes_test(is_staff_user), which bounces any
    non-staff user straight back to settings.LOGIN_URL (this same login
    view) -- which sent them to 'dashboard:home' again: an infinite loop
    for every non-staff dashboard account (event owners, committee
    members, room managers), reachable any time an already-logged-in
    non-staff user's browser lands back on /dashboard/login/ (a stale
    bookmark, browser back, or the CSRF-failure handler bouncing them
    there). Each role must instead land on ITS OWN home page, matching
    exactly where a fresh login for that same account would send them.
    """

    def setUp(self):
        self.event = Event.objects.create(
            name="Congress", start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=2), location="Algiers",
        )

    def _get_login_while_authenticated(self, user):
        self.client.force_login(user)
        return self.client.get(reverse('dashboard:login'))

    def test_event_owner_does_not_loop(self):
        owner = User.objects.create_user(username='owner2', email='owner2@example.com', password='x')
        UserEventAssignment.objects.create(user=owner, event=self.event, role='event_owner', is_active=True)

        response = self._get_login_while_authenticated(owner)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('dashboard:event_owner_submissions_home'))

    def test_room_manager_does_not_loop(self):
        manager = User.objects.create_user(username='manager1', email='manager1@example.com', password='x')
        UserEventAssignment.objects.create(
            user=manager, event=self.event, role='gestionnaire_des_salles', is_active=True,
        )

        response = self._get_login_while_authenticated(manager)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('dashboard:my_final_communications_home'))

    def test_committee_member_does_not_loop(self):
        member = User.objects.create_user(username='committee1', email='committee1@example.com', password='x')
        EPosterCommitteeMember.objects.create(event=self.event, user=member)

        response = self._get_login_while_authenticated(member)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('dashboard:eposter_committee_home'))

    def test_staff_lands_on_dashboard_home_and_it_actually_loads(self):
        staff = User.objects.create_user(username='staffer', password='x', is_staff=True)

        response = self._get_login_while_authenticated(staff)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('dashboard:home'))

        # Unlike the non-staff roles, dashboard:home must not itself
        # redirect for a real staff account -- confirms the fix didn't
        # just move the loop, it actually resolves for this account type.
        home_response = self.client.get(response.url)
        self.assertEqual(home_response.status_code, 200)
