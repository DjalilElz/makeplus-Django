# Migration to rename models to Scientific Contributions
# Uses db_table to preserve existing database tables

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0019_eposterfinalsubmission_and_more'),
    ]

    operations = [
        # Rename field: eposter_code -> contribution_code (column level only, keeps db column)
        migrations.RenameField(
            model_name='epostersubmission',
            old_name='eposter_code',
            new_name='contribution_code',
        ),
        
        # Rename field: poster_number -> contribution_number
        migrations.RenameField(
            model_name='eposterfinalsubmission',
            old_name='poster_number',
            new_name='contribution_number',
        ),
        
        # Update verbose names
        migrations.AlterModelOptions(
            name='epostersubmission',
            options={
                'ordering': ['-submitted_at'],
                'verbose_name': 'Scientific Contribution Submission',
                'verbose_name_plural': 'Scientific Contribution Submissions'
            },
        ),
        
        migrations.AlterModelOptions(
            name='eposterfinalsubmission',
            options={
                'ordering': ['-submitted_at'],
                'verbose_name': 'Scientific Contribution Final Submission',
                'verbose_name_plural': 'Scientific Contribution Final Submissions'
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
    ]
