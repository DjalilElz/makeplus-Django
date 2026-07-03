# Generated manually to fix eposter_code unique constraint issue
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0016_add_eposter_final_submission_safe'),
    ]

    operations = [
        migrations.AlterField(
            model_name='epostersubmission',
            name='eposter_code',
            field=models.CharField(blank=True, null=True, max_length=50, unique=True, verbose_name='Code ePoster'),
        ),
    ]
