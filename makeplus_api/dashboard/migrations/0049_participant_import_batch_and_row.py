from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):
    """
    Hand-written and guarded from the start (IF NOT EXISTS raw SQL paired
    with SeparateDatabaseAndState) -- this app's migration history has
    repeatedly lost its recorded-applied rows in production, which turns
    an ordinary first-time CreateModel into a crash on re-run (see
    0048's own fix for exactly this).
    """

    dependencies = [
        ('dashboard', '0048_attestation_eposter_fields_and_email_template'),
        ('events', '0025_restructure_participant_model'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="""
                    CREATE TABLE IF NOT EXISTS dashboard_participantimportbatch (
                        id UUID PRIMARY KEY,
                        original_filename VARCHAR(255) NOT NULL DEFAULT '',
                        status VARCHAR(20) NOT NULL DEFAULT 'validating',
                        created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                        event_id UUID NOT NULL REFERENCES events_event(id) ON DELETE CASCADE,
                        uploaded_by_id INTEGER NULL REFERENCES auth_user(id) ON DELETE SET NULL
                    );
                    CREATE INDEX IF NOT EXISTS dashboard_participantimportbatch_event_id_idx ON dashboard_participantimportbatch (event_id);
                    CREATE INDEX IF NOT EXISTS dashboard_participantimportbatch_uploaded_by_id_idx ON dashboard_participantimportbatch (uploaded_by_id);

                    CREATE TABLE IF NOT EXISTS dashboard_participantimportrow (
                        id UUID PRIMARY KEY,
                        row_number INTEGER NOT NULL,
                        raw_data JSONB NOT NULL DEFAULT '{}',
                        email VARCHAR(254) NOT NULL DEFAULT '',
                        full_name VARCHAR(255) NOT NULL DEFAULT '',
                        form_data JSONB NOT NULL DEFAULT '{}',
                        resolved_item_ids JSONB NOT NULL DEFAULT '[]',
                        resolved_session_ids JSONB NOT NULL DEFAULT '[]',
                        status VARCHAR(20) NOT NULL DEFAULT 'valid',
                        error_message VARCHAR(500) NOT NULL DEFAULT '',
                        batch_id UUID NOT NULL REFERENCES dashboard_participantimportbatch(id) ON DELETE CASCADE,
                        participant_id INTEGER NULL REFERENCES events_participant(id) ON DELETE SET NULL
                    );
                    CREATE INDEX IF NOT EXISTS dashboard_p_batch_i_b1bc4e_idx ON dashboard_participantimportrow (batch_id, status);
                    CREATE INDEX IF NOT EXISTS dashboard_participantimportrow_participant_id_idx ON dashboard_participantimportrow (participant_id);
                    """,
                    reverse_sql="""
                    DROP TABLE IF EXISTS dashboard_participantimportrow CASCADE;
                    DROP TABLE IF EXISTS dashboard_participantimportbatch CASCADE;
                    """,
                ),
            ],
            state_operations=[
                migrations.CreateModel(
                    name='ParticipantImportBatch',
                    fields=[
                        ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                        ('original_filename', models.CharField(blank=True, max_length=255)),
                        ('status', models.CharField(choices=[('validating', 'Validation en cours'), ('ready', 'Prêt à importer'), ('processing', 'Importation en cours'), ('done', 'Terminé')], default='validating', max_length=20)),
                        ('created_at', models.DateTimeField(auto_now_add=True)),
                        ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='import_batches', to='events.event')),
                        ('uploaded_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                    ],
                    options={
                        'verbose_name': 'Participant Import Batch',
                        'verbose_name_plural': 'Participant Import Batches',
                        'db_table': 'dashboard_participantimportbatch',
                        'ordering': ['-created_at'],
                    },
                ),
                migrations.CreateModel(
                    name='ParticipantImportRow',
                    fields=[
                        ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                        ('row_number', models.IntegerField(help_text='Excel row number, for error reporting')),
                        ('raw_data', models.JSONField(default=dict)),
                        ('email', models.EmailField(blank=True, max_length=254)),
                        ('full_name', models.CharField(blank=True, max_length=255)),
                        ('form_data', models.JSONField(blank=True, default=dict, help_text='Mapped onto FormConfiguration.fields_config')),
                        ('resolved_item_ids', models.JSONField(blank=True, default=list, help_text='Matched BlocItem ids (status/restauration/social_event)')),
                        ('resolved_session_ids', models.JSONField(blank=True, default=list, help_text='Matched Session ids (workshops)')),
                        ('status', models.CharField(choices=[('valid', 'Valide'), ('error', 'Erreur'), ('skipped_duplicate', 'Ignoré (déjà inscrit)'), ('created', 'Créé')], default='valid', max_length=20)),
                        ('error_message', models.CharField(blank=True, max_length=500)),
                        ('batch', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='rows', to='dashboard.participantimportbatch')),
                        ('participant', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='import_rows', to='events.participant')),
                    ],
                    options={
                        'verbose_name': 'Participant Import Row',
                        'verbose_name_plural': 'Participant Import Rows',
                        'db_table': 'dashboard_participantimportrow',
                        'ordering': ['row_number'],
                    },
                ),
                migrations.AddIndex(
                    model_name='participantimportrow',
                    index=models.Index(fields=['batch', 'status'], name='dashboard_p_batch_i_b1bc4e_idx'),
                ),
            ],
        ),
    ]
