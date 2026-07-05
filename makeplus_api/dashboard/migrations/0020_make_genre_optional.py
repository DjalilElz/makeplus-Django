# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0019_rename_to_scientific_contributions'),
    ]

    operations = [
        # Use RunSQL to alter the field directly on the existing table
        migrations.RunSQL(
            # Forward migration - make genre nullable
            sql="""
                ALTER TABLE dashboard_epostersubmission 
                ALTER COLUMN genre DROP NOT NULL;
            """,
            # Reverse migration - make genre required again
            reverse_sql="""
                ALTER TABLE dashboard_epostersubmission 
                ALTER COLUMN genre SET NOT NULL;
            """
        ),
    ]
