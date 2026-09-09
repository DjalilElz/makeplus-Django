from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Hand-written (not via makemigrations): this repo's models.py and
    migration history have drifted apart badly for the eposter models
    (an old EPoster* -> ScientificContribution* rename was never captured
    as a real migration), so a plain `makemigrations` here proposes
    recreating/dropping whole tables instead of just this one field. Do
    not run bare makemigrations for this app until that drift is
    reconciled -- write migrations by hand and verify their operations
    list matches only the intended change.
    """

    dependencies = [
        ('dashboard', '0043_registrationorder_payment_link_sent_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='eventformconfiguration',
            name='require_contribution_number',
            field=models.BooleanField(
                default=True,
                verbose_name='Numéro de contribution obligatoire à la soumission finale',
                help_text="Si désactivé, l'auteur peut soumettre sans code -- le rapprochement se fait alors par e-mail + type de participation.",
            ),
        ),
    ]
