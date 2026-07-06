# Add missing columns to final submission table

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0022_alter_final_submission_original_optional'),
    ]

    operations = [
        # Add specialite column if it doesn't exist
        migrations.RunSQL(
            sql="""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT FROM information_schema.columns 
                        WHERE table_name = 'dashboard_eposterfinalsubmission' 
                        AND column_name = 'specialite'
                    ) THEN
                        ALTER TABLE dashboard_eposterfinalsubmission 
                        ADD COLUMN specialite VARCHAR(100) NOT NULL DEFAULT '';
                    END IF;
                END $$;
            """,
            reverse_sql="ALTER TABLE dashboard_eposterfinalsubmission DROP COLUMN IF EXISTS specialite;",
        ),
        
        # Add domaine_communication column if it doesn't exist
        migrations.RunSQL(
            sql="""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT FROM information_schema.columns 
                        WHERE table_name = 'dashboard_eposterfinalsubmission' 
                        AND column_name = 'domaine_communication'
                    ) THEN
                        ALTER TABLE dashboard_eposterfinalsubmission 
                        ADD COLUMN domaine_communication VARCHAR(100) NOT NULL DEFAULT '';
                    END IF;
                END $$;
            """,
            reverse_sql="ALTER TABLE dashboard_eposterfinalsubmission DROP COLUMN IF EXISTS domaine_communication;",
        ),
        
        # Add poster_number column if it doesn't exist
        migrations.RunSQL(
            sql="""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT FROM information_schema.columns 
                        WHERE table_name = 'dashboard_eposterfinalsubmission' 
                        AND column_name = 'poster_number'
                    ) THEN
                        ALTER TABLE dashboard_eposterfinalsubmission 
                        ADD COLUMN poster_number VARCHAR(50) NOT NULL DEFAULT '';
                    END IF;
                END $$;
            """,
            reverse_sql="ALTER TABLE dashboard_eposterfinalsubmission DROP COLUMN IF EXISTS poster_number;",
        ),
        
        # Add index on poster_number if it doesn't exist
        migrations.RunSQL(
            sql="""
                CREATE INDEX IF NOT EXISTS dashboard_e_poster__f44ff8_idx 
                ON dashboard_eposterfinalsubmission (poster_number);
            """,
            reverse_sql="DROP INDEX IF EXISTS dashboard_e_poster__f44ff8_idx;",
        ),
    ]
