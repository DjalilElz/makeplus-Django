from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from events.models import Event, Room, Session, Participant, RoomAccess, UserEventAssignment
from django.utils import timezone
from datetime import timedelta
import uuid


class Command(BaseCommand):
    help = 'Creates multiple events with users for each role type (organisateur, controlleur_des_badges, participant, exposant)'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('🚀 Creating multiple events with users for each role...\n'))
        
        # Track created users for credentials output
        created_users = []
        
        # Define multiple events
        events_data = [
            {
                'name': 'TechSummit Algeria 2025',
                'description': 'Le plus grand sommet technologique d\'Algérie',
                'location': 'Centre des Congrès, Alger',
                'days_offset': 30,
                'duration_days': 3,
                'status': 'upcoming',
                'prefix': 'tech'
            },
            {
                'name': 'StartupWeek Oran 2025',
                'description': 'Semaine dédiée aux startups et entrepreneurs',
                'location': 'Palais des Expositions, Oran',
                'days_offset': 60,
                'duration_days': 5,
                'status': 'upcoming',
                'prefix': 'startup'
            },
            {
                'name': 'InnoFest Constantine 2025',
                'description': 'Festival d\'innovation et de créativité',
                'location': 'Université Constantine 2, Constantine',
                'days_offset': 90,
                'duration_days': 2,
                'status': 'upcoming',
                'prefix': 'inno'
            },
        ]
        
        for event_data in events_data:
            prefix = event_data.pop('prefix')
            days_offset = event_data.pop('days_offset')
            duration_days = event_data.pop('duration_days')
            
            # Create event
            event, created = Event.objects.get_or_create(
                name=event_data['name'],
                defaults={
                    **event_data,
                    'start_date': timezone.now() + timedelta(days=days_offset),
                    'end_date': timezone.now() + timedelta(days=days_offset + duration_days),
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'✅ Created event: {event.name}'))
            else:
                self.stdout.write(self.style.WARNING(f'⚠️  Event already exists: {event.name}'))
            
            # Create users for each role
            roles_data = [
                {
                    'role': 'organisateur',
                    'username': f'{prefix}_organisateur',
                    'email': f'{prefix}_organisateur@makeplus.com',
                    'first_name': 'Ahmed',
                    'last_name': 'Benali',
                },
                {
                    'role': 'controlleur_des_badges',
                    'username': f'{prefix}_controleur',
                    'email': f'{prefix}_controleur@makeplus.com',
                    'first_name': 'Amina',
                    'last_name': 'Bensebbah',
                },
                {
                    'role': 'participant',
                    'username': f'{prefix}_participant1',
                    'email': f'{prefix}_participant1@makeplus.com',
                    'first_name': 'Karim',
                    'last_name': 'Djebar',
                },
                {
                    'role': 'participant',
                    'username': f'{prefix}_participant2',
                    'email': f'{prefix}_participant2@makeplus.com',
                    'first_name': 'Salima',
                    'last_name': 'Hamdi',
                },
                {
                    'role': 'exposant',
                    'username': f'{prefix}_exposant1',
                    'email': f'{prefix}_exposant1@makeplus.com',
                    'first_name': 'Yacine',
                    'last_name': 'Belkacem',
                },
                {
                    'role': 'exposant',
                    'username': f'{prefix}_exposant2',
                    'email': f'{prefix}_exposant2@makeplus.com',
                    'first_name': 'Fatima',
                    'last_name': 'Zerhouni',
                },
            ]
            
            event_users = []
            event_roles = []  # Track roles separately
            for user_data in roles_data:
                role = user_data.pop('role')
                password = 'makeplus2025'  # Default password for all test users
                
                # Create user
                user, user_created = User.objects.get_or_create(
                    username=user_data['username'],
                    defaults=user_data
                )
                
                if user_created:
                    user.set_password(password)
                    user.save()
                    created_users.append({
                        'event': event.name,
                        'username': user.username,
                        'email': user.email,
                        'password': password,
                        'role': role,
                    })
                    self.stdout.write(f'  ✅ Created user: {user.username} ({role})')
                
                # Create event assignment
                assignment, assign_created = UserEventAssignment.objects.get_or_create(
                    user=user,
                    event=event,
                    defaults={
                        'role': role,
                        'is_active': True,
                    }
                )
                
                event_users.append(user)
                event_roles.append(role)  # Store role for later use
                
                # Set event created_by to the first organisateur
                if role == 'organisateur' and not event.created_by:
                    event.created_by = user
                    event.save()
            
            # Create rooms for the event
            rooms_data = [
                {'name': 'Salle Principale', 'capacity': 300, 'location': 'Rez-de-chaussée'},
                {'name': 'Salle Atelier A', 'capacity': 100, 'location': '1er étage'},
                {'name': 'Salle Atelier B', 'capacity': 80, 'location': '1er étage'},
                {'name': 'Hall Exposition', 'capacity': 500, 'location': 'Rez-de-chaussée'},
            ]
            
            rooms = []
            organisateur = event_users[0] if event_users else None
            for room_data in rooms_data:
                room, room_created = Room.objects.get_or_create(
                    event=event,
                    name=room_data['name'],
                    defaults={
                        **room_data,
                        'description': f"Capacité: {room_data['capacity']} personnes",
                        'is_active': True,
                        'created_by': organisateur,
                    }
                )
                rooms.append(room)
                if room_created:
                    self.stdout.write(f'  ✅ Created room: {room.name}')
            
            # Create sessions
            base_time = event.start_date.replace(hour=9, minute=0)
            sessions_data = [
                {
                    'title': 'Cérémonie d\'Ouverture',
                    'description': 'Discours d\'ouverture et présentation de l\'événement',
                    'room': rooms[0],
                    'start_time': base_time,
                    'duration_hours': 1,
                    'speaker_name': 'Dr. Hassan Lakhdari',
                    'speaker_title': 'Directeur Général',
                    'theme': 'Opening',
                },
                {
                    'title': 'Intelligence Artificielle - Tendances 2025',
                    'description': 'Les dernières avancées en IA et Machine Learning',
                    'room': rooms[1],
                    'start_time': base_time + timedelta(hours=1, minutes=30),
                    'duration_hours': 2,
                    'speaker_name': 'Dr. Amina Tebboune',
                    'speaker_title': 'Chercheuse en IA',
                    'theme': 'AI',
                },
                {
                    'title': 'Développement Web Moderne',
                    'description': 'React, Vue, et les frameworks modernes',
                    'room': rooms[2],
                    'start_time': base_time + timedelta(hours=1, minutes=30),
                    'duration_hours': 2,
                    'speaker_name': 'Mehdi Boudiaf',
                    'speaker_title': 'Lead Developer',
                    'theme': 'Web',
                },
            ]
            
            for session_data in sessions_data:
                duration_hours = session_data.pop('duration_hours')
                end_time = session_data['start_time'] + timedelta(hours=duration_hours)
                
                session, session_created = Session.objects.get_or_create(
                    event=event,
                    title=session_data['title'],
                    defaults={
                        **session_data,
                        'end_time': end_time,
                        'status': 'scheduled',
                        'created_by': organisateur,
                    }
                )
                if session_created:
                    self.stdout.write(f'  ✅ Created session: {session.title}')
            
            # Create participants with badges for participant and exposant users
            participant_users = [(u, r) for u, r in zip(event_users, event_roles) 
                                if r in ['participant', 'exposant']]
            
            for user, role in participant_users:
                badge_id = f"{prefix.upper()}-{uuid.uuid4().hex[:8].upper()}"
                qr_data = f"{event.id}:{user.id}:{badge_id}"
                
                participant, part_created = Participant.objects.get_or_create(
                    user=user,
                    event=event,
                    defaults={
                        'badge_id': badge_id,
                        'qr_code_data': qr_data,
                        'is_checked_in': False,
                    }
                )
                
                if part_created:
                    # Give access to all rooms
                    participant.allowed_rooms.set(rooms)
                    self.stdout.write(f'  ✅ Created participant badge for: {user.username} (Badge: {badge_id})')
            
            self.stdout.write(self.style.SUCCESS(f'✅ Completed setup for: {event.name}\n'))
        
        # Print credentials summary
        self.stdout.write(self.style.SUCCESS('\n' + '='*80))
        self.stdout.write(self.style.SUCCESS('🎉 ALL EVENTS AND USERS CREATED SUCCESSFULLY!'))
        self.stdout.write(self.style.SUCCESS('='*80 + '\n'))
        
        self.stdout.write(self.style.SUCCESS('📧 USER CREDENTIALS FOR TESTING:\n'))
        self.stdout.write(self.style.SUCCESS('Default Password for all users: makeplus2025\n'))
        
        current_event = None
        for user_info in created_users:
            if current_event != user_info['event']:
                current_event = user_info['event']
                self.stdout.write(self.style.SUCCESS(f'\n📅 {current_event}:'))
            
            role_display = {
                'organisateur': '👔 Organisateur',
                'controlleur_des_badges': '🎫 Contrôleur des Badges',
                'participant': '👤 Participant',
                'exposant': '🏢 Exposant',
            }.get(user_info['role'], user_info['role'])
            
            self.stdout.write(f"   {role_display}")
            self.stdout.write(f"      Email: {user_info['email']}")
            self.stdout.write(f"      Username: {user_info['username']}")
        
        self.stdout.write(self.style.SUCCESS('\n' + '='*80))
        self.stdout.write(self.style.SUCCESS(f'📊 SUMMARY:'))
        self.stdout.write(f'   Total Events: {Event.objects.count()}')
        self.stdout.write(f'   Total Users: {User.objects.count()}')
        self.stdout.write(f'   Total Rooms: {Room.objects.count()}')
        self.stdout.write(f'   Total Sessions: {Session.objects.count()}')
        self.stdout.write(f'   Total Participants: {Participant.objects.count()}')
        self.stdout.write(self.style.SUCCESS('='*80 + '\n'))
