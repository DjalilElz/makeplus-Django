"""/auth/me/ keeps the event the person chose (select-event), across app restarts."""
from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from .models import Event, Participant, ParticipantEventRegistration


class MeKeepsChosenEventTests(TestCase):
    def setUp(self):
        def event(name, days_ago):
            return Event.objects.create(
                name=name, start_date=timezone.now() - timedelta(days=days_ago),
                end_date=timezone.now() - timedelta(days=days_ago - 1), location='Alger',
                status='completed',
            )

        self.older = event('Réanimation', 10)
        self.latest = event('SAPBIOL', 40)
        self.foreign = event('Not mine', 5)
        self.user = User.objects.create_user(username='p', email='p@example.com', password='x')
        participant = Participant.objects.create(user=self.user, badge_id='BADGE-ME')
        ParticipantEventRegistration.objects.create(participant=participant, event=self.older)
        # registered last -> what /auth/me/ used to return whatever was chosen
        ParticipantEventRegistration.objects.create(participant=participant, event=self.latest)
        self.client = APIClient()

    def _me(self, event=None):
        token = AccessToken.for_user(self.user)
        if event is not None:
            token['event_id'] = str(event.id)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get('/api/auth/me/')
        self.assertEqual(response.status_code, 200)
        return response.json()['event']

    def test_chosen_event_is_returned(self):
        self.assertEqual(self._me(self.older)['id'], str(self.older.id))

    def test_without_a_choice_the_latest_registration_is_kept(self):
        self.assertEqual(self._me()['id'], str(self.latest.id))

    def test_an_event_the_user_does_not_belong_to_is_ignored(self):
        self.assertEqual(self._me(self.foreign)['id'], str(self.latest.id))
