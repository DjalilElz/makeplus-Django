from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from events.models import Event, Room, Session, Participant, RoomAccess
from django.utils import timezone
from datetime import timedelta
import uuid

class Command(BaseCommand):
    help = 'Creates test data for the MakePlus app'

    def handle(self, *args, **kwargs):
        # Get the event
        try:
            event = Event.objects.get(name='MakePlus 2025')
        except Event.DoesNotExist:
            self.stdout.write(self.style.ERROR('❌ Event not found. Run create_test_users first.'))
            return

        # Get users
        try:
            organizer = User.objects.get(username='organizer1')
            participant1 = User.objects.get(username='participant1')
            participant2 = User.objects.get(username='participant2')
        except User.DoesNotExist as e:
            self.stdout.write(self.style.ERROR(f'❌ User not found: {e}'))
            return

        # Update event created_by
        if not event.created_by:
            event.created_by = organizer
            event.save()

        # Create Rooms
        rooms_data = [
            {'name': 'Salle A', 'capacity': 200, 'location': 'Rez-de-chaussée'},
            {'name': 'Salle B', 'capacity': 150, 'location': '1er étage'},
            {'name': 'Salle C', 'capacity': 100, 'location': '1er étage'},
            {'name': 'Hall Expo', 'capacity': 500, 'location': 'Rez-de-chaussée'},
        ]

        rooms = []
        for room_data in rooms_data:
            room, created = Room.objects.get_or_create(
                event=event,
                name=room_data['name'],
                defaults={
                    **room_data,
                    'description': f"Salle pour {room_data['capacity']} personnes",
                    'is_active': True,
                    'created_by': organizer
                }
            )
            rooms.append(room)
            if created:
                self.stdout.write(self.style.SUCCESS(f'✅ Created room: {room.name}'))

        # Create Sessions
        base_time = event.start_date.replace(hour=9, minute=0)
        
        sessions_data = [
            {
                'title': 'Ouverture & Keynote',
                'description': 'Discours d\'ouverture sur l\'avenir de la technologie en Algérie.',
                'room': rooms[0],
                'start_time': base_time,
                'end_time': base_time + timedelta(hours=1),
                'speaker_name': 'Dr. Arsène Lafleur',
                'speaker_title': 'Directeur de Recherche',
                'theme': 'Innovation',
                'status': 'pas_encore'
            },
            {
                'title': 'Intelligence Artificielle et Machine Learning',
                'description': 'Introduction aux concepts fondamentaux de l\'IA et du ML.',
                'room': rooms[0],
                'start_time': base_time + timedelta(hours=1, minutes=15),
                'end_time': base_time + timedelta(hours=2, minutes=15),
                'speaker_name': 'Dr. Arsène Lafleur',
                'speaker_title': 'Directeur de Recherche',
                'theme': 'IA',
                'status': 'pas_encore'
            },
            {
                'title': 'Développement Mobile avec Flutter',
                'description': 'Atelier pratique sur Flutter et Dart.',
                'room': rooms[1],
                'start_time': base_time + timedelta(hours=1, minutes=15),
                'end_time': base_time + timedelta(hours=3, minutes=15),
                'speaker_name': 'Sarah Chen',
                'speaker_title': 'Lead Developer',
                'theme': 'Mobile',
                'status': 'pas_encore'
            },
            {
                'title': 'Cybersécurité: Atelier "DataOps"',
                'description': 'Démonstration des meilleures pratiques en sécurité.',
                'room': rooms[2],
                'start_time': base_time + timedelta(hours=2, minutes=30),
                'end_time': base_time + timedelta(hours=4, minutes=30),
                'speaker_name': 'Mohammed Benali',
                'speaker_title': 'Security Consultant',
                'theme': 'Sécurité',
                'status': 'pas_encore'
            },
        ]

        for session_data in sessions_data:
            session, created = Session.objects.get_or_create(
                event=event,
                title=session_data['title'],
                defaults={
                    **session_data,
                    'created_by': organizer
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'✅ Created session: {session.title}'))

        # Create Participants
        for user in [participant1, participant2]:
            badge_id = f"BADGE-{uuid.uuid4().hex[:8].upper()}"
            qr_data = f"{event.id}:{user.id}:{badge_id}"
            
            participant, created = Participant.objects.get_or_create(
                user=user,
                event=event,
                defaults={
                    'badge_id': badge_id,
                    'qr_code_data': qr_data,
                    'is_checked_in': False
                }
            )
            if created:
                # Allow access to all rooms
                participant.allowed_rooms.set(rooms)
                self.stdout.write(self.style.SUCCESS(f'✅ Created participant: {user.username} (Badge: {badge_id})'))

        self.stdout.write(self.style.SUCCESS('\n🎉 All test data created successfully!'))
        self.stdout.write(self.style.SUCCESS('\n📊 Summary:'))
        self.stdout.write(f'   Events: {Event.objects.count()}')
        self.stdout.write(f'   Rooms: {Room.objects.filter(event=event).count()}')
        self.stdout.write(f'   Sessions: {Session.objects.filter(event=event).count()}')
        self.stdout.write(f'   Participants: {Participant.objects.filter(event=event).count()}')