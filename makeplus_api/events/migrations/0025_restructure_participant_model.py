# Generated migration for restructuring Participant model

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0024_add_signup_data_field'),
    ]

    operations = [
        # Step 0: This migration's own history row has been lost in
        # production before (django_migrations losing rows for this app
        # is a known recurring issue), causing Django to genuinely
        # re-attempt this whole migration even though its schema changes
        # already landed. Every other step below already guards itself
        # (IF NOT EXISTS / constraint-existence checks) so a re-run is a
        # fast no-op -- except Step 3, which used to re-copy the entire
        # (ever-growing) participant table on every accidental re-run.
        # This raises the timeout for just this migration's transaction
        # so a genuinely-needed first run on a now-larger table -- or a
        # slow re-run before the Step 3 guard below existed -- can't be
        # killed by the pooler's short default statement_timeout.
        migrations.RunSQL(
            sql="SET LOCAL statement_timeout = '10min';",
            reverse_sql=migrations.RunSQL.noop,
        ),

        # Step 1: Create new ParticipantEventRegistration table
        migrations.RunSQL(
            sql="""
            CREATE TABLE IF NOT EXISTS events_participanteventregistration (
                id SERIAL PRIMARY KEY,
                participant_id INTEGER NOT NULL,
                event_id UUID NOT NULL,
                is_checked_in BOOLEAN DEFAULT FALSE,
                checked_in_at TIMESTAMP WITH TIME ZONE,
                registered_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                metadata JSONB DEFAULT '{}',
                UNIQUE (participant_id, event_id)
            );
            
            CREATE INDEX IF NOT EXISTS events_participanteventregistration_event_checked_idx 
                ON events_participanteventregistration (event_id, is_checked_in);
            CREATE INDEX IF NOT EXISTS events_participanteventregistration_participant_event_idx 
                ON events_participanteventregistration (participant_id, event_id);
            """,
            reverse_sql="DROP TABLE IF EXISTS events_participanteventregistration CASCADE;"
        ),
        
        # Step 2: Create junction table for ParticipantEventRegistration allowed_rooms
        migrations.RunSQL(
            sql="""
            CREATE TABLE IF NOT EXISTS events_participanteventregistration_allowed_rooms (
                id SERIAL PRIMARY KEY,
                participanteventregistration_id INTEGER NOT NULL,
                room_id UUID NOT NULL,
                UNIQUE (participanteventregistration_id, room_id)
            );
            """,
            reverse_sql="DROP TABLE IF EXISTS events_participanteventregistration_allowed_rooms CASCADE;"
        ),
        
        # Step 3: Backup existing participant data -- IF NOT EXISTS only
        # protects against the backup table already existing, not against
        # this whole migration having already completed and dropped it
        # (Step 9). Gated on the same "has this already run" signal Step 5
        # uses, so an accidental re-run skips the full-table copy entirely
        # instead of re-copying an ever-growing production table.
        migrations.RunSQL(
            sql="""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_constraint
                    WHERE conname = 'events_participant_user_id_unique'
                ) THEN
                    CREATE TABLE IF NOT EXISTS events_participant_backup AS
                    SELECT * FROM events_participant;
                END IF;
            END $$;
            """,
            reverse_sql="DROP TABLE IF EXISTS events_participant_backup;"
        ),
        
        # Step 4: Drop old constraints and indexes
        migrations.RunSQL(
            sql="""
            -- Drop old unique constraint
            ALTER TABLE events_participant DROP CONSTRAINT IF EXISTS events_participant_user_id_event_id_key;
            
            -- Drop old indexes
            DROP INDEX IF EXISTS events_participant_event_id_is_checked_in_idx;
            """,
            reverse_sql="-- No reverse"
        ),
        
        # Step 5: Remove event_id from participant table and add role
        migrations.RunSQL(
            sql="""
            -- Add role column if not exists
            DO $$ 
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'events_participant' AND column_name = 'role'
                ) THEN
                    ALTER TABLE events_participant ADD COLUMN role VARCHAR(30) DEFAULT 'participant';
                END IF;
            END $$;
            
            -- Make user_id unique (OneToOne relationship)
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_constraint 
                    WHERE conname = 'events_participant_user_id_unique'
                ) THEN
                    -- First, keep only one participant record per user (the most recent one)
                    DELETE FROM events_participant p1
                    WHERE EXISTS (
                        SELECT 1 FROM events_participant p2
                        WHERE p2.user_id = p1.user_id 
                        AND p2.id > p1.id
                    );
                    
                    -- Now add unique constraint
                    ALTER TABLE events_participant ADD CONSTRAINT events_participant_user_id_unique UNIQUE (user_id);
                END IF;
            END $$;
            """,
            reverse_sql="-- No reverse"
        ),
        
        # Step 6: Migrate data from old structure to new structure (SKIPPED - no data after 0022)
        # Skip data migration since all participants were deleted in migration
        # 0022 -- the backup table, when it exists at all, is empty or lacks
        # an event_id column. `events_participant_backup` is now only ever
        # created conditionally (see Step 3), so it may genuinely not exist
        # here -- to_regclass() is used to check that FIRST, and the actual
        # queries against it run as dynamic SQL (EXECUTE), because a static
        # SQL statement referencing a nonexistent table fails to even parse
        # in PL/pgSQL regardless of surrounding IF/AND short-circuiting.
        migrations.RunSQL(
            sql="""
            DO $$
            DECLARE
                has_data boolean := false;
            BEGIN
                IF to_regclass('public.events_participant_backup') IS NOT NULL THEN
                    IF EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name = 'events_participant_backup' AND column_name = 'event_id'
                    ) THEN
                        EXECUTE 'SELECT EXISTS (SELECT 1 FROM events_participant_backup LIMIT 1)' INTO has_data;
                    END IF;

                    IF has_data THEN
                        -- Insert event registrations from backup
                        EXECUTE '
                            INSERT INTO events_participanteventregistration (participant_id, event_id, is_checked_in, checked_in_at, registered_at)
                            SELECT
                                p.id,
                                pb.event_id,
                                pb.is_checked_in,
                                pb.checked_in_at,
                                pb.created_at
                            FROM events_participant_backup pb
                            JOIN events_participant p ON p.user_id = pb.user_id
                            ON CONFLICT (participant_id, event_id) DO NOTHING
                        ';

                        -- Migrate allowed_rooms relationships
                        EXECUTE '
                            INSERT INTO events_participanteventregistration_allowed_rooms (participanteventregistration_id, room_id)
                            SELECT
                                er.id,
                                par.room_id
                            FROM events_participant_backup pb
                            JOIN events_participant p ON p.user_id = pb.user_id
                            JOIN events_participanteventregistration er ON er.participant_id = p.id AND er.event_id = pb.event_id
                            JOIN events_participant_allowed_rooms par ON par.participant_id = pb.id
                            ON CONFLICT (participanteventregistration_id, room_id) DO NOTHING
                        ';
                    END IF;
                END IF;
            END $$;
            """,
            reverse_sql="-- No reverse"
        ),
        
        # Step 7: Drop old event_id column and old allowed_rooms table
        migrations.RunSQL(
            sql="""
            -- Drop old allowed_rooms relationship
            DROP TABLE IF EXISTS events_participant_allowed_rooms CASCADE;
            
            -- Remove event_id column
            ALTER TABLE events_participant DROP COLUMN IF EXISTS event_id;
            
            -- Remove old status columns (moved to EventRegistration)
            ALTER TABLE events_participant DROP COLUMN IF EXISTS is_checked_in;
            ALTER TABLE events_participant DROP COLUMN IF EXISTS checked_in_at;
            """,
            reverse_sql="-- No reverse"
        ),
        
        # Step 8: Add foreign key constraints
        migrations.RunSQL(
            sql="""
            -- Add foreign keys for ParticipantEventRegistration (with existence checks)
            DO $$ 
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_constraint 
                    WHERE conname = 'events_participanteventregistration_participant_fk'
                ) THEN
                    ALTER TABLE events_participanteventregistration 
                        ADD CONSTRAINT events_participanteventregistration_participant_fk 
                        FOREIGN KEY (participant_id) REFERENCES events_participant(id) ON DELETE CASCADE;
                END IF;
                
                IF NOT EXISTS (
                    SELECT 1 FROM pg_constraint 
                    WHERE conname = 'events_participanteventregistration_event_fk'
                ) THEN
                    ALTER TABLE events_participanteventregistration 
                        ADD CONSTRAINT events_participanteventregistration_event_fk 
                        FOREIGN KEY (event_id) REFERENCES events_event(id) ON DELETE CASCADE;
                END IF;
                
                IF NOT EXISTS (
                    SELECT 1 FROM pg_constraint 
                    WHERE conname = 'events_participanteventregistration_allowed_rooms_registration_fk'
                ) THEN
                    ALTER TABLE events_participanteventregistration_allowed_rooms 
                        ADD CONSTRAINT events_participanteventregistration_allowed_rooms_registration_fk 
                        FOREIGN KEY (participanteventregistration_id) REFERENCES events_participanteventregistration(id) ON DELETE CASCADE;
                END IF;
                
                IF NOT EXISTS (
                    SELECT 1 FROM pg_constraint 
                    WHERE conname = 'events_participanteventregistration_allowed_rooms_room_fk'
                ) THEN
                    ALTER TABLE events_participanteventregistration_allowed_rooms 
                        ADD CONSTRAINT events_participanteventregistration_allowed_rooms_room_fk 
                        FOREIGN KEY (room_id) REFERENCES events_room(id) ON DELETE CASCADE;
                END IF;
            END $$;
            """,
            reverse_sql="-- No reverse"
        ),
        
        # Step 9: Clean up backup table
        migrations.RunSQL(
            sql="DROP TABLE IF EXISTS events_participant_backup;",
            reverse_sql="-- No reverse"
        ),
    ]
