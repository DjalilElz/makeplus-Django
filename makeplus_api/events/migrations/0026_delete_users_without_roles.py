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
        
        # Delete users without any role assignments (keep staff and superusers)
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
        
        print(f"Deleted {count} users without roles")


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
