"""Account deletion (store requirement) and the public legal pages."""
from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from .models import Participant


class AccountDeletionTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='amina', email='amina@example.com', password='secret-pw',
            first_name='Amina', last_name='B',
        )
        self.participant = Participant.objects.create(
            user=self.user, badge_id='USER-1-ABC',
            qr_code_data={'email': 'amina@example.com', 'full_name': 'Amina B'},
            metadata={'profile_picture_url': 'https://example.com/a.png'},
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_wrong_password_deletes_nothing(self):
        r = self.client.delete('/api/auth/me/', {'password': 'nope'}, format='json')
        self.assertEqual(r.status_code, 400)
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)

    def test_deletion_erases_identity_including_badge_copy(self):
        r = self.client.delete('/api/auth/me/', {'password': 'secret-pw'}, format='json')
        self.assertEqual(r.status_code, 200)
        self.user.refresh_from_db()
        self.participant.refresh_from_db()
        self.assertFalse(self.user.is_active)
        self.assertEqual((self.user.first_name, self.user.last_name), ('', ''))
        self.assertNotIn('amina', self.user.email + self.user.username)
        # the badge QR payload and metadata held their own copy of name/e-mail
        self.assertEqual(self.participant.qr_code_data, {})
        self.assertEqual(self.participant.metadata, {})


@override_settings(SUPPORT_EMAIL='help@example.org')
class LegalPagesTests(TestCase):
    def test_public_pages_show_the_support_address(self):
        for name in ('legal_privacy_policy', 'legal_account_deletion'):
            r = self.client.get(reverse(name))
            self.assertEqual(r.status_code, 200)
            self.assertContains(r, 'help@example.org')
            self.assertNotContains(r, 'support@makeplus.com')

    def test_deletion_page_describes_anonymisation(self):
        r = self.client.get(reverse('legal_account_deletion'))
        self.assertContains(r, 'identifiant anonyme')
