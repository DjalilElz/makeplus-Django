# Migration to make original_submission optional in final submission
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0021_alter_eposteremailtemplate_type_length'),
    ]

    operations = [
        migrations.RunSQL(
            # PostgreSQL - alter foreign key constraint to allow NULL
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
