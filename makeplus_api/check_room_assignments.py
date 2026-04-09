"""
Check all UserEventAssignments for missing room assignments
Shows which users need to be fixed
"""

def check_all_assignments():
    from events.models import UserEventAssignment, Room
    from django.db.models import Q
    
    print("\n" + "=" * 80)
    print("ROOM ASSIGNMENT AUDIT")
    print("=" * 80)
    
    # Get all assignments with roles that should have rooms
    roles_needing_rooms = ['organisateur', 'gestionnaire_des_salles', 'controlleur_des_badges']
    
    assignments = UserEventAssignment.objects.filter(
        role__in=roles_needing_rooms
    ).select_related('user', 'event').order_by('event__name', 'role')
    
    total = assignments.count()
    with_rooms = 0
    without_rooms = 0
    invalid_rooms = 0
    
    issues = []
    
    print(f"\nFound {total} assignment(s) with roles that can have room assignments\n")
    
    for assignment in assignments:
        room_id = assignment.metadata.get('assigned_room_id') if assignment.metadata else None
        
        status = "❓ UNKNOWN"
        issue = None
        
        if not room_id:
            status = "❌ NO ROOM"
            without_rooms += 1
            issue = {
                'assignment_id': str(assignment.id),
                'user_email': assignment.user.email,
                'user_name': assignment.user.get_full_name(),
                'event_name': assignment.event.name,
                'event_id': str(assignment.event.id),
                'role': assignment.role,
                'problem': 'No room assigned',
                'available_rooms': []
            }
            
            # Get available rooms
            rooms = Room.objects.filter(event=assignment.event)
            for room in rooms:
                issue['available_rooms'].append({
                    'name': room.name,
                    'id': str(room.id)
                })
            
            issues.append(issue)
            
        else:
            # Check if room exists and is valid
            try:
                room = Room.objects.get(id=room_id)
                if room.event_id == assignment.event_id:
                    status = f"✅ {room.name}"
                    with_rooms += 1
                else:
                    status = "⚠️ WRONG EVENT"
                    invalid_rooms += 1
                    issue = {
                        'assignment_id': str(assignment.id),
                        'user_email': assignment.user.email,
                        'user_name': assignment.user.get_full_name(),
                        'event_name': assignment.event.name,
                        'event_id': str(assignment.event.id),
                        'role': assignment.role,
                        'problem': f'Room belongs to different event',
                        'current_room': room.name,
                        'available_rooms': []
                    }
                    rooms = Room.objects.filter(event=assignment.event)
                    for r in rooms:
                        issue['available_rooms'].append({
                            'name': r.name,
                            'id': str(r.id)
                        })
                    issues.append(issue)
                    
            except Room.DoesNotExist:
                status = "⚠️ INVALID ID"
                invalid_rooms += 1
                issue = {
                    'assignment_id': str(assignment.id),
                    'user_email': assignment.user.email,
                    'user_name': assignment.user.get_full_name(),
                    'event_name': assignment.event.name,
                    'event_id': str(assignment.event.id),
                    'role': assignment.role,
                    'problem': f'Room ID {room_id} does not exist',
                    'available_rooms': []
                }
                rooms = Room.objects.filter(event=assignment.event)
                for r in rooms:
                    issue['available_rooms'].append({
                        'name': r.name,
                        'id': str(r.id)
                    })
                issues.append(issue)
        
        # Print status line
        print(f"{status:30} | {assignment.user.email:35} | {assignment.event.name:25} | {assignment.role}")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total assignments:        {total}")
    print(f"✅ With valid rooms:      {with_rooms}")
    print(f"❌ Without rooms:         {without_rooms}")
    print(f"⚠️  With invalid rooms:   {invalid_rooms}")
    
    # Detailed issues
    if issues:
        print("\n" + "=" * 80)
        print("ISSUES REQUIRING ATTENTION")
        print("=" * 80)
        
        for i, issue in enumerate(issues, 1):
            print(f"\n{i}. {issue['problem'].upper()}")
            print(f"   Assignment ID: {issue['assignment_id']}")
            print(f"   User: {issue['user_name']} ({issue['user_email']})")
            print(f"   Event: {issue['event_name']} (ID: {issue['event_id']})")
            print(f"   Role: {issue['role']}")
            
            if 'current_room' in issue:
                print(f"   Current Room: {issue['current_room']}")
            
            if issue['available_rooms']:
                print(f"   Available rooms in this event:")
                for room in issue['available_rooms']:
                    print(f"     - {room['name']} (ID: {room['id']})")
                    
                # Show fix command
                if issue['available_rooms']:
                    first_room = issue['available_rooms'][0]
                    print(f"\n   Fix command:")
                    print(f"   python manage.py fix_room_assignments \\")
                    print(f"       --assignment-id \"{issue['assignment_id']}\" \\")
                    print(f"       --room-id \"{first_room['id']}\"")
            else:
                print(f"   ⚠️  No rooms available in this event! Create rooms first.")
    else:
        print("\n✅ All assignments have valid room assignments!")
    
    print("\n" + "=" * 80)
    
    return {
        'total': total,
        'with_rooms': with_rooms,
        'without_rooms': without_rooms,
        'invalid_rooms': invalid_rooms,
        'issues': issues
    }

# Run automatically
if __name__ == '__main__':
    results = check_all_assignments()
