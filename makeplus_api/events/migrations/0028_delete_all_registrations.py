# Delete all registration submissions (EventRegistration and FormSubmission)

from django.db import migrations


def delete_all_registrations(apps, schema_editor):
    """
    Delete ALL registration submissions:
    1. EventRegistration (old form submissions)
    2. FormSubmission (dashboard form submissions)
    3. FormRegistrationVerification codes
    """
    
    with schema_editor.connection.cursor() as cursor:
        print("Starting deletion of all registration submissions...")
        
        # 1. Delete ALL EventRegistration submissions
        cursor.execute("SELECT COUNT(*) FROM events_eventregistration;")
        registration_count = cursor.fetchone()[0]
        print(f"Found {registration_count} EventRegistration submissions")
        
        if registration_count > 0:
            cursor.execute("TRUNCATE TABLE events_eventregistration CASCADE;")
            print(f"Deleted ALL {registration_count} EventRegistration submissions")
        
        # 2. Delete ALL FormSubmission records from dashboard app
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'dashboard_formsubmission'
            );
        """)
        table_exists = cursor.fetchone()[0]
        
        if table_exists:
            cursor.execute("SELECT COUNT(*) FROM dashboard_formsubmission;")
            form_submission_count = cursor.fetchone()[0]
            print(f"Found {form_submission_count} FormSubmission records")
            
            if form_submission_count > 0:
                cursor.execute("TRUNCATE TABLE dashboard_formsubmission CASCADE;")
                print(f"Deleted ALL {form_submission_count} FormSubmission records")
        
        # 3. Delete ALL FormRegistrationVerification codes
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'events_formregistrationverification'
            );
        """)
        table_exists = cursor.fetchone()[0]
        
        if table_exists:
            cursor.execute("SELECT COUNT(*) FROM events_formregistrationverification;")
            verification_count = cursor.fetchone()[0]
            print(f"Found {verification_count} FormRegistrationVerification codes")
            
            if verification_count > 0:
                cursor.execute("TRUNCATE TABLE events_formregistrationverification CASCADE;")
                print(f"Deleted ALL {verification_count} FormRegistrationVerification codes")
        
        # 4. Delete ALL SignUpVerification codes (old verification codes)
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'events_signupverification'
            );
        """)
        table_exists = cursor.fetchone()[0]
        
        if table_exists:
            cursor.execute("SELECT COUNT(*) FROM events_signupverification;")
            signup_verification_count = cursor.fetchone()[0]
            print(f"Found {signup_verification_count} SignUpVerification codes")
            
            if signup_verification_count > 0:
                cursor.execute("TRUNCATE TABLE events_signupverification CASCADE;")
                print(f"Deleted ALL {signup_verification_count} SignUpVerification codes")
        
        print("All registration submissions deleted successfully!")


def reverse_deletion(apps, schema_editor):
    """Cannot reverse this migration - data is permanently deleted"""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0027_cleanup_old_data'),
    ]

    operations = [
        migrations.RunPython(delete_all_registrations, reverse_deletion),
    ]
