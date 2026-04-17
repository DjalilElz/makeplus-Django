from django.core.management.base import BaseCommand
from events.models import UserEventAssignment
from dashboard.models_eposter import EPosterCommitteeMember


class Command(BaseCommand):
    help = 'Fix existing committee users by creating EPosterCommitteeMember records'

    def handle(self, *args, **options):
        # Find all committee role assignments
        committee_assignments = UserEventAssignment.objects.filter(
            role='committee',
            is_active=True
        ).select_related('user', 'event')

        self.stdout.write(f'Found {committee_assignments.count()} committee assignments')

        created_count = 0
        already_exists_count = 0

        for assignment in committee_assignments:
            # Check if EPosterCommitteeMember already exists
            existing = EPosterCommitteeMember.objects.filter(
                user=assignment.user,
                event=assignment.event
            ).first()

            if existing:
                self.stdout.write(
                    self.style.WARNING(
                        f'  ⚠ Already exists: {assignment.user.get_full_name()} - {assignment.event.name}'
                    )
                )
                already_exists_count += 1
            else:
                # Create EPosterCommitteeMember
                EPosterCommitteeMember.objects.create(
                    user=assignment.user,
                    event=assignment.event,
                    role='member',
                    is_active=True,
                    assigned_by=assignment.assigned_by
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f'  ✓ Created: {assignment.user.get_full_name()} - {assignment.event.name}'
                    )
                )
                created_count += 1

        self.stdout.write(self.style.SUCCESS(f'\n=== SUMMARY ==='))
        self.stdout.write(f'Created: {created_count}')
        self.stdout.write(f'Already existed: {already_exists_count}')
        self.stdout.write(f'Total: {committee_assignments.count()}')
