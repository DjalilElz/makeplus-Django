"""API lists: 20 per page by default, ?page_size= (capped at 500) for one-shot loads."""
from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from events.models import Event, Room, Session


class ApiPaginationTests(TestCase):
    def setUp(self):
        start = timezone.now()
        self.event = Event.objects.create(name='E', start_date=start, end_date=start + timedelta(days=1), location='x')
        room = Room.objects.create(event=self.event, name='R', capacity=10)
        Session.objects.bulk_create([
            Session(event=self.event, room=room, title=f'S{i}', start_time=start + timedelta(minutes=i),
                    end_time=start + timedelta(minutes=i + 1))
            for i in range(45)
        ])
        self.api = APIClient()
        self.api.force_authenticate(User.objects.create_user(username='u', password='x', is_staff=True))

    def test_default_page_is_still_20(self):
        data = self.api.get('/api/sessions/', {'event': self.event.id}).json()
        self.assertEqual((data['count'], len(data['results'])), (45, 20))
        self.assertIsNotNone(data['next'])

    def test_page_size_returns_everything_in_one_request(self):
        data = self.api.get('/api/sessions/', {'event': self.event.id, 'page_size': 500}).json()
        self.assertEqual((data['count'], len(data['results'])), (45, 45))
        self.assertIsNone(data['next'])

    def test_page_size_is_capped(self):
        self.assertEqual(
            len(self.api.get('/api/sessions/', {'event': self.event.id, 'page_size': 10**6}).json()['results']), 45,
        )
