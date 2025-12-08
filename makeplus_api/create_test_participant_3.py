"""
Create test participant 3 with conferences and ateliers for YouTube live testing
"""
import os
import django
import sys

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'makeplus_api.settings')
django.setup()

from django.contrib.auth.models import User
from events.models import (
    Event, Room, Session, Participant, UserEventAssignment, SessionAccess, UserProfile
)
from datetime import datetime, timedelta
from django.utils import timezone

def create_test_participant_3():
    """Create test participant 3 with YouTube live sessions"""
    
    print("=" * 80)
    print("Creating Test Participant 3 with YouTube Live Sessions")
    print("=" * 80)
    
    # Get the first active event
    event = Event.objects.filter(status='active').first()
    if not event:
        # Try to get any event
        event = Event.objects.first()
        if not event:
            print("❌ No event found. Please create an event first.")
            return
    
    print(f"\n✓ Using Event: {event.name}")
    
    # Create or get user
    email = "participant3.test@startupweek.dz"
    try:
        user = User.objects.get(email=email)
        print(f"\n✓ Found existing user: {email}")
    except User.DoesNotExist:
        user = User.objects.create_user(
            username='participant3_test',
            email=email,
            password='test123',
            first_name='Karim',
            last_name='Benzema'
        )
        print(f"\n✓ Created new user: {email}")
        print(f"  Password: test123")
    
    # Create user-level QR code (ONE QR for all events)
    user_qr_data = UserProfile.get_qr_for_user(user)
    print(f"\n✓ User QR Code Generated:")
    print(f"  Badge ID: {user_qr_data['badge_id']}")
    
    # Create or get UserEventAssignment
    assignment, created = UserEventAssignment.objects.get_or_create(
        user=user,
        event=event,
        defaults={
            'role': 'participant',
            'is_active': True,
            'assigned_by': User.objects.filter(is_superuser=True).first()
        }
    )
    if created:
        print(f"\n✓ Created UserEventAssignment: participant role")
    else:
        print(f"\n✓ Using existing UserEventAssignment")
    
    # Create or get Participant profile
    participant, created = Participant.objects.get_or_create(
        user=user,
        event=event,
        defaults={
            'badge_id': user_qr_data['badge_id'],
            'qr_code_data': str(user_qr_data),
            'is_checked_in': True,
            'checked_in_at': timezone.now()
        }
    )
    if created:
        print(f"\n✓ Created Participant profile")
    else:
        print(f"\n✓ Using existing Participant profile")
        participant.badge_id = user_qr_data['badge_id']
        participant.qr_code_data = str(user_qr_data)
        participant.save()
    
    # Get rooms
    rooms = list(Room.objects.filter(event=event))
    if not rooms:
        print("\n❌ No rooms found for this event")
        return
    
    print(f"\n✓ Found {len(rooms)} rooms")
    
    # YouTube test link
    youtube_url = "https://www.youtube.com/watch?v=jI6eO9vaB_Q"
    
    # Base time for sessions (starting tomorrow at 9 AM)
    base_time = timezone.now().replace(hour=9, minute=0, second=0, microsecond=0) + timedelta(days=1)
    
    print("\n" + "=" * 80)
    print("Creating FREE Conferences with YouTube Live")
    print("=" * 80)
    
    conferences_data = [
        {
            'title': 'Conférence: AI & Machine Learning',
            'description': 'Découvrez les dernières avancées en intelligence artificielle',
            'speaker_name': 'Dr. Yasmine Khelifi',
            'speaker_title': 'AI Research Scientist',
            'theme': 'Intelligence Artificielle',
            'start_offset': 0,  # 9:00 AM
            'duration': 90,  # 1h30
        },
        {
            'title': 'Conférence: Blockchain & Web3',
            'description': 'L\'avenir de la technologie décentralisée',
            'speaker_name': 'Ahmed Boudiaf',
            'speaker_title': 'Blockchain Expert',
            'theme': 'Blockchain',
            'start_offset': 120,  # 11:00 AM
            'duration': 90,
        },
        {
            'title': 'Conférence: Cybersecurity',
            'description': 'Protégez votre startup contre les cyberattaques',
            'speaker_name': 'Fatima Cherif',
            'speaker_title': 'Security Consultant',
            'theme': 'Sécurité',
            'start_offset': 240,  # 1:00 PM
            'duration': 90,
        },
    ]
    
    created_conferences = []
    for i, conf_data in enumerate(conferences_data):
        start_time = base_time + timedelta(minutes=conf_data['start_offset'])
        end_time = start_time + timedelta(minutes=conf_data['duration'])
        
        session = Session.objects.create(
            event=event,
            room=rooms[i % len(rooms)],
            title=conf_data['title'],
            description=conf_data['description'],
            speaker_name=conf_data['speaker_name'],
            speaker_title=conf_data['speaker_title'],
            theme=conf_data['theme'],
            start_time=start_time,
            end_time=end_time,
            session_type='conference',
            status='pas_encore',
            is_paid=False,
            youtube_live_url=youtube_url,
            created_by=User.objects.filter(is_superuser=True).first()
        )
        created_conferences.append(session)
        print(f"\n✓ Created: {session.title}")
        print(f"  Room: {session.room.name}")
        print(f"  Time: {start_time.strftime('%Y-%m-%d %H:%M')} - {end_time.strftime('%H:%M')}")
        print(f"  YouTube: {youtube_url}")
    
    print("\n" + "=" * 80)
    print("Creating PAID Ateliers with YouTube Live")
    print("=" * 80)
    
    ateliers_data = [
        {
            'title': 'Atelier: Flutter Mobile Development',
            'description': 'Créez des applications mobiles avec Flutter',
            'speaker_name': 'Karim Benyoucef',
            'speaker_title': 'Mobile Developer',
            'theme': 'Développement Mobile',
            'price': 4500.00,
            'start_offset': 360,  # 3:00 PM
            'duration': 120,
            'payment_status': 'paid',
        },
        {
            'title': 'Atelier: React & Next.js',
            'description': 'Développement web moderne avec React',
            'speaker_name': 'Sarah Meziane',
            'speaker_title': 'Full Stack Developer',
            'theme': 'Développement Web',
            'price': 5000.00,
            'start_offset': 510,  # 5:30 PM
            'duration': 120,
            'payment_status': 'paid',
        },
        {
            'title': 'Atelier: UX/UI Design',
            'description': 'Créez des interfaces utilisateur intuitives',
            'speaker_name': 'Leila Madani',
            'speaker_title': 'UX/UI Designer',
            'theme': 'Design',
            'price': 3500.00,
            'start_offset': 660,  # 8:00 PM (next session time)
            'duration': 90,
            'payment_status': 'paid',
        },
        {
            'title': 'Atelier: Data Science & Python',
            'description': 'Analysez vos données avec Python',
            'speaker_name': 'Mohamed Benali',
            'speaker_title': 'Data Scientist',
            'theme': 'Data Science',
            'price': 6000.00,
            'start_offset': 1200,  # Next day 9:00 AM
            'duration': 150,
            'payment_status': 'free',  # Free access
        },
    ]
    
    total_paid = 0
    for i, atelier_data in enumerate(ateliers_data):
        start_time = base_time + timedelta(minutes=atelier_data['start_offset'])
        end_time = start_time + timedelta(minutes=atelier_data['duration'])
        
        session = Session.objects.create(
            event=event,
            room=rooms[i % len(rooms)],
            title=atelier_data['title'],
            description=atelier_data['description'],
            speaker_name=atelier_data['speaker_name'],
            speaker_title=atelier_data['speaker_title'],
            theme=atelier_data['theme'],
            start_time=start_time,
            end_time=end_time,
            session_type='atelier',
            status='pas_encore',
            is_paid=True,
            price=atelier_data['price'],
            youtube_live_url=youtube_url,
            created_by=User.objects.filter(is_superuser=True).first()
        )
        
        # Create session access
        payment_status = atelier_data['payment_status']
        has_access = payment_status in ['paid', 'free']
        amount_paid = atelier_data['price'] if payment_status == 'paid' else 0
        
        session_access = SessionAccess.objects.create(
            participant=participant,
            session=session,
            payment_status=payment_status,
            has_access=has_access,
            amount_paid=amount_paid,
            paid_at=timezone.now() if payment_status == 'paid' else None
        )
        
        if payment_status == 'paid':
            total_paid += amount_paid
        
        print(f"\n✓ Created: {session.title}")
        print(f"  Room: {session.room.name}")
        print(f"  Time: {start_time.strftime('%Y-%m-%d %H:%M')} - {end_time.strftime('%H:%M')}")
        print(f"  Price: {atelier_data['price']} DZD")
        print(f"  Status: {payment_status.upper()}")
        print(f"  Access: {'✓ Granted' if has_access else '✗ Denied'}")
        print(f"  YouTube: {youtube_url}")
    
    print("\n" + "=" * 80)
    print("SUMMARY - Test Participant 3")
    print("=" * 80)
    print(f"\n👤 User Information:")
    print(f"  Name: {user.get_full_name()}")
    print(f"  Email: {user.email}")
    print(f"  Password: test123")
    print(f"  Badge ID: {user_qr_data['badge_id']}")
    
    print(f"\n📊 Sessions Summary:")
    print(f"  Free Conferences: {len(created_conferences)}")
    print(f"  Paid Ateliers: {len(ateliers_data)}")
    print(f"  - Paid & Access Granted: {sum(1 for a in ateliers_data if a['payment_status'] == 'paid')}")
    print(f"  - Free Access: {sum(1 for a in ateliers_data if a['payment_status'] == 'free')}")
    print(f"  Total Amount Paid: {total_paid} DZD")
    
    print(f"\n🎥 YouTube Live:")
    print(f"  URL: {youtube_url}")
    print(f"  All sessions include this YouTube link for testing")
    
    print(f"\n📅 Session Schedule:")
    all_sessions = created_conferences + [
        Session.objects.get(title=a['title']) for a in ateliers_data
    ]
    for session in sorted(all_sessions, key=lambda s: s.start_time):
        print(f"\n  {session.start_time.strftime('%Y-%m-%d %H:%M')} - {session.title}")
        print(f"    Type: {session.session_type.upper()}")
        print(f"    Room: {session.room.name}")
        if session.is_paid:
            access = SessionAccess.objects.filter(participant=participant, session=session).first()
            print(f"    Price: {session.price} DZD ({access.payment_status if access else 'N/A'})")
    
    print("\n" + "=" * 80)
    print("✅ Test Participant 3 Created Successfully!")
    print("=" * 80)
    print("\n📝 Next Steps:")
    print("  1. Login with: participant3.test@startupweek.dz / test123")
    print("  2. Select the event")
    print("  3. View conferences and ateliers with YouTube live links")
    print("  4. Test YouTube player integration in Flutter app")
    print("  5. Test Q&A system on sessions")
    print("\n")

if __name__ == '__main__':
    create_test_participant_3()
