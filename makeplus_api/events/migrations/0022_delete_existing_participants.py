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
        
        # First, delete caisse transactions that reference participants
        cursor.execute("DELETE FROM caisse_caissetransaction WHERE participant_id IS NOT NULL;")
        print("Deleted caisse transactions")
        
        # Delete all participants (cascades will handle related records)
        cursor.execute("DELETE FROM events_participant;")
        
        # Delete user event assignments for participant role
        cursor.execute("DELETE FROM events_usereventassignment WHERE role = 'participant';")
        
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
