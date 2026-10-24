from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Supabase's own index advisor (run against this app's real production
    query log) measured that several hot queries against
    dashboard_registrationorder -- the event-owner submissions page and
    everything built on top of it, called thousands of times -- pay a
    real-measured ~45% higher plan cost than necessary. They order by
    created_at DESC with no status filter, so the existing index on
    (event, status, created_at) can't serve the sort (status sits between
    event and created_at, breaking the per-event ordering), and they fall
    back to a sort node instead.

    CREATE INDEX CONCURRENTLY (not a plain CREATE INDEX) and atomic=False:
    a plain CREATE INDEX takes a lock that blocks every write to this
    table for the duration of the build. This app's own query log shows
    exactly how bad that gets on a hot table -- a DROP CONSTRAINT during
    a migration replay (different migration, same table family) was
    caught behind live traffic for up to 380 seconds. CONCURRENTLY builds
    the index without blocking reads or writes, at the cost of not being
    allowed inside a transaction, hence atomic=False.
    """

    atomic = False

    dependencies = [
        ('dashboard', '0053_participantimportrow_claimed_at'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="""
                    CREATE INDEX CONCURRENTLY IF NOT EXISTS
                    dash_regorder_created_idx
                    ON dashboard_registrationorder (created_at);
                    """,
                    reverse_sql="""
                    DROP INDEX CONCURRENTLY IF EXISTS
                    dash_regorder_created_idx;
                    """,
                ),
            ],
            state_operations=[
                migrations.AddIndex(
                    model_name='registrationorder',
                    index=models.Index(fields=['created_at'], name='dash_regorder_created_idx'),
                ),
            ],
        ),
    ]
