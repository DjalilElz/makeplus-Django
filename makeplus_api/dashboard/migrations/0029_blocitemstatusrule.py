"""
Add BlocItemStatusRule: status-dependent visibility/price overrides for
items in Restauration/Social Event/Workshops.

Follows the idempotent SeparateDatabaseAndState pattern established in
0026/0027/0028: this production database has repeatedly lost its
django_migrations bookkeeping for this app between deploys, so a plain
CreateModel can crash with "relation already exists" on a re-run even
though the table is already correctly in place.
"""
import django.db.models.deletion
from django.db import migrations, models


def _table_names(schema_editor):
    with schema_editor.connection.cursor() as cursor:
        return set(schema_editor.connection.introspection.table_names(cursor))


def _index_names(schema_editor, table_name):
    with schema_editor.connection.cursor() as cursor:
        constraints = schema_editor.connection.introspection.get_constraints(cursor, table_name)
        return set(constraints.keys())


def create_schema(apps, schema_editor):
    from dashboard.models_blocs import BlocItemStatusRule

    existing_tables = _table_names(schema_editor)
    if 'dashboard_blocitemstatusrule' not in existing_tables:
        schema_editor.create_model(BlocItemStatusRule)
        return

    # Table already exists (bookkeeping loss) -- make sure the two partial
    # unique constraints are present too, adding whichever are missing.
    existing_constraints = _index_names(schema_editor, 'dashboard_blocitemstatusrule')
    if 'uniq_status_rule_item' not in existing_constraints:
        schema_editor.add_constraint(BlocItemStatusRule, BlocItemStatusRule._meta.constraints[0])
    if 'uniq_status_rule_session' not in existing_constraints:
        schema_editor.add_constraint(BlocItemStatusRule, BlocItemStatusRule._meta.constraints[1])


def reverse_noop(apps, schema_editor):
    """No-op reverse -- this migration is a resilience guard as much as a
    schema-creation step, so reversing it should not drop a table that may
    hold real production data."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0028_registrationorder_reviewed_by_caisse'),
        ('events', '0033_unique_user_email'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.CreateModel(
                    name='BlocItemStatusRule',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('target_kind', models.CharField(choices=[('item', 'Bloc Item'), ('session', 'Workshop Session')], max_length=10)),
                        ('is_visible', models.BooleanField(default=True)),
                        ('override_price', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                        ('created_at', models.DateTimeField(auto_now_add=True)),
                        ('updated_at', models.DateTimeField(auto_now=True)),
                        ('status_item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='dependent_rules', to='dashboard.blocitem')),
                        ('target_item', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='status_rules', to='dashboard.blocitem')),
                        ('target_session', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='status_rules', to='events.session')),
                    ],
                    options={
                        'verbose_name': 'Bloc Item Status Rule',
                        'verbose_name_plural': 'Bloc Item Status Rules',
                    },
                ),
                migrations.AddConstraint(
                    model_name='blocitemstatusrule',
                    constraint=models.UniqueConstraint(condition=models.Q(('target_kind', 'item')), fields=('status_item', 'target_item'), name='uniq_status_rule_item'),
                ),
                migrations.AddConstraint(
                    model_name='blocitemstatusrule',
                    constraint=models.UniqueConstraint(condition=models.Q(('target_kind', 'session')), fields=('status_item', 'target_session'), name='uniq_status_rule_session'),
                ),
            ],
            database_operations=[
                migrations.RunPython(create_schema, reverse_noop),
            ],
        ),
    ]
