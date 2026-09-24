import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Hand-written, not `makemigrations`-generated: this app's migration
    state has pre-existing drift unrelated to this change (renamed
    eposter models, other apps' raw-SQL history gaps -- see 0025's and
    0020's fixes), and `makemigrations` picks all of that up too. Kept
    to exactly the two things this change actually needs.

    Every database operation is guarded raw SQL (IF NOT EXISTS), paired
    with SeparateDatabaseAndState so Django's model state still matches
    what plain AddField/CreateModel would have produced. This app's
    migration history has repeatedly lost its recorded-applied rows in
    production before (see 0020/0025) -- this migration hit exactly
    that: it had already fully succeeded once, then got genuinely
    re-attempted and failed with "column font_weight already exists"
    because none of its original operations were re-run-safe.
    """

    dependencies = [
        ('dashboard', '0047_alter_attestationtemplate_template_image_max_length'),
        ('events', '0025_restructure_participant_model'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="""
                    ALTER TABLE dashboard_attestationtemplate ADD COLUMN IF NOT EXISTS font_weight VARCHAR(10) NOT NULL DEFAULT 'regular';
                    ALTER TABLE dashboard_attestationtemplate ADD COLUMN IF NOT EXISTS title_x DOUBLE PRECISION NOT NULL DEFAULT 0.5;
                    ALTER TABLE dashboard_attestationtemplate ADD COLUMN IF NOT EXISTS title_y DOUBLE PRECISION NOT NULL DEFAULT 0.65;
                    ALTER TABLE dashboard_attestationtemplate ADD COLUMN IF NOT EXISTS title_align VARCHAR(10) NOT NULL DEFAULT 'center';
                    ALTER TABLE dashboard_attestationtemplate ADD COLUMN IF NOT EXISTS title_font_size INTEGER NOT NULL DEFAULT 30;
                    ALTER TABLE dashboard_attestationtemplate ADD COLUMN IF NOT EXISTS co_authors_x DOUBLE PRECISION NOT NULL DEFAULT 0.5;
                    ALTER TABLE dashboard_attestationtemplate ADD COLUMN IF NOT EXISTS co_authors_y DOUBLE PRECISION NOT NULL DEFAULT 0.78;
                    ALTER TABLE dashboard_attestationtemplate ADD COLUMN IF NOT EXISTS co_authors_align VARCHAR(10) NOT NULL DEFAULT 'center';
                    ALTER TABLE dashboard_attestationtemplate ADD COLUMN IF NOT EXISTS co_authors_font_size INTEGER NOT NULL DEFAULT 20;
                    """,
                    reverse_sql="""
                    ALTER TABLE dashboard_attestationtemplate DROP COLUMN IF EXISTS font_weight;
                    ALTER TABLE dashboard_attestationtemplate DROP COLUMN IF EXISTS title_x;
                    ALTER TABLE dashboard_attestationtemplate DROP COLUMN IF EXISTS title_y;
                    ALTER TABLE dashboard_attestationtemplate DROP COLUMN IF EXISTS title_align;
                    ALTER TABLE dashboard_attestationtemplate DROP COLUMN IF EXISTS title_font_size;
                    ALTER TABLE dashboard_attestationtemplate DROP COLUMN IF EXISTS co_authors_x;
                    ALTER TABLE dashboard_attestationtemplate DROP COLUMN IF EXISTS co_authors_y;
                    ALTER TABLE dashboard_attestationtemplate DROP COLUMN IF EXISTS co_authors_align;
                    ALTER TABLE dashboard_attestationtemplate DROP COLUMN IF EXISTS co_authors_font_size;
                    """,
                ),
                migrations.RunSQL(
                    sql="""
                    CREATE TABLE IF NOT EXISTS dashboard_attestationemailtemplate (
                        id UUID PRIMARY KEY,
                        recipient_type VARCHAR(20) NOT NULL,
                        subject VARCHAR(300) NOT NULL,
                        body_html TEXT NOT NULL,
                        body_text TEXT NOT NULL DEFAULT '',
                        design_json JSONB NOT NULL DEFAULT '{}',
                        is_active BOOLEAN NOT NULL DEFAULT TRUE,
                        created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                        updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                        created_by_id INTEGER NULL REFERENCES auth_user(id) ON DELETE SET NULL,
                        event_id UUID NOT NULL REFERENCES events_event(id) ON DELETE CASCADE,
                        UNIQUE (event_id, recipient_type)
                    );
                    CREATE INDEX IF NOT EXISTS dashboard_attestationemailtemplate_created_by_id_idx ON dashboard_attestationemailtemplate (created_by_id);
                    CREATE INDEX IF NOT EXISTS dashboard_attestationemailtemplate_event_id_idx ON dashboard_attestationemailtemplate (event_id);
                    """,
                    reverse_sql="DROP TABLE IF EXISTS dashboard_attestationemailtemplate CASCADE;",
                ),
            ],
            state_operations=[
                migrations.AddField(
                    model_name='attestationtemplate',
                    name='font_weight',
                    field=models.CharField(choices=[('regular', 'Normal'), ('medium', 'Medium'), ('bold', 'Gras')], default='regular', max_length=10),
                ),
                migrations.AddField(
                    model_name='attestationtemplate',
                    name='title_x',
                    field=models.FloatField(default=0.5, verbose_name='Titre - Position X'),
                ),
                migrations.AddField(
                    model_name='attestationtemplate',
                    name='title_y',
                    field=models.FloatField(default=0.65, verbose_name='Titre - Position Y'),
                ),
                migrations.AddField(
                    model_name='attestationtemplate',
                    name='title_align',
                    field=models.CharField(choices=[('left', 'Gauche'), ('center', 'Centré'), ('right', 'Droite')], default='center', max_length=10),
                ),
                migrations.AddField(
                    model_name='attestationtemplate',
                    name='title_font_size',
                    field=models.PositiveIntegerField(default=30),
                ),
                migrations.AddField(
                    model_name='attestationtemplate',
                    name='co_authors_x',
                    field=models.FloatField(default=0.5, verbose_name='Co-auteurs - Position X'),
                ),
                migrations.AddField(
                    model_name='attestationtemplate',
                    name='co_authors_y',
                    field=models.FloatField(default=0.78, verbose_name='Co-auteurs - Position Y'),
                ),
                migrations.AddField(
                    model_name='attestationtemplate',
                    name='co_authors_align',
                    field=models.CharField(choices=[('left', 'Gauche'), ('center', 'Centré'), ('right', 'Droite')], default='center', max_length=10),
                ),
                migrations.AddField(
                    model_name='attestationtemplate',
                    name='co_authors_font_size',
                    field=models.PositiveIntegerField(default=20),
                ),
                migrations.CreateModel(
                    name='AttestationEmailTemplate',
                    fields=[
                        ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                        ('recipient_type', models.CharField(choices=[('participant', 'Participant'), ('eposter', 'Présentateur ePoster')], max_length=20)),
                        ('subject', models.CharField(max_length=300)),
                        ('body_html', models.TextField(help_text='HTML content with placeholders: {{prenom}}, {{nom}}, {{event_name}}, {{event_location}}, {{event_start_date}}, {{event_end_date}}, {{titre}}, {{co_auteurs}}')),
                        ('body_text', models.TextField(blank=True, help_text='Plain text version (optional)')),
                        ('design_json', models.JSONField(blank=True, default=dict, help_text='Unlayer editor design JSON')),
                        ('is_active', models.BooleanField(default=True)),
                        ('created_at', models.DateTimeField(auto_now_add=True)),
                        ('updated_at', models.DateTimeField(auto_now=True)),
                        ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                        ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attestation_email_templates', to='events.event')),
                    ],
                    options={
                        'verbose_name': 'Attestation Email Template',
                        'verbose_name_plural': 'Attestation Email Templates',
                        'db_table': 'dashboard_attestationemailtemplate',
                    },
                ),
                migrations.AlterUniqueTogether(
                    name='attestationemailtemplate',
                    unique_together={('event', 'recipient_type')},
                ),
            ],
        ),
    ]
