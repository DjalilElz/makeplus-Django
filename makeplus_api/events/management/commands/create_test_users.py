from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from events.models import UserEventAssignment, Event
from django.utils import timezone
from datetime import timedelta

class Command(BaseCommand):
    help = 'Creates test users with different roles'

    def handle(self, *args, **kwargs):
        # First, create a test event
        event, created = Event.objects.get_or_create(
            name='MakePlus 2025',
            defaults={
                'description': 'Le plus grand événement technologique d\'Algérie',
                'start_date': timezone.now() + timedelta(days=30),
                'end_date': timezone.now() + timedelta(days=32),
                'location': 'Centre des Congrès, Alger',
                'status': 'upcoming',
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'✅ Created event: {event.name}'))
        
        users_data = [
            {
                'username': 'organizer1',
                'email': 'organizer@makeplus.com',
                'password': 'test123',
                'first_name': 'Ahmed',
                'last_name': 'Benali',
                'role': 'organisateur',
            },
            {
                'username': 'controller1',
                'email': 'controller@makeplus.com',
                'password': 'test123',
                'first_name': 'Amina',
                'last_name': 'Bensebbah',
                'role': 'controlleur_des_badges',
            },
            {
                'username': 'participant1',
                'email': 'participant1@makeplus.com',
                'password': 'test123',
                'first_name': 'Karim',
                'last_name': 'Djebar',
                'role': 'participant',
            },
            {
                'username': 'participant2',
                'email': 'participant2@makeplus.com',
                'password': 'test123',
                'first_name': 'Salima',
                'last_name': 'Hamdi',
                'role': 'participant',
            },
            {
                'username': 'exhibitor1',
                'email': 'exhibitor@makeplus.com',
                'password': 'test123',
                'first_name': 'Yacine',
                'last_name': 'Belkacem',
                'role': 'exposant',
            },
        ]

        for user_data in users_data:
            role = user_data.pop('role')
            password = user_data.pop('password')
            
            # Create user if doesn't exist
            user, created = User.objects.get_or_create(
                username=user_data['username'],
                defaults=user_data
            )
            
            if created:
                user.set_password(password)
                user.save()
                
                # Create event assignment
                UserEventAssignment.objects.create(
                    user=user,
                    event=event,
                    role=role,
                    is_active=True
                )
                
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Created user: {user.username} ({role})')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'⚠️  User already exists: {user.username}')
                )

        self.stdout.write(self.style.SUCCESS('\n🎉 All test users created!'))
        self.stdout.write(self.style.SUCCESS(f'📅 Test Event: {event.name}'))