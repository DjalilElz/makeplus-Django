"""
Add RegistrationOrder.reviewed_by_caisse (nullable FK to caisse.Caisse).

Follows the idempotent SeparateDatabaseAndState pattern established in
0026/0027: this production database has repeatedly lost its
django_migrations bookkeeping for this app between deploys, so a plain
AddField can crash with "column already exists" on a re-run even though
the column is already correctly in place. Checking column existence first
makes a re-run a safe no-op instead.
"""
import django.db.models.deletion
from django.db import migrations, models


def _column_names(schema_editor, table_name):
    with schema_editor.connection.cursor() as cursor:
        return {
            col.name for col in
            schema_editor.connection.introspection.get_table_description(cursor, table_name)
        }


def add_reviewed_by_caisse_column(apps, schema_editor):
    from dashboard.models_blocs import RegistrationOrder

    if 'reviewed_by_caisse_id' in _column_names(schema_editor, 'dashboard_registrationorder'):
        return
    schema_editor.add_field(RegistrationOrder, RegistrationOrder._meta.get_field('reviewed_by_caisse'))


def reverse_noop(apps, schema_editor):
    """No-op reverse -- avoid dropping a column that may hold real data."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0027_registrationorder_participant'),
        ('caisse', '0006_payableitem_bloc_item_and_more'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterField(
                    model_name='registrationorder',
                    name='status',
                    field=models.CharField(
                        choices=[
                            ('pending', 'Reserved (awaiting caisse confirmation)'),
                            ('approved', 'Confirmed at Caisse'),
                            ('rejected', 'Rejected'),
                        ],
                        default='pending', max_length=20,
                    ),
                ),
                migrations.AlterField(
                    model_name='registrationorder',
                    name='admin_notes',
                    field=models.TextField(
                        blank=True, help_text='Notes from whoever confirmed/rejected this (caisse or admin)'
                    ),
                ),
                migrations.AddField(
                    model_name='registrationorder',
                    name='reviewed_by_caisse',
                    field=models.ForeignKey(
                        blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                        related_name='reviewed_registration_orders', to='caisse.caisse',
                        help_text='Which caisse station confirmed or rejected this reservation on event day',
                    ),
                ),
            ],
            database_operations=[
                migrations.RunPython(add_reviewed_by_caisse_column, reverse_noop),
            ],
        ),
    ]
