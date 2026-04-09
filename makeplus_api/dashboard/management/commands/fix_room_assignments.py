"""
Management command to fix missing room assignments in UserEventAssignment metadata
Usage: python manage.py fix_room_assignments
"""

from django.core.management.base import BaseCommand
from events.models import UserEventAssignment, Room
import uuid


class Command(BaseCommand):
    help = 'Fix missing room assignments in UserEventAssignment metadata'

    def add_arguments(self, parser):
        parser.add_argument(
            '--assignment-id',
            type=str,
            help='Specific assignment ID to fix',
        )
        parser.add_argument(
            '--room-id',
            type=str,
            help='Room UUID to assign',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes',
        )

    def handle(self, *args, **options):
        assignment_id = options.get('assignment_id')
        room_id = options.get('room_id')
        dry_run = options.get('dry_run', False)

        if assignment_id and room_id:
            # Fix specific assignment
            self.fix_specific_assignment(assignment_id, room_id, dry_run)
        else:
            # List all assignments that could have room assignments but don't
            self.list_missing_assignments()

    def fix_specific_assignment(self, assignment_id, room_id, dry_run):
        """Fix a specific assignment by ID"""
        try:
            assignment = UserEventAssignment.objects.get(id=assignment_id)
        except UserEventAssignment.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Assignment with ID {assignment_id} not found'))
            return

        # Verify room exists and belongs to the same event
        try:
            room = Room.objects.get(id=room_id)
        except Room.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Room with ID {room_id} not found'))
            return

        if room.event_id != assignment.event_id:
            self.stdout.write(self.style.ERROR(
                f'Room {room.name} does not belong to event {assignment.event.name}'
            ))
            return

        # Check if role is eligible for room assignment
        if assignment.role not in ['organisateur', 'gestionnaire_des_salles', 'controlleur_des_badges']:
            self.stdout.write(self.style.WARNING(
                f'Role {assignment.role} does not typically require room assignment'
            ))

        # Update metadata
        if dry_run:
            self.stdout.write(self.style.WARNING('[DRY RUN] Would update:'))
        
        self.stdout.write(f'Assignment ID: {assignment.id}')
        self.stdout.write(f'User: {assignment.user.get_full_name()} ({assignment.user.email})')
        self.stdout.write(f'Event: {assignment.event.name}')
        self.stdout.write(f'Role: {assignment.role}')
        self.stdout.write(f'Room: {room.name} (ID: {room.id})')
        
        if not dry_run:
            assignment.metadata = assignment.metadata or {}
            assignment.metadata['assigned_room_id'] = str(room.id)
            assignment.save()
            self.stdout.write(self.style.SUCCESS('✓ Room assignment updated successfully!'))
        else:
            self.stdout.write(self.style.WARNING('Run without --dry-run to apply changes'))

    def list_missing_assignments(self):
        """List all assignments that could have rooms but don't"""
        roles_with_rooms = ['organisateur', 'gestionnaire_des_salles', 'controlleur_des_badges']
        
        # Get all assignments with roles that can have room assignments
        assignments = UserEventAssignment.objects.filter(
            role__in=roles_with_rooms
        ).select_related('user', 'event')

        missing = []
        has_assignment = []

        for assignment in assignments:
            room_id = assignment.metadata.get('assigned_room_id') if assignment.metadata else None
            
            if not room_id:
                missing.append(assignment)
            else:
                has_assignment.append((assignment, room_id))

        # Display results
        self.stdout.write(self.style.SUCCESS(f'\n=== Room Assignment Status ===\n'))
        
        if has_assignment:
            self.stdout.write(self.style.SUCCESS(f'✓ {len(has_assignment)} assignment(s) with rooms:'))
            for assignment, room_id in has_assignment:
                try:
                    room = Room.objects.get(id=room_id)
                    self.stdout.write(f'  - {assignment.user.email} → {room.name} (Event: {assignment.event.name})')
                except Room.DoesNotExist:
                    self.stdout.write(self.style.ERROR(f'  - {assignment.user.email} → INVALID ROOM ID: {room_id}'))

        if missing:
            self.stdout.write(self.style.WARNING(f'\n⚠ {len(missing)} assignment(s) WITHOUT rooms:'))
            for assignment in missing:
                self.stdout.write(f'\n  Assignment ID: {assignment.id}')
                self.stdout.write(f'  User: {assignment.user.get_full_name()} ({assignment.user.email})')
                self.stdout.write(f'  Event: {assignment.event.name} (ID: {assignment.event.id})')
                self.stdout.write(f'  Role: {assignment.role}')
                
                # Show available rooms for this event
                rooms = Room.objects.filter(event=assignment.event)
                if rooms:
                    self.stdout.write(f'  Available rooms:')
                    for room in rooms:
                        self.stdout.write(f'    - {room.name} (ID: {room.id})')
                else:
                    self.stdout.write(self.style.ERROR('    No rooms available for this event'))
                
                self.stdout.write(f'\n  To fix: python manage.py fix_room_assignments --assignment-id {assignment.id} --room-id <room-uuid>')

        if not missing and not has_assignment:
            self.stdout.write(self.style.WARNING('No assignments found with eligible roles'))
