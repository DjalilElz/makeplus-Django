"""
Add database indexes for caisse performance optimization
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('caisse', '0001_initial'),
    ]

    operations = [
        # Caisse indexes
        migrations.AddIndex(
            model_name='caisse',
            index=models.Index(fields=['event', 'name'], name='caisse_event_name_idx'),
        ),
        
        # Transaction indexes  
        migrations.AddIndex(
            model_name='caissetransaction',
            index=models.Index(fields=['caisse', 'status', '-created_at'], name='transaction_caisse_status_idx'),
        ),
        migrations.AddIndex(
            model_name='caissetransaction',
            index=models.Index(fields=['participant', '-created_at'], name='transaction_participant_idx'),
        ),
        
        # Payable Item indexes
        migrations.AddIndex(
            model_name='payableitem',
            index=models.Index(fields=['event', 'item_type'], name='payableitem_event_type_idx'),
        ),
    ]
