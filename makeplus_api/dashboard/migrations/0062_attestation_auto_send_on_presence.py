from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Guarded (ADD COLUMN IF NOT EXISTS) instead of a plain AddField:
    production has repeatedly lost rows from django_migrations, so this
    migration can be replayed against a database that already has the
    column.
    """

    dependencies = [
        ('dashboard', '0061_decision_email_attempt_at'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="""
                    ALTER TABLE dashboard_attestationtemplate
                    ADD COLUMN IF NOT EXISTS auto_send_on_presence boolean NOT NULL DEFAULT false;
                    """,
                    reverse_sql="""
                    ALTER TABLE dashboard_attestationtemplate DROP COLUMN IF EXISTS auto_send_on_presence;
                    """,
                ),
            ],
            state_operations=[
                migrations.AddField(
                    model_name='attestationtemplate',
                    name='auto_send_on_presence',
                    field=models.BooleanField(default=False, verbose_name="Envoyer automatiquement l'attestation à la présence (caisse)"),
                ),
            ],
        ),
    ]
