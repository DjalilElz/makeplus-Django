"""
Add EventBlocConfig.require_payment_proof: an admin toggle to make the
bank-receipt-upload requirement on the public registration form
optional per event, independent of price.

Follows the idempotent SeparateDatabaseAndState pattern established in
0026+: this production database has repeatedly lost its
django_migrations bookkeeping between deploys, so a plain AddField can
crash with "column already exists" on a re-run even though the column
is already correctly in place.
"""
from django.db import migrations, models


def add_column(apps, schema_editor):
    from dashboard.models_blocs import EventBlocConfig

    table = 'dashboard_eventblocconfig'
    with schema_editor.connection.cursor() as cursor:
        columns = {
            col.name for col in
            schema_editor.connection.introspection.get_table_description(cursor, table)
        }
    if 'require_payment_proof' not in columns:
        schema_editor.add_field(EventBlocConfig, EventBlocConfig._meta.get_field('require_payment_proof'))


def reverse_noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0031_drop_stale_status_rule_unique_indexes'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddField(
                    model_name='eventblocconfig',
                    name='require_payment_proof',
                    field=models.BooleanField(default=True),
                ),
            ],
            database_operations=[
                migrations.RunPython(add_column, reverse_noop),
            ],
        ),
    ]
