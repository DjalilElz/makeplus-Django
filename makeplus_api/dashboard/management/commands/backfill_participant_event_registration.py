"""
One-off backfill: restore ParticipantEventRegistration (and reactivate a
deactivated UserEventAssignment role='participant') for participants who
still have a live RegistrationOrder for an event but lost their event-
registration link.

Root cause (now fixed in dashboard/views_event_owner.py::registration_delete):
that view used to revoke a participant's event access whenever ANY of
their orders was deleted -- even if they had another, still-valid order
for the same event (a real, common case: duplicate-email resubmissions,
see diagnose_registration_gap). Deleting one duplicate silently made the
participant invisible to the caisse even though their remaining order
was untouched. This repairs the accounts already affected by that.

Read the report first with --dry-run before running for real.
"""
from django.core.management.base import BaseCommand

from dashboard.models_blocs import RegistrationOrder
from events.models import ParticipantEventRegistration, UserEventAssignment


class Command(BaseCommand):
    help = 'Backfill ParticipantEventRegistration/UserEventAssignment for participants with a live order but no event-registration link'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Report what would change without writing anything',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        orders_with_participant = RegistrationOrder.objects.exclude(
            participant__isnull=True
        ).select_related('participant__user', 'event')

        # One (event, participant) pair per group -- a participant with
        # several orders for the same event only needs fixing once.
        seen = set()
        fixed = 0

        for order in orders_with_participant:
            key = (order.event_id, order.participant_id)
            if key in seen:
                continue
            seen.add(key)

            participant = order.participant
            event = order.event

            reg_exists = ParticipantEventRegistration.objects.filter(
                event=event, participant=participant
            ).exists()
            assignment = UserEventAssignment.objects.filter(
                user=participant.user, event=event, role='participant'
            ).first()

            needs_reg = not reg_exists
            needs_assignment = assignment is None
            needs_reactivate = assignment is not None and not assignment.is_active

            if not (needs_reg or needs_assignment or needs_reactivate):
                continue

            fixed += 1
            self.stdout.write(
                f"{event.name} ({event.id}) / {participant.user.email} ({participant.id}): "
                f"registration={'missing' if needs_reg else 'ok'}, "
                f"role={'missing' if needs_assignment else ('inactive' if needs_reactivate else 'ok')}"
            )

            if dry_run:
                continue

            if needs_reg:
                ParticipantEventRegistration.objects.get_or_create(event=event, participant=participant)
            if needs_assignment:
                UserEventAssignment.objects.get_or_create(
                    user=participant.user, event=event, defaults={'role': 'participant'}
                )
            elif needs_reactivate:
                assignment.is_active = True
                assignment.save(update_fields=['is_active'])

        self.stdout.write(self.style.SUCCESS(
            f"\n{'Would fix' if dry_run else 'Fixed'}: {fixed} participant(s)"
        ))
