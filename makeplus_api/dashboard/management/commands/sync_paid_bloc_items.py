"""
Management command to sync registration bloc items (status/restauration/
social_event) to payable items for caisse, mirroring sync_paid_sessions.py.
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from events.models import Event
from dashboard.models_blocs import BlocItem
from caisse.models import PayableItem


class Command(BaseCommand):
    help = 'Sync active registration bloc items to payable items for caisse'

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
                self.stdout.write(f"Syncing bloc items for event: {events[0].name}")
            except Event.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Event with ID {event_id} not found"))
                return
        else:
            events = Event.objects.all()
            self.stdout.write(f"Syncing bloc items for all {events.count()} events")

        total_created = 0
        total_updated = 0
        total_deactivated = 0

        for event in events:
            self.stdout.write(f"\n{'='*60}")
            self.stdout.write(f"Event: {event.name}")
            self.stdout.write(f"{'='*60}")

            active_bloc_items = BlocItem.objects.filter(event=event, is_active=True)
            self.stdout.write(f"Found {active_bloc_items.count()} active bloc items")

            with transaction.atomic():
                processed_bloc_item_ids = []

                for bloc_item in active_bloc_items:
                    new_name = f"{bloc_item.get_bloc_display()} - {bloc_item.name}"
                    payable_item, created = PayableItem.objects.get_or_create(
                        event=event,
                        bloc_item=bloc_item,
                        defaults={
                            'name': new_name,
                            'price': bloc_item.price,
                            'item_type': 'bloc',
                            'is_active': True,
                        }
                    )

                    if created:
                        total_created += 1
                        self.stdout.write(
                            self.style.SUCCESS(f"  + Created: {payable_item.name} - {payable_item.price} DA")
                        )
                    else:
                        updated = False
                        if payable_item.name != new_name:
                            payable_item.name = new_name
                            updated = True
                        if payable_item.price != bloc_item.price:
                            payable_item.price = bloc_item.price
                            updated = True
                        if not payable_item.is_active:
                            payable_item.is_active = True
                            updated = True

                        if updated:
                            payable_item.save()
                            total_updated += 1
                            self.stdout.write(
                                self.style.WARNING(f"  ~ Updated: {payable_item.name} - {payable_item.price} DA")
                            )

                    processed_bloc_item_ids.append(bloc_item.id)

                # Deactivate payable items for bloc items that are no longer active/exist.
                orphaned_items = PayableItem.objects.filter(
                    event=event,
                    item_type='bloc',
                    bloc_item__isnull=False,
                    is_active=True
                ).exclude(bloc_item_id__in=processed_bloc_item_ids)

                if orphaned_items.exists():
                    count = orphaned_items.count()
                    orphaned_items.update(is_active=False)
                    total_deactivated += count
                    self.stdout.write(
                        self.style.WARNING(f"  ! Deactivated {count} orphaned items")
                    )

        self.stdout.write(f"\n{'='*60}")
        self.stdout.write(self.style.SUCCESS("SYNC COMPLETE"))
        self.stdout.write(f"{'='*60}")
        self.stdout.write(f"Created: {total_created}")
        self.stdout.write(f"Updated: {total_updated}")
        self.stdout.write(f"Deactivated: {total_deactivated}")
        self.stdout.write(f"{'='*60}\n")
