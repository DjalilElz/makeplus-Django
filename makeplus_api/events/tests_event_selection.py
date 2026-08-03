"""
Multi-event login flow: a user attached to more than one event picks one
instead of having it silently chosen for them.

Run with:
    python manage.py test events.tests_event_selection --settings=makeplus_api.test_settings
"""
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Event, Participant, ParticipantEventRegistration, UserEventAssignment
from .utils import make_event_selection_token


def _make_event(name):
    now = timezone.now()
    return Event.objects.create(
        name=name,
        start_date=now,
        end_date=now + timezone.timedelta(days=1),
        location='Alger',
        status='active',
    )


def _register_participant(user, event):
    participant, _ = Participant.objects.get_or_create(
        user=user, defaults={'badge_id': f'BADGE-{user.id}'}
    )
    ParticipantEventRegistration.objects.get_or_create(participant=participant, event=event)
    return participant


class EventSelectionTests(TestCase):
    def setUp(self):
        self.password = 'testpass12345'
        self.user = User.objects.create_user(
            username='multi', email='multi@example.com', password=self.password,
            first_name='Multi', last_name='Event',
        )
        self.event_a = _make_event('Event A')
        self.event_b = _make_event('Event B')
        self.other_event = _make_event('Not Mine')

    def _login(self, email=None):
        return self.client.post(
            '/api/auth/token/',
            {'email': email or self.user.email, 'password': self.password},
            content_type='application/json',
        )

    # --- login branch -----------------------------------------------------

    def test_single_event_user_logs_in_normally(self):
        """One event -> tokens straight away, no selection step (no regression)."""
        _register_participant(self.user, self.event_a)

        data = self._login().json()

        self.assertNotIn('requires_event_selection', data)
        self.assertIn('access', data)
        self.assertEqual(data['event']['id'], str(self.event_a.id))
        self.assertEqual(data['role'], 'participant')

    def test_multi_event_user_is_asked_to_choose(self):
        _register_participant(self.user, self.event_a)
        _register_participant(self.user, self.event_b)

        resp = self._login()
        data = resp.json()

        self.assertTrue(data['requires_event_selection'])
        self.assertTrue(data['temp_token'])
        # No real credentials handed out before a choice is made.
        self.assertNotIn('access', data)
        self.assertNotIn('refresh', data)

        ids = {e['id'] for e in data['available_events']}
        self.assertEqual(ids, {str(self.event_a.id), str(self.event_b.id)})
        self.assertNotIn(str(self.other_event.id), ids)
        self.assertEqual(data['user']['email'], self.user.email)

    def test_staff_role_across_two_events_also_asked(self):
        """Multi-event detection covers UserEventAssignment, not just participants."""
        for event in (self.event_a, self.event_b):
            UserEventAssignment.objects.create(
                user=self.user, event=event, role='controlleur_des_badges', is_active=True
            )

        self.assertTrue(self._login().json()['requires_event_selection'])

    # --- selection --------------------------------------------------------

    def test_select_event_returns_working_tokens(self):
        _register_participant(self.user, self.event_a)
        _register_participant(self.user, self.event_b)
        temp_token = self._login().json()['temp_token']

        resp = self.client.post(
            '/api/auth/select-event/',
            {'event_id': str(self.event_b.id)},
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {temp_token}',
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()

        self.assertEqual(data['event']['id'], str(self.event_b.id))
        self.assertEqual(data['role'], 'participant')
        self.assertIn('access', data)

        # The chosen event must ride along in the JWT, or every event-scoped
        # endpoint falls back to "no event context".
        from rest_framework_simplejwt.tokens import AccessToken
        self.assertEqual(AccessToken(data['access'])['event_id'], str(self.event_b.id))

    def test_cannot_select_an_event_you_are_not_attached_to(self):
        _register_participant(self.user, self.event_a)
        _register_participant(self.user, self.event_b)
        temp_token = self._login().json()['temp_token']

        resp = self.client.post(
            '/api/auth/select-event/',
            {'event_id': str(self.other_event.id)},
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {temp_token}',
        )
        self.assertEqual(resp.status_code, 403)

    def test_invalid_and_missing_tokens_are_rejected(self):
        for header in (None, 'Bearer garbage', 'Bearer '):
            kwargs = {'HTTP_AUTHORIZATION': header} if header else {}
            resp = self.client.post(
                '/api/auth/select-event/',
                {'event_id': str(self.event_a.id)},
                content_type='application/json',
                **kwargs,
            )
            self.assertEqual(resp.status_code, 401, msg=f'header={header!r}')

    def test_temp_token_cannot_be_used_as_an_access_token(self):
        """
        The whole reason the temp token is a signing value and not a JWT: a
        user who has not picked an event yet must not be able to call the
        rest of the API with it.
        """
        _register_participant(self.user, self.event_a)
        _register_participant(self.user, self.event_b)
        temp_token = self._login().json()['temp_token']

        resp = self.client.get(
            '/api/auth/me/', HTTP_AUTHORIZATION=f'Bearer {temp_token}'
        )
        self.assertIn(resp.status_code, (401, 403))

    # --- switching --------------------------------------------------------

    def test_switch_event_after_login(self):
        _register_participant(self.user, self.event_a)
        _register_participant(self.user, self.event_b)
        temp_token = self._login().json()['temp_token']
        access = self.client.post(
            '/api/auth/select-event/',
            {'event_id': str(self.event_a.id)},
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {temp_token}',
        ).json()['access']

        resp = self.client.post(
            '/api/auth/switch-event/',
            {'event_id': str(self.event_b.id)},
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {access}',
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()['event']['id'], str(self.event_b.id))

    def test_my_events_lists_all_accessible_events(self):
        _register_participant(self.user, self.event_a)
        _register_participant(self.user, self.event_b)
        temp_token = self._login().json()['temp_token']
        access = self.client.post(
            '/api/auth/select-event/',
            {'event_id': str(self.event_a.id)},
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {temp_token}',
        ).json()['access']

        data = self.client.get(
            '/api/auth/my-events/', HTTP_AUTHORIZATION=f'Bearer {access}'
        ).json()

        self.assertEqual(data['count'], 2)
        self.assertEqual(
            {e['id'] for e in data['events']},
            {str(self.event_a.id), str(self.event_b.id)},
        )
        self.assertTrue(all(e['role'] == 'participant' for e in data['events']))
