from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from .models import (
    Event, Participant, ParticipantEventRegistration, Room, RoomAccess,
    Session, SessionAccess, SessionQuestion, SignUpVerification,
    FormRegistrationVerification, PasswordResetVerification,
    UserEventAssignment,
)
from .form_validation_service import get_or_create_user_by_email, verify_form_registration
from .signup_service import send_signup_verification_code, verify_signup_code
from .password_reset_service import request_password_reset, verify_password_reset
from dashboard.models_form import FormConfiguration
from dashboard.models_blocs import RegistrationOrder


class PublicAuthEndpointTests(TestCase):
    """
    Signup/form-validation endpoints must work for a device carrying a
    stale or invalid access_token (e.g. left over from a previous, since-
    expired session). JWTAuthentication runs globally by default and
    401s on a bad token before permission_classes is even consulted, so
    these views need authentication_classes = [] -- permission_classes
    alone isn't enough. See signup_views.py / form_validation_views.py.
    """

    def test_signup_request_ignores_a_bad_bearer_token(self):
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Bearer not-a-real-token')

        response = client.post('/api/auth/signup/request/', {
            'email': 'freshsignup@example.com',
            'first_name': 'Fresh',
            'last_name': 'Signup',
            'password': 'testpass12345',
        }, format='json')

        self.assertNotEqual(response.status_code, 401)

    def test_form_validation_resend_ignores_a_bad_bearer_token(self):
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Bearer not-a-real-token')

        response = client.post('/api/forms/validate/resend/', {
            'email': 'someone@example.com',
            'form_slug': 'does-not-exist',
            'form_data': {},
        }, format='json')

        self.assertNotEqual(response.status_code, 401)

    def test_password_reset_request_ignores_a_bad_bearer_token(self):
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Bearer not-a-real-token')

        response = client.post('/api/auth/password-reset/request/', {
            'email': 'someone@example.com',
            'new_password': 'irrelevant1234',
        }, format='json')

        self.assertNotEqual(response.status_code, 401)


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
    "Cet email est déjà utilisé..." or create a duplicate account.
    """

    def test_send_code_refuses_only_for_real_accounts(self):
        User.objects.create_user(username='real', email='real@example.com', password='realpass')
        success, message, _wait = send_signup_verification_code(
            email='real@example.com', first_name='X', password='pw', last_name='Y',
        )
        self.assertFalse(success)
        self.assertEqual(message, 'Cet email est déjà utilisé par un compte existant')

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


class PasswordResetTests(TestCase):
    """
    Self-service "mot de passe oublie" flow: request a code, verify it,
    new password takes effect and old sessions get killed.
    """

    def test_request_refuses_unknown_email(self):
        success, message, _wait = request_password_reset(
            email='nobody@example.com', new_password='newpass1234',
        )
        self.assertFalse(success)
        self.assertEqual(message, 'Aucun compte trouvé avec cet email')

    def test_request_refuses_placeholder_account(self):
        """
        A placeholder (event-registration-only, no usable password) has
        nothing to reset -- that email should go through signup instead.
        """
        placeholder = User.objects.create(username='placeholder3', email='p3@example.com')
        placeholder.set_unusable_password()
        placeholder.save()

        success, message, _wait = request_password_reset(
            email='p3@example.com', new_password='newpass1234',
        )
        self.assertFalse(success)
        self.assertEqual(message, 'Aucun compte trouvé avec cet email')

    def test_request_rejects_weak_password(self):
        User.objects.create_user(username='weak', email='weak@example.com', password='oldpass1234')
        success, message, _wait = request_password_reset(
            email='weak@example.com', new_password='1234',
        )
        self.assertFalse(success)

    def test_request_succeeds_for_real_account(self):
        User.objects.create_user(username='real2', email='real2@example.com', password='oldpass1234')
        success, message, _wait = request_password_reset(
            email='real2@example.com', new_password='brandnewpass1234',
        )
        self.assertTrue(success, message)

    @patch.object(PasswordResetVerification, 'generate_code', return_value='777888')
    def test_verify_applies_new_password_and_rejects_old_one(self, _mock_code):
        user = User.objects.create_user(username='resetme', email='resetme@example.com', password='oldpass1234')

        code, _verification = PasswordResetVerification.create_verification(
            email='resetme@example.com',
            new_password_hash=make_password('brandnewpass1234'),
        )

        success, message = verify_password_reset(email='resetme@example.com', code=code)
        self.assertTrue(success, message)

        user.refresh_from_db()
        self.assertTrue(user.check_password('brandnewpass1234'))
        self.assertFalse(user.check_password('oldpass1234'))

    def test_verify_rejects_invalid_code(self):
        User.objects.create_user(username='resetme2', email='resetme2@example.com', password='oldpass1234')
        PasswordResetVerification.create_verification(
            email='resetme2@example.com',
            new_password_hash=make_password('brandnewpass1234'),
        )

        success, message = verify_password_reset(email='resetme2@example.com', code='000000')
        self.assertFalse(success)

    @patch.object(PasswordResetVerification, 'generate_code', return_value='111222')
    def test_verify_blacklists_existing_sessions(self, _mock_code):
        from rest_framework_simplejwt.tokens import RefreshToken
        from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken

        user = User.objects.create_user(username='resetme3', email='resetme3@example.com', password='oldpass1234')
        old_refresh = RefreshToken.for_user(user)

        code, _verification = PasswordResetVerification.create_verification(
            email='resetme3@example.com',
            new_password_hash=make_password('brandnewpass1234'),
        )
        success, message = verify_password_reset(email='resetme3@example.com', code=code)
        self.assertTrue(success, message)

        self.assertTrue(
            BlacklistedToken.objects.filter(token__jti=old_refresh['jti']).exists()
        )


class SessionQuestionFlowTests(TestCase):
    """
    Regression coverage for the session Q&A feature.

    Guards three things that were previously all broken at once:
      1. EventContextMiddleware always saw event_id=None, because nothing put
         it in the JWT — for participants specifically, because the login
         serializer only ever looked at UserEventAssignment, which plain
         participants never get.
      2. SessionQuestionViewSet.create() filtered Participant by a field
         (`event=`) that doesn't exist on the model — would have raised
         FieldError the moment #1 was fixed and this code path was ever hit.
      3. IsGestionnaire.has_object_permission required obj.event directly,
         which SessionQuestion doesn't have — answering was a 403 for everyone.
    """

    def setUp(self):
        self.event = Event.objects.create(
            name='Congress', start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=2), location='Algiers',
            status='active',
        )
        self.room = Room.objects.create(event=self.event, name='Salle A', capacity=100, location='Floor 1')
        self.session = Session.objects.create(
            event=self.event, room=self.room, title='Opening Talk',
            start_time=timezone.now(), end_time=timezone.now() + timedelta(hours=1),
        )

        self.participant_user = User.objects.create_user(
            username='asker', email='asker@example.com', password='pw12345',
        )
        self.participant = Participant.objects.create(user=self.participant_user, badge_id='BADGE-1')
        ParticipantEventRegistration.objects.create(participant=self.participant, event=self.event)

        self.gestionnaire_user = User.objects.create_user(
            username='gestionnaire', email='gestionnaire@example.com', password='pw12345',
        )
        UserEventAssignment.objects.create(
            user=self.gestionnaire_user, event=self.event,
            role='gestionnaire_des_salles', is_active=True,
        )

    def _login(self, email, password):
        client = APIClient()
        response = client.post('/api/auth/token/', {'email': email, 'password': password}, format='json')
        self.assertEqual(response.status_code, 200, response.data)
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {response.data["access"]}')
        return client, response.data

    def test_participant_login_embeds_event_id_claim(self):
        """
        A plain participant has no UserEventAssignment — the JWT must still
        carry event_id, resolved from their event registration instead.
        """
        _client, data = self._login('asker@example.com', 'pw12345')
        access = AccessToken(data['access'])
        self.assertEqual(access['event_id'], str(self.event.id))
        self.assertEqual(data['role'], 'participant')
        self.assertEqual(data['event']['id'], str(self.event.id))

    def test_event_id_claim_survives_token_refresh(self):
        _client, data = self._login('asker@example.com', 'pw12345')
        refresh = RefreshToken(data['refresh'])
        new_access = refresh.access_token
        self.assertEqual(new_access['event_id'], str(self.event.id))

    def test_participant_can_ask_and_response_is_anonymous(self):
        client, _data = self._login('asker@example.com', 'pw12345')

        response = client.post('/api/session-questions/', {
            'session': str(self.session.id),
            'question_text': 'Combien de temps dure la pause déjeuner ?',
        }, format='json')

        self.assertEqual(response.status_code, 201, response.data)
        self.assertNotIn('participant_name', response.data)
        self.assertNotIn('participant', response.data)

        question = SessionQuestion.objects.get(id=response.data['id'])
        self.assertEqual(question.participant_id, self.participant.id)

    def test_participant_not_registered_for_event_is_rejected(self):
        """
        Defends the event_context / is_registered_for_event check directly,
        bypassing login (which would only ever mint a token for an event the
        participant IS registered for) by forging a token for a foreign event.
        """
        other_event = Event.objects.create(
            name='Other Congress', start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=1), location='Oran',
        )
        token = AccessToken.for_user(self.participant_user)
        token['event_id'] = str(other_event.id)

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = client.post('/api/session-questions/', {
            'session': str(self.session.id),
            'question_text': 'Should be rejected',
        }, format='json')

        self.assertEqual(response.status_code, 403, response.data)

    def test_gestionnaire_can_answer_question(self):
        question = SessionQuestion.objects.create(
            session=self.session, participant=self.participant,
            question_text='Y a-t-il du café ?',
        )

        client, _data = self._login('gestionnaire@example.com', 'pw12345')
        response = client.post(f'/api/session-questions/{question.id}/answer/', {
            'answer_text': 'Oui, dans le hall.',
        }, format='json')

        self.assertEqual(response.status_code, 200, response.data)
        self.assertNotIn('participant_name', response.data)
        question.refresh_from_db()
        self.assertTrue(question.is_answered)
        self.assertEqual(question.answered_by_id, self.gestionnaire_user.id)

    def test_non_gestionnaire_cannot_answer_question(self):
        question = SessionQuestion.objects.create(
            session=self.session, participant=self.participant,
            question_text='Y a-t-il du café ?',
        )

        client, _data = self._login('asker@example.com', 'pw12345')
        response = client.post(f'/api/session-questions/{question.id}/answer/', {
            'answer_text': 'Trying to self-answer',
        }, format='json')

        self.assertEqual(response.status_code, 403, response.data)


class UserEventDataDeleteAPITests(TestCase):
    """
    Partial data deletion (Play Store Data Safety requirement): a
    participant can erase everything tied to ONE event without deleting
    their whole account.
    """

    def setUp(self):
        self.event = Event.objects.create(
            name='Congress', start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=2), location='Algiers',
            status='active',
        )
        self.other_event = Event.objects.create(
            name='Other Congress', start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=2), location='Oran',
            status='active',
        )
        self.room = Room.objects.create(event=self.event, name='Salle A', capacity=100, location='Floor 1')
        self.session = Session.objects.create(
            event=self.event, room=self.room, title='Opening Talk',
            start_time=timezone.now(), end_time=timezone.now() + timedelta(hours=1),
            is_paid=True, price=1000,
        )

        self.user = User.objects.create_user(
            username='leaver', email='leaver@example.com', password='pw12345',
        )
        self.participant = Participant.objects.create(user=self.user, badge_id='BADGE-1')
        ParticipantEventRegistration.objects.create(participant=self.participant, event=self.event)
        ParticipantEventRegistration.objects.create(participant=self.participant, event=self.other_event)

        self.question = SessionQuestion.objects.create(
            session=self.session, participant=self.participant, question_text='Une question ?',
        )
        self.session_access = SessionAccess.objects.create(
            participant=self.participant, session=self.session,
            has_access=True, payment_status='paid', amount_paid=1000,
        )
        self.room_access = RoomAccess.objects.create(
            participant=self.participant, room=self.room, status='granted',
        )
        self.order = RegistrationOrder.objects.create(
            event=self.event, participant=self.participant,
            full_name='Leaver Test', email='leaver@example.com',
            items_snapshot=[], total_before_reduction=0, total_after_reduction=0,
        )

    def _login(self):
        client = APIClient()
        response = client.post(
            '/api/auth/token/', {'email': 'leaver@example.com', 'password': 'pw12345'}, format='json',
        )
        self.assertEqual(response.status_code, 200, response.data)

        if response.data.get('requires_event_selection'):
            # This participant is registered for more than one event, so
            # login stops at a temp selection token instead of real JWTs.
            client.credentials(HTTP_AUTHORIZATION=f'Bearer {response.data["temp_token"]}')
            response = client.post(
                '/api/auth/select-event/', {'event_id': str(self.event.id)}, format='json',
            )
            self.assertEqual(response.status_code, 200, response.data)

        client.credentials(HTTP_AUTHORIZATION=f'Bearer {response.data["access"]}')
        return client

    def test_deletes_only_this_events_data(self):
        client = self._login()
        response = client.delete(f'/api/auth/me/events/{self.event.id}/')
        self.assertEqual(response.status_code, 200, response.data)

        self.assertFalse(
            ParticipantEventRegistration.objects.filter(participant=self.participant, event=self.event).exists()
        )
        self.assertFalse(SessionQuestion.objects.filter(id=self.question.id).exists())
        self.assertFalse(SessionAccess.objects.filter(id=self.session_access.id).exists())
        self.assertFalse(RoomAccess.objects.filter(id=self.room_access.id).exists())
        self.assertFalse(RegistrationOrder.objects.filter(id=self.order.id).exists())

        # Other event, and the account itself, untouched.
        self.assertTrue(
            ParticipantEventRegistration.objects.filter(participant=self.participant, event=self.other_event).exists()
        )
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)
        self.assertTrue(Participant.objects.filter(id=self.participant.id).exists())

    def test_blocks_deletion_when_registration_is_confirmed(self):
        self.order.status = 'approved'
        self.order.save(update_fields=['status'])

        client = self._login()
        response = client.delete(f'/api/auth/me/events/{self.event.id}/')

        self.assertEqual(response.status_code, 400, response.data)
        self.assertTrue(RegistrationOrder.objects.filter(id=self.order.id).exists())
        self.assertTrue(
            ParticipantEventRegistration.objects.filter(participant=self.participant, event=self.event).exists()
        )

    def test_requires_authentication(self):
        client = APIClient()
        response = client.delete(f'/api/auth/me/events/{self.event.id}/')
        self.assertEqual(response.status_code, 401)

    def test_404_for_an_event_never_registered_for(self):
        unrelated_event = Event.objects.create(
            name='Unrelated', start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=2), location='Constantine',
            status='active',
        )
        client = self._login()
        response = client.delete(f'/api/auth/me/events/{unrelated_event.id}/')
        self.assertEqual(response.status_code, 404, response.data)
