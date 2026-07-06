# Drop duplicate contribution_number column if it exists

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0024_force_nullable_final_submission_fields'),
    ]

    operations = [
        # Drop contribution_number column if it exists (we use poster_number instead)
        migrations.RunSQL(
            sql="""
                ALTER TABLE dashboard_eposterfinalsubmission 
                DROP COLUMN IF EXISTS contribution_number;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
