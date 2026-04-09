"""
Setup test participant with sessions, room access, and session access
Creates a participant for StartupWeek Oran 2025 with multiple sessions
"""

import os
import django

# Force USE_SUPABASE for production database
os.environ['USE_SUPABASE'] = 'true'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'makeplus_api.settings')
django.setup()

from django.contrib.auth.models import User
from events.models import (
    Event, Session, Participant, UserEventAssignment, 
    SessionAccess, RoomAccess, Room
)
from django.utils import timezone
import random

print("🔧 Connecting to PRODUCTION database (Supabase)...")

try:
    # Get StartupWeek Oran 2025 event
    event = Event.objects.get(name='StartupWeek Oran 2025')
    print(f"✅ Found event: {event.name}")
    print(f"   Dates: {event.start_date} to {event.end_date}")
    
    # Create or get test participant user
    participant_email = 'participant.test@startupweek.dz'
    participant_user, created = User.objects.get_or_create(
        email=participant_email,
        defaults={
            'username': 'participant_test',
            'first_name': 'Ahmed',
            'last_name': 'Benali',
            'is_active': True
        }
    )
    
    if created:
        participant_user.set_password('makeplus2025')
        participant_user.save()
        print(f"✅ Created user: {participant_user.get_full_name()} ({participant_email})")
    else:
        print(f"✅ Found existing user: {participant_user.get_full_name()} ({participant_email})")
    
    # Create UserEventAssignment for participant
    assignment, created = UserEventAssignment.objects.get_or_create(
        user=participant_user,
        event=event,
        defaults={
            'role': 'participant',
            'is_active': True
        }
    )
    
    if created:
        print(f"✅ Created event assignment: participant role")
    else:
        assignment.role = 'participant'
        assignment.is_active = True
        assignment.save()
        print(f"✅ Updated event assignment: participant role")
    
    # Create or get Participant profile
    badge_id = f'PART-{random.randint(1000, 9999)}'
    participant, created = Participant.objects.get_or_create(
        user=participant_user,
        event=event,
        defaults={
            'badge_id': badge_id,
            'qr_code_data': f'{{"user_id": {participant_user.id}, "event_id": "{event.id}", "badge_id": "{badge_id}"}}'
        }
    )
    
    if created:
        print(f"✅ Created participant profile")
        print(f"   Badge: {participant.badge_id}")
    else:
        print(f"✅ Found existing participant profile")
        print(f"   Badge: {participant.badge_id}")
    
    # Get all sessions from this event
    all_sessions = list(Session.objects.filter(event=event))
    
    if not all_sessions:
        print("❌ No sessions found in this event!")
    else:
        print(f"\n📚 Found {len(all_sessions)} sessions in the event")
        
        # Assign participant to multiple sessions (conferences and workshops)
        conferences = [s for s in all_sessions if s.session_type == 'conference']
        workshops = [s for s in all_sessions if s.session_type == 'workshop']
        
        print(f"   - {len(conferences)} conferences")
        print(f"   - {len(workshops)} workshops")
        
        # Select some sessions to assign
        selected_sessions = []
        
        # Add 3 conferences
        if conferences:
            selected_sessions.extend(random.sample(conferences, min(3, len(conferences))))
        
        # Add 2 workshops
        if workshops:
            selected_sessions.extend(random.sample(workshops, min(2, len(workshops))))
        
        print(f"\n🎯 Assigning {len(selected_sessions)} sessions to participant...")
        
        created_count = 0
        for session in selected_sessions:
            # Create SessionAccess (participant registered for session)
            # If session is free, mark as 'free', otherwise 'paid'
            payment_status = 'free' if not hasattr(session, 'price') or session.price == 0 else 'paid'
            
            access, created = SessionAccess.objects.get_or_create(
                session=session,
                participant=participant,
                defaults={
                    'has_access': True,
                    'payment_status': payment_status,
                    'paid_at': timezone.now() if payment_status == 'paid' else None,
                    'amount_paid': session.price if hasattr(session, 'price') else 0
                }
            )
            
            if created:
                created_count += 1
                session_type_icon = "🎤" if session.session_type == 'conference' else "🛠️"
                print(f"  ✅ {session_type_icon} {session.title}")
                print(f"     Type: {session.session_type}")
                print(f"     Date: {session.start_time.strftime('%Y-%m-%d %H:%M')}")
                print(f"     Room: {session.room.name if session.room else 'N/A'}")
        
        print(f"\n✨ Created {created_count} new session registrations")
        
        # Create room access history (participant scanned into some rooms)
        rooms = list(Room.objects.filter(event=event)[:3])
        
        if rooms:
            print(f"\n🚪 Creating room access history...")
            
            room_access_count = 0
            for room in rooms:
                # Create 1-3 access records per room
                for i in range(random.randint(1, 3)):
                    days_ago = random.randint(0, 7)
                    accessed_at = timezone.now() - timezone.timedelta(days=days_ago)
                    
                    access, created = RoomAccess.objects.get_or_create(
                        room=room,
                        participant=participant,
                        accessed_at__date=accessed_at.date(),
                        defaults={
                            'status': 'granted',
                            'accessed_at': accessed_at,
                            'denial_reason': ''
                        }
                    )
                    
                    if created:
                        room_access_count += 1
            
            print(f"  ✅ Created {room_access_count} room access records")
        
        # Show summary
        print(f"\n" + "="*60)
        print(f"✨ TEST PARTICIPANT SETUP COMPLETE!")
        print(f"="*60)
        print(f"\n🔑 Login Credentials:")
        print(f"   Email: {participant_email}")
        print(f"   Password: makeplus2025")
        print(f"   Event ID: {event.id}")
        print(f"   Event: {event.name}")
        
        print(f"\n👤 Participant Details:")
        print(f"   Name: {participant_user.get_full_name()}")
        print(f"   Badge: {participant.badge_id}")
        
        print(f"\n📊 Assigned Content:")
        total_sessions = SessionAccess.objects.filter(participant=participant).count()
        total_rooms = RoomAccess.objects.filter(participant=participant).values('room').distinct().count()
        
        print(f"   Sessions registered: {total_sessions}")
        conferences_count = SessionAccess.objects.filter(
            participant=participant, 
            session__session_type='conference'
        ).count()
        workshops_count = SessionAccess.objects.filter(
            participant=participant, 
            session__session_type='workshop'
        ).count()
        print(f"     - Conferences: {conferences_count}")
        print(f"     - Workshops: {workshops_count}")
        print(f"   Rooms accessed: {total_rooms}")
        
        print(f"\n📡 API Endpoints to Test:")
        print(f"   POST /api/auth/login/")
        print(f"   GET  /api/auth/me/")
        print(f"   GET  /api/sessions/ (participant's sessions)")
        print(f"   GET  /api/session-access/ (participant's registrations)")
        print(f"   GET  /api/room-access/ (participant's room history)")
        
        print(f"\n🌐 Production URL:")
        print(f"   https://makeplus-django-5.onrender.com")
        
        print(f"\n" + "="*60)
        
except Event.DoesNotExist:
    print("❌ Event 'StartupWeek Oran 2025' not found")
    print("\n💡 Available events:")
    events = Event.objects.all()[:5]
    for e in events:
        print(f"   - {e.name} (ID: {e.id})")
        
except Exception as e:
    print(f"❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()
