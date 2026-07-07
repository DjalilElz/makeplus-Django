"""
Enforce email uniqueness on auth_user at the database level.

auth.User is Django's built-in model (not ours to AlterField on directly),
so this adds the constraint via raw SQL instead. Blank emails are excluded
from the constraint so multiple accounts without an email (e.g. superusers
created via createsuperuser) don't collide.
"""

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0032_alter_exposantscan_notes'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.RunSQL(
            sql="CREATE UNIQUE INDEX IF NOT EXISTS auth_user_email_uniq_idx ON auth_user (email) WHERE email <> '';",
            reverse_sql="DROP INDEX IF EXISTS auth_user_email_uniq_idx;",
        ),
    ]
