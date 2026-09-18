# Fix EmailLoginCode table - Change id from bigint to uuid

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0019_add_emaillogincode_missing_columns'),
    ]

    operations = [
        # Drop the old (bigint-id) table and recreate with a UUID id --
        # guarded on the id column's actual type, not just table
        # existence: this app's migration history for this range has
        # repeatedly lost its recorded-applied rows in production (see
        # 0016's rename_indexes_if_exist), which makes Django genuinely
        # re-attempt this migration. An unconditional DROP TABLE here
        # would silently wipe every real login code on each such re-run;
        # once the id column is already uuid, there is nothing to fix.
        migrations.RunSQL(
            sql="""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name = 'events_emaillogincode'
                        AND column_name = 'id'
                        AND data_type = 'uuid'
                    ) THEN
                        DROP TABLE IF EXISTS events_emaillogincode CASCADE;

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

                        CREATE INDEX events_emai_user_id_b75a1f_idx
                        ON events_emaillogincode (user_id, event_id, is_used);

                        CREATE INDEX events_emai_code_ha_idx
                        ON events_emaillogincode (code_hash);

                        CREATE INDEX events_emai_created_idx
                        ON events_emaillogincode (created_at DESC);
                    END IF;
                END $$;
            """,
            reverse_sql="DROP TABLE IF EXISTS events_emaillogincode CASCADE;"
        ),
    ]
