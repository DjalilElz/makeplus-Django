import io
import json
from datetime import datetime, timedelta
from unittest import mock

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from openpyxl import Workbook

from events.models import Event


def _xlsx(rows):
    wb = Workbook()
    ws = wb.active
    for row in rows:
        ws.append(row)
    buf = io.BytesIO()
    wb.save(buf)
    return SimpleUploadedFile(
        'liste.xlsx', buf.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )


SHEET = [
    ['Nom', 'Prénom', 'E-mail', 'Spécialité', 'Date'],
    ['Benali', 'Amina', 'Amina@Example.com', 'Néphrologie', datetime(2026, 11, 20)],
    ['Kaci', 'Yacine', 'pas-un-email', 'Cardiologie', None],
    [None, None, None, None, None],
    ['Saidi', 'Lina', 'lina@example.com', 'Résident', None],
    ['Benali', 'Amina', 'amina@example.com', 'Doublon', None],
]


class CampaignSheetTests(TestCase):

    def setUp(self):
        self.admin = User.objects.create_superuser('admin', 'admin@example.com', 'x')
        self.client.force_login(self.admin)
        self.event = Event.objects.create(
            name='Congrès', start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=1), location='Alger',
        )

    def _create(self, **extra):
        data = {
            'name': 'Relance', 'subject': 'Bonjour {{prenom}}', 'from_email': 'noreply@example.com',
            'from_name': 'Orga', 'reply_to': '', 'track_opens': 'on', 'track_clicks': 'on',
            'body_html': '<p>{{name}} – {{specialite}} – {{date}} – {{event_name}}</p>',
            'builder_config': '{}', 'sheet_file': _xlsx(SHEET),
        }
        data.update(extra)
        self.client.post(reverse('dashboard:campaign_create'), data)
        from dashboard.models_email import EmailCampaign
        return EmailCampaign.objects.get(name='Relance')

    def test_parse_endpoint_returns_columns_as_variables(self):
        res = self.client.post(reverse('dashboard:campaign_parse_sheet'), {'sheet_file': _xlsx(SHEET)}).json()
        self.assertTrue(res['success'])
        self.assertEqual([c['key'] for c in res['columns']], ['nom', 'prenom', 'e_mail', 'specialite', 'date'])
        self.assertEqual(res['email_column'], 'e_mail')
        self.assertEqual(res['row_count'], 4)  # the empty row is dropped
        self.assertEqual(res['valid_email_count'], 3)

    def test_parse_endpoint_rejects_unsupported_file(self):
        res = self.client.post(reverse('dashboard:campaign_parse_sheet'),
                               {'sheet_file': SimpleUploadedFile('x.pdf', b'%PDF')})
        self.assertEqual(res.status_code, 400)
        self.assertFalse(res.json()['success'])

    def test_csv_with_semicolons(self):
        from dashboard.campaign_sheet import parse_sheet
        upload = SimpleUploadedFile('l.csv', 'Nom;Email\nAli;ali@example.com\n'.encode('cp1252'))
        columns, rows, email_column = parse_sheet(upload)
        self.assertEqual(email_column, 'email')
        self.assertEqual(rows, [{'nom': 'Ali', 'email': 'ali@example.com'}])

    def test_create_stores_sheet_and_adds_only_selected_rows(self):
        campaign = self._create(event=str(self.event.id))
        self.assertEqual(campaign.sheet_filename, 'liste.xlsx')
        self.assertEqual(len(campaign.sheet_rows), 4)
        self.assertEqual(campaign.sheet_rows[0]['date'], '20/11/2026')
        self.assertEqual(campaign.recipients.count(), 0)  # nobody until picked

        url = reverse('dashboard:campaign_add_sheet_recipients', args=[campaign.id])
        self.client.post(url, {'rows': ['0', '1']})  # row 1 has an invalid e-mail
        self.assertEqual(list(campaign.recipients.values_list('email', flat=True)), ['amina@example.com'])
        recipient = campaign.recipients.get()
        self.assertEqual(recipient.name, 'Amina Benali')
        self.assertEqual(recipient.data['specialite'], 'Néphrologie')

        # "all": the rest, skipping the invalid e-mail and the duplicate.
        self.client.post(url, {'all': '1'})
        self.assertEqual(sorted(campaign.recipients.values_list('email', flat=True)),
                         ['amina@example.com', 'lina@example.com'])

        page = self.client.get(reverse('dashboard:campaign_detail', args=[campaign.id]))
        self.assertContains(page, 'Néphrologie')
        self.assertContains(page, 'E-mail manquant ou invalide')

    def test_send_fills_sheet_and_event_variables(self):
        campaign = self._create(event=str(self.event.id))
        self.client.post(reverse('dashboard:campaign_add_sheet_recipients', args=[campaign.id]), {'rows': ['0']})

        client = mock.Mock()
        client.send_email.return_value = {'MessageID': 'm1'}
        with mock.patch('dashboard.postmark_client.get_postmark_client', return_value=client):
            res = self.client.post(reverse('dashboard:campaign_send', args=[campaign.id])).json()
        self.assertTrue(res['done'])
        kwargs = client.send_email.call_args.kwargs
        self.assertEqual(kwargs['subject'], 'Bonjour Amina')
        self.assertEqual(kwargs['html_content'], '<p>Amina Benali – Néphrologie – 20/11/2026 – Congrès</p>')
        self.assertEqual(kwargs['to_name'], 'Amina Benali')

    def test_test_send_uses_a_real_row(self):
        campaign = self._create()
        with mock.patch('dashboard.email_sender.send_email', return_value=(True, None, 'id')) as send:
            res = self.client.post(reverse('dashboard:campaign_send_test', args=[campaign.id]),
                                   json.dumps({'email': 'me@example.com'}), content_type='application/json').json()
        self.assertTrue(res['success'], res)
        self.assertEqual(send.call_args.kwargs['to_email'], 'me@example.com')
        self.assertIn('Néphrologie', send.call_args.kwargs['html_content'])

    def test_edit_can_remove_the_sheet(self):
        campaign = self._create()
        self.client.post(reverse('dashboard:campaign_edit', args=[campaign.id]), {
            'name': 'Relance', 'subject': 's', 'from_email': 'noreply@example.com',
            'body_html': '<p>x</p>', 'builder_config': '{}', 'remove_sheet': '1',
        })
        campaign.refresh_from_db()
        self.assertEqual(campaign.sheet_rows, [])
        self.assertEqual(campaign.sheet_filename, '')

    def test_form_pages_render_with_sheet(self):
        self.assertEqual(self.client.get(reverse('dashboard:campaign_create')).status_code, 200)
        campaign = self._create()
        page = self.client.get(reverse('dashboard:campaign_edit', args=[campaign.id]))
        self.assertContains(page, 'id="sheet-columns-data"')
        self.assertContains(page, 'Fichier actuel')
        self.assertContains(page, 'enctype="multipart/form-data"')
