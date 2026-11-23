import shutil
import tempfile
from datetime import timedelta
from unittest import mock

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.utils import timezone

from events.form_validation_service import create_participant_for_event
from events.models import Event

_TEST_MEDIA = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=_TEST_MEDIA)
class AttestationEposterDetailsTests(TestCase):
    """
    A participation attestation must not carry a poster title unless the
    event explicitly turned ePoster details on.
    """

    def setUp(self):
        from dashboard.models_attestation import AttestationTemplate
        from dashboard.models_eposter import ScientificContributionSubmission
        self.event = Event.objects.create(
            name="Congress", start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=2), location="Algiers",
        )
        user = User.objects.create_user(username='amina', email='amina@example.com', password='x',
                                        first_name='Amina', last_name='B')
        self.participant = create_participant_for_event(user, self.event)
        ScientificContributionSubmission.objects.create(
            event=self.event, nom='B', prenom='Amina', email='AMINA@example.com', telephone='0',
            secteur='public', etablissement='CHU', wilaya='Alger', type_participation='e_poster',
            theme='T', titre_travail='Poster title', auteurs=[{'prenom': 'Karim', 'nom': 'S'}],
            introduction='i', materiels_methodes='m', resultats='r', conclusion='c', status='accepted',
        )
        self.template = AttestationTemplate.objects.create(
            event=self.event,
            template_image=SimpleUploadedFile('t.png', b'x', content_type='image/png'),
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(_TEST_MEDIA, ignore_errors=True)

    def _send(self):
        from dashboard.attestation_service import send_attestation_to_participant
        with mock.patch('dashboard.attestation_service.generate_attestation_pdf', return_value=b'%PDF') as pdf, \
                mock.patch('dashboard.email_sender.send_email', return_value=(True, None, 'id')) as email:
            self.assertEqual(send_attestation_to_participant(self.template, self.participant), (True, None))
        return pdf.call_args.kwargs, email.call_args.kwargs

    def test_default_sends_plain_participation_attestation(self):
        self.assertFalse(self.template.include_eposter_details)
        pdf_kwargs, email_kwargs = self._send()
        self.assertIsNone(pdf_kwargs['poster_title'])
        self.assertIsNone(pdf_kwargs['co_authors_text'])
        self.assertIn('participation', email_kwargs['html_content'])
        self.assertNotIn('Poster title', email_kwargs['html_content'])

    def test_opted_in_event_draws_poster_details(self):
        self.template.include_eposter_details = True
        self.template.save()
        pdf_kwargs, email_kwargs = self._send()
        self.assertEqual(pdf_kwargs['poster_title'], 'Poster title')
        self.assertEqual(pdf_kwargs['co_authors_text'], 'Karim S')
        self.assertIn('Poster title', email_kwargs['html_content'])

    def test_settings_page_saves_the_switch(self):
        from django.urls import reverse
        admin = User.objects.create_superuser('admin', 'a@example.com', 'x')
        self.client.force_login(admin)
        url = reverse('dashboard:attestation_settings', args=[self.event.id])
        self.client.post(url, {'include_eposter_details': 'on'})
        self.template.refresh_from_db()
        self.assertTrue(self.template.include_eposter_details)
        self.client.post(url, {})
        self.template.refresh_from_db()
        self.assertFalse(self.template.include_eposter_details)


@override_settings(MEDIA_ROOT=_TEST_MEDIA)
class AttestationResendTests(AttestationEposterDetailsTests):
    """The send page can resend to people who already received theirs."""

    def setUp(self):
        super().setUp()
        from dashboard.models_attestation import AttestationSendLog
        admin = User.objects.create_superuser('boss', 'boss@example.com', 'x')
        self.client.force_login(admin)
        self.log = AttestationSendLog.objects.create(event=self.event, participant=self.participant, status='sent')
        plain = User.objects.create_user(username='omar', email='omar@example.com', password='x')
        self.plain = create_participant_for_event(plain, self.event)

    def _start(self, **extra):
        from django.urls import reverse
        data = {'action': 'start', 'participant_ids': [str(self.participant.id)]}
        data.update(extra)
        return self.client.post(reverse('dashboard:attestation_send', args=[self.event.id]), data, follow=True)

    def test_already_sent_is_skipped_without_the_option(self):
        self._start()
        self.log.refresh_from_db()
        self.assertEqual(self.log.status, 'sent')

    def test_resend_option_queues_it_again(self):
        page = self._start(resend='1')
        self.log.refresh_from_db()
        self.assertEqual(self.log.status, 'pending')
        self.assertEqual(page.status_code, 200)

    def test_eposter_filter_lists_only_presenters(self):
        from django.urls import reverse
        url = reverse('dashboard:attestation_send', args=[self.event.id])
        page = self.client.get(url + '?profile=eposter')
        self.assertContains(page, 'amina@example.com')
        self.assertNotContains(page, 'omar@example.com')
        self.assertContains(page, 'Présentateurs ePoster (1)')
        self.assertContains(self.client.get(url), 'omar@example.com')
