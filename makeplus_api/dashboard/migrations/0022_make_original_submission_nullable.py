# Make original_submission_id nullable in final submission table

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0021_alter_eposteremailtemplate_type_length'),
    ]

    operations = [
        # Make original_submission_id nullable
        migrations.RunSQL(
            sql="""
                ALTER TABLE dashboard_eposterfinalsubmission 
                ALTER COLUMN original_submission_id DROP NOT NULL;
            """,
            reverse_sql="""
                ALTER TABLE dashboard_eposterfinalsubmission 
                ALTER COLUMN original_submission_id SET NOT NULL;
            """,
        ),
    ]
