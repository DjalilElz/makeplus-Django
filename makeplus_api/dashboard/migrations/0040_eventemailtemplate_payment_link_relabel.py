"""
Rename the 'payment_link' choice's display label to 'Préinscription' on
EventEmailTemplate.template_type -- the stored value stays 'payment_link'
(no data migration needed, nothing already saved changes meaning), only
the human-readable label shown in the dashboard changes.

choices on a CharField are Python-level validation only -- no database
schema change, so this is a pure state-only AlterField (same as 0038/0039).
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0039_eventemailtemplate_order_confirmation_payment_link'),
    ]

    operations = [
        migrations.AlterField(
            model_name='eventemailtemplate',
            name='template_type',
            field=models.CharField(
                choices=[
                    ('invitation', 'Invitation'),
                    ('confirmation', 'Confirmation'),
                    ('reminder', 'Reminder'),
                    ('follow_up', 'Follow-up'),
                    ('announcement', 'Announcement'),
                    ('registration_confirmation', 'Registration Confirmation'),
                    ('order_confirmation', 'Order Confirmation (Paid)'),
                    ('payment_link', 'Préinscription'),
                    ('custom', 'Custom'),
                ],
                default='custom',
                help_text='Type of email template',
                max_length=30,
            ),
        ),
    ]
