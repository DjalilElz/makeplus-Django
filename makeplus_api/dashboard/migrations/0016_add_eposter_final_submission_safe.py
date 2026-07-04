# Safe migration - uses IF NOT EXISTS to avoid conflicts

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0015_emailcampaign_external_campaign_id_and_more'),
        ('events', '0032_alter_exposantscan_notes'),
    ]

    operations = [
        # Add eposter_code column if it doesn't exist
        migrations.RunSQL(
            sql="""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT FROM information_schema.columns 
                        WHERE table_name = 'dashboard_epostersubmission' 
                        AND column_name = 'eposter_code'
                    ) THEN
                        ALTER TABLE dashboard_epostersubmission 
                        ADD COLUMN eposter_code VARCHAR(50) UNIQUE;
                    END IF;
                END $$;
            """,
            reverse_sql="ALTER TABLE dashboard_epostersubmission DROP COLUMN IF EXISTS eposter_code;",
        ),
        
        # Create EPosterFinalSubmission table if it doesn't exist
        migrations.RunSQL(
            sql="""
                CREATE TABLE IF NOT EXISTS dashboard_eposterfinalsubmission (
                    id UUID PRIMARY KEY,
                    nom VARCHAR(100) NOT NULL,
                    email VARCHAR(254) NOT NULL,
                    telephone VARCHAR(20) NOT NULL,
                    specialite VARCHAR(100) NOT NULL,
                    domaine_communication VARCHAR(100) NOT NULL,
                    poster_number VARCHAR(50) NOT NULL,
                    titre VARCHAR(500) NOT NULL,
                    auteurs TEXT NOT NULL,
                    co_auteurs TEXT,
                    abstract_file VARCHAR(100) NOT NULL,
                    ip_address INET,
                    user_agent TEXT,
                    submitted_at TIMESTAMP WITH TIME ZONE NOT NULL,
                    updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
                    event_id UUID NOT NULL REFERENCES events_event(id) ON DELETE CASCADE,
                    original_submission_id UUID NOT NULL UNIQUE REFERENCES dashboard_epostersubmission(id) ON DELETE CASCADE
                );
            """,
            reverse_sql="DROP TABLE IF EXISTS dashboard_eposterfinalsubmission;",
        ),
        
        # Create indexes if they don't exist
        migrations.RunSQL(
            sql="""
                DO $$
                BEGIN
                    -- Only create indexes if the table and column exist
                    IF EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'dashboard_eposterfinalsubmission'
                    ) AND EXISTS (
                        SELECT FROM information_schema.columns 
                        WHERE table_name = 'dashboard_eposterfinalsubmission' 
                        AND column_name = 'poster_number'
                    ) THEN
                        CREATE INDEX IF NOT EXISTS dashboard_e_event_i_418864_idx 
                        ON dashboard_eposterfinalsubmission (event_id, submitted_at DESC);
                        
                        CREATE INDEX IF NOT EXISTS dashboard_e_poster__f44ff8_idx 
                        ON dashboard_eposterfinalsubmission (poster_number);
                    END IF;
                END $$;
            """,
            reverse_sql="""
                DROP INDEX IF EXISTS dashboard_e_event_i_418864_idx;
                DROP INDEX IF EXISTS dashboard_e_poster__f44ff8_idx;
            """,
        ),
    ]
