# Generated migration for performance optimization

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0008_merge_20251218_1006'),
    ]

    operations = [
        # Add composite indexes for common queries
        migrations.AddIndex(
            model_name='participant',
            index=models.Index(fields=['event', 'is_checked_in'], name='participant_event_checkin_idx'),
        ),
        migrations.AddIndex(
            model_name='session',
            index=models.Index(fields=['event', 'session_type'], name='session_event_type_idx'),
        ),
        migrations.AddIndex(
            model_name='session',
            index=models.Index(fields=['event', 'start_time'], name='session_event_start_idx'),
        ),
        migrations.AddIndex(
            model_name='usereventassignment',
            index=models.Index(fields=['event', 'role', 'is_active'], name='assignment_event_role_idx'),
        ),
        migrations.AddIndex(
            model_name='roomaccess',
            index=models.Index(fields=['room', 'access_time'], name='roomaccess_room_time_idx'),
        ),
        migrations.AddIndex(
            model_name='exposantscan',
            index=models.Index(fields=['participant', 'scan_time'], name='scan_participant_time_idx'),
        ),
        migrations.AddIndex(
            model_name='sessionquestion',
            index=models.Index(fields=['session', 'is_answered'], name='question_session_answer_idx'),
        ),
    ]
