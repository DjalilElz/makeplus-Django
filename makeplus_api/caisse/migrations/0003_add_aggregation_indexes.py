# Generated migration for caisse performance optimization

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('caisse', '0002_add_performance_indexes'),
    ]

    operations = [
        # Add indexes for aggregation queries
        migrations.AddIndex(
            model_name='caissetransaction',
            index=models.Index(fields=['caisse', 'total_amount'], name='transaction_caisse_total_idx'),
        ),
        migrations.AddIndex(
            model_name='caissetransaction',
            index=models.Index(fields=['caisse', 'participant'], name='transaction_caisse_part_idx'),
        ),
        migrations.AddIndex(
            model_name='caissetransaction',
            index=models.Index(fields=['created_at'], name='transaction_created_idx'),
        ),
    ]
