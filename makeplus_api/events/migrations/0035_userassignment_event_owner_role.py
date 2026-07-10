"""
Add 'event_owner' to UserEventAssignment's role choices, for accounts
that can log in and view (read-only) the registration submissions for
their own event.

choices on a CharField are Python-level validation only -- no database
schema change, so this is a pure state-only AlterField (no ALTER TABLE
of any kind, nothing that could conflict with the actual column).
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0034_session_is_active'),
    ]

    operations = [
        migrations.AlterField(
            model_name='usereventassignment',
            name='role',
            field=models.CharField(
                max_length=30,
                choices=[
                    ('gestionnaire_des_salles', 'Gestionnaire de Salle'),
                    ('controlleur_des_badges', 'Contrôleur'),
                    ('exposant', 'Exposant'),
                    ('committee', 'Committee'),
                    ('event_owner', 'Event Owner'),
                    ('participant', 'Participant'),
                ],
            ),
        ),
    ]
