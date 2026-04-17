from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from events.models import (
    Event, Participant, Session, Room, UserEventAssignment, 
    RoomAccess, SessionAccess, Annonce, SessionQuestion, 
    RoomAssignment, ExposantScan, EventRegistration, EmailLoginCode
)
from caisse.models import Caisse, PayableItem, CaisseTransaction
from dashboard.models_email import EmailTemplate, EventEmailTemplate, EmailLog
from dashboard.models_eposter import EPosterSubmission, EPosterValidation, EPosterCommitteeMember, EPosterEmailTemplate

User = get_user_model()


class Command(BaseCommand):
    help = 'Clean database and keep only admin user'

    def add_arguments(self, parser):
        parser.add_argument(
            '--admin-username',
            type=str,
            default='admin',
            help='Username of the admin to keep (default: admin)'
        )
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirm deletion without prompting'
        )

    def handle(self, *args, **options):
        admin_username = options['admin_username']
        confirm = options['confirm']

        # Check if admin exists
        try:
            admin_user = User.objects.get(username=admin_username)
            self.stdout.write(self.style.SUCCESS(f'Found admin user: {admin_username}'))
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Admin user "{admin_username}" not found!'))
            return

        # Count records to be deleted
        users_count = User.objects.exclude(username=admin_username).count()
        events_count = Event.objects.count()
        participants_count = Participant.objects.count()
        sessions_count = Session.objects.count()
        rooms_count = Room.objects.count()
        transactions_count = CaisseTransaction.objects.count()
        caisses_count = Caisse.objects.count()
        email_logs_count = EmailLog.objects.count()
        eposter_submissions_count = EPosterSubmission.objects.count()
        eposter_validations_count = EPosterValidation.objects.count()
        registrations_count = EventRegistration.objects.count()

        self.stdout.write(self.style.WARNING('\n=== DATABASE CLEANUP SUMMARY ==='))
        self.stdout.write(f'Users to delete: {users_count}')
        self.stdout.write(f'Events to delete: {events_count}')
        self.stdout.write(f'Participants to delete: {participants_count}')
        self.stdout.write(f'Sessions to delete: {sessions_count}')
        self.stdout.write(f'Rooms to delete: {rooms_count}')
        self.stdout.write(f'Transactions to delete: {transactions_count}')
        self.stdout.write(f'Caisses to delete: {caisses_count}')
        self.stdout.write(f'Email logs to delete: {email_logs_count}')
        self.stdout.write(f'ePoster submissions to delete: {eposter_submissions_count}')
        self.stdout.write(f'ePoster validations to delete: {eposter_validations_count}')
        self.stdout.write(f'Event registrations to delete: {registrations_count}')
        self.stdout.write(f'\nAdmin user to KEEP: {admin_username}\n')

        if not confirm:
            response = input('Are you sure you want to delete all this data? Type "yes" to confirm: ')
            if response.lower() != 'yes':
                self.stdout.write(self.style.WARNING('Operation cancelled.'))
                return

        # Delete data
        self.stdout.write(self.style.WARNING('\nDeleting data...'))

        # Delete in order to respect foreign key constraints
        deleted_counts = {}

        deleted_counts['EPosterValidation'] = EPosterValidation.objects.all().delete()[0]
        deleted_counts['EPosterSubmission'] = EPosterSubmission.objects.all().delete()[0]
        deleted_counts['EPosterCommitteeMember'] = EPosterCommitteeMember.objects.all().delete()[0]
        deleted_counts['EPosterEmailTemplate'] = EPosterEmailTemplate.objects.all().delete()[0]
        deleted_counts['EmailLog'] = EmailLog.objects.all().delete()[0]
        deleted_counts['EventEmailTemplate'] = EventEmailTemplate.objects.all().delete()[0]
        deleted_counts['EmailTemplate'] = EmailTemplate.objects.all().delete()[0]
        deleted_counts['CaisseTransaction'] = CaisseTransaction.objects.all().delete()[0]
        deleted_counts['Caisse'] = Caisse.objects.all().delete()[0]
        deleted_counts['PayableItem'] = PayableItem.objects.all().delete()[0]
        deleted_counts['ExposantScan'] = ExposantScan.objects.all().delete()[0]
        deleted_counts['RoomAssignment'] = RoomAssignment.objects.all().delete()[0]
        deleted_counts['SessionQuestion'] = SessionQuestion.objects.all().delete()[0]
        deleted_counts['Annonce'] = Annonce.objects.all().delete()[0]
        deleted_counts['SessionAccess'] = SessionAccess.objects.all().delete()[0]
        deleted_counts['RoomAccess'] = RoomAccess.objects.all().delete()[0]
        deleted_counts['Participant'] = Participant.objects.all().delete()[0]
        deleted_counts['EventRegistration'] = EventRegistration.objects.all().delete()[0]
        deleted_counts['Session'] = Session.objects.all().delete()[0]
        deleted_counts['Room'] = Room.objects.all().delete()[0]
        deleted_counts['UserEventAssignment'] = UserEventAssignment.objects.all().delete()[0]
        deleted_counts['Event'] = Event.objects.all().delete()[0]
        deleted_counts['EmailLoginCode'] = EmailLoginCode.objects.all().delete()[0]
        deleted_counts['User'] = User.objects.exclude(username=admin_username).delete()[0]

        self.stdout.write(self.style.SUCCESS('\n=== DELETION COMPLETE ==='))
        for model, count in deleted_counts.items():
            self.stdout.write(f'{model}: {count} deleted')

        self.stdout.write(self.style.SUCCESS(f'\n✓ Database cleaned! Only admin user "{admin_username}" remains.'))
