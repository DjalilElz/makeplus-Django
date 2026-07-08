"""
Add RegistrationOrder.participant (nullable FK to events.Participant).

Follows the idempotent SeparateDatabaseAndState pattern established in
0026_blocitem_eventblocconfig_reductionperiod_and_more.py: this production
database has repeatedly lost its django_migrations bookkeeping for this
app between deploys, so a plain AddField can crash with "column already
exists" on a re-run even though the column is already correctly in place.
Checking column existence first makes a re-run a safe no-op instead.
"""
import django.db.models.deletion
from django.db import migrations, models


def _column_names(schema_editor, table_name):
    with schema_editor.connection.cursor() as cursor:
        return {
            col.name for col in
            schema_editor.connection.introspection.get_table_description(cursor, table_name)
        }


def add_participant_column(apps, schema_editor):
    from dashboard.models_blocs import RegistrationOrder

    if 'participant_id' in _column_names(schema_editor, 'dashboard_registrationorder'):
        return
    schema_editor.add_field(RegistrationOrder, RegistrationOrder._meta.get_field('participant'))


def reverse_noop(apps, schema_editor):
    """No-op reverse -- avoid dropping a column that may hold real data."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0026_blocitem_eventblocconfig_reductionperiod_and_more'),
        ('events', '0033_unique_user_email'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddField(
                    model_name='registrationorder',
                    name='participant',
                    field=models.ForeignKey(
                        blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                        related_name='registration_orders', to='events.participant',
                    ),
                ),
            ],
            database_operations=[
                migrations.RunPython(add_participant_column, reverse_noop),
            ],
        ),
    ]
