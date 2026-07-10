"""
Add BlocItem.description: an optional free-text description shown under
the item's name on the public registration form.

Follows the idempotent SeparateDatabaseAndState pattern established in
0026+: this production database has repeatedly lost its
django_migrations bookkeeping between deploys, so a plain AddField can
crash with "column already exists" on a re-run even though the column
is already correctly in place.
"""
from django.db import migrations, models


def add_column(apps, schema_editor):
    from dashboard.models_blocs import BlocItem

    table = 'dashboard_blocitem'
    with schema_editor.connection.cursor() as cursor:
        columns = {
            col.name for col in
            schema_editor.connection.introspection.get_table_description(cursor, table)
        }
    if 'description' not in columns:
        schema_editor.add_field(BlocItem, BlocItem._meta.get_field('description'))


def reverse_noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0032_eventblocconfig_require_payment_proof'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddField(
                    model_name='blocitem',
                    name='description',
                    field=models.TextField(blank=True, default=''),
                ),
            ],
            database_operations=[
                migrations.RunPython(add_column, reverse_noop),
            ],
        ),
    ]
