"""
Quick Fix Script: Assign Room to UserEventAssignment
====================================================

CASE: User aopagest1@gmail.com needs room "Aula" assigned for event "AOPA"

Usage Option 1 - Django Shell:
    python manage.py shell
    >>> from fix_assignment_25 import fix_assignment
    >>> fix_assignment()

Usage Option 2 - Direct execution:
    python manage.py shell < fix_assignment_25.py

Usage Option 3 - Copy-paste into Django shell
"""

def fix_assignment():
    """Fix assignment ID 25 - assign Aula room"""
    from events.models import UserEventAssignment, Room, Event
    from django.contrib.auth.models import User
    
    print("\n" + "=" * 60)
    print("Fixing Room Assignment for User ID 26")
    print("=" * 60)
    
    try:
        # Method 1: By Assignment ID (if you know it)
        assignment_id = "25"
        assignment = UserEventAssignment.objects.get(id=assignment_id)
        
        print(f"✓ Found assignment:")
        print(f"  - ID: {assignment.id}")
        print(f"  - User: {assignment.user.get_full_name()} ({assignment.user.email})")
        print(f"  - Event: {assignment.event.name}")
        print(f"  - Role: {assignment.role}")
        print(f"  - Current metadata: {assignment.metadata}")
        
        # Find the Aula room for this event
        room = Room.objects.get(event=assignment.event, name="Aula")
        print(f"\n✓ Found room: {room.name} (ID: {room.id})")
        
        # Update metadata with room assignment
        assignment.metadata = assignment.metadata or {}
        assignment.metadata['assigned_room_id'] = str(room.id)
        assignment.save()
        
        print(f"\n✅ SUCCESS! Room assigned.")
        print(f"   Updated metadata: {assignment.metadata}")
        
        # Verify the fix
        assignment.refresh_from_db()
        room_id = assignment.metadata.get('assigned_room_id')
        if room_id:
            assigned_room = Room.objects.get(id=room_id)
            print(f"\n✓ Verification: User is now assigned to room '{assigned_room.name}'")
        
        return True
        
    except UserEventAssignment.DoesNotExist:
        print(f"❌ ERROR: Assignment with ID {assignment_id} not found")
        print("\nTrying alternative lookup method...")
        return fix_by_email()
        
    except Room.DoesNotExist:
        print(f"❌ ERROR: Room 'Aula' not found in event '{assignment.event.name}'")
        print("\nAvailable rooms:")
        rooms = Room.objects.filter(event=assignment.event)
        for r in rooms:
            print(f"  - {r.name} (ID: {r.id})")
        return False
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def fix_by_email():
    """Alternative method: Find by email and event name"""
    from events.models import UserEventAssignment, Room, Event
    from django.contrib.auth.models import User
    
    print("\nSearching by email and event name...")
    
    try:
        user = User.objects.get(email="aopagest1@gmail.com")
        print(f"✓ Found user: {user.get_full_name()} ({user.email})")
        
        event = Event.objects.get(name="AOPA")
        print(f"✓ Found event: {event.name}")
        
        assignment = UserEventAssignment.objects.get(user=user, event=event)
        print(f"✓ Found assignment (ID: {assignment.id}, Role: {assignment.role})")
        
        room = Room.objects.get(event=event, name="Aula")
        print(f"✓ Found room: {room.name}")
        
        # Update
        assignment.metadata = assignment.metadata or {}
        assignment.metadata['assigned_room_id'] = str(room.id)
        assignment.save()
        
        print(f"\n✅ SUCCESS! Room assigned via alternative method.")
        print(f"   Assignment ID: {assignment.id}")
        print(f"   Room: {room.name}")
        print(f"   Metadata: {assignment.metadata}")
        
        return True
        
    except User.DoesNotExist:
        print("❌ User not found with email: aopagest1@gmail.com")
        return False
    except Event.DoesNotExist:
        print("❌ Event 'AOPA' not found")
        return False
    except UserEventAssignment.DoesNotExist:
        print("❌ No assignment found for this user in event 'AOPA'")
        return False
    except Room.DoesNotExist:
        print("❌ Room 'Aula' not found in event 'AOPA'")
        print("\nAvailable rooms in AOPA:")
        try:
            event = Event.objects.get(name="AOPA")
            rooms = Room.objects.filter(event=event)
            for r in rooms:
                print(f"  - {r.name} (ID: {r.id})")
        except:
            pass
        return False

# Auto-run if executed as script
if __name__ == '__main__':
    fix_assignment()
