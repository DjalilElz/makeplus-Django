"""
Controller access decision ("Laisser entrer" / "Refuser l'accès") and the
Stats dashboard built on it: account filter, insights, charts data and
the single Excel export.
"""
from datetime import timedelta
from io import BytesIO

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from events.form_validation_service import create_participant_for_event
from events.models import ControllerScan, Event, ExposantScan, UserEventAssignment


class ControllerDecisionTests(TestCase):
    def setUp(self):
        self.event = Event.objects.create(
            name='Congress', start_date=timezone.now(), end_date=timezone.now() + timedelta(days=1), location='Alger',
        )
        self.controller = User.objects.create_user(username='ctrl', password='x', first_name='Karim', last_name='C')
        UserEventAssignment.objects.create(user=self.controller, event=self.event, role='controlleur_des_badges')
        self.attendee = User.objects.create_user(username='att', email='att@example.com', password='x',
                                                 first_name='Amina', last_name='B')
        create_participant_for_event(self.attendee, self.event)
        self.api = APIClient()
        self.api.force_authenticate(self.controller)

    def _scan(self, user):
        return self.api.post('/api/participants/scan/', {'qr_data': str(user.id)}, format='json')

    def test_scan_returns_its_id_and_the_decision_is_recorded(self):
        response = self._scan(self.attendee)
        self.assertEqual(response.status_code, 200)
        scan_id = response.json()['scan_id']
        self.assertTrue(ControllerScan.objects.filter(id=scan_id, access_decision='').exists())

        response = self.api.post('/api/participants/scan-decision/', {'scan_id': scan_id, 'decision': 'granted'}, format='json')
        self.assertEqual(response.status_code, 200)
        scan = ControllerScan.objects.get(id=scan_id)
        self.assertEqual(scan.access_decision, 'granted')
        self.assertIsNotNone(scan.decided_at)

        # The controller can change their mind.
        self.api.post('/api/participants/scan-decision/', {'scan_id': scan_id, 'decision': 'denied'}, format='json')
        self.assertEqual(ControllerScan.objects.get(id=scan_id).access_decision, 'denied')

    def test_unregistered_badge_can_be_refused(self):
        stranger = User.objects.create_user(username='str', email='s@example.com', password='x')
        other_event = Event.objects.create(name='Other', start_date=timezone.now(), end_date=timezone.now(), location='x')
        create_participant_for_event(stranger, other_event)
        response = self._scan(stranger)
        self.assertEqual(response.status_code, 403)
        scan_id = response.json()['scan_id']
        self.assertEqual(ControllerScan.objects.get(id=scan_id).status, 'not_registered')
        response = self.api.post('/api/participants/scan-decision/', {'scan_id': scan_id, 'decision': 'denied'}, format='json')
        self.assertEqual(response.status_code, 200)

    def test_bad_decision_and_other_controllers_scan_rejected(self):
        scan_id = self._scan(self.attendee).json()['scan_id']
        self.assertEqual(self.api.post('/api/participants/scan-decision/', {'scan_id': scan_id, 'decision': 'maybe'},
                                       format='json').status_code, 400)
        other = User.objects.create_user(username='other', password='x')
        other_api = APIClient()
        other_api.force_authenticate(other)
        self.assertEqual(other_api.post('/api/participants/scan-decision/', {'scan_id': scan_id, 'decision': 'granted'},
                                        format='json').status_code, 404)
        self.assertEqual(ControllerScan.objects.get(id=scan_id).access_decision, '')


class StatsDashboardTests(TestCase):
    def setUp(self):
        self.event = Event.objects.create(
            name='Congress', start_date=timezone.now(), end_date=timezone.now() + timedelta(days=1), location='Alger',
        )
        self.admin = User.objects.create_user(username='admin', password='x', is_staff=True, is_superuser=True)
        self.c1 = User.objects.create_user(username='c1', password='x', first_name='Karim', last_name='Un')
        self.c2 = User.objects.create_user(username='c2', password='x', first_name='Sara', last_name='Deux')
        stand_user = User.objects.create_user(username='stand', password='x', first_name='Labo', last_name='Hikma')
        self.stand = create_participant_for_event(stand_user, self.event)
        self.visitors = []
        for i in range(3):
            user = User.objects.create_user(username=f'v{i}', email=f'v{i}@example.com', password='x')
            self.visitors.append((user, create_participant_for_event(user, self.event)))

        base = timezone.localtime().replace(hour=10, minute=0, second=0, microsecond=0)
        self.base = base

        def scan(controller, visitor, at, **extra):
            user, participant = visitor
            obj = ControllerScan.objects.create(
                controller=controller, event=self.event, participant_user_id=user.id, badge_id=participant.badge_id,
                participant_name=user.username, participant_email=user.email, **extra,
            )
            ControllerScan.objects.filter(id=obj.id).update(scanned_at=at)  # auto_now_add

        # c1: 3 scans at 10h, one of them a double (same badge 2 minutes later)
        scan(self.c1, self.visitors[0], base, access_decision='granted')
        scan(self.c1, self.visitors[0], base + timedelta(minutes=2), access_decision='granted')
        scan(self.c1, self.visitors[1], base + timedelta(minutes=20), access_decision='denied')
        # c2: 1 scan at 11h, not registered, no decision
        scan(self.c2, self.visitors[2], base + timedelta(hours=1), status='not_registered')
        for i, visitor in enumerate(self.visitors[:2]):
            e = ExposantScan.objects.create(exposant=self.stand, scanned_participant=visitor[1], event=self.event)
            ExposantScan.objects.filter(id=e.id).update(scanned_at=base + timedelta(hours=1, minutes=i))
        self.client.force_login(self.admin)
        self.url = reverse('dashboard:event_stats', args=[self.event.id])

    def test_dashboard_figures_and_insights(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        insights = response.context['insights']
        totals = insights['controller_totals']
        self.assertEqual((totals['scans'], totals['granted'], totals['denied'], totals['undecided']), (4, 2, 1, 1))
        self.assertEqual((totals['not_registered'], totals['refused'], totals['doubles']), (1, 2, 1))
        karim = next(a for a in insights['controllers'] if a['name'] == 'Karim Un')
        self.assertEqual((karim['scans'], karim['distinct'], karim['doubles']), (3, 2, 1))
        self.assertEqual(karim['peak']['count'], 3)
        self.assertEqual(insights['double_incidents'][0]['count'], 2)
        self.assertEqual(insights['stands'][0]['name'], 'Labo Hikma')
        self.assertEqual((insights['stands'][0]['distinct'], insights['stands'][0]['rank']), (2, 1))
        self.assertEqual(insights['timeline']['granularity'], 'hour')
        self.assertEqual(insights['timeline']['labels'], ['10h', '11h'])
        self.assertEqual(insights['timeline']['controller_scans'], [3, 1])
        # 10h: 3 controller scans; 11h: 1 controller + 2 stand scans -> tie, the earliest wins.
        self.assertEqual(insights['peaks']['scans']['label'], '10h–11h')
        self.assertEqual(insights['peaks']['scans']['count'], 3)
        self.assertContains(response, 'stats-chart-data')
        self.assertContains(response, 'Classement des stands')

    def test_account_filter_applies_to_everything(self):
        response = self.client.get(self.url, {'account': f'c{self.c2.id}'})
        insights = response.context['insights']
        self.assertEqual(insights['controller_totals']['scans'], 1)
        self.assertEqual(insights['exposant_totals']['scans'], 0)
        response = self.client.get(self.url, {'account': f'e{self.stand.id}'})
        insights = response.context['insights']
        self.assertEqual((insights['controller_totals']['scans'], insights['exposant_totals']['scans']), (0, 2))
        # Old bookmarked links keep working.
        response = self.client.get(self.url, {'controller_id': self.c1.id})
        self.assertEqual(response.context['account'], f'c{self.c1.id}')
        # Unknown account -> everything.
        response = self.client.get(self.url, {'account': 'c999999'})
        self.assertEqual(response.context['insights']['controller_totals']['scans'], 4)

    def test_period_filter_applies_to_scans(self):
        day = self.base.strftime('%Y-%m-%d')
        response = self.client.get(self.url, {'date_from': f'{day}T10:30', 'date_to': f'{day}T23:59'})
        insights = response.context['insights']
        self.assertEqual((insights['controller_totals']['scans'], insights['exposant_totals']['scans']), (1, 2))
        self.assertTrue(any(s['label'].startswith('Jour 1') for s in response.context['day_shortcuts']))

    def test_excel_has_every_sheet(self):
        from openpyxl import load_workbook
        response = self.client.get(reverse('dashboard:event_stats_export_excel', args=[self.event.id]))
        self.assertEqual(response.status_code, 200)
        wb = load_workbook(BytesIO(response.content))
        self.assertEqual(wb.sheetnames, [
            'Résumé', 'Activité', 'Contrôleurs', 'Stands', 'Compte par heure', 'Paiements', 'Doubles scans',
            'Transactions', 'Présence', 'Scans contrôleurs', 'Scans exposants',
        ])
        decisions = [row[7] for row in wb['Scans contrôleurs'].iter_rows(min_row=2, values_only=True)]
        self.assertEqual(sorted(decisions), ['Accès refusé', 'Laissé entrer', 'Laissé entrer', 'Sans décision'])
        self.assertEqual(wb['Doubles scans'].max_row, 2)
        # Filters reach the export too.
        response = self.client.get(reverse('dashboard:event_stats_export_excel', args=[self.event.id]),
                                   {'account': f'c{self.c2.id}'})
        wb = load_workbook(BytesIO(response.content))
        self.assertEqual(wb['Scans contrôleurs'].max_row, 2)



class StatsExportFormFieldsTests(TestCase):
    """The stats Excel carries the registration-form answers (Spécialité...)."""

    def setUp(self):
        from decimal import Decimal
        from caisse.models import Caisse, CaisseTransaction
        from dashboard.models_blocs import RegistrationOrder
        from dashboard.models_form import FormConfiguration, FormSubmission
        from events.models import ParticipantEventRegistration
        self.event = Event.objects.create(
            name='Congress', start_date=timezone.now(), end_date=timezone.now() + timedelta(days=1), location='Alger',
        )
        self.admin = User.objects.create_user(username='admin', password='x', is_staff=True, is_superuser=True)
        self.client.force_login(self.admin)
        form = FormConfiguration.objects.create(name='Inscription', slug='insc', event=self.event, created_by=self.admin, fields_config=[
            {'name': 'last_name', 'label': 'Nom', 'type': 'text'},
            {'name': 'email', 'label': 'E-mail', 'type': 'email'},
            {'name': 'field_1', 'label': 'Spécialité', 'type': 'select', 'options': ['Néphrologie', 'Urologie']},
            {'name': 'field_3', 'label': 'Secteur', 'type': 'checkbox', 'options': ['Public', 'Privé']},
        ])
        caisse = Caisse.objects.create(name='Caisse 1', email='c@example.com', event=self.event)
        people = [('amina', 'Néphrologie', ['Public'], True, 3000), ('bilal', 'Urologie', ['Privé'], False, 0),
                  ('chahra', 'Néphrologie', [], False, 0), ('djamel', None, None, False, 0)]
        for name, spec, secteur, present, paid in people:
            user = User.objects.create_user(username=name, email=f'{name}@example.com', password='x', first_name=name.title())
            participant = create_participant_for_event(user, self.event)
            if spec is not None:
                data = {'email': user.email, 'field_1': spec, 'field_3': secteur}
                sub = FormSubmission.objects.create(form=form, data=data, email=user.email)
                if name != 'chahra':  # chahra is matched by e-mail only (no order)
                    RegistrationOrder.objects.create(event=self.event, form_submission=sub, participant=participant,
                                                     email=user.email, full_name=name)
            if present:
                ParticipantEventRegistration.objects.filter(participant=participant).update(
                    is_checked_in=True, checked_in_at=timezone.now())
            if paid:
                CaisseTransaction.objects.create(caisse=caisse, participant=participant, total_amount=Decimal(paid),
                                                 status='completed', payment_method='cash')

    def test_form_answers_columns_and_breakdown(self):
        from openpyxl import load_workbook
        response = self.client.get(reverse('dashboard:event_stats_export_excel', args=[self.event.id]))
        wb = load_workbook(BytesIO(response.content))
        self.assertIn('Inscrits', wb.sheetnames)
        ws = wb['Inscrits']
        head = [c.value for c in ws[1]]
        self.assertEqual(head, ['Nom', 'Prénom', 'E-mail', 'Badge', 'Spécialité', 'Secteur', 'Présent',
                                'Présent depuis', 'Montant payé (DZD)'])
        self.assertIsNotNone(ws.auto_filter.ref)  # Excel filter arrows on the header
        rows = {r[2]: r for r in ws.iter_rows(min_row=2, values_only=True)}
        self.assertEqual(rows['amina@example.com'][4:7], ('Néphrologie', 'Public', 'Oui'))
        self.assertEqual(rows['amina@example.com'][8], 3000)
        self.assertEqual(rows['chahra@example.com'][4], 'Néphrologie')
        self.assertEqual(rows['djamel@example.com'][4] or '', '')
        presence_head = [c.value for c in wb['Présence'][1]]
        self.assertEqual(presence_head[-2:], ['Spécialité', 'Secteur'])
        self.assertEqual([c.value for c in wb['Transactions'][2]][-2:], ['Néphrologie', 'Public'])

        breakdown = list(wb['Par champ du formulaire'].iter_rows(values_only=True))
        spec = {r[0]: r[1:] for r in breakdown if r and r[0] in ('Néphrologie', 'Urologie', '(Non renseigné)')}
        self.assertEqual(spec['Néphrologie'], (2, 1, 50, 3000))
        self.assertEqual(spec['Urologie'], (1, 0, 0, 0))


    def test_page_filter_by_form_answer(self):
        from openpyxl import load_workbook
        url = reverse('dashboard:event_stats', args=[self.event.id])
        page = self.client.get(url)
        self.assertContains(page, 'Réponse au formulaire')
        self.assertContains(page, 'value="field_1::Néphrologie"')
        self.assertEqual(page.context['total_registered'], 4)

        page = self.client.get(url, {'answer': 'field_1::Néphrologie'})
        ctx = page.context
        self.assertEqual((ctx['total_registered'], ctx['presence_total']), (2, 1))  # amina + chahra; amina present
        self.assertEqual(ctx['money_stats']['total_amount'], 3000)
        self.assertContains(page, 'name="answer" value="field_1::Néphrologie"')  # kept by the search forms

        page = self.client.get(url, {'answer': 'field_1::Urologie'})
        self.assertEqual((page.context['total_registered'], page.context['presence_total']), (1, 0))
        self.assertEqual(page.context['money_stats']['total_amount'], 0)

        page = self.client.get(url, {'answer': 'field_3::Privé'})  # checkbox answer
        self.assertEqual(page.context['total_registered'], 1)

        page = self.client.get(url, {'answer': 'field_1::Inconnu'})  # stale value -> everyone
        self.assertEqual((page.context['total_registered'], page.context['answer']), (4, ''))

        response = self.client.get(reverse('dashboard:event_stats_export_excel', args=[self.event.id]),
                                   {'answer': 'field_1::Néphrologie'})
        wb = load_workbook(BytesIO(response.content))
        self.assertIn(('Spécialité', 'Néphrologie'), [tuple(r[:2]) for r in wb['Résumé'].iter_rows(values_only=True)])
        self.assertEqual(wb['Présence'].max_row, 2)


class WebappStatsApiTests(TestCase):
    """The webapp's own stats screens get the same insights for one account."""

    def setUp(self):
        self.event = Event.objects.create(
            name='Congress', start_date=timezone.now(), end_date=timezone.now() + timedelta(days=1), location='Alger',
        )
        self.controller = User.objects.create_user(username='ctrl', password='x')
        UserEventAssignment.objects.create(user=self.controller, event=self.event, role='controlleur_des_badges')
        self.visitors = []
        for i in range(2):
            user = User.objects.create_user(username=f'v{i}', email=f'v{i}@example.com', password='x')
            self.visitors.append((user, create_participant_for_event(user, self.event)))

    def test_controller_statistics_include_decisions_doubles_and_hours(self):
        for (user, participant), decision in ((self.visitors[0], 'granted'), (self.visitors[0], ''),
                                              (self.visitors[1], 'denied')):
            ControllerScan.objects.create(
                controller=self.controller, event=self.event, participant_user_id=user.id,
                badge_id=participant.badge_id, participant_name=user.username, participant_email=user.email,
                access_decision=decision,
            )
        api = APIClient()
        api.force_authenticate(self.controller)
        data = api.get(f'/api/my-room/statistics/?event_id={self.event.id}').json()
        self.assertEqual(data['my_check_ins_today'], 3)
        today = data['today']
        self.assertEqual((today['scans'], today['distinct'], today['granted'], today['denied'], today['undecided'],
                          today['doubles']), (3, 2, 1, 1, 1, 1))
        self.assertEqual(data['totals']['scans'], 3)
        self.assertEqual(sum(data['hourly_today']['counts']), 3)
        self.assertEqual(data['peak_today']['count'], 3)
        self.assertEqual({s['access_decision'] for s in data['recent_scans']}, {'granted', 'denied', ''})

    def test_exposant_my_scans_include_distinct_visitors_and_hours(self):
        stand_user = User.objects.create_user(username='stand', password='x')
        stand = create_participant_for_event(stand_user, self.event)
        UserEventAssignment.objects.filter(user=stand_user, event=self.event).update(role='exposant')
        for _, participant in self.visitors + [self.visitors[0]]:
            ExposantScan.objects.create(exposant=stand, scanned_participant=participant, event=self.event)
        api = APIClient()
        api.force_authenticate(stand_user)
        data = api.get(f'/api/exposant-scans/my_scans/?event_id={self.event.id}').json()
        self.assertEqual((data['total_visits'], data['today_visits']), (3, 3))
        self.assertEqual((data['distinct_visitors'], data['today_distinct_visitors']), (2, 2))
        self.assertEqual(sum(data['hourly_today']['counts']), 3)
        self.assertEqual(len(data['scans']), 3)
