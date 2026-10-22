"""
Bulk participant import views: download an event-specific Excel
template, upload a filled copy for validation/preview, then confirm to
actually create the registrations in small batches (same two-phase
pattern as attestation_send/campaign_send, so a large file can't time
out a single request).
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import never_cache

from events.models import Event
from .models_import import ParticipantImportBatch, ParticipantImportRow
from .participant_import_service import (
    build_import_columns, generate_import_template_workbook, create_import_batch, process_import_row,
    send_pending_confirmation_emails,
)
from .views_blocs import get_public_bloc_context
from .views_event_owner import _can_access_event_orders, _redirect_to_submissions

# Row creation is pure DB work (no network calls). It used to run ~20+
# queries deep per row (duplicate QR generation, a per-row form-config
# lookup, get_or_create round-trips for rows that are usually brand
# new) -- enough, at 10/request, to occasionally approach gunicorn's
# 30s worker timeout on a large file. Those redundant queries were
# removed (see create_participant_for_event / build_initial_qr_data /
# the form_config caching below), so each row is now roughly half the
# DB round-trips it used to be -- batch size is restored accordingly.
# A timed-out creation batch is still safe to retry either way (rows
# only ever move past 'valid' once actually created, inside their own
# transaction.atomic() in process_import_row).
BATCH_SIZE = 10

# The confirmation-email phase (action=send_emails below) runs
# separately, after creation, and does make a live network call per
# row -- kept smaller so a slow/stalled call can't by itself consume a
# whole batch's share of gunicorn's 30s worker timeout. Unlike a
# creation batch, a timed-out email batch loses nothing: rows stay
# confirmation_email_sent=False and just get picked up by the next call.
EMAIL_BATCH_SIZE = 5


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
    remaining_valid = batch.rows.filter(status='valid').count()
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
        pending_qs = batch.rows.filter(status='valid').order_by('row_number')
        rows = list(pending_qs[:BATCH_SIZE])

        if not rows:
            batch.status = 'done'
            batch.save(update_fields=['status'])
            return JsonResponse({
                'success': True, 'done': True, 'created_this_batch': 0, 'failed_this_batch': 0,
                'remaining': 0, 'rows': [],
            })

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

        remaining = batch.rows.filter(status='valid').count()
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
        return JsonResponse({'success': True, 'done': remaining == 0, 'sent_this_batch': sent_count, 'remaining': remaining})

    return redirect('dashboard:participant_import_preview', event_id=event.id, batch_id=batch.id)
