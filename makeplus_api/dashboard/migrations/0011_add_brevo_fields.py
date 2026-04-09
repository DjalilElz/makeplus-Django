# Generated migration for Brevo integration

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0010_merge_20260401_1022'),
    ]

    operations = [
        migrations.AddField(
            model_name='emailcampaign',
            name='external_campaign_id',
            field=models.CharField(blank=True, help_text='Brevo campaign ID', max_length=100),
        ),
        migrations.AddField(
            model_name='emailrecipient',
            name='external_id',
            field=models.CharField(blank=True, help_text='Brevo contact ID', max_length=100),
        ),
        migrations.AddField(
            model_name='emailrecipient',
            name='opens_count',
            field=models.IntegerField(default=0, help_text='Total opens count'),
        ),
        migrations.AddField(
            model_name='emailrecipient',
            name='clicks_count',
            field=models.IntegerField(default=0, help_text='Total clicks count'),
        ),
        migrations.AddIndex(
            model_name='emailrecipient',
            index=models.Index(fields=['external_id'], name='dashboard_e_externa_idx'),
        ),
    ]
