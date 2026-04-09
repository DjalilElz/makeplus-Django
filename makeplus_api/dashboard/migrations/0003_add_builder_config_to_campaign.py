# Generated migration to add builder_config field to EmailCampaign

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0002_add_design_json_to_eposter_email_template'),
    ]

    operations = [
        migrations.AddField(
            model_name='emailcampaign',
            name='builder_config',
            field=models.TextField(blank=True, help_text='Unlayer email builder design JSON'),
        ),
    ]
