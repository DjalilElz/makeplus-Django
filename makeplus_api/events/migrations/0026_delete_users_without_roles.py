# Delete users without any role assignments

from django.db import migrations


def delete_users_without_roles(apps, schema_editor):
    """Delete users who have no UserEventAssignment (no role)"""
    
    with schema_editor.connection.cursor() as cursor:
        # Get count of users without roles
        cursor.execute("""
            SELECT COUNT(*) 
            FROM auth_user u
            WHERE NOT EXISTS (
                SELECT 1 FROM events_usereventassignment uea 
                WHERE uea.user_id = u.id
            )
            AND NOT u.is_staff 
            AND NOT u.is_superuser;
        """)
        count = cursor.fetchone()[0]
        print(f"Found {count} users without roles (excluding staff/superusers)")
        
        # Delete related JWT token blacklist records (blacklisted tokens first, then outstanding tokens)
        # Step 1: Delete blacklisted tokens that reference outstanding tokens for these users
        cursor.execute("""
            DELETE FROM token_blacklist_blacklistedtoken 
            WHERE token_id IN (
                SELECT id FROM token_blacklist_outstandingtoken 
                WHERE user_id IN (
                    SELECT u.id 
                    FROM auth_user u
                    WHERE NOT EXISTS (
                        SELECT 1 FROM events_usereventassignment uea 
                        WHERE uea.user_id = u.id
                    )
                    AND NOT u.is_staff 
                    AND NOT u.is_superuser
                )
            );
        """)
        
        # Step 2: Delete outstanding tokens
        cursor.execute("""
            DELETE FROM token_blacklist_outstandingtoken 
            WHERE user_id IN (
                SELECT u.id 
                FROM auth_user u
                WHERE NOT EXISTS (
                    SELECT 1 FROM events_usereventassignment uea 
                    WHERE uea.user_id = u.id
                )
                AND NOT u.is_staff 
                AND NOT u.is_superuser
            );
        """)
        
        # Delete related UserProfile records
        cursor.execute("""
            DELETE FROM events_userprofile 
            WHERE user_id IN (
                SELECT u.id 
                FROM auth_user u
                WHERE NOT EXISTS (
                    SELECT 1 FROM events_usereventassignment uea 
                    WHERE uea.user_id = u.id
                )
                AND NOT u.is_staff 
                AND NOT u.is_superuser
            );
        """)
        
        # Delete related Participant records
        cursor.execute("""
            DELETE FROM events_participant 
            WHERE user_id IN (
                SELECT u.id 
                FROM auth_user u
                WHERE NOT EXISTS (
                    SELECT 1 FROM events_usereventassignment uea 
                    WHERE uea.user_id = u.id
                )
                AND NOT u.is_staff 
                AND NOT u.is_superuser
            );
        """)
        
        # Now delete users without any role assignments (keep staff and superusers)
        cursor.execute("""
            DELETE FROM auth_user 
            WHERE id IN (
                SELECT u.id 
                FROM auth_user u
                WHERE NOT EXISTS (
                    SELECT 1 FROM events_usereventassignment uea 
                    WHERE uea.user_id = u.id
                )
                AND NOT u.is_staff 
                AND NOT u.is_superuser
            );
        """)
        
        print(f"Deleted {count} users without roles and their related records")


def reverse_delete(apps, schema_editor):
    """Cannot reverse this migration"""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0025_restructure_participant_model'),
    ]

    operations = [
        migrations.RunPython(delete_users_without_roles, reverse_delete),
    ]
