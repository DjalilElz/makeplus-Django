from django.db import migrations, models


class Migration(migrations.Migration):
    """
    ScientificContributionSubmission.decision_email_send_count: how many times
    the decision e-mail was successfully sent (it can be re-sent, one by one or
    in bulk). Guarded SQL; the migration state uses the historical model name
    'epostersubmission' (see 0058).
    """

    dependencies = [
        ('dashboard', '0059_eventformconfiguration_members_see_identity'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddField(
                    model_name='epostersubmission',
                    name='decision_email_send_count',
                    field=models.PositiveIntegerField(default=0),
                ),
            ],
            database_operations=[
                migrations.RunSQL(
                    sql=(
                        "ALTER TABLE dashboard_epostersubmission "
                        "ADD COLUMN IF NOT EXISTS decision_email_send_count integer NOT NULL DEFAULT 0;"
                    ),
                    reverse_sql=migrations.RunSQL.noop,
                ),
            ],
        ),
    ]
