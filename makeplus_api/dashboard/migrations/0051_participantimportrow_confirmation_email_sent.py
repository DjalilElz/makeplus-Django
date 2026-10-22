from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Hand-written and guarded (IF NOT EXISTS / SeparateDatabaseAndState) --
    see 0049's own docstring for why every migration in this app is
    written this way.
    """

    dependencies = [
        ('dashboard', '0050_eposter_assignment_and_scoped_code'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="""
                    ALTER TABLE dashboard_participantimportrow
                    ADD COLUMN IF NOT EXISTS confirmation_email_sent BOOLEAN NOT NULL DEFAULT FALSE;
                    """,
                    reverse_sql="""
                    ALTER TABLE dashboard_participantimportrow
                    DROP COLUMN IF EXISTS confirmation_email_sent;
                    """,
                ),
            ],
            state_operations=[
                migrations.AddField(
                    model_name='participantimportrow',
                    name='confirmation_email_sent',
                    field=models.BooleanField(default=False),
                ),
            ],
        ),
    ]
