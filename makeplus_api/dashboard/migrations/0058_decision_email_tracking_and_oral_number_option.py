from django.db import migrations, models


class Migration(migrations.Migration):
    """
    - ScientificContributionSubmission.decision_email_sent_at / decision_email_error:
      when the accept/reject e-mail went out, or why it didn't (no template,
      send failure) -- shown on the contributions pages.
    - EventFormConfiguration.require_communication_number: the final-submission
      number is now required (or optional) separately for oral communications;
      require_contribution_number keeps governing e-posters. Each existing event
      starts with its current single setting, copied ONLY when the column is
      first created, so a replay never overwrites an organizer's choice.

    Hand-written, guarded SQL (see 0044's docstring): the eposter models'
    migration state has drifted, and production loses django_migrations rows,
    so every statement must be safe to run twice.
    """

    dependencies = [
        ('dashboard', '0057_eventsponsor_and_order_payment'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddField(
                    model_name='epostersubmission',
                    name='decision_email_sent_at',
                    field=models.DateTimeField(blank=True, null=True),
                ),
                migrations.AddField(
                    model_name='epostersubmission',
                    name='decision_email_error',
                    field=models.CharField(blank=True, default='', max_length=255),
                ),
                migrations.AddField(
                    model_name='eventformconfiguration',
                    name='require_communication_number',
                    field=models.BooleanField(
                        default=True,
                        verbose_name='Numéro obligatoire pour les communications orales',
                    ),
                ),
            ],
            database_operations=[
                migrations.RunSQL(
                    sql="""
                    ALTER TABLE dashboard_epostersubmission
                        ADD COLUMN IF NOT EXISTS decision_email_sent_at timestamp with time zone NULL;
                    ALTER TABLE dashboard_epostersubmission
                        ADD COLUMN IF NOT EXISTS decision_email_error varchar(255) NOT NULL DEFAULT '';
                    DO $$
                    BEGIN
                        IF NOT EXISTS (
                            SELECT 1 FROM information_schema.columns
                            WHERE table_name = 'dashboard_eventformconfiguration'
                              AND column_name = 'require_communication_number'
                        ) THEN
                            ALTER TABLE dashboard_eventformconfiguration
                                ADD COLUMN require_communication_number boolean NOT NULL DEFAULT TRUE;
                            UPDATE dashboard_eventformconfiguration
                                SET require_communication_number = require_contribution_number;
                        END IF;
                    END $$;
                    """,
                    reverse_sql=migrations.RunSQL.noop,
                ),
            ],
        ),
    ]
