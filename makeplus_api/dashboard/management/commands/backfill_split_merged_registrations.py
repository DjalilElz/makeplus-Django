"""
One-off backfill: split apart RegistrationOrders that got silently merged
into someone else's account because they shared an email but were
genuinely different people.

Root cause (fixed going forward in events.form_validation_service.
get_or_create_user_for_manual_registration, used by the event owner's
"Nouvelle inscription" page): the account for a submission used to be
looked up by email alone. When many different real attendees were
registered under one shared/placeholder email (a sponsor's guest list,
a receptionist's inbox for walk-ins without their own email), every
registration after the first silently reused whichever account/badge
was created by the first one. The order itself still stored each
person's own name correctly (why they looked fine in the event owner's
Submissions list) -- but the underlying account/Participant/badge that
caisse actually searches and displays never got it.

This command finds every RegistrationOrder whose stored full_name
doesn't match the name on the account it's linked to, and gives it its
own brand-new User/Participant/UserEventAssignment/
ParticipantEventRegistration (reusing the same email) -- exactly what
would have happened had the order been created after the fix. The one
order per merged cluster whose name DOES already match the account
(whoever the merge happened to keep) is left untouched.

ALWAYS run with --dry-run first and review the output before running
for real -- this creates new accounts/badges for a lot of rows on
events with large shared-email clusters.
"""
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import IntegrityError, transaction

from dashboard.models_blocs import RegistrationOrder
from events.form_validation_service import create_participant_for_event


def _normalize(name):
    return ' '.join((name or '').split()).strip().lower()


def _names_match(order_full_name, user):
    user_full_name = f"{user.first_name} {user.last_name}"
    return _normalize(order_full_name) == _normalize(user_full_name)


def _next_available_email(email):
    """
    auth_user.email has a real DB-level unique constraint in this
    database (discovered the hard way -- get_or_create_user_by_email/
    get_or_create_user_for_manual_registration never needed to care
    since they always look an existing email up first). A split-off
    account can never reuse the bare email -- by definition it's
    already taken by the account being split away from -- so this
    finds the first free +tag variant instead (local+dup2@domain,
    local+dup3@domain, ...), standard subaddressing that Gmail/Outlook/
    Yahoo/iCloud and most modern providers deliver to the same inbox
    as the plain address.
    """
    local, _, domain = email.partition('@')
    if not domain:
        domain = 'invalid.local'
    candidate = f'{local}@{domain}'
    n = 2
    while User.objects.filter(email__iexact=candidate).exists():
        candidate = f'{local}+dup{n}@{domain}'
        n += 1
    return candidate


class Command(BaseCommand):
    help = "Split RegistrationOrders that were silently merged into another account sharing the same email"

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Show what would change without writing anything',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        candidates = RegistrationOrder.objects.exclude(participant__isnull=True).select_related(
            'participant__user', 'event',
        ).order_by('created_at')

        mismatched = [
            order for order in candidates
            if order.full_name and order.email and not _names_match(order.full_name, order.participant.user)
        ]

        self.stdout.write(f"Found {len(mismatched)} orders whose stored name doesn't match their linked account\n")

        if dry_run:
            for order in mismatched:
                self.stdout.write(
                    f"  [DRY RUN] Would split order {order.id} ({order.email!r}, {order.full_name!r}) "
                    f"off of account user_id={order.participant.user_id} "
                    f"({order.participant.user.get_full_name()!r})"
                )
            self.stdout.write(self.style.WARNING(f"\nDry run only -- {len(mismatched)} orders would be split. No changes made."))
            return

        fixed = 0
        failed = 0
        for order in mismatched:
            first_name, _, last_name = order.full_name.strip().partition(' ')

            try:
                with transaction.atomic():
                    new_email = _next_available_email(order.email)

                    username_base = new_email.split('@')[0]
                    username = username_base
                    counter = 1
                    while User.objects.filter(username=username).exists():
                        username = f"{username_base}{counter}"
                        counter += 1

                    new_user = User.objects.create(
                        username=username, email=new_email,
                        first_name=first_name, last_name=last_name,
                    )
                    new_user.set_unusable_password()
                    new_user.save(update_fields=['password'])

                    new_participant = create_participant_for_event(new_user, order.event)
                    order.participant = new_participant
                    order.save(update_fields=['participant'])
            except IntegrityError as exc:
                # One bad/edge-case row (e.g. a race on the email/username
                # we just checked) must not take down the whole batch --
                # the atomic block above already rolled that one row back
                # cleanly, so it's safe to just log and move on.
                self.stdout.write(self.style.ERROR(f"  ! Failed to split order {order.id} ({order.email}): {exc}"))
                failed += 1
                continue

            note = f" (email changed to {new_email})" if new_email != order.email else ""
            self.stdout.write(self.style.SUCCESS(
                f"  + Split order {order.id} ({order.email}) -> new participant {new_participant.id} "
                f"(badge {new_participant.badge_id}, user_id={new_user.id}){note}"
            ))
            fixed += 1

        self.stdout.write(f"\nFixed: {fixed}" + (f" | Failed: {failed}" if failed else ""))
