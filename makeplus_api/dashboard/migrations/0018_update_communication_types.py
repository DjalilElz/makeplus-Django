# Generated migration for updating communication types

from django.db import migrations, models


def migrate_poster_to_eposter(apps, schema_editor):
    """Migrate all existing 'poster' submissions to 'e_poster'"""
    EPosterSubmission = apps.get_model('dashboard', 'EPosterSubmission')
    
    # Update all poster submissions to e_poster
    updated_count = EPosterSubmission.objects.filter(
        type_participation='poster'
    ).update(type_participation='e_poster')
    
    print(f"Migrated {updated_count} poster submissions to e_poster")


def reverse_migration(apps, schema_editor):
    """Reverse: Convert e_poster back to poster (only for rollback)"""
    # Note: This is not perfect as we can't distinguish between original e_poster
    # and migrated poster submissions, but it's for rollback safety
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0017_alter_epostersubmission_eposter_code'),
    ]

    operations = [
        # Step 1: Migrate existing data from 'poster' to 'e_poster'
        migrations.RunPython(migrate_poster_to_eposter, reverse_migration),
        
        # Step 2: Update the TYPE_PARTICIPATION_CHOICES field
        migrations.AlterField(
            model_name='epostersubmission',
            name='type_participation',
            field=models.CharField(
                choices=[
                    ('e_poster', 'E-Poster'),
                    ('communication_orale', 'Communication Orale'),
                    ('table_ronde', 'Table Ronde'),
                    ('atelier', 'Atelier')
                ],
                max_length=30,
                verbose_name='Type de participation'
            ),
        ),
    ]
