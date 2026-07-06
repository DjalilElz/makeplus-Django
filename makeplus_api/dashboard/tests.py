from datetime import timedelta

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from events.models import Event
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
