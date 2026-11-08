"""POST /api/auth/logout/ (mobile app): revokes the refresh token."""
from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken


class ApiLogoutTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='u', email='u@example.com', password='x')
        self.client = APIClient(enforce_csrf_checks=True)

    def test_post_blacklists_the_refresh_token(self):
        refresh = str(RefreshToken.for_user(self.user))
        response = self.client.post('/api/auth/logout/', {'refresh': refresh}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'success': True, 'revoked': True})
        # The revoked refresh token can no longer mint access tokens.
        response = self.client.post('/api/auth/token/refresh/', {'refresh': refresh}, format='json')
        self.assertEqual(response.status_code, 401)

    def test_post_without_or_with_a_bad_token_still_succeeds(self):
        for body in ({}, {'refresh': 'not-a-token'}):
            response = self.client.post('/api/auth/logout/', body, format='json')
            self.assertEqual(response.status_code, 200)
            self.assertFalse(response.json()['revoked'])

    def test_web_logout_get_still_redirects(self):
        response = self.client.get('/api/auth/logout/')
        self.assertEqual(response.status_code, 302)
