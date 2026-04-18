# Generated migration for signup_data field

from django.db import migrations


def add_signup_data_field(apps, schema_editor):
    """Add signup_data field to SignUpVerification table if it doesn't exist"""
    from django.db import connection
    
    with connection.cursor() as cursor:
        # Check if signup_data column exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = 'events_signupverification' 
                AND column_name = 'signup_data'
            );
        """)
        
        if not cursor.fetchone()[0]:
            cursor.execute("""
                ALTER TABLE events_signupverification 
                ADD COLUMN signup_data JSONB DEFAULT '{}'::jsonb NOT NULL;
            """)
            print("✓ Added signup_data field to SignUpVerification")
        else:
            print("✓ signup_data field already exists in SignUpVerification")


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0023_add_verification_models'),
    ]

    operations = [
        migrations.RunPython(add_signup_data_field, migrations.RunPython.noop),
    ]
