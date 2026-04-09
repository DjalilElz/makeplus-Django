# Generated migration to add design_json field to EPosterEmailTemplate

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='eposteremailtemplate',
            name='design_json',
            field=models.TextField(blank=True, help_text='Unlayer design JSON'),
        ),
    ]
