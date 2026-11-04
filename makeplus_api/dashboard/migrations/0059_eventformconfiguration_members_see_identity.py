from django.db import migrations, models


class Migration(migrations.Migration):
    """
    EventFormConfiguration.members_see_identity: per event, whether plain
    committee members see the authors' identity (name, e-mail, phone, grade,
    institution, co-authors). Default False = blind review, today's behaviour
    for every event. Attached files stay supervisor-only either way.

    Guarded SQL (IF NOT EXISTS): production loses django_migrations rows, so
    this must be safe to replay (see 0044's docstring).
    """

    dependencies = [
        ('dashboard', '0058_decision_email_tracking_and_oral_number_option'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddField(
                    model_name='eventformconfiguration',
                    name='members_see_identity',
                    field=models.BooleanField(
                        default=False,
                        verbose_name="Les membres du comité voient l'identité des auteurs",
                    ),
                ),
            ],
            database_operations=[
                migrations.RunSQL(
                    sql=(
                        "ALTER TABLE dashboard_eventformconfiguration "
                        "ADD COLUMN IF NOT EXISTS members_see_identity boolean NOT NULL DEFAULT FALSE;"
                    ),
                    reverse_sql=migrations.RunSQL.noop,
                ),
            ],
        ),
    ]
