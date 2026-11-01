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
