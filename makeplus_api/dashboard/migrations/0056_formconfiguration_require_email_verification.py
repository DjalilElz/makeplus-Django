from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Guarded (ADD COLUMN IF NOT EXISTS) instead of a plain AddField:
    production has repeatedly lost rows from django_migrations, so this
    migration can be replayed against a database that already has the
    column -- a plain AddField would then fail and block the deploy.
    """

    dependencies = [
        ('dashboard', '0055_blocitem_show_on_public_form'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="""
                    ALTER TABLE dashboard_formconfiguration
                    ADD COLUMN IF NOT EXISTS require_email_verification boolean NOT NULL DEFAULT true;
                    """,
                    reverse_sql="""
                    ALTER TABLE dashboard_formconfiguration DROP COLUMN IF EXISTS require_email_verification;
                    """,
                ),
            ],
            state_operations=[
                migrations.AddField(
                    model_name='formconfiguration',
                    name='require_email_verification',
                    field=models.BooleanField(default=True),
                ),
            ],
        ),
    ]
