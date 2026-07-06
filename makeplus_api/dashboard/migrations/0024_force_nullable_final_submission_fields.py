# Force remove NOT NULL constraints from final submission fields

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0023_add_missing_final_submission_columns'),
    ]

    operations = [
        # Force remove NOT NULL constraints - using ALTER COLUMN directly
        migrations.RunSQL(
            sql="""
                -- Remove NOT NULL from specialite
                ALTER TABLE dashboard_eposterfinalsubmission 
                ALTER COLUMN specialite DROP NOT NULL;
                
                -- Remove NOT NULL from domaine_communication  
                ALTER TABLE dashboard_eposterfinalsubmission 
                ALTER COLUMN domaine_communication DROP NOT NULL;
                
                -- Remove NOT NULL from poster_number (contribution_number)
                ALTER TABLE dashboard_eposterfinalsubmission 
                ALTER COLUMN poster_number DROP NOT NULL;
            """,
            reverse_sql="""
                ALTER TABLE dashboard_eposterfinalsubmission 
                ALTER COLUMN specialite SET NOT NULL;
                
                ALTER TABLE dashboard_eposterfinalsubmission 
                ALTER COLUMN domaine_communication SET NOT NULL;
                
                ALTER TABLE dashboard_eposterfinalsubmission 
                ALTER COLUMN poster_number SET NOT NULL;
            """,
        ),
    ]
