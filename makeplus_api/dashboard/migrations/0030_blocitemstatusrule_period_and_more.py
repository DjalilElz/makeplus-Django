"""
Evolve BlocItemStatusRule into a combined status x period rules table:
make status_item nullable, add a nullable period FK, and drop the old
(status_item, target_item/session) unique constraints -- with both axes
now optional, a null-safe uniqueness check isn't practical across
backends, so uniqueness is instead guaranteed by the admin save view's
update_or_create (see bloc_status_rules_save).

Follows the idempotent SeparateDatabaseAndState pattern established in
0026+: this production database has repeatedly lost its
django_migrations bookkeeping between deploys, so a plain AddField/
AlterField/RemoveConstraint can crash with "already exists"/"does not
exist" on a re-run even though the change is already correctly in place.
"""
import django.db.models.deletion
from django.db import migrations, models


def _column_info(schema_editor, table_name):
    with schema_editor.connection.cursor() as cursor:
        return {
            col.name: col for col in
            schema_editor.connection.introspection.get_table_description(cursor, table_name)
        }


def _constraint_names(schema_editor, table_name):
    with schema_editor.connection.cursor() as cursor:
        constraints = schema_editor.connection.introspection.get_constraints(cursor, table_name)
        return set(constraints.keys())


def migrate_schema(apps, schema_editor):
    from dashboard.models_blocs import BlocItem, BlocItemStatusRule

    table = 'dashboard_blocitemstatusrule'
    columns = _column_info(schema_editor, table)

    if 'period_id' not in columns:
        schema_editor.add_field(BlocItemStatusRule, BlocItemStatusRule._meta.get_field('period'))

    status_item_col = columns.get('status_item_id')
    if status_item_col is not None and status_item_col.null_ok is False:
        new_field = BlocItemStatusRule._meta.get_field('status_item')
        old_field = new_field.clone()
        old_field.null = False
        old_field.blank = False
        old_field.set_attributes_from_name('status_item')
        old_field.model = BlocItemStatusRule
        # clone() resets remote_field.model back to a lazy string ref --
        # restore the resolved class so schema_editor can compare db_tables.
        old_field.remote_field.model = BlocItem
        schema_editor.alter_field(BlocItemStatusRule, old_field, new_field)

    existing_constraints = _constraint_names(schema_editor, table)
    if 'uniq_status_rule_item' in existing_constraints:
        schema_editor.execute(f'ALTER TABLE {table} DROP CONSTRAINT IF EXISTS uniq_status_rule_item')
    if 'uniq_status_rule_session' in existing_constraints:
        schema_editor.execute(f'ALTER TABLE {table} DROP CONSTRAINT IF EXISTS uniq_status_rule_session')

    existing_constraints = _constraint_names(schema_editor, table)
    if 'dashboard_b_status__d5e9a1_idx' not in existing_constraints:
        schema_editor.add_index(
            BlocItemStatusRule, models.Index(fields=['status_item', 'period'], name='dashboard_b_status__d5e9a1_idx')
        )


def reverse_noop(apps, schema_editor):
    """No-op reverse -- avoid destructive changes to a table with real data."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0029_blocitemstatusrule'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.RemoveConstraint(
                    model_name='blocitemstatusrule',
                    name='uniq_status_rule_item',
                ),
                migrations.RemoveConstraint(
                    model_name='blocitemstatusrule',
                    name='uniq_status_rule_session',
                ),
                migrations.AlterField(
                    model_name='blocitemstatusrule',
                    name='status_item',
                    field=models.ForeignKey(
                        blank=True, null=True, on_delete=django.db.models.deletion.CASCADE,
                        related_name='dependent_rules', to='dashboard.blocitem',
                    ),
                ),
                migrations.AddField(
                    model_name='blocitemstatusrule',
                    name='period',
                    field=models.ForeignKey(
                        blank=True, null=True, on_delete=django.db.models.deletion.CASCADE,
                        related_name='item_price_rules', to='dashboard.reductionperiod',
                    ),
                ),
                migrations.AddIndex(
                    model_name='blocitemstatusrule',
                    index=models.Index(fields=['status_item', 'period'], name='dashboard_b_status__d5e9a1_idx'),
                ),
                migrations.AlterModelOptions(
                    name='blocitemstatusrule',
                    options={'verbose_name': 'Bloc Item Price Rule', 'verbose_name_plural': 'Bloc Item Price Rules'},
                ),
            ],
            database_operations=[
                migrations.RunPython(migrate_schema, reverse_noop),
            ],
        ),
    ]
