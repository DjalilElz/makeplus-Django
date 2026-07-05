# Migration to make original_submission optional in final submission
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0021_alter_eposteremailtemplate_type_length'),
    ]

    operations = [
        migrations.AlterField(
            model_name='eposterfinalsubmission',
            name='original_submission',
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='final_submission',
                to='dashboard.epostersubmission',
                verbose_name='Soumission originale'
            ),
        ),
    ]
