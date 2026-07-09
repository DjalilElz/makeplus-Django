"""
Fix-up for migration 0030: the old uniq_status_rule_item /
uniq_status_rule_session constraints were created (in 0029) as
conditional UniqueConstraints, which on Postgres are implemented as
PARTIAL UNIQUE INDEXES, not real table constraints -- Postgres has no
conditional/partial CONSTRAINT, only conditional INDEXES. 0030 tried to
remove them with `ALTER TABLE ... DROP CONSTRAINT IF EXISTS ...`, which
only touches objects registered in pg_constraint; since these were
actually indexes, that command silently found nothing to drop (no
error, thanks to IF EXISTS) and the stale partial indexes stayed in
place. That's the same locking column pair (status_item_id,
target_item_id) the new nullable-period-aware save logic now legitimately
needs to insert more than one row for (e.g. one row with period=None and
another with a real period), so real production saves for
already-configured status rules started failing with
"duplicate key value violates unique constraint".

This migration drops them the correct way (`DROP INDEX IF EXISTS`),
which works for both a genuine index and is a safe no-op if a database
somehow doesn't have them (e.g. SQLite, where 0030's table-rebuild
already removed them as a side effect).
"""
from django.db import migrations


def drop_stale_indexes(apps, schema_editor):
    with schema_editor.connection.cursor() as cursor:
        cursor.execute('DROP INDEX IF EXISTS uniq_status_rule_item')
        cursor.execute('DROP INDEX IF EXISTS uniq_status_rule_session')


def reverse_noop(apps, schema_editor):
    """No-op reverse -- these constraints are obsolete under the new
    nullable status_item/period model and shouldn't be recreated."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0030_blocitemstatusrule_period_and_more'),
    ]

    operations = [
        migrations.RunPython(drop_stale_indexes, reverse_noop),
    ]
