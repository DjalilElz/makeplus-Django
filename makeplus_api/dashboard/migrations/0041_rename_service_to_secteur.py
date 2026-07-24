from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0040_eventemailtemplate_payment_link_relabel'),
    ]

    operations = [
        migrations.RenameField(
            model_name='epostersubmission',
            old_name='service',
            new_name='secteur',
        ),
        migrations.AlterField(
            model_name='epostersubmission',
            name='secteur',
            field=models.CharField(
                choices=[('public', 'Public'), ('prive', 'Privé')],
                max_length=200,
                verbose_name='Secteur',
            ),
        ),
    ]
