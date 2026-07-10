"""
One-off fix for a production migration-history inconsistency: caisse.0005
got recorded as applied before its dependency events.0018, which trips
Django's check_consistent_history() and blocks every subsequent `migrate`.
Usage: python manage.py fix_migration_history [--dry-run]
"""

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Fix inconsistent migration history: caisse.0005 applied before events.0018'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Show what would change without writing anything')

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT applied FROM django_migrations WHERE app='caisse' AND name='0005_alter_payableitem_item_type_and_more'"
            )
            caisse_row = cursor.fetchone()
            cursor.execute(
                "SELECT applied FROM django_migrations WHERE app='events' AND name='0018_session_max_participants'"
            )
            events_row = cursor.fetchone()

            if events_row is not None:
                self.stdout.write(self.style.SUCCESS('events.0018 is already recorded as applied -- nothing to do.'))
                return

            if caisse_row is None:
                self.stdout.write(self.style.WARNING(
                    'caisse.0005 is not recorded as applied either -- history is not in the broken '
                    'state described in the deploy log; run `migrate` normally.'
                ))
                return

            caisse_applied = caisse_row[0]
            events_applied = caisse_applied - timedelta(seconds=1)
            self.stdout.write(f'caisse.0005 applied at {caisse_applied}; will record events.0018 as applied at {events_applied}')

            cursor.execute(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name='events_session' AND column_name='max_participants'"
            )
            column_exists = cursor.fetchone() is not None
            self.stdout.write(f'events_session.max_participants column exists: {column_exists}')

            if dry_run:
                self.stdout.write(self.style.WARNING('[DRY RUN] No changes made. Run without --dry-run to apply.'))
                return

            if not column_exists:
                cursor.execute('ALTER TABLE events_session ADD COLUMN max_participants INTEGER NULL')
                self.stdout.write(self.style.SUCCESS('Added events_session.max_participants column.'))

            cursor.execute(
                "INSERT INTO django_migrations (app, name, applied) VALUES (%s, %s, %s)",
                ['events', '0018_session_max_participants', events_applied],
            )
            self.stdout.write(self.style.SUCCESS(
                'Recorded events.0018 as applied. Migration history is now consistent -- `migrate` will proceed normally.'
            ))
