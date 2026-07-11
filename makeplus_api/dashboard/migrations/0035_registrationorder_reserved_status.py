"""
Add 'reserved' to RegistrationOrder.status choices and relabel the
existing three (Registered/Reserved/Confirmed/Cancelled instead of the
previous Reserved/Confirmed at Caisse/Rejected wording), so event
owners can hold a spot without it implying real payment/access.

choices on a CharField are Python-level validation only -- no database
schema change, so this is a pure state-only AlterField.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0034_registrationorder_period'),
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
                    ('approved', 'Confirmed'),
                    ('rejected', 'Cancelled'),
                ],
                default='pending',
            ),
        ),
    ]
