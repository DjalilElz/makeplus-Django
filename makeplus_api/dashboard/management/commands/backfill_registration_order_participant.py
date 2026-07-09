"""
One-off backfill: set RegistrationOrder.participant for orders created
before that field was populated at reservation time (finalize_paid_registration).
Older rows -- especially ones approved under the since-removed admin
review flow, which silently left participant unset if no matching User
existed at approval time -- have participant=None, which makes them
invisible to the caisse (all reservation lookups filter by participant).

A reservation must show up at the caisse regardless of whether the
person ever opened the mobile app: if no account exists at all for the
order's email, a placeholder one (unusable password, same mechanism new
submissions already use) is created rather than skipping the order.
"""
from django.core.management.base import BaseCommand

from dashboard.models_blocs import RegistrationOrder
from events.form_validation_service import create_participant_for_event, get_or_create_user_by_email


class Command(BaseCommand):
    help = 'Backfill RegistrationOrder.participant for orders where it is still null'

    def handle(self, *args, **options):
        orphaned = RegistrationOrder.objects.filter(participant__isnull=True).exclude(email='')
        self.stdout.write(f"Found {orphaned.count()} orders with no participant set")

        fixed = 0
        for order in orphaned:
            first_name, _, last_name = order.full_name.strip().partition(' ')
            user = get_or_create_user_by_email(order.email, first_name=first_name, last_name=last_name)

            order.participant = create_participant_for_event(user, order.event)
            order.save(update_fields=['participant'])
            self.stdout.write(self.style.SUCCESS(
                f"  + Fixed {order.id} ({order.email}) -> participant {order.participant_id}"
                + ('' if user.has_usable_password() else ' (placeholder account created)')
            ))
            fixed += 1

        self.stdout.write(f"\nFixed: {fixed}")
