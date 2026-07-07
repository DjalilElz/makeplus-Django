from datetime import timedelta

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from events.models import Event, UserEventAssignment
from .models_eposter import ScientificContributionFinalSubmission, ScientificContributionSubmission


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
from .models_blocs import EventBlocConfig, BlocItem, ReductionPeriod, RegistrationOrder
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
        self.assertEqual(r['distinct_blocs_count'], 2)

    def test_workshops_counts_as_a_bloc(self):
        r = self._compute(item_ids=[self.status_item.id], session_ids=[self.paid_session.id])
        self.assertEqual(r['distinct_blocs_count'], 2)  # status + workshops
        self.assertEqual(r['total_before_reduction'], Decimal('1300.00'))

    def test_free_session_not_charged(self):
        r = self._compute(session_ids=[self.free_session.id])
        # free session is not is_paid -> excluded entirely
        self.assertEqual(r['total_before_reduction'], Decimal('0.00'))
        self.assertEqual(r['distinct_blocs_count'], 0)

    def test_period_reduction_applies_by_date(self):
        ReductionPeriod.objects.create(
            event=self.event, start_date=self.today - timedelta(days=1),
            end_date=self.today + timedelta(days=1), discount_percent=Decimal('10'),
        )
        self.config.reduction_by_period_enabled = True
        self.config.save()
        r = self._compute(item_ids=[self.status_item.id])  # 1000
        self.assertEqual(r['period_discount_percent'], Decimal('10.00'))
        self.assertEqual(r['total_after_reduction'], Decimal('900.00'))

    def test_period_reduction_outside_range_is_zero(self):
        ReductionPeriod.objects.create(
            event=self.event, start_date=self.today + timedelta(days=5),
            end_date=self.today + timedelta(days=10), discount_percent=Decimal('10'),
        )
        self.config.reduction_by_period_enabled = True
        self.config.save()
        r = self._compute(item_ids=[self.status_item.id])
        self.assertEqual(r['period_discount_percent'], Decimal('0.00'))
        self.assertEqual(r['total_after_reduction'], Decimal('1000.00'))

    def test_blocs_reduction_by_count(self):
        self.config.reduction_by_blocs_enabled = True
        self.config.reduction_2_blocs = Decimal('20')
        self.config.save()
        r = self._compute(item_ids=[self.status_item.id, self.resto_item.id])  # 1500, 2 blocs
        self.assertEqual(r['blocs_discount_percent'], Decimal('20.00'))
        self.assertEqual(r['total_after_reduction'], Decimal('1200.00'))

    def test_reductions_are_additive(self):
        ReductionPeriod.objects.create(
            event=self.event, start_date=self.today - timedelta(days=1),
            end_date=self.today + timedelta(days=1), discount_percent=Decimal('10'),
        )
        self.config.reduction_by_period_enabled = True
        self.config.reduction_by_blocs_enabled = True
        self.config.reduction_2_blocs = Decimal('20')
        self.config.save()
        r = self._compute(item_ids=[self.status_item.id, self.resto_item.id])  # 1500, 2 blocs
        # 10% + 20% = 30% additive
        self.assertEqual(r['total_discount_percent'], Decimal('30.00'))
        self.assertEqual(r['total_after_reduction'], Decimal('1050.00'))

    def test_item_from_hidden_bloc_is_ignored(self):
        self.config.show_social_event = False
        self.config.save()
        r = self._compute(item_ids=[self.status_item.id, self.social_item.id])
        # social_event hidden -> its item excluded
        self.assertEqual(r['total_before_reduction'], Decimal('1000.00'))
        self.assertEqual(r['distinct_blocs_count'], 1)

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

    def _enable_blocs(self):
        EventBlocConfig.objects.create(event=self.event, show_status=True)

    def test_no_blocs_shows_plain_form(self):
        response = self.client.get(reverse('public_form', args=[self.form.slug]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Submit Form')
        self.assertNotContains(response, 'Confirmer')
        self.assertNotContains(response, 'quittance de banque')

    def test_blocs_visible_shows_cart_and_receipt(self):
        self._enable_blocs()
        response = self.client.get(reverse('public_form', args=[self.form.slug]))
        self.assertContains(response, 'Total de votre panier')
        self.assertContains(response, 'quittance de banque')
        self.assertContains(response, "Confirmer l'inscription")
        self.assertContains(response, 'Adherent')

    def test_paid_submission_creates_pending_order(self):
        self._enable_blocs()
        receipt = _Upload('receipt.pdf', b'%PDF-1.4 fake', content_type='application/pdf')
        response = self.client.post(reverse('public_form', args=[self.form.slug]), {
            'first_name': 'Karim', 'last_name': 'B', 'email': 'k@example.com',
            'items_status': str(self.item.id),
            'accept_conditions': '1',
            'receipt_file': receipt,
        })
        self.assertEqual(response.status_code, 200)
        order = RegistrationOrder.objects.get(event=self.event)
        self.assertEqual(order.status, 'pending')
        self.assertEqual(order.total_after_reduction, Decimal('1000.00'))
        self.assertEqual(order.email, 'k@example.com')
        self.assertTrue(order.receipt_file)
        self.assertTrue(FormSubmission.objects.filter(form=self.form).exists())

    def test_paid_submission_requires_receipt(self):
        self._enable_blocs()
        response = self.client.post(reverse('public_form', args=[self.form.slug]), {
            'first_name': 'Karim', 'last_name': 'B', 'email': 'k@example.com',
            'items_status': str(self.item.id), 'accept_conditions': '1',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(RegistrationOrder.objects.filter(event=self.event).exists())
        self.assertContains(response, 'bank receipt')

    def test_paid_submission_requires_conditions(self):
        self._enable_blocs()
        receipt = _Upload('receipt.pdf', b'%PDF-1.4 fake', content_type='application/pdf')
        response = self.client.post(reverse('public_form', args=[self.form.slug]), {
            'first_name': 'Karim', 'last_name': 'B', 'email': 'k@example.com',
            'items_status': str(self.item.id), 'receipt_file': receipt,
        })
        self.assertFalse(RegistrationOrder.objects.filter(event=self.event).exists())
        self.assertContains(response, 'accept the conditions')

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
        self.assertContains(response, 'only one option')


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

    def test_create_and_delete_item(self):
        self.client.force_login(self.admin)
        self.client.post(reverse('dashboard:bloc_item_save', args=[self.event.id]), {
            'bloc': 'restauration', 'name': 'Dinner', 'price': '800', 'order': '0',
        })
        item = BlocItem.objects.get(event=self.event, name='Dinner')
        self.assertEqual(item.price, Decimal('800'))
        self.client.post(reverse('dashboard:bloc_item_delete', args=[item.id]))
        self.assertFalse(BlocItem.objects.filter(id=item.id).exists())

    def test_approve_order(self):
        self.client.force_login(self.admin)
        order = RegistrationOrder.objects.create(
            event=self.event, email='k@example.com', full_name='K',
            receipt_file=_Upload('r.pdf', b'x', content_type='application/pdf'),
        )
        self.client.post(reverse('dashboard:registration_order_update', args=[order.id]), {
            'action': 'approve', 'admin_notes': 'ok',
        })
        order.refresh_from_db()
        self.assertEqual(order.status, 'approved')
        self.assertEqual(order.reviewed_by, self.admin)
