"""
Submissions list: theme filter and "theme then number" order for events
with a predefined theme list, and the rows-only chunks of the infinite scroll.
"""
from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from dashboard.models_eposter import (
    EventFormConfiguration,
    ScientificContributionSubmission as Submission,
)
from dashboard.views_eposter_dashboard import OTHER_THEMES, SUBMISSIONS_CHUNK
from events.models import Event

THEMES = ['NEPHROLOGIE CLINIQUE', 'EPURATION EXTRA RENAL', 'TRANSPLANTATION RENAL']


class SubmissionsListFilterTests(TestCase):
    def setUp(self):
        self.event = Event.objects.create(
            name='SANDT', start_date=timezone.now(), end_date=timezone.now() + timedelta(days=2), location='Alger',
        )
        self.config = EventFormConfiguration.objects.create(
            event=self.event, form_type='communicant', theme_field_mode='select', theme_options=THEMES,
        )
        self.url = reverse('dashboard:contributions_submissions_list', args=[self.event.id])
        self.client.force_login(User.objects.create_user(username='staff', password='x', is_staff=True))

    def _sub(self, title, theme, code=None, status='accepted', kind='e_poster'):
        return Submission.objects.create(
            event=self.event, nom='N', prenom='P', email=f'{title}@example.com', telephone='0',
            etablissement='CHU', wilaya='Alger', type_participation=kind, theme=theme,
            titre_travail=title, introduction='i', materiels_methodes='m', resultats='r',
            conclusion='c', status=status, contribution_code=code,
        )

    def _titles(self, response):
        return [s.titre_travail for s in response.context['submissions']]

    def test_default_order_is_theme_list_order_then_number(self):
        self._sub('trans-2', THEMES[2], '2')
        self._sub('nephro-54', THEMES[0], '54')
        self._sub('nephro-none', THEMES[0], None, status='pending')
        self._sub('nephro-4', THEMES[0], '4')
        self._sub('epur-11', THEMES[1], '11')
        self._sub('nephro-12', THEMES[0], '12')
        self._sub('stray', 'Theme A', '1')
        r = self.client.get(self.url)
        self.assertEqual(r.context['order'], 'theme')
        self.assertEqual(
            self._titles(r),
            ['nephro-4', 'nephro-12', 'nephro-54', 'nephro-none', 'epur-11', 'trans-2', 'stray'],
        )

    def test_recent_order_still_available(self):
        first = self._sub('first', THEMES[0], '1')
        second = self._sub('second', THEMES[0], '2')
        Submission.objects.filter(pk=first.pk).update(submitted_at=timezone.now() - timedelta(days=1))
        r = self.client.get(self.url, {'order': 'recent'})
        self.assertEqual(self._titles(r), ['second', 'first'])

    def test_theme_filter_and_other_themes(self):
        self._sub('nephro', THEMES[0], '1')
        self._sub('epur', THEMES[1], '2')
        self._sub('stray', 'test', '3')
        self.assertEqual(self._titles(self.client.get(self.url, {'theme': THEMES[1]})), ['epur'])
        self.assertEqual(self._titles(self.client.get(self.url, {'theme': OTHER_THEMES})), ['stray'])

    def test_theme_combines_with_status_and_type(self):
        self._sub('ok', THEMES[0], '1')
        self._sub('pending', THEMES[0], None, status='pending')
        self._sub('oral', THEMES[0], None, kind='communication_orale')
        self._sub('other-theme', THEMES[1], '2')
        r = self.client.get(self.url, {'status': 'accepted', 'type': 'e_poster', 'theme': THEMES[0]})
        self.assertEqual(self._titles(r), ['ok'])

    def test_free_text_event_has_no_theme_filter_and_keeps_newest_first(self):
        self.config.theme_field_mode = 'free_text'
        self.config.save()
        old = self._sub('old', 'Anything', '1')
        self._sub('new', 'Other', '2')
        Submission.objects.filter(pk=old.pk).update(submitted_at=timezone.now() - timedelta(days=1))
        r = self.client.get(self.url, {'theme': 'Other'})  # ignored: no list
        self.assertEqual(r.context['order'], 'recent')
        self.assertEqual(self._titles(r), ['new', 'old'])
        self.assertNotContains(r, 'name="theme"')

    def test_infinite_scroll_chunks(self):
        for n in range(SUBMISSIONS_CHUNK + 3):
            self._sub(f's{n}', THEMES[0], str(n + 1))
        page = self.client.get(self.url)
        self.assertEqual(len(page.context['submissions']), SUBMISSIONS_CHUNK)
        self.assertContains(page, 'id="load-more"')
        self.assertNotContains(page, 'class="pagination')

        chunk = self.client.get(self.url, {'page': 2, 'partial': '1'})
        self.assertEqual(chunk['X-Has-Next'], '0')
        self.assertNotContains(chunk, '<html')
        self.assertEqual(chunk.content.decode().count('<tr>'), 3)
        self.assertContains(chunk, f's{SUBMISSIONS_CHUNK + 2}')

        past_end = self.client.get(self.url, {'page': 9, 'partial': '1'})
        self.assertEqual(past_end['X-Has-Next'], '0')
        self.assertEqual(past_end.content, b'')
