# Migration to rename models to Scientific Contributions
# Uses db_table to preserve existing database tables

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0018_update_communication_types'),
    ]

    operations = [
        # Update verbose names first
        migrations.AlterModelOptions(
            name='epostersubmission',
            options={
                'ordering': ['-submitted_at'],
                'verbose_name': 'Scientific Contribution Submission',
                'verbose_name_plural': 'Scientific Contribution Submissions'
            },
        ),
        
        migrations.AlterModelOptions(
            name='epostervalidation',
            options={
                'ordering': ['-validated_at'],
                'verbose_name': 'Scientific Contribution Validation',
                'verbose_name_plural': 'Scientific Contribution Validations'
            },
        ),
        
        migrations.AlterModelOptions(
            name='epostercommitteemember',
            options={
                'ordering': ['-assigned_at'],
                'verbose_name': 'Scientific Contribution Committee Member',
                'verbose_name_plural': 'Scientific Contribution Committee Members'
            },
        ),
        
        migrations.AlterModelOptions(
            name='eposteremailtemplate',
            options={
                'ordering': ['template_type'],
                'verbose_name': 'Scientific Contribution Email Template',
                'verbose_name_plural': 'Scientific Contribution Email Templates'
            },
        ),
        
        # Rename poster_number to contribution_number in final submission table (if it exists)
        migrations.RunSQL(
            sql="""
                DO $$ 
                BEGIN
                    -- Check if table exists and has poster_number column
                    IF EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'dashboard_eposterfinalsubmission'
                    ) AND EXISTS (
                        SELECT FROM information_schema.columns 
                        WHERE table_name = 'dashboard_eposterfinalsubmission' 
                        AND column_name = 'poster_number'
                    ) THEN
                        -- Rename poster_number to contribution_number
                        ALTER TABLE dashboard_eposterfinalsubmission 
                        RENAME COLUMN poster_number TO contribution_number;
                    END IF;
                END $$;
            """,
            reverse_sql="""
                DO $$ 
                BEGIN
                    IF EXISTS (
                        SELECT FROM information_schema.columns 
                        WHERE table_name = 'dashboard_eposterfinalsubmission' 
                        AND column_name = 'contribution_number'
                    ) THEN
                        ALTER TABLE dashboard_eposterfinalsubmission 
                        RENAME COLUMN contribution_number TO poster_number;
                    END IF;
                END $$;
            """,
        ),
    ]
