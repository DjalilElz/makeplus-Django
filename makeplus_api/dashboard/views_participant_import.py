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
)
from .views_blocs import get_public_bloc_context
from .views_event_owner import _can_access_event_orders, _redirect_to_submissions

BATCH_SIZE = 10


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


@never_cache
@login_required
def participant_import_process(request, event_id, batch_id):
    """
    Two-phase, same shape as attestation_send: action=start shows the
    progress page (and flips the batch to 'processing'); action=batch
    processes the next BATCH_SIZE still-'valid' rows and reports
    progress as JSON -- only rows that were 'valid' after preview are
    ever touched here, error/duplicate rows are left alone.
    """
    event = get_object_or_404(Event, id=event_id)
    if not _can_access_event_orders(request.user, event):
        raise PermissionDenied("You do not have access to this event's submissions.")

    batch = get_object_or_404(ParticipantImportBatch, id=batch_id, event=event)

    if request.method == 'POST' and request.POST.get('action') == 'start':
        total = batch.rows.filter(status='valid').count()
        if total == 0:
            messages.warning(request, "Aucune ligne valide à importer dans ce fichier.")
            return redirect('dashboard:participant_import_preview', event_id=event.id, batch_id=batch.id)

        batch.status = 'processing'
        batch.save(update_fields=['status'])
        return render(request, 'dashboard/event_owner/import_progress.html', {'event': event, 'batch': batch, 'total': total})

    if request.method == 'POST' and request.POST.get('action') == 'batch':
        pending_qs = batch.rows.filter(status='valid').order_by('row_number')
        rows = list(pending_qs[:BATCH_SIZE])

        if not rows:
            batch.status = 'done'
            batch.save(update_fields=['status'])
            return JsonResponse({'success': True, 'done': True, 'created_this_batch': 0, 'failed_this_batch': 0, 'remaining': 0})

        bloc_context = get_public_bloc_context(event, include_inactive=False)
        config = bloc_context['config'] if bloc_context else None

        created_count = 0
        failed_count = 0
        for row in rows:
            process_import_row(row, event, config, bloc_context)
            row.save(update_fields=['status', 'error_message', 'participant'])
            if row.status == 'created':
                created_count += 1
            else:
                failed_count += 1

        remaining = batch.rows.filter(status='valid').count()
        if remaining == 0:
            batch.status = 'done'
            batch.save(update_fields=['status'])

        return JsonResponse({
            'success': True, 'done': remaining == 0,
            'created_this_batch': created_count, 'failed_this_batch': failed_count,
            'remaining': remaining,
        })

    return redirect('dashboard:participant_import_preview', event_id=event.id, batch_id=batch.id)
