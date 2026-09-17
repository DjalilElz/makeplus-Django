import uuid
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


CREATE_SQL = """
CREATE TABLE IF NOT EXISTS "dashboard_attestationtemplate" (
    "id" uuid NOT NULL PRIMARY KEY,
    "template_image" varchar(100) NOT NULL,
    "text_x" double precision NOT NULL,
    "text_y" double precision NOT NULL,
    "text_align" varchar(10) NOT NULL,
    "font_choice" varchar(30) NOT NULL,
    "font_size" integer NOT NULL CHECK ("font_size" >= 0),
    "font_color" varchar(7) NOT NULL,
    "created_at" timestamp with time zone NOT NULL,
    "updated_at" timestamp with time zone NOT NULL,
    "created_by_id" integer NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED,
    "event_id" uuid NOT NULL UNIQUE REFERENCES "events_event" ("id") DEFERRABLE INITIALLY DEFERRED
);
CREATE TABLE IF NOT EXISTS "dashboard_attestationsendlog" (
    "id" uuid NOT NULL PRIMARY KEY,
    "status" varchar(20) NOT NULL,
    "error_message" varchar(500) NOT NULL,
    "sent_at" timestamp with time zone NOT NULL,
    "event_id" uuid NOT NULL REFERENCES "events_event" ("id") DEFERRABLE INITIALLY DEFERRED,
    "participant_id" bigint NOT NULL REFERENCES "events_participant" ("id") DEFERRABLE INITIALLY DEFERRED,
    "sent_by_id" integer NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED
);
CREATE INDEX IF NOT EXISTS "dashboard_a_event_i_fff33e_idx" ON "dashboard_attestationsendlog" ("event_id", "sent_at" DESC);
CREATE INDEX IF NOT EXISTS "dashboard_a_partici_8fca0e_idx" ON "dashboard_attestationsendlog" ("participant_id");
CREATE INDEX IF NOT EXISTS "dashboard_attestationtemplate_created_by_id_idx" ON "dashboard_attestationtemplate" ("created_by_id");
CREATE INDEX IF NOT EXISTS "dashboard_attestationsendlog_event_id_idx" ON "dashboard_attestationsendlog" ("event_id");
CREATE INDEX IF NOT EXISTS "dashboard_attestationsendlog_participant_id_idx" ON "dashboard_attestationsendlog" ("participant_id");
CREATE INDEX IF NOT EXISTS "dashboard_attestationsendlog_sent_by_id_idx" ON "dashboard_attestationsendlog" ("sent_by_id");
"""

DROP_SQL = """
DROP TABLE IF EXISTS "dashboard_attestationsendlog";
DROP TABLE IF EXISTS "dashboard_attestationtemplate";
"""


class Migration(migrations.Migration):
    """
    Hand-written rather than via makemigrations: this app's model state
    has known, unrelated drift around the eposter models (see
    [[makeplus-migration-bookkeeping-desync]] memory) that a bare
    makemigrations pulls into any generated migration regardless of what
    you're actually changing. These two models are brand new, so the
    state_operations below are their straightforward CreateModel/AddIndex,
    written directly from models_attestation.py.

    The actual database_operations use CREATE TABLE/INDEX IF NOT EXISTS
    (Postgres) instead of plain CreateModel, since this project's
    django_migrations bookkeeping has repeatedly lost track of whether a
    migration already ran between deploys -- a plain CreateModel would
    crash with "relation already exists" if re-run, exactly like past
    incidents on this project.
    """

    dependencies = [
        ('dashboard', '0045_scientificcontributionfinalsubmission_submission_type'),
        ('events', '0039_add_password_reset_verification'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.CreateModel(
                    name='AttestationTemplate',
                    fields=[
                        ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                        ('template_image', models.ImageField(upload_to='events/attestation_templates/', verbose_name='Image du modèle')),
                        ('text_x', models.FloatField(default=0.5, verbose_name='Position X (fraction de la largeur)')),
                        ('text_y', models.FloatField(default=0.5, verbose_name='Position Y (fraction de la hauteur)')),
                        ('text_align', models.CharField(choices=[('left', 'Gauche'), ('center', 'Centré'), ('right', 'Droite')], default='center', max_length=10)),
                        ('font_choice', models.CharField(choices=[('great_vibes', 'Great Vibes (élégant, cursif)'), ('playfair', 'Playfair Display (serif élégant)'), ('montserrat', 'Montserrat (moderne, sans-serif)')], default='playfair', max_length=30)),
                        ('font_size', models.PositiveIntegerField(default=60)),
                        ('font_color', models.CharField(default='#000000', max_length=7, verbose_name='Couleur (hex)')),
                        ('created_at', models.DateTimeField(auto_now_add=True)),
                        ('updated_at', models.DateTimeField(auto_now=True)),
                        ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                        ('event', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='attestation_template', to='events.event')),
                    ],
                    options={
                        'verbose_name': 'Attestation Template',
                        'verbose_name_plural': 'Attestation Templates',
                        'db_table': 'dashboard_attestationtemplate',
                    },
                ),
                migrations.CreateModel(
                    name='AttestationSendLog',
                    fields=[
                        ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                        ('status', models.CharField(choices=[('pending', 'En attente'), ('sent', 'Envoyé'), ('failed', 'Échoué')], max_length=20)),
                        ('error_message', models.CharField(blank=True, max_length=500)),
                        ('sent_at', models.DateTimeField(auto_now_add=True)),
                        ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attestation_sends', to='events.event')),
                        ('participant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attestation_sends', to='events.participant')),
                        ('sent_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                    ],
                    options={
                        'verbose_name': 'Attestation Send Log',
                        'verbose_name_plural': 'Attestation Send Logs',
                        'db_table': 'dashboard_attestationsendlog',
                        'ordering': ['-sent_at'],
                    },
                ),
                migrations.AddIndex(
                    model_name='attestationsendlog',
                    index=models.Index(fields=['event', '-sent_at'], name='dashboard_a_event_i_fff33e_idx'),
                ),
                migrations.AddIndex(
                    model_name='attestationsendlog',
                    index=models.Index(fields=['participant'], name='dashboard_a_partici_8fca0e_idx'),
                ),
            ],
            database_operations=[
                migrations.RunSQL(sql=CREATE_SQL, reverse_sql=DROP_SQL),
            ],
        ),
    ]
