# Migration to make original_submission optional in final submission
from django.db import migrations


def do_nothing(apps, schema_editor):
    """No-op function for state tracking"""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0021_alter_eposteremailtemplate_type_length'),
    ]

    operations = [
        # Use RunSQL for actual database change (bypasses Django ORM)
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
        # Use RunPython no-op to prevent Django from trying to track model state
        migrations.RunPython(do_nothing, reverse_code=do_nothing),
    ]
