import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Paying organisation on a caisse payment ('sponsoring'), and the payment
    method labels. Guarded SQL (IF NOT EXISTS): production has repeatedly
    lost rows from django_migrations, so this can be replayed against a
    database that already has the column.
    """

    dependencies = [
        ('caisse', '0006_payableitem_bloc_item_and_more'),
        ('dashboard', '0057_eventsponsor_and_order_payment'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="""
                    ALTER TABLE caisse_caissetransaction
                        ADD COLUMN IF NOT EXISTS sponsor_id bigint NULL
                        REFERENCES dashboard_eventsponsor (id) DEFERRABLE INITIALLY DEFERRED;
                    CREATE INDEX IF NOT EXISTS caisse_caissetransaction_sponsor_id_idx
                        ON caisse_caissetransaction (sponsor_id);
                    """,
                    reverse_sql="ALTER TABLE caisse_caissetransaction DROP COLUMN IF EXISTS sponsor_id;",
                ),
            ],
            state_operations=[
                migrations.AddField(
                    model_name='caissetransaction',
                    name='sponsor',
                    field=models.ForeignKey(blank=True, help_text="Paying organisation, for 'sponsoring' only", null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='caisse_transactions', to='dashboard.eventsponsor'),
                ),
                # Labels only -- no database change.
                migrations.AlterField(
                    model_name='caissetransaction',
                    name='payment_method',
                    field=models.CharField(choices=[('cash', 'Espèces'), ('bank_transfer', 'Virement bancaire'), ('sponsoring', 'Prise en charge (Sponsoring)'), ('mixed', 'Mixte (espèces + virement)')], default='cash', max_length=20),
                ),
            ],
        ),
    ]
