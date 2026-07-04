# Migration to rename models to Scientific Contributions
# Uses db_table to preserve existing database tables

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0018_update_communication_types'),
    ]

    operations = [
        # Update verbose names only - safe operation that doesn't modify database structure
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
        
        # Note: Column renames are handled by db_column in model Meta
        # No database schema changes needed here
    ]
