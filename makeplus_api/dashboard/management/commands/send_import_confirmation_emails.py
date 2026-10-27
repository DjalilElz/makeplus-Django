"""
Sends the registration confirmation email (QR code + the full summary of
what the person is registered for) to participants created by a bulk
import whose email never went out.

The import page sends these emails itself, but only while it stays open
after creation finishes -- leaving the page stopped it, and most imports
ended with every row still unsent (SARM 2026: 766 participants, none
emailed). This command catches up on any of them.

Each email is sent synchronously and its rows are marked sent ONLY once
the email provider accepted it, so the command is safe to interrupt and
re-run: nobody is emailed twice, nobody is skipped.

    python manage.py send_import_confirmation_emails --event <uuid> --dry-run
    python manage.py send_import_confirmation_emails --event <uuid> --preview-to me@example.com
    python manage.py send_import_confirmation_emails --event <uuid>
"""
import time

from django.core.management.base import BaseCommand, CommandError

from dashboard.models_import import ParticipantImportRow
from events.form_validation_service import send_registration_confirmation_email_sync
from events.models import Event


class Command(BaseCommand):
    help = "Send missing registration confirmation emails to imported participants of one event"

    def add_arguments(self, parser):
        parser.add_argument('--event', required=True, help='Event id')
        parser.add_argument('--dry-run', action='store_true', help='Only list who would be emailed')
        parser.add_argument('--limit', type=int, default=0, help='Stop after this many emails (0 = all)')
        parser.add_argument('--preview-to', default='',
                            help="Send the first pending participant's email to this address instead, "
                                 "without marking anything sent")
        parser.add_argument('--pause', type=float, default=0.2, help='Seconds between two emails')

    def handle(self, *args, **options):
        try:
            event = Event.objects.get(id=options['event'])
        except (Event.DoesNotExist, ValueError):
            raise CommandError(f"Event {options['event']} not found")

        rows = (
            ParticipantImportRow.objects
            .filter(batch__event=event, status='created', confirmation_email_sent=False,
                    participant__user__isnull=False)
            .select_related('participant__user')
            .order_by('batch__created_at', 'row_number')
        )
        # One email per person, even if they were imported by several batches.
        rows_by_user = {}
        for row in rows:
            rows_by_user.setdefault(row.participant.user_id, []).append(row)
        users = [user_rows[0].participant.user for user_rows in rows_by_user.values()]

        self.stdout.write(f"{event.name}: {len(users)} participant(s) never received their confirmation email")
        if options['dry_run']:
            for user in users[:20]:
                self.stdout.write(f"  {user.get_full_name()} <{user.email}>")
            if len(users) > 20:
                self.stdout.write(f"  ... and {len(users) - 20} more")
            return

        if options['preview_to']:
            if not users:
                return
            user = users[0]
            original_email = user.email
            user.email = options['preview_to']  # in memory only, never saved
            success, error = send_registration_confirmation_email_sync(user, event)
            user.email = original_email
            self.stdout.write(f"Preview of {user.get_full_name()}'s email sent to {options['preview_to']}: "
                              f"{'OK' if success else error}")
            return

        sent = failed = 0
        for user in users[:options['limit'] or None]:
            success, error = send_registration_confirmation_email_sync(user, event)
            if success:
                ParticipantImportRow.objects.filter(
                    id__in=[row.id for row in rows_by_user[user.id]]
                ).update(confirmation_email_sent=True)
                sent += 1
            else:
                failed += 1
                self.stderr.write(f"  FAILED {user.email}: {error}")
            if (sent + failed) % 25 == 0:
                self.stdout.write(f"  {sent + failed}/{len(users)} ({sent} sent, {failed} failed)")
            time.sleep(options['pause'])

        self.stdout.write(self.style.SUCCESS(f"Done: {sent} sent, {failed} failed"))
