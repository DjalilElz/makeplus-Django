from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from events.models import Event, Room, Session, Participant, RoomAccess, UserEventAssignment
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken

class Command(BaseCommand):
    help = 'Complete database reset - removes all events, users, and related data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirm deletion without prompting',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('\n' + '='*80))
        self.stdout.write(self.style.WARNING('⚠️  DATABASE RESET - ALL DATA WILL BE DELETED'))
        self.stdout.write(self.style.WARNING('='*80 + '\n'))
        
        if not options['confirm']:
            confirm = input('Are you sure you want to delete ALL data? Type "yes" to confirm: ')
            if confirm.lower() != 'yes':
                self.stdout.write(self.style.ERROR('❌ Reset cancelled'))
                return
        
        self.stdout.write(self.style.WARNING('\n🗑️  Starting database cleanup...\n'))
        
        # Delete in correct order to avoid foreign key issues
        models_to_delete = [
            ('Room Access Records', RoomAccess),
            ('Participants', Participant),
            ('Sessions', Session),
            ('Rooms', Room),
            ('User Event Assignments', UserEventAssignment),
            ('Events', Event),
            ('Blacklisted Tokens', BlacklistedToken),
            ('Outstanding Tokens', OutstandingToken),
            ('Users (non-superuser)', None),  # Special handling
        ]
        
        for model_name, model in models_to_delete:
            if model is None:
                # Delete non-superuser users
                deleted_count = User.objects.filter(is_superuser=False).delete()[0]
            else:
                deleted_count = model.objects.all().delete()[0]
            
            if deleted_count > 0:
                self.stdout.write(self.style.SUCCESS(f'   ✅ Deleted {deleted_count} {model_name}'))
            else:
                self.stdout.write(f'   ⚪ No {model_name} to delete')
        
        self.stdout.write(self.style.SUCCESS('\n' + '='*80))
        self.stdout.write(self.style.SUCCESS('✅ DATABASE RESET COMPLETE'))
        self.stdout.write(self.style.SUCCESS('='*80))
        self.stdout.write(self.style.SUCCESS('\n💡 Run "python manage.py create_multi_event_data" to create test data\n'))