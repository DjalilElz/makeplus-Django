"""
One-off backfill: mark every participant who already has at least one
completed caisse transaction for an event, but isn't marked present yet,
as present.

Root cause (fixed going forward in caisse.views.process_transaction,
which now calls _mark_participant_present on every completed
transaction): the caisse only started setting
events.ParticipantEventRegistration.is_checked_in/checked_in_at as a
side effect of a transaction recently. Anyone who transacted at a caisse
before that fix went live has a real completed CaisseTransaction but was
never marked present, so they're invisible on the event Stats page's
Présence tab and undercounted in its "participants présents" figure even
though they genuinely showed up.

checked_in_at is set to that participant's EARLIEST completed
transaction time for this event (not "now") -- the real moment they
first showed up, not an artificial mass check-in at whatever time this
command happens to run.

ALWAYS run with --dry-run first and review the output before running for
real.
"""
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Min

from caisse.models import CaisseTransaction
from events.models import Event, ParticipantEventRegistration


class Command(BaseCommand):
    help = (
        "Mark participants with a completed caisse transaction for an "
        "event, but not yet marked present, as present"
    )

    def add_arguments(self, parser):
        parser.add_argument('event_id', type=str, help="UUID of the event to backfill")
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Show what would change without writing anything',
        )

    def handle(self, *args, **options):
        event_id = options['event_id']
        dry_run = options['dry_run']

        try:
            event = Event.objects.get(id=event_id)
        except Event.DoesNotExist:
            raise CommandError(f"No event found with id {event_id!r}")
        except ValueError as exc:
            raise CommandError(f"Invalid event id {event_id!r}: {exc}")

        earliest_by_participant = dict(
            CaisseTransaction.objects.filter(caisse__event=event, status='completed')
            .values('participant_id')
            .annotate(earliest=Min('created_at'))
            .values_list('participant_id', 'earliest')
        )

        if not earliest_by_participant:
            self.stdout.write("No completed caisse transactions found for this event.")
            return

        registrations = ParticipantEventRegistration.objects.filter(
            event=event,
            participant_id__in=earliest_by_participant.keys(),
            is_checked_in=False,
        ).select_related('participant__user')

        if not registrations:
            self.stdout.write(self.style.SUCCESS(
                "Nothing to backfill -- everyone with a completed transaction is already marked present."
            ))
            return

        updated = 0
        for reg in registrations:
            checked_in_at = earliest_by_participant[reg.participant_id]
            if dry_run:
                self.stdout.write(
                    f"  [DRY RUN] Would mark present: {reg.participant.user.email} "
                    f"(first transaction at {checked_in_at})"
                )
            else:
                reg.is_checked_in = True
                reg.checked_in_at = checked_in_at
                reg.save(update_fields=['is_checked_in', 'checked_in_at'])
                self.stdout.write(f"  + Marked present: {reg.participant.user.email} (at {checked_in_at})")
            updated += 1

        verb = 'Would mark' if dry_run else 'Marked'
        self.stdout.write(self.style.SUCCESS(f"\n{verb} present: {updated}"))
