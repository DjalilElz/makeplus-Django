# Generated migration for Brevo integration

from django.db import migrations, models


def add_brevo_fields_if_not_exist(apps, schema_editor):
    """Add Brevo fields only if they don't exist"""
    from django.db import connection
    
    with connection.cursor() as cursor:
        # Check and add external_campaign_id to emailcampaign
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = 'dashboard_emailcampaign' 
                AND column_name = 'external_campaign_id'
            );
        """)
        if not cursor.fetchone()[0]:
            cursor.execute("""
                ALTER TABLE dashboard_emailcampaign 
                ADD COLUMN external_campaign_id VARCHAR(100) DEFAULT '' NOT NULL;
            """)
            cursor.execute("""
                ALTER TABLE dashboard_emailcampaign 
                ALTER COLUMN external_campaign_id DROP DEFAULT;
            """)
        
        # Check and add external_id to emailrecipient
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = 'dashboard_emailrecipient' 
                AND column_name = 'external_id'
            );
        """)
        if not cursor.fetchone()[0]:
            cursor.execute("""
                ALTER TABLE dashboard_emailrecipient 
                ADD COLUMN external_id VARCHAR(100) DEFAULT '' NOT NULL;
            """)
            cursor.execute("""
                ALTER TABLE dashboard_emailrecipient 
                ALTER COLUMN external_id DROP DEFAULT;
            """)
        
        # Check and add opens_count to emailrecipient
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = 'dashboard_emailrecipient' 
                AND column_name = 'opens_count'
            );
        """)
        if not cursor.fetchone()[0]:
            cursor.execute("""
                ALTER TABLE dashboard_emailrecipient 
                ADD COLUMN opens_count INTEGER DEFAULT 0 NOT NULL;
            """)
        
        # Check and add clicks_count to emailrecipient
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = 'dashboard_emailrecipient' 
                AND column_name = 'clicks_count'
            );
        """)
        if not cursor.fetchone()[0]:
            cursor.execute("""
                ALTER TABLE dashboard_emailrecipient 
                ADD COLUMN clicks_count INTEGER DEFAULT 0 NOT NULL;
            """)
        
        # Check and add index on external_id
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1 FROM pg_indexes 
                WHERE indexname = 'dashboard_e_externa_idx'
            );
        """)
        if not cursor.fetchone()[0]:
            cursor.execute("""
                CREATE INDEX dashboard_e_externa_idx 
                ON dashboard_emailrecipient (external_id);
            """)


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0010_merge_20260401_1022'),
    ]

    operations = [
        migrations.RunPython(add_brevo_fields_if_not_exist, migrations.RunPython.noop),
    ]
