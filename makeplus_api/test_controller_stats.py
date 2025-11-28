"""
Test script to verify controller room statistics endpoint
Run with: python test_controller_stats.py
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'makeplus_api.settings')
django.setup()

from django.contrib.auth.models import User
from events.models import Event, Room, RoomAssignment, UserEventAssignment, Participant, RoomAccess
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

# Get the test controller user
try:
    user = User.objects.get(email='mohamed.brahimi@startupweek.dz')
    print(f"✅ Found user: {user.username} ({user.email})")
    
    # Get their event assignment
    assignment = UserEventAssignment.objects.filter(
        user=user,
        role='controlleur_des_badges',
        is_active=True
    ).first()
    
    if assignment:
        print(f"✅ User is a controller for event: {assignment.event.name}")
        
        # Get their room assignment
        room_assignment = RoomAssignment.objects.filter(
            user=user,
            event=assignment.event,
            is_active=True
        ).first()
        
        if room_assignment:
            print(f"✅ User is assigned to room: {room_assignment.room.name}")
            
            # Count room accesses
            total_accesses = RoomAccess.objects.filter(room=room_assignment.room).count()
            print(f"📊 Total room accesses: {total_accesses}")
            
            # Generate JWT token
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            
            # Add event context to token
            refresh['event_id'] = str(assignment.event.id)
            access_token = str(refresh.access_token)
            
            print(f"\n🔑 JWT Token generated")
            print(f"Event ID in context: {assignment.event.id}")
            
            # Test the API endpoint
            client = APIClient()
            client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
            
            # Add event context header
            response = client.get(
                '/api/my-room/statistics/',
                HTTP_X_EVENT_ID=str(assignment.event.id)
            )
            
            print(f"\n📡 API Response Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"\n✅ SUCCESS! Statistics retrieved:")
                print(f"   Room: {data['room']['name']}")
                print(f"   Total Scans: {data['statistics']['total_scans']}")
                print(f"   Today Scans: {data['statistics']['today_scans']}")
                print(f"   Granted: {data['statistics']['granted']}")
                print(f"   Denied: {data['statistics']['denied']}")
                print(f"   Unique Participants: {data['statistics']['unique_participants']}")
                print(f"   Recent Scans: {len(data['recent_scans'])}")
            else:
                print(f"\n❌ ERROR: {response.json()}")
        else:
            print("❌ User has no room assignment")
    else:
        print("❌ User is not a controller")
        
except User.DoesNotExist:
    print("❌ User not found: mohamed.brahimi@startupweek.dz")
except Exception as e:
    print(f"❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()
