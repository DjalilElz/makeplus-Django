# Delete existing participants (development phase)

from django.db import migrations


def delete_participants(apps, schema_editor):
    """Delete all existing participants and their related data using raw SQL"""
    
    # Use raw SQL to avoid model state issues
    with schema_editor.connection.cursor() as cursor:
        # Get count before deletion
        cursor.execute("SELECT COUNT(*) FROM events_participant;")
        participant_count = cursor.fetchone()[0]
        print(f"Deleting {participant_count} participants...")
        
        # Delete all participants (cascades will handle related records)
        cursor.execute("DELETE FROM events_participant;")
        
        # Delete user event assignments for participant role
        cursor.execute("DELETE FROM events_usereventassignment WHERE role = 'participant';")
        cursor.execute("SELECT ROW_COUNT();")
        
        print(f"Deleted participant assignments")
        
        # Note: We don't delete users as they might be needed for the new system
        print("Participant deletion complete")


def reverse_delete(apps, schema_editor):
    """Cannot reverse this migration"""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0021_add_verification_models'),
    ]

    operations = [
        migrations.RunPython(delete_participants, reverse_delete),
    ]
