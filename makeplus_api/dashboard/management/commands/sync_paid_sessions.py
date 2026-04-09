"""
Management command to sync paid sessions to payable items
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from events.models import Event, Session
from caisse.models import PayableItem


class Command(BaseCommand):
    help = 'Sync paid sessions to payable items for caisse'

    def add_arguments(self, parser):
        parser.add_argument(
            '--event',
            type=str,
            help='Event ID to sync (optional, syncs all events if not provided)',
        )

    def handle(self, *args, **options):
        event_id = options.get('event')
        
        if event_id:
            try:
                events = [Event.objects.get(id=event_id)]
                self.stdout.write(f"Syncing paid sessions for event: {events[0].name}")
            except Event.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Event with ID {event_id} not found"))
                return
        else:
            events = Event.objects.all()
            self.stdout.write(f"Syncing paid sessions for all {events.count()} events")
        
        total_created = 0
        total_updated = 0
        total_deactivated = 0
        
        for event in events:
            self.stdout.write(f"\n{'='*60}")
            self.stdout.write(f"Event: {event.name}")
            self.stdout.write(f"{'='*60}")
            
            # Get all paid sessions for this event
            paid_sessions = Session.objects.filter(
                event=event,
                is_paid=True,
                price__gt=0
            )
            
            self.stdout.write(f"Found {paid_sessions.count()} paid sessions")
            
            with transaction.atomic():
                # Track which sessions we've processed
                processed_session_ids = []
                
                for session in paid_sessions:
                    # Check if payable item already exists for this session
                    payable_item, created = PayableItem.objects.get_or_create(
                        event=event,
                        session=session,
                        defaults={
                            'name': f"{session.get_session_type_display()} - {session.title}",
                            'description': session.description or f"{session.speaker_name} - {session.start_time.strftime('%d/%m/%Y %H:%M')}",
                            'price': session.price,
                            'item_type': 'session',
                            'is_active': True
                        }
                    )
                    
                    if created:
                        total_created += 1
                        self.stdout.write(
                            self.style.SUCCESS(f"  ✓ Created: {payable_item.name} - {payable_item.price} DA")
                        )
                    else:
                        # Update existing item if price or name changed
                        updated = False
                        new_name = f"{session.get_session_type_display()} - {session.title}"
                        
                        if payable_item.name != new_name:
                            payable_item.name = new_name
                            updated = True
                        
                        if payable_item.price != session.price:
                            payable_item.price = session.price
                            updated = True
                        
                        if payable_item.description != session.description:
                            payable_item.description = session.description or f"{session.speaker_name} - {session.start_time.strftime('%d/%m/%Y %H:%M')}"
                            updated = True
                        
                        if not payable_item.is_active:
                            payable_item.is_active = True
                            updated = True
                        
                        if updated:
                            payable_item.save()
                            total_updated += 1
                            self.stdout.write(
                                self.style.WARNING(f"  ↻ Updated: {payable_item.name} - {payable_item.price} DA")
                            )
                    
                    processed_session_ids.append(session.id)
                
                # Deactivate payable items for sessions that are no longer paid or don't exist
                orphaned_items = PayableItem.objects.filter(
                    event=event,
                    item_type='session',
                    session__isnull=False,
                    is_active=True
                ).exclude(session_id__in=processed_session_ids)
                
                if orphaned_items.exists():
                    count = orphaned_items.count()
                    orphaned_items.update(is_active=False)
                    total_deactivated += count
                    self.stdout.write(
                        self.style.WARNING(f"  ⚠ Deactivated {count} orphaned items")
                    )
        
        self.stdout.write(f"\n{'='*60}")
        self.stdout.write(self.style.SUCCESS("SYNC COMPLETE"))
        self.stdout.write(f"{'='*60}")
        self.stdout.write(f"Created: {total_created}")
        self.stdout.write(f"Updated: {total_updated}")
        self.stdout.write(f"Deactivated: {total_deactivated}")
        self.stdout.write(f"{'='*60}\n")
