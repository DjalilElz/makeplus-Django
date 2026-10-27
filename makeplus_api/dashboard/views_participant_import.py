"""
Bulk participant import views: download an event-specific Excel
template, upload a filled copy for validation/preview, then confirm to
actually create the registrations in small batches (same two-phase
pattern as attestation_send/campaign_send, so a large file can't time
out a single request).
"""
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.cache import never_cache

from events.models import Event
from .models_import import ParticipantImportBatch, ParticipantImportRow
from .participant_import_service import (
    build_import_columns, generate_import_template_workbook, create_import_batch, process_import_row,
    send_pending_confirmation_emails,
)
from .views_blocs import get_public_bloc_context
from .views_event_owner import _can_access_event_orders, _redirect_to_submissions

# Row creation is pure DB work (no network calls), but each row is still
# several queries deep (user/participant lookups, a FormSubmission,
# compute_order's pricing lookups when the event has blocs) and every one
# of those queries is a real network round-trip to Postgres -- at
# 10/request, observed in production to reliably take long enough that
# the browser's fetch() gives up (and the client-side retry logic kicks
# in) well before the request actually finishes server-side, even though
# the server keeps going and the rows DO eventually get created. Kept
# small enough that one request's total round-trip time stays
# comfortably short regardless of per-query latency. A timed-out
# creation batch is still safe to retry either way (rows only ever move
# past 'valid'/'claimed' once actually created, inside their own
# transaction.atomic() in process_import_row).
BATCH_SIZE = 3

# How long a row may sit 'claimed' before the next batch call treats it
# as abandoned (the request that claimed it was killed by gunicorn's
# worker timeout, or the server restarted) and makes it claimable again.
# Comfortably above gunicorn's 30s worker timeout so a request that's
# still genuinely working through its claimed rows is never reclaimed
# out from under it.
STALE_CLAIM_SECONDS = 120

# The confirmation-email phase (action=send_emails below) runs
# separately, after creation, and each row here does MORE than a
# creation row: a handful of DB queries to rebuild the QR code (an
# EXISTING participant, so get_qr_for_user's full lookup chain actually
# runs, unlike the cheap new-participant path) plus a live Postmark API
# call on top -- at the per-query latency observed in production
# (~300ms/query), kept smaller than BATCH_SIZE so a slow/stalled row
# can't by itself consume a whole request's share of gunicorn's 30s
# worker timeout. Unlike a creation batch, a timed-out email batch loses
# nothing: rows stay confirmation_email_sent=False and just get picked
# up by the next call.
EMAIL_BATCH_SIZE = 2


@never_cache
@login_required
def participant_import_template(request, event_id):
    """Downloads the Excel template built specifically for this event's
    actual configured form fields and enabled blocs/workshops."""
    event = get_object_or_404(Event, id=event_id)
    if not _can_access_event_orders(request.user, event):
        raise PermissionDenied("You do not have access to this event's submissions.")

    wb = generate_import_template_workbook(event)
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    safe_name = ''.join(c if c.isalnum() else '_' for c in event.name)[:50]
    response['Content-Disposition'] = f'attachment; filename="import_{safe_name}.xlsx"'
    wb.save(response)
    return response


@never_cache
@login_required
def participant_import_upload(request, event_id):
    """GET shows the upload form (with a link to download the template
    first); POST parses + validates the file into a new batch and
    redirects to its preview for review before anything is created."""
    event = get_object_or_404(Event, id=event_id)
    if not _can_access_event_orders(request.user, event):
        raise PermissionDenied("You do not have access to this event's submissions.")

    if request.method == 'POST':
        uploaded_file = request.FILES.get('import_file')
        if not uploaded_file:
            messages.error(request, "Veuillez choisir un fichier Excel.")
            return redirect('dashboard:participant_import_upload', event_id=event.id)

        try:
            batch = create_import_batch(event, request.user, uploaded_file)
        except Exception as e:
            messages.error(request, f"Impossible de lire ce fichier : {e}")
            return redirect('dashboard:participant_import_upload', event_id=event.id)

        if not batch.rows.exists():
            messages.warning(request, "Aucune ligne de données trouvée dans ce fichier.")
            return redirect('dashboard:participant_import_upload', event_id=event.id)

        return redirect('dashboard:participant_import_preview', event_id=event.id, batch_id=batch.id)

    context = {
        'event': event,
        'columns': build_import_columns(event),
    }
    return render(request, 'dashboard/event_owner/import_upload.html', context)


@never_cache
@login_required
def participant_import_preview(request, event_id, batch_id):
    """Shows the per-row validation report (valid/error/duplicate) for a
    just-uploaded batch -- nothing has been created yet. Confirming
    here is what actually starts creating registrations."""
    event = get_object_or_404(Event, id=event_id)
    if not _can_access_event_orders(request.user, event):
        raise PermissionDenied("You do not have access to this event's submissions.")

    batch = get_object_or_404(ParticipantImportBatch, id=batch_id, event=event)
    rows = list(batch.rows.order_by('row_number'))

    counts = {
        'valid': sum(1 for r in rows if r.status == 'valid'),
        'error': sum(1 for r in rows if r.status == 'error'),
        'skipped_duplicate': sum(1 for r in rows if r.status == 'skipped_duplicate'),
    }

    context = {'event': event, 'batch': batch, 'rows': rows, 'counts': counts}
    return render(request, 'dashboard/event_owner/import_preview.html', context)


def _row_label(row):
    """Short display string for the live per-row log -- name if we have
    one, email otherwise."""
    return row.full_name or row.email or f"Ligne {row.row_number}"


def _progress_snapshot(batch):
    """
    Everything the progress page needs to render its current state from
    scratch, whether this is the very first 'start' or a resume after a
    reload/lost connection -- see creation_total's docstring for why
    'done so far' is derived this way instead of re-counting 'valid'
    rows directly (that count only shrinks as rows get processed, which
    would make the bar look like it jumped backwards on every resume).
    """
    total = batch.creation_total or 0
    # 'claimed' rows are mid-flight (another request is actively
    # creating them right now) -- not done, but also not up for grabs,
    # so they count the same as 'valid' for "not done yet" purposes.
    remaining_valid = batch.rows.filter(status__in=['valid', 'claimed']).count()
    done_so_far = max(0, total - remaining_valid)
    created_count = batch.rows.filter(status='created').count()
    failed_count = max(0, done_so_far - created_count)
    email_remaining = batch.rows.filter(status='created', confirmation_email_sent=False).count()
    return {
        'total': total,
        'done_so_far': done_so_far,
        'created_count': created_count,
        'failed_count': failed_count,
        'creation_done': remaining_valid == 0,
        'email_total': created_count,
        'email_remaining': email_remaining,
    }


@never_cache
@login_required
def participant_import_process(request, event_id, batch_id):
    """
    Two-phase, same shape as attestation_send: action=start shows the
    progress page (and flips the batch to 'processing'); action=batch
    processes the next BATCH_SIZE still-'valid' rows and reports
    progress as JSON -- only rows that were 'valid' after preview are
    ever touched here, error/duplicate rows are left alone.

    Also reachable with a plain GET on this same URL (no action) --
    re-renders the exact same progress page from the batch's current
    state instead of restarting it, so reopening this page after a
    lost connection, a closed tab, or a refresh resumes rather than
    reprocessing or losing track of progress. See _progress_snapshot.
    """
    event = get_object_or_404(Event, id=event_id)
    if not _can_access_event_orders(request.user, event):
        raise PermissionDenied("You do not have access to this event's submissions.")

    batch = get_object_or_404(ParticipantImportBatch, id=batch_id, event=event)

    if request.method == 'GET':
        if batch.creation_total is None:
            # Never actually started (e.g. someone navigated here
            # directly) -- there's nothing to resume, send them back to
            # the preview page to confirm first.
            return redirect('dashboard:participant_import_preview', event_id=event.id, batch_id=batch.id)
        return render(request, 'dashboard/event_owner/import_progress.html',
                      {'event': event, 'batch': batch, **_progress_snapshot(batch)})

    if request.POST.get('action') == 'start':
        if batch.creation_total is None:
            total = batch.rows.filter(status='valid').count()
            if total == 0:
                messages.warning(request, "Aucune ligne valide à importer dans ce fichier.")
                return redirect('dashboard:participant_import_preview', event_id=event.id, batch_id=batch.id)
            batch.creation_total = total
            batch.status = 'processing'
            batch.save(update_fields=['creation_total', 'status'])
        return render(request, 'dashboard/event_owner/import_progress.html',
                      {'event': event, 'batch': batch, **_progress_snapshot(batch)})

    if request.POST.get('action') == 'batch':
        # Claiming happens under a row-level lock so two requests that
        # overlap in time -- a reload whose old request is still
        # finishing server-side, two tabs, a client retry after a
        # dropped connection -- can never both grab the same row and
        # race to create it twice. skip_locked means a request that
        # arrives while another is mid-claim just moves on to whatever
        # rows aren't currently locked, instead of blocking.
        stale_cutoff = timezone.now() - timedelta(seconds=STALE_CLAIM_SECONDS)
        with transaction.atomic():
            batch.rows.filter(status='claimed', claimed_at__lt=stale_cutoff).update(status='valid', claimed_at=None)

            row_ids = list(
                batch.rows.select_for_update(skip_locked=True)
                .filter(status='valid').order_by('row_number')
                .values_list('id', flat=True)[:BATCH_SIZE]
            )
            if row_ids:
                ParticipantImportRow.objects.filter(id__in=row_ids).update(status='claimed', claimed_at=timezone.now())

        if not row_ids:
            # Nothing free to claim right now. Either genuinely done, or
            # every remaining row is currently claimed by another
            # in-flight request -- tell the client to check back shortly
            # rather than treating this as an error or as completion.
            still_pending = batch.rows.filter(status__in=['valid', 'claimed']).count()
            if still_pending == 0:
                batch.status = 'done'
                batch.save(update_fields=['status'])
                return JsonResponse({
                    'success': True, 'done': True, 'created_this_batch': 0, 'failed_this_batch': 0,
                    'remaining': 0, 'rows': [],
                })
            return JsonResponse({
                'success': True, 'done': False, 'busy': True, 'created_this_batch': 0, 'failed_this_batch': 0,
                'remaining': still_pending, 'rows': [],
            })

        rows = list(ParticipantImportRow.objects.filter(id__in=row_ids).order_by('row_number'))

        bloc_context = get_public_bloc_context(event, include_inactive=False)
        config = bloc_context['config'] if bloc_context else None
        # Looked up once for the whole batch -- same form for every row
        # of this event, so this was a wasted query per row before.
        form_config = event.custom_forms.first()

        created_count = 0
        failed_count = 0
        row_details = []
        for row in rows:
            label = _row_label(row)
            process_import_row(row, event, config, bloc_context, form_config)
            row.save(update_fields=['status', 'error_message', 'participant'])
            if row.status == 'created':
                created_count += 1
                row_details.append({'status': 'created', 'label': label, 'email': row.email})
            else:
                failed_count += 1
                row_details.append({
                    'status': 'error', 'label': label, 'email': row.email,
                    'error': row.error_message,
                })

        remaining = batch.rows.filter(status__in=['valid', 'claimed']).count()
        if remaining == 0:
            batch.status = 'done'
            batch.save(update_fields=['status'])

        return JsonResponse({
            'success': True, 'done': remaining == 0,
            'created_this_batch': created_count, 'failed_this_batch': failed_count,
            'remaining': remaining, 'rows': row_details,
        })

    if request.POST.get('action') == 'send_emails':
        # Separate phase from creation above -- see
        # send_pending_confirmation_emails' docstring for why.
        sent_count = send_pending_confirmation_emails(batch, EMAIL_BATCH_SIZE)
        remaining = batch.rows.filter(status='created', confirmation_email_sent=False).count()
        # sent_count == 0 with rows remaining: they all failed to send --
        # stop instead of retrying them in a loop.
        return JsonResponse({'success': True, 'done': remaining == 0 or sent_count == 0,
                             'sent_this_batch': sent_count, 'remaining': remaining})

    return redirect('dashboard:participant_import_preview', event_id=event.id, batch_id=batch.id)
