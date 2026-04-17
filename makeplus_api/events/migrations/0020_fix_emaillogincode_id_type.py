# Fix EmailLoginCode table - Change id from bigint to uuid

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0019_add_emaillogincode_missing_columns'),
    ]

    operations = [
        # Drop the old table and recreate with correct structure
        migrations.RunSQL(
            sql="""
                -- Drop the old table
                DROP TABLE IF EXISTS events_emaillogincode CASCADE;
                
                -- Create new table with UUID id
                CREATE TABLE events_emaillogincode (
                    id UUID PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE,
                    event_id UUID NOT NULL REFERENCES events_event(id) ON DELETE CASCADE,
                    code_hash VARCHAR(64) NOT NULL,
                    is_used BOOLEAN NOT NULL DEFAULT FALSE,
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
                    used_at TIMESTAMP WITH TIME ZONE NULL,
                    ip_address INET NULL,
                    user_agent TEXT DEFAULT ''
                );
                
                -- Create indexes
                CREATE INDEX events_emai_user_id_b75a1f_idx 
                ON events_emaillogincode (user_id, event_id, is_used);
                
                CREATE INDEX events_emai_code_ha_idx 
                ON events_emaillogincode (code_hash);
                
                CREATE INDEX events_emai_created_idx 
                ON events_emaillogincode (created_at DESC);
            """,
            reverse_sql="DROP TABLE IF EXISTS events_emaillogincode CASCADE;"
        ),
    ]
