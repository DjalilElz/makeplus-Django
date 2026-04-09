"""
Add database indexes for performance optimization
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0002_alter_usereventassignment_role'),
    ]

    operations = [
        # Event indexes
        migrations.AddIndex(
            model_name='event',
            index=models.Index(fields=['status', '-start_date'], name='event_status_date_idx'),
        ),
        
        # Session indexes
        migrations.AddIndex(
            model_name='session',
            index=models.Index(fields=['event', 'start_time'], name='session_event_time_idx'),
        ),
        
        # UserEventAssignment indexes
        migrations.AddIndex(
            model_name='usereventassignment',
            index=models.Index(fields=['event', 'role', 'is_active'], name='assignment_event_role_idx'),
        ),
    ]
