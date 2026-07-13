"""
Add 'to_contact' and 'to_recontact' to RegistrationOrder.status choices --
plain follow-up bookkeeping statuses for the event-owner submissions page,
same as 'reserved' (no payment/access implied).

choices on a CharField are Python-level validation only -- no database
schema change, so this is a pure state-only AlterField (same as 0035).
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0037_formconfiguration_use_banner_image'),
    ]

    operations = [
        migrations.AlterField(
            model_name='registrationorder',
            name='status',
            field=models.CharField(
                max_length=20,
                choices=[
                    ('pending', 'Registered'),
                    ('reserved', 'Reserved'),
                    ('to_contact', 'To Contact'),
                    ('to_recontact', 'To Recontact'),
                    ('approved', 'Confirmed'),
                    ('rejected', 'Cancelled'),
                ],
                default='pending',
            ),
        ),
    ]
