"""
Self-heal for a prod migration-history inconsistency: caisse.0005 was
recorded as applied before its dependency events.0018, which trips
Django's check_consistent_history() and blocks every `migrate` call.
Postgres-only; safe to call repeatedly (no-ops once history is consistent
or on backends where the affected rows don't exist).
"""

from datetime import timedelta


def fix_migration_history(dry_run=False, log=lambda msg: None):
    """Returns True if a fix was (or would be, in dry-run mode) applied."""
    from django.db import connection

    if connection.vendor != 'postgresql':
        return False

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
            log('events.0018 is already recorded as applied -- nothing to do.')
            return False

        if caisse_row is None:
            log('caisse.0005 is not recorded as applied either -- history is not in the broken state; nothing to do.')
            return False

        caisse_applied = caisse_row[0]
        events_applied = caisse_applied - timedelta(seconds=1)
        log(f'caisse.0005 applied at {caisse_applied}; will record events.0018 as applied at {events_applied}')

        cursor.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name='events_session' AND column_name='max_participants'"
        )
        column_exists = cursor.fetchone() is not None
        log(f'events_session.max_participants column exists: {column_exists}')

        if dry_run:
            log('[DRY RUN] No changes made.')
            return True

        if not column_exists:
            cursor.execute('ALTER TABLE events_session ADD COLUMN max_participants INTEGER NULL')
            log('Added events_session.max_participants column.')

        cursor.execute(
            "INSERT INTO django_migrations (app, name, applied) VALUES (%s, %s, %s)",
            ['events', '0018_session_max_participants', events_applied],
        )
        log('Recorded events.0018 as applied. Migration history is now consistent.')
        return True
