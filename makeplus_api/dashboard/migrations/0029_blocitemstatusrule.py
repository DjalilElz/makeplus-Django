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


def create_schema(apps, schema_editor):
    from dashboard.models_blocs import BlocItemStatusRule

    existing_tables = _table_names(schema_editor)
    if 'dashboard_blocitemstatusrule' not in existing_tables:
        # create_model() uses the LIVE model class, so on a fresh table
        # this already produces the model's current shape (nullable
        # status_item, period FK, no more uniq_status_rule_item/session --
        # those were dropped in 0031). Migrations 0030-0032 idempotently
        # no-op on a table that already matches their target shape.
        schema_editor.create_model(BlocItemStatusRule)
        return

    # Table already exists (bookkeeping loss) -- nothing else to do here.
    # uniq_status_rule_item/uniq_status_rule_session used to be
    # backfilled at this point, but they were removed from the model in
    # 0030/0031 (superseded by a nullable status_item + period FK), so
    # there's nothing left for this migration to ensure beyond the
    # table's existence; 0030+ bring the rest of the schema up to date.


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
