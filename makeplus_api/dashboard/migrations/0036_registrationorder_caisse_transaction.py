"""
Add RegistrationOrder.caisse_transaction (nullable FK to
caisse.CaisseTransaction): a reliable link back to the exact
transaction caisse.services.confirm_registration_order creates when an
event owner confirms a registration, so cancelling it later can void
that specific transaction precisely.

Follows the idempotent SeparateDatabaseAndState pattern established in
this app (0026+, 0033, 0034): this production database has repeatedly
lost its django_migrations bookkeeping between deploys, so a plain
AddField can crash with "column already exists" on a re-run even
though the column is already correctly in place.
"""
import django.db.models.deletion
from django.db import migrations, models


def add_column(apps, schema_editor):
    from dashboard.models_blocs import RegistrationOrder

    table = 'dashboard_registrationorder'
    with schema_editor.connection.cursor() as cursor:
        columns = {
            col.name for col in
            schema_editor.connection.introspection.get_table_description(cursor, table)
        }
    if 'caisse_transaction_id' not in columns:
        schema_editor.add_field(RegistrationOrder, RegistrationOrder._meta.get_field('caisse_transaction'))


def reverse_noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0035_registrationorder_reserved_status'),
        ('caisse', '0006_payableitem_bloc_item_and_more'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddField(
                    model_name='registrationorder',
                    name='caisse_transaction',
                    field=models.ForeignKey(
                        blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                        related_name='owner_confirmed_orders', to='caisse.caissetransaction',
                    ),
                ),
            ],
            database_operations=[
                migrations.RunPython(add_column, reverse_noop),
            ],
        ),
    ]
