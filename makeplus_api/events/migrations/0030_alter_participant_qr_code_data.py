# Generated migration to change Participant.qr_code_data from TextField to JSONField

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0029_convert_qr_code_data_to_json'),
    ]

    operations = [
        migrations.AlterField(
            model_name='participant',
            name='qr_code_data',
            field=models.JSONField(default=dict, blank=True, help_text='QR code content as JSON'),
        ),
    ]
