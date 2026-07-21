"""
Add 'order_confirmation' and 'payment_link' to EventEmailTemplate.template_type
choices -- lets an event admin write their own subject/body for the
registration-confirmation email (caisse.services._send_confirmation_email)
and the payment-link email (dashboard.views_event_owner.send_payment_link_email),
same as the existing 'registration_confirmation' type.

choices on a CharField are Python-level validation only -- no database
schema change, so this is a pure state-only AlterField (same as 0038).
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0038_registrationorder_contact_statuses'),
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
                    ('payment_link', 'Payment Link'),
                    ('custom', 'Custom'),
                ],
                default='custom',
                help_text='Type of email template',
                max_length=30,
            ),
        ),
    ]
