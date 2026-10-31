import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Paying organisations per event, and how each registration was paid.

    Guarded SQL (IF NOT EXISTS) instead of plain CreateModel/AddField:
    production has repeatedly lost rows from django_migrations, so this
    migration can be replayed against a database that already has these
    tables/columns -- the plain operations would then fail and block the
    deploy.
    """

    dependencies = [
        ('dashboard', '0056_formconfiguration_require_email_verification'),
        ('events', '0041_backfill_free_atelier_is_paid'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="""
                    CREATE TABLE IF NOT EXISTS dashboard_eventsponsor (
                        id bigserial PRIMARY KEY,
                        name varchar(200) NOT NULL,
                        is_active boolean NOT NULL DEFAULT true,
                        "order" integer NOT NULL DEFAULT 0,
                        created_at timestamp with time zone NOT NULL DEFAULT now(),
                        event_id uuid NOT NULL REFERENCES events_event (id) DEFERRABLE INITIALLY DEFERRED
                    );
                    CREATE INDEX IF NOT EXISTS dashboard_eventsponsor_event_id_idx ON dashboard_eventsponsor (event_id);

                    ALTER TABLE dashboard_registrationorder
                        ADD COLUMN IF NOT EXISTS payment_mode varchar(20) NOT NULL DEFAULT '';
                    ALTER TABLE dashboard_registrationorder
                        ADD COLUMN IF NOT EXISTS paid_at timestamp with time zone NULL;
                    ALTER TABLE dashboard_registrationorder
                        ADD COLUMN IF NOT EXISTS sponsor_id bigint NULL
                        REFERENCES dashboard_eventsponsor (id) DEFERRABLE INITIALLY DEFERRED;
                    CREATE INDEX IF NOT EXISTS dashboard_registrationorder_sponsor_id_idx
                        ON dashboard_registrationorder (sponsor_id);
                    """,
                    reverse_sql="""
                    ALTER TABLE dashboard_registrationorder DROP COLUMN IF EXISTS sponsor_id;
                    ALTER TABLE dashboard_registrationorder DROP COLUMN IF EXISTS paid_at;
                    ALTER TABLE dashboard_registrationorder DROP COLUMN IF EXISTS payment_mode;
                    DROP TABLE IF EXISTS dashboard_eventsponsor;
                    """,
                ),
            ],
            state_operations=[
                migrations.CreateModel(
                    name='EventSponsor',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('name', models.CharField(max_length=200)),
                        ('is_active', models.BooleanField(default=True)),
                        ('order', models.IntegerField(default=0)),
                        ('created_at', models.DateTimeField(auto_now_add=True)),
                        ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sponsors', to='events.event')),
                    ],
                    options={
                        'verbose_name': 'Event Sponsor',
                        'verbose_name_plural': 'Event Sponsors',
                        'ordering': ['order', 'name'],
                    },
                ),
                migrations.AddField(
                    model_name='registrationorder',
                    name='payment_mode',
                    field=models.CharField(blank=True, choices=[('cash', 'Espèces'), ('bank_transfer', 'Virement bancaire'), ('sponsoring', 'Prise en charge (Sponsoring)')], default='', max_length=20),
                ),
                migrations.AddField(
                    model_name='registrationorder',
                    name='paid_at',
                    field=models.DateTimeField(blank=True, null=True),
                ),
                migrations.AddField(
                    model_name='registrationorder',
                    name='sponsor',
                    field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='orders', to='dashboard.eventsponsor'),
                ),
            ],
        ),
    ]
