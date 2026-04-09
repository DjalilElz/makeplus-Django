from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from events.models import Event, UserEventAssignment
from django.utils import timezone
from datetime import timedelta


class Command(BaseCommand):
    help = 'Create test users assigned to multiple events to test event selection'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('\n' + '='*80))
        self.stdout.write(self.style.SUCCESS('🔄 CREATING MULTI-EVENT USERS FOR TESTING'))
        self.stdout.write(self.style.SUCCESS('='*80 + '\n'))
        
        # Get all events
        events = list(Event.objects.all().order_by('start_date'))
        
        if len(events) < 2:
            self.stdout.write(self.style.ERROR('❌ Need at least 2 events. Run create_multi_event_data first.'))
            return
        
        # Create a user assigned to multiple events with different roles
        multi_event_users = [
            {
                'username': 'multi_user1',
                'email': 'multi.user@makeplus.com',
                'password': 'makeplus2025',
                'first_name': 'Hakim',
                'last_name': 'Mansouri',
                'assignments': [
                    {'event_index': 0, 'role': 'participant'},
                    {'event_index': 1, 'role': 'gestionnaire_des_salles'},
                    {'event_index': 2, 'role': 'controlleur_des_badges'},
                ]
            },
            {
                'username': 'multi_user2',
                'email': 'cross.event@makeplus.com',
                'password': 'makeplus2025',
                'first_name': 'Hanane',
                'last_name': 'Boudiaf',
                'assignments': [
                    {'event_index': 0, 'role': 'exposant'},
                    {'event_index': 1, 'role': 'participant'},
                ]
            },
        ]
        
        created_users = []
        
        for user_data in multi_event_users:
            assignments_data = user_data.pop('assignments')
            password = user_data.pop('password')
            
            # Create or get user
            user, created = User.objects.get_or_create(
                username=user_data['username'],
                defaults=user_data
            )
            
            if created:
                user.set_password(password)
                user.save()
                self.stdout.write(self.style.SUCCESS(f'✅ Created user: {user.username}'))
            else:
                # Delete old assignments
                UserEventAssignment.objects.filter(user=user).delete()
                self.stdout.write(self.style.WARNING(f'⚠️  User exists, updating: {user.username}'))
            
            # Create event assignments
            for assignment_data in assignments_data:
                event = events[assignment_data['event_index']]
                role = assignment_data['role']
                
                UserEventAssignment.objects.create(
                    user=user,
                    event=event,
                    role=role,
                    is_active=True
                )
                
                self.stdout.write(f'   → Assigned to {event.name} as {role}')
            
            created_users.append({
                'username': user.username,
                'email': user.email,
                'password': password,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'events': len(assignments_data)
            })
        
        self.stdout.write(self.style.SUCCESS('\n' + '='*80))
        self.stdout.write(self.style.SUCCESS('✅ MULTI-EVENT USERS CREATED'))
        self.stdout.write(self.style.SUCCESS('='*80 + '\n'))
        
        self.stdout.write(self.style.SUCCESS('📧 TEST USERS FOR MULTI-EVENT LOGIN:\n'))
        
        for user_info in created_users:
            self.stdout.write(self.style.SUCCESS(f'👤 {user_info["first_name"]} {user_info["last_name"]}'))
            self.stdout.write(f'   Email: {user_info["email"]}')
            self.stdout.write(f'   Username: {user_info["username"]}')
            self.stdout.write(f'   Password: {user_info["password"]}')
            self.stdout.write(f'   Assigned to: {user_info["events"]} events')
            self.stdout.write('')
        
        self.stdout.write(self.style.SUCCESS('='*80))
        self.stdout.write(self.style.SUCCESS('🧪 TEST THE NEW LOGIN FLOW:'))
        self.stdout.write('1. Login with: multi.user@makeplus.com / makeplus2025')
        self.stdout.write('2. You will receive list of 3 events')
        self.stdout.write('3. Select one event to get full access token')
        self.stdout.write(self.style.SUCCESS('='*80 + '\n'))
