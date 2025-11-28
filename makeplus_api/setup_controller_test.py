"""
Find controllers and create room access test data
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'makeplus_api.settings')
django.setup()

from django.contrib.auth.models import User
from events.models import Event, Room, RoomAssignment, UserEventAssignment, Participant, RoomAccess
from django.utils import timezone

# Find all controllers
controllers = UserEventAssignment.objects.filter(
    role='controlleur_des_badges',
    is_active=True
).select_related('user', 'event')

print("📋 Controllers in database:")
for assignment in controllers:
    user = assignment.user
    print(f"  - {user.username} ({user.email}) - Event: {assignment.event.name}")
    
    # Check room assignment
    room_assignment = RoomAssignment.objects.filter(
        user=user,
        event=assignment.event,
        is_active=True
    ).first()
    
    if room_assignment:
        print(f"    ✅ Assigned to: {room_assignment.room.name}")
        
        # Check room accesses
        accesses = RoomAccess.objects.filter(room=room_assignment.room).count()
        print(f"    📊 Room has {accesses} access records")
    else:
        print(f"    ❌ No room assignment")
    print()

# If we have controllers with room assignments, create some test access data
if controllers.exists():
    controller = controllers.first()
    room_assignment = RoomAssignment.objects.filter(
        user=controller.user,
        event=controller.event,
        is_active=True
    ).first()
    
    if room_assignment:
        # Get some participants from the same event
        participants = Participant.objects.filter(event=controller.event)[:5]
        
        if participants.exists():
            print(f"\n🎯 Creating test access data for {room_assignment.room.name}...")
            
            for i, participant in enumerate(participants):
                # Create some access records (granted and denied)
                status = 'granted' if i < 3 else 'denied'
                
                access, created = RoomAccess.objects.get_or_create(
                    room=room_assignment.room,
                    participant=participant,
                    verified_by=controller.user,
                    defaults={
                        'status': status,
                        'accessed_at': timezone.now(),
                        'denial_reason': 'Test denial' if status == 'denied' else None
                    }
                )
                
                if created:
                    print(f"  ✅ Created {status} access for {participant.user.get_full_name()}")
                else:
                    print(f"  ℹ️  Access already exists for {participant.user.get_full_name()}")
            
            print(f"\n✨ Test data created! Use this controller for testing:")
            print(f"   Email: {controller.user.email}")
            print(f"   Password: makeplus2025")
            print(f"   Room: {room_assignment.room.name}")
