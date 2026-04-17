# Delete existing participants (development phase)

from django.db import migrations


def delete_participants(apps, schema_editor):
    """Delete all existing participants and their related data"""
    Participant = apps.get_model('events', 'Participant')
    UserEventAssignment = apps.get_model('events', 'UserEventAssignment')
    User = apps.get_model('auth', 'User')
    
    # Get all participants
    participants = Participant.objects.all()
    participant_user_ids = list(participants.values_list('user_id', flat=True))
    
    print(f"Deleting {participants.count()} participants...")
    
    # Delete participants (this will cascade to related records)
    participants.delete()
    
    # Delete user event assignments for participant role
    deleted_assignments = UserEventAssignment.objects.filter(role='participant').delete()
    print(f"Deleted {deleted_assignments[0]} participant assignments")
    
    # Delete users who were only participants (no other roles)
    users_to_delete = User.objects.filter(
        id__in=participant_user_ids
    ).exclude(
        event_assignments__role__in=['gestionnaire_des_salles', 'controlleur_des_badges', 'exposant', 'committee']
    )
    
    deleted_users = users_to_delete.delete()
    print(f"Deleted {deleted_users[0]} participant-only users")


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
