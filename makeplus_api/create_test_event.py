# -*- coding: utf-8 -*-
"""
Create a complete test event with users, rooms, sessions, and participants
for mobile app testing
"""

import os
import sys
import django
import json
from datetime import datetime, timedelta
from decimal import Decimal

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'makeplus_api.settings')
django.setup()

from django.contrib.auth.models import User
from events.models import (
    Event, Room, Session, UserEventAssignment, 
    Participant, UserProfile
)
from django.utils import timezone

def create_test_event():
    print("🚀 Creating comprehensive test event for mobile app...")
    
    # 1. Create Event
    print("\n📅 Creating event...")
    event, created = Event.objects.get_or_create(
        name="Tech Conference 2025",
        defaults={
            'description': 'Annual technology conference featuring the latest innovations in AI, Cloud Computing, and Mobile Development',
            'start_date': timezone.now() + timedelta(days=7),
            'end_date': timezone.now() + timedelta(days=9),
            'location': 'Convention Center, Paris',
            'location_details': 'Main Hall, 2nd Floor',
            'status': 'upcoming',
            'organizer_contact': 'contact@techconf2025.com',
        }
    )
    if created:
        print(f"   ✅ Event created: {event.name}")
    else:
        print(f"   ℹ️  Event already exists: {event.name}")
    
    # 2. Create Users with different roles
    print("\n👥 Creating users...")
    
    users_data = [
        # Organisateurs
        {'username': 'organizer1', 'password': 'pass123', 'first_name': 'Alice', 'last_name': 'Johnson', 'email': 'alice@techconf.com', 'role': 'organisateur'},
        {'username': 'organizer2', 'password': 'pass123', 'first_name': 'Bob', 'last_name': 'Smith', 'email': 'bob@techconf.com', 'role': 'organisateur'},
        
        # Gestionnaires des salles
        {'username': 'room_manager1', 'password': 'pass123', 'first_name': 'Carol', 'last_name': 'Williams', 'email': 'carol@techconf.com', 'role': 'gestionnaire_des_salles'},
        {'username': 'room_manager2', 'password': 'pass123', 'first_name': 'David', 'last_name': 'Brown', 'email': 'david@techconf.com', 'role': 'gestionnaire_des_salles'},
        
        # Contrôleurs des badges
        {'username': 'controller1', 'password': 'pass123', 'first_name': 'Emma', 'last_name': 'Davis', 'email': 'emma@techconf.com', 'role': 'controlleur_des_badges'},
        {'username': 'controller2', 'password': 'pass123', 'first_name': 'Frank', 'last_name': 'Miller', 'email': 'frank@techconf.com', 'role': 'controlleur_des_badges'},
        {'username': 'controller3', 'password': 'pass123', 'first_name': 'Grace', 'last_name': 'Wilson', 'email': 'grace@techconf.com', 'role': 'controlleur_des_badges'},
        
        # Exposants
        {'username': 'exhibitor1', 'password': 'pass123', 'first_name': 'Henry', 'last_name': 'Moore', 'email': 'henry@techcorp.com', 'role': 'exposant'},
        {'username': 'exhibitor2', 'password': 'pass123', 'first_name': 'Iris', 'last_name': 'Taylor', 'email': 'iris@innovate.com', 'role': 'exposant'},
        {'username': 'exhibitor3', 'password': 'pass123', 'first_name': 'Jack', 'last_name': 'Anderson', 'email': 'jack@startup.io', 'role': 'exposant'},
        
        # Regular participants
        {'username': 'participant1', 'password': 'pass123', 'first_name': 'Karen', 'last_name': 'Thomas', 'email': 'karen@email.com', 'role': 'participant'},
        {'username': 'participant2', 'password': 'pass123', 'first_name': 'Leo', 'last_name': 'Jackson', 'email': 'leo@email.com', 'role': 'participant'},
        {'username': 'participant3', 'password': 'pass123', 'first_name': 'Maria', 'last_name': 'White', 'email': 'maria@email.com', 'role': 'participant'},
        {'username': 'participant4', 'password': 'pass123', 'first_name': 'Nathan', 'last_name': 'Harris', 'email': 'nathan@email.com', 'role': 'participant'},
        {'username': 'participant5', 'password': 'pass123', 'first_name': 'Olivia', 'last_name': 'Martin', 'email': 'olivia@email.com', 'role': 'participant'},
    ]
    
    created_users = {}
    for user_data in users_data:
        username = user_data['username']
        role = user_data.pop('role')
        password = user_data.pop('password')
        
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'first_name': user_data['first_name'],
                'last_name': user_data['last_name'],
                'email': user_data['email']
            }
        )
        
        if created:
            user.set_password(password)
            user.save()
            print(f"   ✅ User created: {username} ({role})")
        else:
            print(f"   ℹ️  User exists: {username} ({role})")
        
        # Create user profile with QR code
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.get_or_create_qr_code()
        
        created_users[username] = {'user': user, 'role': role}
    
    # 3. Assign users to event with roles
    print("\n🔐 Assigning roles to event...")
    for username, data in created_users.items():
        user = data['user']
        role = data['role']
        
        if role != 'participant':  # Participants are created separately
            assignment, created = UserEventAssignment.objects.get_or_create(
                user=user,
                event=event,
                defaults={'role': role, 'is_active': True}
            )
            if created:
                print(f"   ✅ Assigned {user.username} as {role}")
            else:
                print(f"   ℹ️  {user.username} already assigned as {role}")
    
    # 4. Create Participants (including regular participants)
    print("\n👤 Creating participants...")
    for username, data in created_users.items():
        user = data['user']
        
        # Get or create QR code from user profile
        qr_data = UserProfile.get_qr_for_user(user)
        
        participant, created = Participant.objects.get_or_create(
            user=user,
            event=event,
            defaults={
                'is_checked_in': username in ['participant1', 'participant2'],  # Some checked in
                'badge_id': f"BADGE-{user.id}-{event.id}",
                'qr_code_data': json.dumps(qr_data)
            }
        )
        
        if created:
            print(f"   ✅ Participant created: {user.get_full_name()}")
        else:
            print(f"   ℹ️  Participant exists: {user.get_full_name()}")
    
    # 5. Create Rooms
    print("\n🏛️  Creating rooms...")
    rooms_data = [
        {'name': 'Main Hall', 'capacity': 500, 'location': 'Building A, Ground Floor', 'description': 'Large auditorium for keynote sessions'},
        {'name': 'Conference Room A', 'capacity': 100, 'location': 'Building A, 1st Floor', 'description': 'Medium-sized room for technical talks'},
        {'name': 'Conference Room B', 'capacity': 100, 'location': 'Building A, 1st Floor', 'description': 'Medium-sized room for workshops'},
        {'name': 'Workshop Space 1', 'capacity': 50, 'location': 'Building B, Ground Floor', 'description': 'Hands-on workshop area'},
        {'name': 'Workshop Space 2', 'capacity': 50, 'location': 'Building B, Ground Floor', 'description': 'Interactive learning space'},
    ]
    
    rooms = []
    for room_data in rooms_data:
        room, created = Room.objects.get_or_create(
            event=event,
            name=room_data['name'],
            defaults={
                'capacity': room_data['capacity'],
                'location': room_data['location'],
                'description': room_data['description'],
                'current_participants': 0,
                'is_active': True
            }
        )
        rooms.append(room)
        
        if created:
            print(f"   ✅ Room created: {room.name} (capacity: {room.capacity})")
        else:
            print(f"   ℹ️  Room exists: {room.name}")
    
    # 6. Create Sessions
    print("\n📋 Creating sessions...")
    
    base_date = event.start_date
    
    sessions_data = [
        # Day 1 - Main Hall
        {
            'title': 'Opening Keynote: Future of AI',
            'room': rooms[0],
            'start_time': base_date.replace(hour=9, minute=0),
            'end_time': base_date.replace(hour=10, minute=30),
            'session_type': 'conference',
            'speaker_name': 'Dr. Sarah Chen',
            'speaker_title': 'Chief AI Scientist',
            'speaker_bio': 'Leading expert in machine learning with 15 years of experience',
            'theme': 'Artificial Intelligence',
            'is_paid': False,
            'youtube_live_url': 'https://youtube.com/live/keynote2025',
            'status': 'pas_encore',
        },
        
        # Day 1 - Conference Room A
        {
            'title': 'Deep Learning Best Practices',
            'room': rooms[1],
            'start_time': base_date.replace(hour=11, minute=0),
            'end_time': base_date.replace(hour=12, minute=30),
            'session_type': 'conference',
            'speaker_name': 'Michael Rodriguez',
            'speaker_title': 'Senior ML Engineer',
            'speaker_bio': 'Specializes in neural networks and computer vision',
            'theme': 'Machine Learning',
            'is_paid': False,
            'status': 'pas_encore',
        },
        
        # Day 1 - Workshop Space 1
        {
            'title': 'Hands-on: Building Your First Neural Network',
            'room': rooms[3],
            'start_time': base_date.replace(hour=14, minute=0),
            'end_time': base_date.replace(hour=17, minute=0),
            'session_type': 'atelier',
            'speaker_name': 'Emma Watson',
            'speaker_title': 'ML Education Specialist',
            'speaker_bio': 'Passionate about teaching AI to developers',
            'theme': 'Workshop',
            'is_paid': True,
            'price': Decimal('49.99'),
            'status': 'pas_encore',
        },
        
        # Day 2 - Main Hall
        {
            'title': 'Cloud Architecture at Scale',
            'room': rooms[0],
            'start_time': base_date.replace(hour=9, minute=0) + timedelta(days=1),
            'end_time': base_date.replace(hour=10, minute=30) + timedelta(days=1),
            'session_type': 'conference',
            'speaker_name': 'James Liu',
            'speaker_title': 'Cloud Solutions Architect',
            'speaker_bio': 'Expert in distributed systems and microservices',
            'theme': 'Cloud Computing',
            'is_paid': False,
            'youtube_live_url': 'https://youtube.com/live/cloud2025',
            'status': 'pas_encore',
        },
        
        # Day 2 - Conference Room B
        {
            'title': 'Mobile Development Trends 2025',
            'room': rooms[2],
            'start_time': base_date.replace(hour=11, minute=0) + timedelta(days=1),
            'end_time': base_date.replace(hour=12, minute=30) + timedelta(days=1),
            'session_type': 'conference',
            'speaker_name': 'Lisa Martinez',
            'speaker_title': 'Mobile Tech Lead',
            'speaker_bio': 'Flutter and React Native expert',
            'theme': 'Mobile Development',
            'is_paid': False,
            'status': 'pas_encore',
        },
        
        # Day 2 - Workshop Space 2
        {
            'title': 'Advanced Flutter Workshop',
            'room': rooms[4],
            'start_time': base_date.replace(hour=14, minute=0) + timedelta(days=1),
            'end_time': base_date.replace(hour=17, minute=0) + timedelta(days=1),
            'session_type': 'atelier',
            'speaker_name': 'Alex Turner',
            'speaker_title': 'Flutter Developer',
            'speaker_bio': 'Building beautiful mobile apps for 8 years',
            'theme': 'Workshop',
            'is_paid': True,
            'price': Decimal('59.99'),
            'status': 'pas_encore',
        },
        
        # Day 3 - Main Hall
        {
            'title': 'Closing Keynote: Tech for Good',
            'room': rooms[0],
            'start_time': base_date.replace(hour=16, minute=0) + timedelta(days=2),
            'end_time': base_date.replace(hour=17, minute=30) + timedelta(days=2),
            'session_type': 'conference',
            'speaker_name': 'Dr. Patricia Green',
            'speaker_title': 'Tech Ethics Researcher',
            'speaker_bio': 'Advocate for responsible technology development',
            'theme': 'Technology Ethics',
            'is_paid': False,
            'youtube_live_url': 'https://youtube.com/live/closing2025',
            'status': 'pas_encore',
        },
    ]
    
    for session_data in sessions_data:
        session, created = Session.objects.get_or_create(
            event=event,
            room=session_data['room'],
            title=session_data['title'],
            defaults={
                'description': f"Join us for {session_data['title']}",
                'start_time': session_data['start_time'],
                'end_time': session_data['end_time'],
                'session_type': session_data['session_type'],
                'speaker_name': session_data['speaker_name'],
                'speaker_title': session_data['speaker_title'],
                'speaker_bio': session_data['speaker_bio'],
                'theme': session_data['theme'],
                'is_paid': session_data['is_paid'],
                'price': session_data.get('price', Decimal('0.00')),
                'youtube_live_url': session_data.get('youtube_live_url', ''),
                'status': session_data['status'],
            }
        )
        
        if created:
            session_type_emoji = '🎤' if session_data['session_type'] == 'conference' else '🛠️'
            print(f"   ✅ {session_type_emoji} Session created: {session.title}")
        else:
            print(f"   ℹ️  Session exists: {session.title}")
    
    # Summary
    print("\n" + "="*70)
    print("✨ TEST EVENT SETUP COMPLETE!")
    print("="*70)
    print(f"\n📅 Event: {event.name}")
    print(f"   📍 Location: {event.location}")
    print(f"   📆 Dates: {event.start_date.strftime('%Y-%m-%d')} to {event.end_date.strftime('%Y-%m-%d')}")
    print(f"   🆔 Event ID: {event.id}")
    
    print(f"\n👥 Users Created (all passwords: pass123):")
    print(f"   • 2 Organizers (organizer1, organizer2)")
    print(f"   • 2 Room Managers (room_manager1, room_manager2)")
    print(f"   • 3 Controllers (controller1, controller2, controller3)")
    print(f"   • 3 Exhibitors (exhibitor1, exhibitor2, exhibitor3)")
    print(f"   • 5 Participants (participant1-5)")
    
    print(f"\n🏛️  Rooms: {Room.objects.filter(event=event).count()} rooms")
    print(f"📋 Sessions: {Session.objects.filter(event=event).count()} sessions")
    print(f"   • {Session.objects.filter(event=event, session_type='conference').count()} conferences")
    print(f"   • {Session.objects.filter(event=event, session_type='atelier').count()} workshops (paid)")
    
    print(f"\n🎫 Participants: {Participant.objects.filter(event=event).count()} registered")
    print(f"   • {Participant.objects.filter(event=event, is_checked_in=True).count()} checked in")
    
    print("\n" + "="*70)
    print("🚀 READY FOR MOBILE APP TESTING!")
    print("="*70)
    print("\nTest Users (username / password / role):")
    for username, data in created_users.items():
        print(f"   {username} / pass123 / {data['role']}")
    
    return event

if __name__ == '__main__':
    create_test_event()
