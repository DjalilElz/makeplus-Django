# Generated manually to fix ExposantScan notes field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0031_add_controller_scan_model'),
    ]

    operations = [
        migrations.AlterField(
            model_name='exposantscan',
            name='notes',
            field=models.TextField(blank=True, null=True, help_text='Optional notes about the visit'),
        ),
    ]
