"""
Assign room to a controller and create test access data
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'makeplus_api.settings')
django.setup()

from django.contrib.auth.models import User
from events.models import Event, Room, RoomAssignment, UserEventAssignment, Participant, RoomAccess
from django.utils import timezone
import random

# Get the StartupWeek controller
try:
    user = User.objects.get(email='leila.madani@startupweek.dz')
    print(f"✅ Found controller: {user.username} ({user.email})")
    
    # Get their event assignment
    assignment = UserEventAssignment.objects.get(
        user=user,
        role='controlleur_des_badges',
        is_active=True
    )
    event = assignment.event
    print(f"✅ Event: {event.name}")
    
    # Get a room from this event
    room = Room.objects.filter(event=event).first()
    
    if room:
        print(f"✅ Found room: {room.name}")
        
        # Create room assignment
        room_assignment, created = RoomAssignment.objects.get_or_create(
            user=user,
            room=room,
            event=event,
            defaults={
                'is_active': True,
                'start_time': event.start_date,
                'end_time': event.end_date
            }
        )
        
        if created:
            print(f"✅ Created room assignment")
        else:
            print(f"ℹ️  Room assignment already exists")
        
        # Get participants from this event
        participants = list(Participant.objects.filter(event=event))
        
        if participants:
            print(f"\n🎯 Creating test access data...")
            
            # Create various access records
            for i in range(min(10, len(participants))):
                participant = participants[i]
                
                # Mix of granted and denied
                status = 'granted' if i < 7 else 'denied'
                
                # Some from today, some from yesterday
                if i < 5:
                    accessed_at = timezone.now()
                else:
                    accessed_at = timezone.now() - timezone.timedelta(days=1)
                
                access, created = RoomAccess.objects.get_or_create(
                    room=room,
                    participant=participant,
                    accessed_at__date=accessed_at.date(),
                    defaults={
                        'status': status,
                        'accessed_at': accessed_at,
                        'verified_by': user,
                        'denial_reason': f'Badge not valid for this session' if status == 'denied' else ''
                    }
                )
                
                if created:
                    print(f"  ✅ {status.upper()}: {participant.user.get_full_name()} - {accessed_at.strftime('%Y-%m-%d %H:%M')}")
            
            # Count statistics
            total = RoomAccess.objects.filter(room=room).count()
            today = RoomAccess.objects.filter(room=room, accessed_at__date=timezone.now().date()).count()
            granted = RoomAccess.objects.filter(room=room, status='granted').count()
            denied = RoomAccess.objects.filter(room=room, status='denied').count()
            
            print(f"\n📊 Statistics for {room.name}:")
            print(f"   Total scans: {total}")
            print(f"   Today's scans: {today}")
            print(f"   Granted: {granted}")
            print(f"   Denied: {denied}")
            
            print(f"\n✨ Ready for testing!")
            print(f"\n🔑 Controller Login:")
            print(f"   Email: {user.email}")
            print(f"   Password: makeplus2025")
            print(f"   Room: {room.name}")
            print(f"   Event: {event.name}")
            print(f"\n📡 API Endpoint: GET /api/my-room/statistics/")
        else:
            print("❌ No participants found for this event")
    else:
        print("❌ No rooms found for this event")
        
except User.DoesNotExist:
    print("❌ Controller not found")
except Exception as e:
    print(f"❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()
