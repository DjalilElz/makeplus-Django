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

    The actual DB operation is idempotent (ADD COLUMN IF NOT EXISTS) --
    see the project's documented recurring issue: production's
    django_migrations bookkeeping keeps losing track of migrations
    between Render deploys, so a plain AddField here already crashed
    once with "column already exists" when this same migration got
    re-run against a database that already had it.
    """

    dependencies = [
        ('dashboard', '0043_registrationorder_payment_link_sent_at'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddField(
                    model_name='eventformconfiguration',
                    name='require_contribution_number',
                    field=models.BooleanField(
                        default=True,
                        verbose_name='Numéro de contribution obligatoire à la soumission finale',
                        help_text="Si désactivé, l'auteur peut soumettre sans code -- le rapprochement se fait alors par e-mail + type de participation.",
                    ),
                ),
            ],
            database_operations=[
                migrations.RunSQL(
                    sql=(
                        "ALTER TABLE dashboard_eventformconfiguration "
                        "ADD COLUMN IF NOT EXISTS require_contribution_number boolean NOT NULL DEFAULT TRUE;"
                    ),
                    reverse_sql=(
                        "ALTER TABLE dashboard_eventformconfiguration "
                        "DROP COLUMN IF EXISTS require_contribution_number;"
                    ),
                ),
            ],
        ),
    ]
