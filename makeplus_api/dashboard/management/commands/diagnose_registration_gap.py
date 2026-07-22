"""
Read-only diagnostic: explains the gap between the RegistrationOrder count
shown on the event-owner submissions page and the caisse dashboard's
participant count for an event. Makes NO changes to the database -- safe
to run directly against production.

Usage:
    python manage.py diagnose_registration_gap                  # every event
    python manage.py diagnose_registration_gap <event id>
    python manage.py diagnose_registration_gap "name substring"
"""
from collections import Counter

from django.core.management.base import BaseCommand
from django.db.models import Q

from dashboard.models_blocs import RegistrationOrder
from events.models import Event, ParticipantEventRegistration, UserEventAssignment


class Command(BaseCommand):
    help = 'Read-only: explain the gap between RegistrationOrder count and caisse participant count for an event'

    def add_arguments(self, parser):
        parser.add_argument(
            'event', nargs='?', default=None,
            help='Event id (UUID) or a name substring; omit to check every event',
        )

    def handle(self, *args, **options):
        query = options['event']
        if query:
            events = Event.objects.filter(Q(id=query) | Q(name__icontains=query))
            if not events.exists():
                self.stdout.write(self.style.ERROR(f"No event matches '{query}'"))
                return
        else:
            events = Event.objects.all()

        for event in events:
            self._report(event)

    def _report(self, event):
        orders = RegistrationOrder.objects.filter(event=event)
        total_orders = orders.count()
        if total_orders == 0:
            return

        null_participant_count = orders.filter(participant__isnull=True).count()

        orders_with_participant = orders.exclude(participant__isnull=True)
        unique_participants_from_orders = orders_with_participant.values('participant_id').distinct().count()

        # Same email appearing on more than one order for this event.
        email_counts = Counter(
            (e or '').strip().lower()
            for e in orders.exclude(email='').values_list('email', flat=True)
        )
        duplicate_emails = {email: count for email, count in email_counts.items() if count > 1}
        orders_from_duplicate_emails = sum(duplicate_emails.values())

        # What the caisse dashboard actually counts (caisse/views.py::caisse_dashboard).
        participant_user_ids = set(
            UserEventAssignment.objects.filter(event=event, role='participant').values_list('user_id', flat=True)
        )
        caisse_participant_count = ParticipantEventRegistration.objects.filter(
            event=event, participant__user_id__in=participant_user_ids
        ).count()

        # A participant linked to an order, but with no 'participant'-role
        # UserEventAssignment for this event -- e.g. they already hold a
        # different role for this event (UserEventAssignment is unique on
        # (user, event), so get_or_create('participant') never adds a
        # second row). These orders exist and have a participant, but are
        # still invisible to the caisse's role='participant' filter.
        order_participant_user_ids = set(
            orders_with_participant.values_list('participant__user_id', flat=True)
        )
        missing_participant_role = order_participant_user_ids - participant_user_ids

        self.stdout.write(self.style.MIGRATE_HEADING(f"\n{event.name} ({event.id})"))
        self.stdout.write(f"  RegistrationOrder rows (all statuses):          {total_orders}")
        self.stdout.write(f"    -- with participant=null (invisible to caisse): {null_participant_count}")
        self.stdout.write(f"    -- unique participants among the rest:          {unique_participants_from_orders}")
        self.stdout.write(f"  Caisse dashboard participant count:             {caisse_participant_count}")
        self.stdout.write(
            f"  Orders sharing an email with >=1 other order:   {orders_from_duplicate_emails} "
            f"(across {len(duplicate_emails)} distinct emails)"
        )
        self.stdout.write(
            f"  Has an order+participant but no 'participant' role for this event: {len(missing_participant_role)}"
        )
        if duplicate_emails:
            top = sorted(duplicate_emails.items(), key=lambda kv: -kv[1])[:10]
            self.stdout.write("  Top duplicate emails (email: order count):")
            for email, count in top:
                self.stdout.write(f"    {email}: {count}")
