import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('caisse', '0005_alter_payableitem_item_type_and_more'),
        ('dashboard', '0026_blocitem_eventblocconfig_reductionperiod_and_more'),
    ]

    operations = [
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
    ]
