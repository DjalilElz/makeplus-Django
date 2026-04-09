# Migration to add missing fields to FormConfiguration

from django.db import migrations, models


def add_missing_fields_if_not_exist(apps, schema_editor):
    """Add missing fields to FormConfiguration if they don't exist"""
    from django.db import connection
    
    with connection.cursor() as cursor:
        # Check if table exists first
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'dashboard_formconfiguration'
            );
        """)
        
        if not cursor.fetchone()[0]:
            # Table doesn't exist, skip this migration
            return
        
        # Check and add allow_multiple_submissions
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = 'dashboard_formconfiguration' 
                AND column_name = 'allow_multiple_submissions'
            );
        """)
        if not cursor.fetchone()[0]:
            cursor.execute("""
                ALTER TABLE dashboard_formconfiguration 
                ADD COLUMN allow_multiple_submissions BOOLEAN DEFAULT FALSE NOT NULL;
            """)
        
        # Check and add banner_image (if it doesn't exist)
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = 'dashboard_formconfiguration' 
                AND column_name = 'banner_image'
            );
        """)
        if not cursor.fetchone()[0]:
            cursor.execute("""
                ALTER TABLE dashboard_formconfiguration 
                ADD COLUMN banner_image VARCHAR(100) DEFAULT '' NOT NULL;
            """)
            cursor.execute("""
                ALTER TABLE dashboard_formconfiguration 
                ALTER COLUMN banner_image DROP DEFAULT;
            """)
        
        # Check and add countdown_enabled
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = 'dashboard_formconfiguration' 
                AND column_name = 'countdown_enabled'
            );
        """)
        if not cursor.fetchone()[0]:
            cursor.execute("""
                ALTER TABLE dashboard_formconfiguration 
                ADD COLUMN countdown_enabled BOOLEAN DEFAULT FALSE NOT NULL;
            """)
        
        # Check and add countdown_date
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = 'dashboard_formconfiguration' 
                AND column_name = 'countdown_date'
            );
        """)
        if not cursor.fetchone()[0]:
            cursor.execute("""
                ALTER TABLE dashboard_formconfiguration 
                ADD COLUMN countdown_date TIMESTAMP WITH TIME ZONE NULL;
            """)
        
        # Check and add countdown_title
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = 'dashboard_formconfiguration' 
                AND column_name = 'countdown_title'
            );
        """)
        if not cursor.fetchone()[0]:
            cursor.execute("""
                ALTER TABLE dashboard_formconfiguration 
                ADD COLUMN countdown_title VARCHAR(255) DEFAULT 'Event Starts In' NOT NULL;
            """)


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0013_add_design_json_to_eposter_email_template'),
    ]

    operations = [
        migrations.RunPython(add_missing_fields_if_not_exist, migrations.RunPython.noop),
    ]
