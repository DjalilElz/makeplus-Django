"""
Add PayableItem.bloc_item, the 'bloc' item_type choice, and
CaisseTransaction.payment_method.

Made idempotent (check column existence before adding) following the
pattern established in dashboard/migrations/0026+: this production
database has repeatedly lost its django_migrations bookkeeping between
deploys, which made this migration crash with
'column "bloc_item_id" of relation "caisse_payableitem" already exists'
on a re-run even though the columns were already correctly in place.
"""
import django.db.models.deletion
from django.db import migrations, models


def _column_names(schema_editor, table_name):
    with schema_editor.connection.cursor() as cursor:
        return {
            col.name for col in
            schema_editor.connection.introspection.get_table_description(cursor, table_name)
        }


def add_columns(apps, schema_editor):
    from .models import PayableItem, CaisseTransaction

    payable_item_columns = _column_names(schema_editor, 'caisse_payableitem')
    if 'bloc_item_id' not in payable_item_columns:
        schema_editor.add_field(PayableItem, PayableItem._meta.get_field('bloc_item'))

    transaction_columns = _column_names(schema_editor, 'caisse_caissetransaction')
    if 'payment_method' not in transaction_columns:
        schema_editor.add_field(CaisseTransaction, CaisseTransaction._meta.get_field('payment_method'))


def reverse_noop(apps, schema_editor):
    """No-op reverse -- avoid dropping columns that may hold real data."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('caisse', '0005_alter_payableitem_item_type_and_more'),
        ('dashboard', '0026_blocitem_eventblocconfig_reductionperiod_and_more'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddField(
                    model_name='payableitem',
                    name='bloc_item',
                    field=models.ForeignKey(
                        blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                        related_name='payable_items', to='dashboard.blocitem',
                        help_text='Link to the registration bloc item this mirrors (status/restauration/social_event)',
                    ),
                ),
                migrations.AlterField(
                    model_name='payableitem',
                    name='item_type',
                    field=models.CharField(
                        choices=[
                            ('session', 'Session/Workshop'), ('dinner', 'Dinner/Meal'),
                            ('access', 'Access/Entry'), ('bloc', 'Registration Bloc Item'),
                            ('other', 'Other'),
                        ],
                        default='other', max_length=20,
                    ),
                ),
                migrations.AddField(
                    model_name='caissetransaction',
                    name='payment_method',
                    field=models.CharField(
                        choices=[('cash', 'Cash'), ('bank_transfer', 'Bank Transfer'), ('mixed', 'Mixed (cash + bank transfer)')],
                        default='cash', max_length=20,
                    ),
                ),
            ],
            database_operations=[
                migrations.RunPython(add_columns, reverse_noop),
            ],
        ),
    ]
