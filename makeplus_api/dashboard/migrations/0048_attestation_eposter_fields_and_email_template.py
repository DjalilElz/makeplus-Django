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
    """

    dependencies = [
        ('dashboard', '0047_alter_attestationtemplate_template_image_max_length'),
        ('events', '0025_restructure_participant_model'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
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
    ]
