from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Guarded (ADD COLUMN IF NOT EXISTS) instead of a plain AddField:
    production has repeatedly lost rows from django_migrations, so this
    migration can be replayed against a database that already has the
    column.
    """

    dependencies = [
        ('dashboard', '0062_attestation_auto_send_on_presence'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="""
                    ALTER TABLE dashboard_attestationtemplate
                    ADD COLUMN IF NOT EXISTS include_eposter_details boolean NOT NULL DEFAULT false;
                    """,
                    reverse_sql="""
                    ALTER TABLE dashboard_attestationtemplate DROP COLUMN IF EXISTS include_eposter_details;
                    """,
                ),
            ],
            state_operations=[
                migrations.AddField(
                    model_name='attestationtemplate',
                    name='include_eposter_details',
                    field=models.BooleanField(default=False, verbose_name='Ajouter le titre du poster et les co-auteurs (présentateurs ePoster)'),
                ),
            ],
        ),
    ]
