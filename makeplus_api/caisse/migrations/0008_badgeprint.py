import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Badge print log. Guarded SQL (IF NOT EXISTS): production has repeatedly
    lost rows from django_migrations, so this can be replayed against a
    database that already has the table.
    """

    dependencies = [
        ('caisse', '0007_caissetransaction_sponsor'),
        ('events', '0001_initial'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="""
                    CREATE TABLE IF NOT EXISTS caisse_badgeprint (
                        id bigserial PRIMARY KEY,
                        printed_at timestamp with time zone NOT NULL,
                        event_id bigint NOT NULL
                            REFERENCES events_event (id) DEFERRABLE INITIALLY DEFERRED,
                        participant_id bigint NOT NULL
                            REFERENCES events_participant (id) DEFERRABLE INITIALLY DEFERRED,
                        caisse_id bigint NULL
                            REFERENCES caisse_caisse (id) DEFERRABLE INITIALLY DEFERRED
                    );
                    CREATE INDEX IF NOT EXISTS caisse_bp_event_printed_idx
                        ON caisse_badgeprint (event_id, printed_at DESC);
                    CREATE INDEX IF NOT EXISTS caisse_bp_part_event_idx
                        ON caisse_badgeprint (participant_id, event_id);
                    CREATE INDEX IF NOT EXISTS caisse_badgeprint_caisse_id_idx
                        ON caisse_badgeprint (caisse_id);
                    """,
                    reverse_sql="DROP TABLE IF EXISTS caisse_badgeprint;",
                ),
            ],
            state_operations=[
                migrations.CreateModel(
                    name='BadgePrint',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('printed_at', models.DateTimeField(default=django.utils.timezone.now)),
                        ('caisse', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='badge_prints', to='caisse.caisse')),
                        ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='badge_prints', to='events.event')),
                        ('participant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='badge_prints', to='events.participant')),
                    ],
                    options={
                        'verbose_name': 'Badge Print',
                        'verbose_name_plural': 'Badge Prints',
                        'ordering': ['-printed_at'],
                        'indexes': [
                            models.Index(fields=['event', '-printed_at'], name='caisse_bp_event_printed_idx'),
                            models.Index(fields=['participant', 'event'], name='caisse_bp_part_event_idx'),
                        ],
                    },
                ),
            ],
        ),
    ]
