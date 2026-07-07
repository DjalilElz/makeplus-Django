from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from .models import Event, Participant, SignUpVerification, FormRegistrationVerification
from .form_validation_service import get_or_create_user_by_email, verify_form_registration
from .signup_service import send_signup_verification_code, verify_signup_code
from dashboard.models_form import FormConfiguration


class PlaceholderAccountTests(TestCase):
    """
    Registering for an event no longer requires an existing mobile-app
    account. A placeholder (unusable password) account is created once the
    email is verified, so someone can register before ever signing up.
    """

    def test_creates_placeholder_when_no_account_exists(self):
        user = get_or_create_user_by_email('new@example.com', 'Karim', 'B')
        self.assertEqual(user.email, 'new@example.com')
        self.assertEqual(user.first_name, 'Karim')
        self.assertFalse(user.has_usable_password())

    def test_reuses_existing_account(self):
        existing = User.objects.create_user(username='karim', email='k@example.com', password='realpass')
        user = get_or_create_user_by_email('k@example.com', 'Ignored', 'Name')
        self.assertEqual(user.pk, existing.pk)
        self.assertTrue(user.has_usable_password())

    @patch.object(FormRegistrationVerification, 'generate_code', return_value='111222')
    def test_free_flow_verification_creates_placeholder_and_participant(self, _mock_code):
        admin = User.objects.create_user(username='admin', password='x', is_staff=True)
        event = Event.objects.create(
            name="Congress", start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=2), location="Algiers",
        )
        form = FormConfiguration.objects.create(
            name="Reg", slug="reg-free", event=event, created_by=admin,
            fields_config=[
                {'name': 'first_name', 'label': 'First', 'type': 'text', 'required': True},
                {'name': 'last_name', 'label': 'Last', 'type': 'text', 'required': True},
                {'name': 'email', 'label': 'Email', 'type': 'email', 'required': True},
            ],
        )
        code, _verification = FormRegistrationVerification.create_verification(
            email='nobody@example.com',
            form=form,
            form_data={'first_name': 'Sara', 'last_name': 'H', 'email': 'nobody@example.com'},
        )
        success, participant, message = verify_form_registration(
            email='nobody@example.com', form_slug='reg-free', code=code,
        )
        self.assertTrue(success, message)
        user = User.objects.get(email='nobody@example.com')
        self.assertFalse(user.has_usable_password())
        self.assertEqual(user.first_name, 'Sara')
        self.assertTrue(Participant.objects.filter(user=user, role='participant').exists())


class SignupClaimTests(TestCase):
    """
    Signing up in the app with an email that already has a placeholder
    account (from event registration) should claim it, not refuse with
    "Email already registered" or create a duplicate account.
    """

    def test_send_code_refuses_only_for_real_accounts(self):
        User.objects.create_user(username='real', email='real@example.com', password='realpass')
        success, message, _wait = send_signup_verification_code(
            email='real@example.com', first_name='X', password='pw', last_name='Y',
        )
        self.assertFalse(success)
        self.assertEqual(message, 'Email already registered')

    def test_send_code_allows_placeholder_accounts(self):
        placeholder = User.objects.create(username='placeholder', email='placeholder@example.com')
        placeholder.set_unusable_password()
        placeholder.save()
        success, message, _wait = send_signup_verification_code(
            email='placeholder@example.com', first_name='X', password='pw', last_name='Y',
        )
        self.assertTrue(success, message)

    @patch.object(SignUpVerification, 'generate_code', return_value='555444')
    def test_verify_claims_placeholder_account(self, _mock_code):
        placeholder = User.objects.create(username='placeholder2', email='p2@example.com', first_name='', last_name='')
        placeholder.set_unusable_password()
        placeholder.save()

        code, _verification = SignUpVerification.create_verification(
            email='p2@example.com',
            signup_data={
                'first_name': 'Real',
                'last_name': 'Name',
                'password_hash': 'pbkdf2_sha256$hashedvalue',
            },
        )
        success, user, message = verify_signup_code(email='p2@example.com', code=code)
        self.assertTrue(success, message)
        self.assertEqual(user.pk, placeholder.pk)
        self.assertEqual(user.first_name, 'Real')
        self.assertTrue(user.has_usable_password())
        self.assertEqual(User.objects.filter(email='p2@example.com').count(), 1)
        self.assertTrue(Participant.objects.filter(user=user).exists())
