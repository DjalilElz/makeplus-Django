"""
One-off fix for a production migration-history inconsistency: caisse.0005
got recorded as applied before its dependency events.0018, which trips
Django's check_consistent_history() and blocks every subsequent `migrate`.
Usage: python manage.py fix_migration_history [--dry-run]

This is also run automatically by manage.py before every `migrate` call,
so this command exists mainly for manual inspection/dry-run.
"""

from django.core.management.base import BaseCommand

from dashboard.migration_history_fix import fix_migration_history


class Command(BaseCommand):
    help = 'Fix inconsistent migration history: caisse.0005 applied before events.0018'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Show what would change without writing anything')

    def handle(self, *args, **options):
        fix_migration_history(dry_run=options['dry_run'], log=self.stdout.write)
