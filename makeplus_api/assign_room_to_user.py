"""
Assign Salle Principale to mohamed.brahimi@startupweek.dz for testing
"""
import os
import django
import sys
from datetime import datetime, timedelta

# Setup Django
sys.path.append('E:/makeplus/makeplus_backend/makeplus_api')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'makeplus_api.settings')
django.setup()

from django.contrib.auth.models import User
from events.models import Event, Room, Session, RoomAssignment

try:
    # Get the user
    user = User.objects.get(email='mohamed.brahimi@startupweek.dz')
    print(f"✅ Found user: {user.username} ({user.email})")
    
    # Get the event
    event = Event.objects.get(name='StartupWeek Oran 2025')
    print(f"✅ Found event: {event.name}")
    
    # Get the main room
    room = Room.objects.get(event=event, name='Salle Principale')
    print(f"✅ Found room: {room.name}")
    
    # Create room assignment (gestionnaire is responsible for this room)
    assignment, created = RoomAssignment.objects.get_or_create(
        user=user,
        room=room,
        event=event,
        role='gestionnaire_des_salles',
        defaults={
            'start_time': datetime.now(),
            'end_time': datetime.now() + timedelta(days=30)
        }
    )
    
    if created:
        print(f"✅ Created room assignment for {user.email} to manage {room.name}")
    else:
        print(f"✅ Room assignment already exists for {user.email} to manage {room.name}")
    
    # Create 3 test sessions in this room
    sessions_data = [
        {
            'title': 'Conférence: Innovation et Startups',
            'session_type': 'conference',
            'start_time': datetime.now() + timedelta(hours=2),
            'end_time': datetime.now() + timedelta(hours=3, minutes=30),
            'speaker_name': 'Dr. Amina Belkacem',
            'speaker_title': 'CEO, TechVentures',
            'theme': 'Innovation',
            'status': 'pas_encore'
        },
        {
            'title': 'Atelier: Pitch Your Startup',
            'session_type': 'atelier',
            'start_time': datetime.now() + timedelta(hours=4),
            'end_time': datetime.now() + timedelta(hours=5, minutes=30),
            'speaker_name': 'Karim Meziane',
            'speaker_title': 'Investor & Mentor',
            'theme': 'Entrepreneurship',
            'status': 'pas_encore',
            'is_paid': True,
            'price': '2000.00'
        },
        {
            'title': 'Conférence: Marketing Digital pour Startups',
            'session_type': 'conference',
            'start_time': datetime.now() + timedelta(hours=6),
            'end_time': datetime.now() + timedelta(hours=7, minutes=30),
            'speaker_name': 'Sarah Hassani',
            'speaker_title': 'Marketing Director, AlgTech',
            'theme': 'Marketing',
            'status': 'pas_encore'
        }
    ]
    
    print("\n📅 Creating test sessions...")
    for session_data in sessions_data:
        session, created = Session.objects.get_or_create(
            event=event,
            room=room,
            title=session_data['title'],
            defaults={
                **session_data,
                'description': f"Description pour {session_data['title']}",
                'speaker_bio': f"Expert en {session_data['theme']}",
                'created_by': user
            }
        )
        
        if created:
            print(f"  ✅ Created: {session.title} ({session.session_type}) - Status: {session.status}")
        else:
            print(f"  ℹ️  Already exists: {session.title}")
    
    print("\n" + "="*60)
    print("✅ SETUP COMPLETE!")
    print("="*60)
    print(f"\n👤 User: {user.email}")
    print(f"🎪 Event: {event.name}")
    print(f"🏠 Assigned Room: {room.name}")
    print(f"📊 Sessions Created: {Session.objects.filter(room=room, event=event).count()}")
    print("\n💡 The user can now manage sessions in 'Salle Principale'")
    print("   - Change status: pas_encore → en_cours → termine")
    print("   - Create new sessions")
    print("   - Update/delete sessions")
    
except User.DoesNotExist:
    print("❌ Error: User with email 'mohamed.brahimi@startupweek.dz' not found")
except Event.DoesNotExist:
    print("❌ Error: Event 'StartupWeek Oran 2025' not found")
except Room.DoesNotExist:
    print("❌ Error: Room 'Salle Principale' not found in this event")
except Exception as e:
    print(f"❌ Error: {str(e)}")
