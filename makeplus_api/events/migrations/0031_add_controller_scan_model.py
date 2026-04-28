# Generated manually on 2026-04-28 15:30
# Clean migration that only creates ControllerScan model
# Uses RunSQL with IF NOT EXISTS to handle existing table

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0030_alter_participant_qr_code_data'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Use raw SQL with IF NOT EXISTS to avoid errors if table already exists
        migrations.RunSQL(
            # Forward SQL - Create table only if it doesn't exist
            sql="""
            CREATE TABLE IF NOT EXISTS events_controllerscan (
                id BIGSERIAL PRIMARY KEY,
                controller_id INTEGER NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE,
                event_id UUID NOT NULL REFERENCES events_event(id) ON DELETE CASCADE,
                participant_user_id INTEGER NOT NULL,
                badge_id VARCHAR(100) NOT NULL,
                participant_name VARCHAR(255) NOT NULL,
                participant_email VARCHAR(254) NOT NULL,
                scanned_at TIMESTAMP WITH TIME ZONE NOT NULL,
                status VARCHAR(20) NOT NULL DEFAULT 'success',
                error_message TEXT NOT NULL DEFAULT '',
                total_paid_items INTEGER NOT NULL DEFAULT 0,
                total_amount NUMERIC(10, 2) NOT NULL DEFAULT 0
            );
            
            CREATE INDEX IF NOT EXISTS events_controllerscan_scanned_at_idx 
                ON events_controllerscan (scanned_at DESC);
            
            CREATE INDEX IF NOT EXISTS events_cont_control_b4e68d_idx 
                ON events_controllerscan (controller_id, scanned_at DESC);
            
            CREATE INDEX IF NOT EXISTS events_cont_event_i_d74a38_idx 
                ON events_controllerscan (event_id, scanned_at DESC);
            
            CREATE INDEX IF NOT EXISTS events_cont_control_132a72_idx 
                ON events_controllerscan (controller_id, event_id, scanned_at DESC);
            """,
            # Reverse SQL - Drop table
            reverse_sql="""
            DROP TABLE IF EXISTS events_controllerscan CASCADE;
            """
        ),
    ]
