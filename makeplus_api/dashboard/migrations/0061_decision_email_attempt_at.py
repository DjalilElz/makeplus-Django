from django.db import migrations, models


class Migration(migrations.Migration):
    """
    ScientificContributionSubmission.decision_email_attempt_at: when the
    decision e-mail was last attempted (sent or not) -- lets the dashboard show
    a bulk send's progress live. Guarded SQL; historical model name
    'epostersubmission' in the state (see 0058).
    """

    dependencies = [
        ('dashboard', '0060_decision_email_send_count'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddField(
                    model_name='epostersubmission',
                    name='decision_email_attempt_at',
                    field=models.DateTimeField(blank=True, null=True, db_index=True),
                ),
            ],
            database_operations=[
                migrations.RunSQL(
                    sql=(
                        "ALTER TABLE dashboard_epostersubmission "
                        "ADD COLUMN IF NOT EXISTS decision_email_attempt_at timestamp with time zone NULL; "
                        "CREATE INDEX IF NOT EXISTS dashboard_epostersubmission_decision_email_attempt_at_idx "
                        "ON dashboard_epostersubmission (decision_email_attempt_at);"
                    ),
                    reverse_sql=migrations.RunSQL.noop,
                ),
            ],
        ),
    ]
