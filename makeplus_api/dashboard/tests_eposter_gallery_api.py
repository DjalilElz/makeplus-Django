"""The mobile app's e-poster gallery (/api/eposter/<event>/gallery/)."""
from datetime import timedelta

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from events.models import Event
from .models_eposter import ScientificContributionFinalSubmission as Final
from .models_eposter import ScientificContributionSubmission as Submission


class EposterGalleryApiTests(TestCase):
    def setUp(self):
        self.event = Event.objects.create(
            name='Réanimation', start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=2), location='Alger',
        )
        self.url = f'/api/eposter/{self.event.id}/gallery/'

    def _final(self, number, title, submission_type='e_poster', original=None):
        return Final.objects.create(
            event=self.event, original_submission=original, submission_type=submission_type,
            nom='Auteur', email=f'{title}@example.com', telephone='0', contribution_number=number,
            titre=title, auteurs='A. Auteur',
            abstract_file=SimpleUploadedFile(f'{title}.pdf', b'%PDF-1.4', content_type='application/pdf'),
        )

    def _original(self, type_participation):
        return Submission.objects.create(
            event=self.event, nom='Auteur', prenom='A', email='a@example.com', telephone='0',
            grade='professeur', etablissement='CHU', wilaya='Alger',
            type_participation=type_participation, theme='Theme', titre_travail='Original',
            introduction='i', materiels_methodes='m', resultats='r', conclusion='c',
        )

    def _gallery(self, **params):
        response = APIClient().get(self.url, params)
        self.assertEqual(response.status_code, 200)
        return response.json()

    def test_standalone_final_eposters_are_listed(self):
        # no original abstract (no call-for-abstracts stage): was invisible in the app
        self._final('2', 'standalone')
        data = self._gallery()
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['results'][0]['title'], 'standalone')

    def test_linked_poster_without_type_still_listed_and_orals_excluded(self):
        self._final('1', 'linked', submission_type=None, original=self._original('e_poster'))
        self._final('5', 'oral', submission_type='communication_orale')
        titles = [r['title'] for r in self._gallery()['results']]
        self.assertEqual(titles, ['linked'])

    def test_numbers_sorted_as_numbers(self):
        for number in ('10', '2', '', '1', '015'):
            self._final(number, f'p{number or "none"}')
        numbers = [r['contribution_number'] for r in self._gallery()['results']]
        # 015 is fifteen; a poster without a number comes last
        self.assertEqual(numbers, ['1', '2', '10', '015', ''])

    def test_search(self):
        self._final('1', 'Sepsis grave')
        self._final('2', 'Autre')
        self.assertEqual(self._gallery(q='sepsis')['count'], 1)
