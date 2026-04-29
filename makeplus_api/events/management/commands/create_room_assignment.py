"""
Management command to create room assignment for gestionaire1
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from makeplus_api.events.models import RoomAssignment, Room, Event
from django.utils import timezone
from datetime import timedelta


class Command(BaseCommand):
    help = 'Create room assignment for gestionaire1@wemakeplus.com'

    def handle(self, *args, **options):
        try:
            # Get the user
            user = User.objects.get(email='gestionaire1@wemakeplus.com')
            self.stdout.write(f"Found user: {user.email} (ID: {user.id})")
            
            # Get the event
            event = Event.objects.get(name='TechSummit Algeria 2026')
            self.stdout.write(f"Found event: {event.name} (ID: {event.id})")
            
            # Get the room "salle A"
            room = Room.objects.filter(event=event, name__icontains='salle A').first()
            if not room:
                # Try to find any room
                room = Room.objects.filter(event=event).first()
            
            if not room:
                self.stdout.write(self.style.ERROR('No room found for this event!'))
                return
            
            self.stdout.write(f"Found room: {room.name} (ID: {room.id})")
            
            # Check if assignment already exists
            existing = RoomAssignment.objects.filter(
                user=user,
                event=event,
                room=room
            ).first()
            
            if existing:
                self.stdout.write(self.style.WARNING(f'Room assignment already exists (ID: {existing.id})'))
                self.stdout.write(f'  Room: {existing.room.name}')
                self.stdout.write(f'  Active: {existing.is_active}')
                self.stdout.write(f'  Start: {existing.start_time}')
                self.stdout.write(f'  End: {existing.end_time}')
                
                # Update it to be active
                existing.is_active = True
                existing.save()
                self.stdout.write(self.style.SUCCESS('Updated existing assignment to active'))
                return
            
            # Create new room assignment
            assignment = RoomAssignment.objects.create(
                user=user,
                room=room,
                event=event,
                role='gestionnaire_des_salles',
                start_time=event.start_date,
                end_time=event.end_date,
                is_active=True,
                assigned_by=User.objects.filter(is_superuser=True).first()
            )
            
            self.stdout.write(self.style.SUCCESS(f'Successfully created room assignment (ID: {assignment.id})'))
            self.stdout.write(f'  User: {user.email}')
            self.stdout.write(f'  Room: {room.name}')
            self.stdout.write(f'  Event: {event.name}')
            self.stdout.write(f'  Role: {assignment.role}')
            self.stdout.write(f'  Active: {assignment.is_active}')
            
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR('User gestionaire1@wemakeplus.com not found!'))
        except Event.DoesNotExist:
            self.stdout.write(self.style.ERROR('Event TechSummit Algeria 2026 not found!'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))
