"""
Scientific committee decisions: a member's opinion never changes a
submission's status; the supervisor's own choice is the final decision
(status, reason, P-number, e-mail), for rejections as well as acceptances.
"""
from datetime import timedelta
from unittest import mock

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from dashboard.models_eposter import (
    ScientificContributionCommitteeMember as Member,
    ScientificContributionSubmission as Submission,
    ScientificContributionValidation as Validation,
)
from events.models import Event


class ContributionDecisionTests(TestCase):
    def setUp(self):
        self.event = Event.objects.create(
            name='Congress', start_date=timezone.now(), end_date=timezone.now() + timedelta(days=2), location='Alger',
        )
        self.supervisor = User.objects.create_user(username='sup', password='x')
        self.member = User.objects.create_user(username='mem', password='x')
        Member.objects.create(event=self.event, user=self.supervisor, role='supervisor', is_active=True)
        Member.objects.create(event=self.event, user=self.member, role='member', is_active=True)
        self.submission = self._submission('e_poster')
        self.submission.assigned_to.add(self.member)
        patcher = mock.patch('dashboard.views_eposter_dashboard.send_decision_email')
        self.send_email = patcher.start()
        self.addCleanup(patcher.stop)

    def _submission(self, kind):
        return Submission.objects.create(
            event=self.event, nom='Ben Ali', prenom='Karim', email='karim@example.com', telephone='0',
            grade='professeur', etablissement='CHU', wilaya='Alger', type_participation=kind,
            theme='T', titre_travail='Title', introduction='i', materiels_methodes='m', resultats='r',
            conclusion='c', status='pending',
        )

    def _opinion(self, user, submission, approved, comments=''):
        self.client.force_login(user)
        return self.client.post(
            reverse('dashboard:contributions_validate_submission', args=[self.event.id, submission.id]),
            {'is_approved': 'true' if approved else 'false', 'comments': comments},
        )

    def test_member_approval_no_longer_auto_accepts(self):
        # validations_required is 1: this single approval used to accept it.
        response = self._opinion(self.member, self.submission, True)
        self.assertFalse(response.json()['final'])
        self.submission.refresh_from_db()
        self.assertEqual(self.submission.status, 'pending')
        self.assertIsNone(self.submission.final_decision_by)
        self.assertTrue(Validation.objects.filter(submission=self.submission, committee_member=self.member).exists())
        self.send_email.assert_not_called()

    def test_supervisor_rejection_is_final(self):
        self._opinion(self.member, self.submission, True)  # a member recommended acceptance
        response = self._opinion(self.supervisor, self.submission, False, 'Hors thème')
        self.assertEqual(response.json(), {**response.json(), 'success': True, 'final': True, 'status': 'rejected'})
        self.submission.refresh_from_db()
        self.assertEqual(self.submission.status, 'rejected')
        self.assertEqual(self.submission.rejection_reason, 'Hors thème')
        self.assertEqual(self.submission.final_decision_by, self.supervisor)
        self.send_email.assert_called_once()

    def test_supervisor_acceptance_numbers_the_eposter(self):
        self._opinion(self.supervisor, self.submission, True)
        self.submission.refresh_from_db()
        self.assertEqual(self.submission.status, 'accepted')
        self.assertEqual(self.submission.contribution_code, '1')
        self.assertEqual(self.submission.final_decision_by, self.supervisor)
        self.send_email.assert_called_once()

    def test_rejected_count_on_the_dashboard(self):
        self._opinion(self.supervisor, self.submission, False, 'Non')
        self.client.force_login(self.supervisor)
        response = self.client.get(reverse('dashboard:contributions_dashboard', args=[self.event.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['stats']['rejected'], 1)

    def test_actions_menu_reject_still_works(self):
        self.client.force_login(self.supervisor)
        self.client.post(
            reverse('dashboard:contributions_set_status', args=[self.event.id, self.submission.id]),
            {'status': 'rejected', 'rejection_reason': 'Doublon'},
        )
        self.submission.refresh_from_db()
        self.assertEqual((self.submission.status, self.submission.rejection_reason), ('rejected', 'Doublon'))

    def test_detail_page_wording(self):
        self.client.force_login(self.supervisor)
        url = reverse('dashboard:contributions_submission_detail', args=[self.event.id, self.submission.id])
        self.assertContains(self.client.get(url), 'Votre décision')
        self.client.force_login(self.member)
        self.assertContains(self.client.get(url), 'Recommander le rejet')

    def test_apply_supervisor_opinions_backlog(self):
        # Opinions recorded before the fix: saved, but the submission stayed pending.
        other = self._submission('communication_orale')
        Validation.objects.create(submission=self.submission, committee_member=self.supervisor,
                                  is_approved=False, comments='Hors sujet')
        Validation.objects.create(submission=other, committee_member=self.member, is_approved=False)
        self.client.force_login(self.supervisor)
        dashboard = self.client.get(reverse('dashboard:contributions_dashboard', args=[self.event.id]))
        self.assertEqual(dashboard.context['unapplied_supervisor_opinions'], 1)
        self.assertContains(dashboard, 'Appliquer les décisions')

        self.client.post(reverse('dashboard:contributions_apply_supervisor_opinions', args=[self.event.id]))
        self.submission.refresh_from_db()
        other.refresh_from_db()
        self.assertEqual((self.submission.status, self.submission.rejection_reason), ('rejected', 'Hors sujet'))
        self.assertEqual(self.submission.final_decision_by, self.supervisor)
        self.assertEqual(other.status, 'pending')  # a member's opinion is never applied
        self.send_email.assert_called_once()
        dashboard = self.client.get(reverse('dashboard:contributions_dashboard', args=[self.event.id]))
        self.assertEqual(dashboard.context['unapplied_supervisor_opinions'], 0)

    def test_apply_supervisor_opinions_is_supervisor_only(self):
        Validation.objects.create(submission=self.submission, committee_member=self.supervisor, is_approved=False)
        self.client.force_login(self.member)
        self.client.post(reverse('dashboard:contributions_apply_supervisor_opinions', args=[self.event.id]))
        self.submission.refresh_from_db()
        self.assertEqual(self.submission.status, 'pending')

    def test_eposter_numbers_are_plain_and_continue_after_old_formats(self):
        from dashboard.views_eposter_dashboard import eposter_number_value, generate_next_eposter_number
        self.assertEqual(generate_next_eposter_number(self.event), '1')
        old = self._submission('e_poster')
        Submission.objects.filter(id=old.id).update(status='accepted', contribution_code='EPOSTER-46AE7D35-003')
        self.assertEqual(generate_next_eposter_number(self.event), '4')  # never reuses 1-3
        self.assertEqual([eposter_number_value(c) for c in ('12', 'P-7', 'EPOSTER-AB-010', '', None)],
                         [12, 7, 10, None, None])
        # Two acceptances in a row: 4 then 5.
        second = self._submission('e_poster')
        self._opinion(self.supervisor, self.submission, True)
        self._opinion(self.supervisor, second, True)
        self.submission.refresh_from_db()
        second.refresh_from_db()
        self.assertEqual((self.submission.contribution_code, second.contribution_code), ('4', '5'))
        # A communication orale is never numbered automatically.
        oral = self._submission('communication_orale')
        self._opinion(self.supervisor, oral, True)
        oral.refresh_from_db()
        self.assertFalse(oral.contribution_code)

    def test_backlog_finalizes_old_auto_acceptances_by_the_supervisor(self):
        # Accepted by the old automatic rule right after the supervisor's approval.
        Submission.objects.filter(id=self.submission.id).update(status='accepted')
        Validation.objects.create(submission=self.submission, committee_member=self.supervisor, is_approved=True)
        # Accepted by the old rule after a plain member's approval: not the supervisor's, not touched.
        member_only = self._submission('e_poster')
        Submission.objects.filter(id=member_only.id).update(status='accepted')
        Validation.objects.create(submission=member_only, committee_member=self.member, is_approved=True)

        self.client.force_login(self.supervisor)
        dashboard = self.client.get(reverse('dashboard:contributions_dashboard', args=[self.event.id]))
        self.assertEqual(dashboard.context['unapplied_supervisor_opinions'], 1)
        self.assertEqual(dashboard.context['missing_decision_templates'], ['e_poster_accepted'])
        self.assertContains(dashboard, "Modèles d'e-mail manquants")

        self.send_email.return_value = False  # no template -> nothing sent
        response = self.client.post(
            reverse('dashboard:contributions_apply_supervisor_opinions', args=[self.event.id]), follow=True)
        self.assertContains(response, '1 e-mail(s) non envoyé(s)')
        self.submission.refresh_from_db()
        member_only.refresh_from_db()
        self.assertEqual((self.submission.status, self.submission.final_decision_by), ('accepted', self.supervisor))
        self.assertEqual(self.submission.contribution_code, '1')
        self.assertIsNone(member_only.final_decision_by)


class DecisionEmailTrackingTests(TestCase):
    """Who received the accept/reject e-mail: recorded, listed, filterable, resendable."""

    def setUp(self):
        from dashboard.models_eposter import ScientificContributionEmailTemplate as Template
        self.event = Event.objects.create(
            name='Congress', start_date=timezone.now(), end_date=timezone.now() + timedelta(days=2), location='Alger',
        )
        self.supervisor = User.objects.create_user(username='sup', password='x')
        Member.objects.create(event=self.event, user=self.supervisor, role='supervisor', is_active=True)
        Template.objects.create(event=self.event, template_type='e_poster_accepted', subject='Acceptée {{titre}}',
                                body_html='<p>Numéro {{contribution_number}}</p>', is_active=True)
        self.poster = ContributionDecisionTests._submission(self, 'e_poster')
        self.oral = ContributionDecisionTests._submission(self, 'communication_orale')
        patcher = mock.patch('dashboard.email_sender.send_email', return_value=(True, None, 'msg-1'))
        self.send_email = patcher.start()
        self.addCleanup(patcher.stop)
        self.client.force_login(self.supervisor)

    def _decide(self, submission, approved):
        return self.client.post(
            reverse('dashboard:contributions_validate_submission', args=[self.event.id, submission.id]),
            {'is_approved': 'true' if approved else 'false', 'comments': 'motif'},
        )

    def test_sent_and_not_sent_are_recorded(self):
        self._decide(self.poster, True)       # template exists -> sent
        self._decide(self.oral, False)        # no communication_orale_rejected template -> not sent
        self.poster.refresh_from_db()
        self.oral.refresh_from_db()
        self.assertEqual(self.poster.decision_email_state, 'sent')
        self.assertIsNotNone(self.poster.decision_email_sent_at)
        self.assertEqual(self.oral.decision_email_state, 'not_sent')
        self.assertIn('communication_orale_rejected', self.oral.decision_email_error)
        self.assertEqual(self.send_email.call_count, 1)

        list_url = reverse('dashboard:contributions_submissions_list', args=[self.event.id])
        sent = self.client.get(list_url, {'email': 'sent'})
        self.assertEqual([s.id for s in sent.context['submissions']], [self.poster.id])
        not_sent = self.client.get(list_url, {'email': 'not_sent'})
        self.assertEqual([s.id for s in not_sent.context['submissions']], [self.oral.id])
        self.assertContains(not_sent, 'Non envoyé')

        stats = self.client.get(reverse('dashboard:contributions_dashboard', args=[self.event.id])).context['stats']
        self.assertEqual((stats['emails_sent'], stats['emails_not_sent']), (1, 1))

        detail = self.client.get(reverse('dashboard:contributions_submission_detail', args=[self.event.id, self.oral.id]))
        self.assertContains(detail, 'non envoyé')
        self.assertContains(detail, 'communication_orale_rejected')

    def test_resend_after_creating_the_missing_template(self):
        from dashboard.models_eposter import ScientificContributionEmailTemplate as Template
        self._decide(self.oral, False)
        Template.objects.create(event=self.event, template_type='communication_orale_rejected', subject='Décision',
                                body_html='<p>{{remarque}}</p>', is_active=True)
        response = self.client.post(
            reverse('dashboard:contributions_resend_decision_email', args=[self.event.id, self.oral.id]), follow=True)
        self.assertContains(response, 'E-mail de décision envoyé')
        self.oral.refresh_from_db()
        self.assertEqual((self.oral.decision_email_state, self.oral.decision_email_error), ('sent', ''))

    def test_postmark_failure_is_recorded(self):
        self.send_email.return_value = (False, 'Inactive recipient', None)
        self._decide(self.poster, True)
        self.poster.refresh_from_db()
        self.assertEqual(self.poster.decision_email_state, 'not_sent')
        self.assertIn('Inactive recipient', self.poster.decision_email_error)

    def test_excel_has_the_email_columns(self):
        from io import BytesIO
        from openpyxl import load_workbook
        self._decide(self.poster, True)
        response = self.client.get(reverse('dashboard:contributions_export_excel', args=[self.event.id]))
        ws = load_workbook(BytesIO(response.content)).active
        headers = [c.value for c in ws[1]]
        self.assertIn('E-mail de décision', headers)
        col = headers.index('E-mail de décision')
        values = [row[col] for row in ws.iter_rows(min_row=2, values_only=True)]
        self.assertIn('Envoyé', values)


class OralNumberOptionTests(TestCase):
    """The final-submission number is required (or not) separately for oral communications."""

    def test_switches_are_independent(self):
        from dashboard.models_eposter import EventFormConfiguration
        from dashboard.views_eposter_final import _require_contribution_number
        event = Event.objects.create(name='E', start_date=timezone.now(), end_date=timezone.now(), location='x')
        self.assertTrue(_require_contribution_number(event, 'communication_orale'))  # no config: required
        EventFormConfiguration.objects.create(event=event, form_type='communicant',
                                              require_contribution_number=True, require_communication_number=False)
        self.assertTrue(_require_contribution_number(event, 'e_poster'))
        self.assertFalse(_require_contribution_number(event, 'communication_orale'))
        oral_form = self.client.get(reverse('public_final_submission_communication', args=[event.id]))
        self.assertFalse(oral_form.context['require_contribution_number'])
        self.assertContains(oral_form, 'laissez vide si aucun numéro')
        poster_form = self.client.get(reverse('public_final_submission_eposter', args=[event.id]))
        self.assertTrue(poster_form.context['require_contribution_number'])
