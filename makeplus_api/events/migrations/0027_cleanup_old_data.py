# Comprehensive cleanup of old data to prevent migration errors

from django.db import migrations


def cleanup_old_data(apps, schema_editor):
    """
    Clean up old data that might cause issues:
    1. Delete old form submissions/registrations
    2. Clean up orphaned participant data
    3. Remove any inconsistent records
    """
    
    with schema_editor.connection.cursor() as cursor:
        print("Starting comprehensive data cleanup...")
        
        # 1. Delete old EventRegistration submissions (form submissions, not participant registrations)
        cursor.execute("SELECT COUNT(*) FROM events_eventregistration;")
        registration_count = cursor.fetchone()[0]
        print(f"Found {registration_count} old event registration submissions")
        
        if registration_count > 0:
            cursor.execute("DELETE FROM events_eventregistration;")
            print(f"Deleted {registration_count} old event registration submissions")
        
        # 2. Delete FormSubmission records from dashboard app
        cursor.execute("""
            SELECT COUNT(*) FROM dashboard_formsubmission 
            WHERE EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'dashboard_formsubmission');
        """)
        if cursor.fetchone():
            form_submission_count = cursor.fetchone()[0] if cursor.fetchone() else 0
            if form_submission_count > 0:
                cursor.execute("DELETE FROM dashboard_formsubmission;")
                print(f"Deleted {form_submission_count} form submissions")
        
        # 3. Clean up orphaned SignUpVerification records (older than 1 day)
        cursor.execute("""
            DELETE FROM events_signupverification 
            WHERE created_at < NOW() - INTERVAL '1 day';
        """)
        print("Cleaned up old signup verification codes")
        
        # 4. Clean up orphaned FormRegistrationVerification records (older than 1 day)
        cursor.execute("""
            DELETE FROM events_formregistrationverification 
            WHERE created_at < NOW() - INTERVAL '1 day';
        """)
        print("Cleaned up old form registration verification codes")
        
        # 5. Clean up orphaned UserProfile records (users that don't exist)
        cursor.execute("""
            DELETE FROM events_userprofile 
            WHERE user_id NOT IN (SELECT id FROM auth_user);
        """)
        print("Cleaned up orphaned user profiles")
        
        # 6. Clean up orphaned Participant records (users that don't exist)
        cursor.execute("""
            DELETE FROM events_participant 
            WHERE user_id NOT IN (SELECT id FROM auth_user);
        """)
        print("Cleaned up orphaned participant records")
        
        # 7. Clean up orphaned UserEventAssignment records (users or events that don't exist)
        cursor.execute("""
            DELETE FROM events_usereventassignment 
            WHERE user_id NOT IN (SELECT id FROM auth_user)
            OR event_id NOT IN (SELECT id FROM events_event);
        """)
        print("Cleaned up orphaned user event assignments")
        
        # 8. Clean up orphaned ParticipantEventRegistration records
        cursor.execute("""
            DELETE FROM events_participanteventregistration 
            WHERE participant_id NOT IN (SELECT id FROM events_participant)
            OR event_id NOT IN (SELECT id FROM events_event);
        """)
        print("Cleaned up orphaned participant event registrations")
        
        print("Data cleanup completed successfully!")


def reverse_cleanup(apps, schema_editor):
    """Cannot reverse this migration"""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0025_restructure_participant_model'),
    ]

    operations = [
        migrations.RunPython(cleanup_old_data, reverse_cleanup),
    ]
