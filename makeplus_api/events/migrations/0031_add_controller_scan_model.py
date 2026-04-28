# Generated manually on 2026-04-28 15:30
# Clean migration that only creates ControllerScan model

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0030_alter_participant_qr_code_data'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ControllerScan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('participant_user_id', models.IntegerField(help_text='User ID of scanned participant')),
                ('badge_id', models.CharField(help_text='Badge ID scanned', max_length=100)),
                ('participant_name', models.CharField(help_text='Participant full name', max_length=255)),
                ('participant_email', models.EmailField(help_text='Participant email', max_length=254)),
                ('scanned_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('status', models.CharField(choices=[('success', 'Success'), ('error', 'Error'), ('not_registered', 'Not Registered')], default='success', max_length=20)),
                ('error_message', models.TextField(blank=True, help_text='Error message if scan failed')),
                ('total_paid_items', models.IntegerField(default=0, help_text='Number of paid items at scan time')),
                ('total_amount', models.DecimalField(decimal_places=2, default=0, help_text='Total amount paid', max_digits=10)),
                ('controller', models.ForeignKey(help_text='Controller who scanned', on_delete=django.db.models.deletion.CASCADE, related_name='controller_scans', to=settings.AUTH_USER_MODEL)),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='controller_scans', to='events.event')),
            ],
            options={
                'ordering': ['-scanned_at'],
            },
        ),
        migrations.AddIndex(
            model_name='controllerscan',
            index=models.Index(fields=['controller', '-scanned_at'], name='events_cont_control_b4e68d_idx'),
        ),
        migrations.AddIndex(
            model_name='controllerscan',
            index=models.Index(fields=['event', '-scanned_at'], name='events_cont_event_i_d74a38_idx'),
        ),
        migrations.AddIndex(
            model_name='controllerscan',
            index=models.Index(fields=['controller', 'event', '-scanned_at'], name='events_cont_control_132a72_idx'),
        ),
    ]
