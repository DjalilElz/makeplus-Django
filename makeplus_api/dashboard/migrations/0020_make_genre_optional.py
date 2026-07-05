# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0019_rename_to_scientific_contributions'),
    ]

    operations = [
        migrations.AlterField(
            model_name='scientificcontributionsubmission',
            name='genre',
            field=models.CharField(blank=True, choices=[('homme', 'Homme'), ('femme', 'Femme')], max_length=10, null=True, verbose_name='Genre'),
        ),
    ]
