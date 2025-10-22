from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from events.models import Event, UserEventAssignment
from django.utils import timezone
from datetime import timedelta

class Command(BaseCommand):
    help = 'Complete reset of test users with verification'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING('\n' + '='*60))
        self.stdout.write(self.style.WARNING('COMPLETE TEST ENVIRONMENT RESET'))
        self.stdout.write(self.style.WARNING('='*60 + '\n'))
        
        # Step 1: Ensure event exists
        self.stdout.write('📅 Step 1: Ensuring event exists...')
        event, event_created = Event.objects.get_or_create(
            name='MakePlus 2025',
            defaults={
                'description': 'Le plus grand événement technologique d\'Algérie',
                'start_date': timezone.now() + timedelta(days=30),
                'end_date': timezone.now() + timedelta(days=32),
                'location': 'Centre des Congrès, Alger',
                'status': 'upcoming',
            }
        )
        
        if event_created:
            self.stdout.write(self.style.SUCCESS(f'   ✅ Created event: {event.name}'))
        else:
            self.stdout.write(self.style.SUCCESS(f'   ✓ Event exists: {event.name}'))
        
        # Step 2: Create/Update users
        self.stdout.write('\n👥 Step 2: Creating/Updating users...')
        
        users_data = [
            {
                'username': 'organizer1',
                'email': 'organizer@makeplus.com',
                'first_name': 'Ahmed',
                'last_name': 'Benali',
                'role': 'organizer',
            },
            {
                'username': 'controller1',
                'email': 'controller@makeplus.com',
                'first_name': 'Amina',
                'last_name': 'Bensebbah',
                'role': 'controller',
            },
            {
                'username': 'participant1',
                'email': 'participant1@makeplus.com',
                'first_name': 'Karim',
                'last_name': 'Djebar',
                'role': 'participant',
            },
            {
                'username': 'participant2',
                'email': 'participant2@makeplus.com',
                'first_name': 'Salima',
                'last_name': 'Hamdi',
                'role': 'participant',
            },
            {
                'username': 'exhibitor1',
                'email': 'exhibitor@makeplus.com',
                'first_name': 'Yacine',
                'last_name': 'Belkacem',
                'role': 'exhibitor',
            },
        ]
        
        created_count = 0
        updated_count = 0
        
        for user_data in users_data:
            role = user_data.pop('role')
            username = user_data['username']
            
            # Get or create user
            user, user_created = User.objects.get_or_create(
                username=username,
                defaults=user_data
            )
            
            if not user_created:
                # Update existing user
                for key, value in user_data.items():
                    setattr(user, key, value)
                updated_count += 1
            else:
                created_count += 1
            
            # CRITICAL: Set password and activate
            user.set_password('test123')
            user.is_active = True
            user.save()
            
            # Verify password immediately
            password_valid = user.check_password('test123')
            password_status = "✅ VERIFIED" if password_valid else "❌ FAILED"
            
            # Create or update event assignment
            assignment, assignment_created = UserEventAssignment.objects.get_or_create(
                user=user,
                event=event,
                defaults={
                    'role': role,
                    'is_active': True
                }
            )
            
            # Update role if assignment already existed
            if not assignment_created:
                assignment.role = role
                assignment.is_active = True
                assignment.save()
            
            status = "CREATED" if user_created else "UPDATED"
            self.stdout.write(
                self.style.SUCCESS(
                    f'   {status}: {username:<15} | Role: {role:<12} | Password: {password_status}'
                )
            )
        
        # Step 3: Verification
        self.stdout.write('\n🔍 Step 3: Running verification...')
        
        total_users = User.objects.filter(
            username__in=['organizer1', 'controller1', 'participant1', 'participant2', 'exhibitor1']
        ).count()
        
        active_users = User.objects.filter(
            username__in=['organizer1', 'controller1', 'participant1', 'participant2', 'exhibitor1'],
            is_active=True
        ).count()
        
        total_assignments = UserEventAssignment.objects.filter(event=event).count()
        
        self.stdout.write(self.style.SUCCESS(f'   ✓ Total users: {total_users}/5'))
        self.stdout.write(self.style.SUCCESS(f'   ✓ Active users: {active_users}/5'))
        self.stdout.write(self.style.SUCCESS(f'   ✓ Role assignments: {total_assignments}/5'))
        
        # Step 4: Test authentication
        self.stdout.write('\n🧪 Step 4: Testing authentication...')
        
        from django.contrib.auth import authenticate
        
        test_auth = authenticate(username='organizer1', password='test123')
        if test_auth:
            self.stdout.write(self.style.SUCCESS('   ✅ Authentication test PASSED'))
            self.stdout.write(self.style.SUCCESS(f'      User: {test_auth.username} | Active: {test_auth.is_active}'))
        else:
            self.stdout.write(self.style.ERROR('   ❌ Authentication test FAILED'))
        
        # Summary
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('✅ RESET COMPLETE!'))
        self.stdout.write('='*60)
        
        self.stdout.write('\n📋 Summary:')
        self.stdout.write(f'   Event: {event.name}')
        self.stdout.write(f'   Users created: {created_count}')
        self.stdout.write(f'   Users updated: {updated_count}')
        self.stdout.write(f'   Total users: {total_users}')
        self.stdout.write(f'   Role assignments: {total_assignments}')
        
        self.stdout.write('\n🔑 Login Credentials:')
        self.stdout.write('   All users have password: test123')
        self.stdout.write('\n📱 Test Users:')
        for user_data in users_data:
            self.stdout.write(f'   • {user_data["username"]:<15} → {user_data["first_name"]} {user_data["last_name"]}')
        
        self.stdout.write('\n🧪 Next Steps:')
        self.stdout.write('   1. Go to http://127.0.0.1:8000/swagger/')
        self.stdout.write('   2. POST /api/auth/login/')
        self.stdout.write('   3. Use: {"username": "organizer1", "password": "test123"}')
        self.stdout.write('   4. Should return tokens and user data\n')