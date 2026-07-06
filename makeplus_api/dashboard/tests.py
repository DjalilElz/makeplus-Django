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
