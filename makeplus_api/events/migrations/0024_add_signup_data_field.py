# Generated migration for signup_data field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0023_add_verification_models'),
    ]

    operations = [
        migrations.AddField(
            model_name='signupverification',
            name='signup_data',
            field=models.JSONField(blank=True, default=dict, help_text='Temporary storage for first_name, last_name, password_hash'),
        ),
    ]
