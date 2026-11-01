from django.db import migrations


class Migration(migrations.Migration):
    """
    ControllerScan.access_decision / decided_at: what the controller did
    after a scan ("Laisser entrer" / "Refuser l'accès" in the webapp).

    Raw guarded SQL only, no state operations: ControllerScan itself was
    created by raw SQL in 0031 and has never been part of this app's
    migration state (see the NOTE in 0039), so an AddField here would fail
    with KeyError ('events', 'controllerscan'). IF NOT EXISTS keeps it safe
    to replay, since production has lost django_migrations rows before.
    """

    dependencies = [
        ('events', '0041_backfill_free_atelier_is_paid'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            ALTER TABLE events_controllerscan
                ADD COLUMN IF NOT EXISTS access_decision varchar(10) NOT NULL DEFAULT '';
            ALTER TABLE events_controllerscan
                ADD COLUMN IF NOT EXISTS decided_at timestamp with time zone NULL;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
