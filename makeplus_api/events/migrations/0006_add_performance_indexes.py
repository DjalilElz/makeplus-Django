# Generated migration for performance optimization

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0005_userprofile'),
    ]

    operations = [
        # Add index on Event status and start_date for faster filtering
        migrations.AlterModelOptions(
            name='event',
            options={'ordering': ['-start_date']},
        ),
        
        # Add index on Room event for faster lookups
        migrations.AlterModelOptions(
            name='room',
            options={'ordering': ['name']},
        ),
        
        # Add index on Session event and room for faster filtering
        migrations.AlterModelOptions(
            name='session',
            options={'ordering': ['start_time']},
        ),
        
        # Add index on Participant event for faster counting
        migrations.AlterModelOptions(
            name='participant',
            options={'ordering': ['-created_at']},
        ),
        
        # Add index on UserEventAssignment for role filtering
        migrations.AlterModelOptions(
            name='usereventassignment',
            options={'ordering': ['-created_at']},
        ),
    ]
