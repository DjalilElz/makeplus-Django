# Safe migration to add or alter eposter_code field with null=True
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0016_add_eposter_final_submission_safe'),
    ]

    operations = [
        # Alter eposter_code to allow NULL values
        migrations.RunSQL(
            sql="""
                DO $$
                BEGIN
                    -- Check if column exists
                    IF EXISTS (
                        SELECT FROM information_schema.columns 
                        WHERE table_name = 'dashboard_epostersubmission' 
                        AND column_name = 'eposter_code'
                    ) THEN
                        -- Alter existing column to allow NULL
                        ALTER TABLE dashboard_epostersubmission 
                        ALTER COLUMN eposter_code DROP NOT NULL;
                    ELSE
                        -- Add column with NULL allowed
                        ALTER TABLE dashboard_epostersubmission 
                        ADD COLUMN eposter_code VARCHAR(50) UNIQUE NULL;
                    END IF;
                END $$;
            """,
            reverse_sql="-- No reverse operation",
        ),
    ]
