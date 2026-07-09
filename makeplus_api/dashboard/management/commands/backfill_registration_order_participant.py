"""
One-off backfill: set RegistrationOrder.participant for orders created
before that field was populated at reservation time (finalize_paid_registration).
Older rows -- especially ones approved under the since-removed admin
review flow, which silently left participant unset if no matching User
existed at approval time -- have participant=None, which makes them
invisible to the caisse (all reservation lookups filter by participant).
"""
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from dashboard.models_blocs import RegistrationOrder
from events.form_validation_service import create_participant_for_event


class Command(BaseCommand):
    help = 'Backfill RegistrationOrder.participant for orders where it is still null'

    def handle(self, *args, **options):
        orphaned = RegistrationOrder.objects.filter(participant__isnull=True).exclude(email='')
        self.stdout.write(f"Found {orphaned.count()} orders with no participant set")

        fixed = 0
        skipped = 0
        for order in orphaned:
            user = User.objects.filter(email=order.email).first()
            if not user:
                self.stdout.write(self.style.WARNING(
                    f"  ! Skipped {order.id} ({order.email}) -- no matching account"
                ))
                skipped += 1
                continue

            order.participant = create_participant_for_event(user, order.event)
            order.save(update_fields=['participant'])
            self.stdout.write(self.style.SUCCESS(
                f"  + Fixed {order.id} ({order.email}) -> participant {order.participant_id}"
            ))
            fixed += 1

        self.stdout.write(f"\nFixed: {fixed}  Skipped (no account): {skipped}")
