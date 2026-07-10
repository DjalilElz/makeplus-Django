"""
Add RegistrationOrder.period (nullable FK to ReductionPeriod): a
snapshot of whichever reduction period was active on the day the order
was placed, for the event-owner submissions view.

Follows the idempotent SeparateDatabaseAndState pattern established in
0026+: this production database has repeatedly lost its
django_migrations bookkeeping between deploys, so a plain AddField can
crash with "column already exists" on a re-run even though the column
is already correctly in place.
"""
import django.db.models.deletion
from django.db import migrations, models


def _column_names(schema_editor, table_name):
    with schema_editor.connection.cursor() as cursor:
        return {
            col.name for col in
            schema_editor.connection.introspection.get_table_description(cursor, table_name)
        }


def add_period_column(apps, schema_editor):
    from dashboard.models_blocs import RegistrationOrder

    if 'period_id' in _column_names(schema_editor, 'dashboard_registrationorder'):
        return
    schema_editor.add_field(RegistrationOrder, RegistrationOrder._meta.get_field('period'))


def reverse_noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0033_blocitem_description'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddField(
                    model_name='registrationorder',
                    name='period',
                    field=models.ForeignKey(
                        blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                        related_name='registration_orders', to='dashboard.reductionperiod',
                        help_text='Reduction period active when this order was placed (snapshot).',
                    ),
                ),
            ],
            database_operations=[
                migrations.RunPython(add_period_column, reverse_noop),
            ],
        ),
    ]
