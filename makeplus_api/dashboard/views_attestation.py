"""
Attestation (certificate) generation views: admin uploads/configures a
per-event template, picks recipients, and the system generates + e-mails
a personalized PDF to each of them.
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.cache import never_cache

from events.models import Event, Participant, ParticipantEventRegistration
from .models_attestation import AttestationTemplate, AttestationSendLog
from .views import is_staff_user

BATCH_SIZE = 10


@never_cache
@login_required
@user_passes_test(is_staff_user)
def attestation_settings(request, event_id):
    """
    Upload/configure the event's attestation template: background image,
    where the participant's name goes on it (as a fraction of the
    image's own width/height, set by clicking the preview in the
    template), font, size, and color.
    """
    event = get_object_or_404(Event, id=event_id)
    template = AttestationTemplate.objects.filter(event=event).first()

    if request.method == 'POST':
        image_file = request.FILES.get('template_image')

        if not template and not image_file:
            messages.error(request, "Veuillez sélectionner une image pour le modèle d'attestation.")
            return redirect('dashboard:attestation_settings', event_id=event.id)

        if not template:
            template = AttestationTemplate(event=event, created_by=request.user)

        if image_file:
            template.template_image = image_file

        try:
            template.text_x = float(request.POST.get('text_x', template.text_x if template.pk else 0.5))
            template.text_y = float(request.POST.get('text_y', template.text_y if template.pk else 0.5))
        except (TypeError, ValueError):
            messages.error(request, "Position invalide -- cliquez sur l'aperçu pour repositionner le nom.")
            return redirect('dashboard:attestation_settings', event_id=event.id)

        text_align = request.POST.get('text_align', 'center')
        if text_align not in dict(AttestationTemplate.ALIGN_CHOICES):
            text_align = 'center'
        template.text_align = text_align

        font_choice = request.POST.get('font_choice', 'playfair')
        if font_choice not in dict(AttestationTemplate.FONT_CHOICES):
            font_choice = 'playfair'
        template.font_choice = font_choice

        try:
            font_size = int(request.POST.get('font_size', 60))
            template.font_size = max(8, min(300, font_size))
        except (TypeError, ValueError):
            template.font_size = 60

        font_color = request.POST.get('font_color', '#000000').strip()
        if len(font_color) == 7 and font_color.startswith('#'):
            template.font_color = font_color

        try:
            template.save()
        except Exception as e:
            # A storage-backend failure (bad/expired credentials, network
            # issue, misconfigured bucket) must not crash the whole page
            # with a raw 500 -- surface it as a normal, readable error
            # instead so the admin knows exactly what to check.
            error_text = str(e)
            if 'AccessDenied' in error_text or 'Invalid Compact JWS' in error_text or 'Unauthorized' in error_text:
                messages.error(
                    request,
                    "Échec de l'enregistrement : la clé de connexion au stockage (SUPABASE_SERVICE_KEY) "
                    "semble invalide ou expirée. Vérifiez-la dans les paramètres du serveur (Render) -- elle "
                    "doit être la clé « service_role » du projet Supabase, pas la clé « anon » ni le mot de passe. "
                    f"Détail technique : {error_text}"
                )
            else:
                messages.error(request, f"Échec de l'enregistrement du modèle : {error_text}")
            return redirect('dashboard:attestation_settings', event_id=event.id)

        messages.success(request, "Modèle d'attestation enregistré.")
        return redirect('dashboard:attestation_settings', event_id=event.id)

    context = {
        'event': event,
        'template': template,
        'font_choices': AttestationTemplate.FONT_CHOICES,
        'align_choices': AttestationTemplate.ALIGN_CHOICES,
    }
    return render(request, 'dashboard/attestation/settings.html', context)


@never_cache
@login_required
@user_passes_test(is_staff_user)
def attestation_send(request, event_id):
    """
    Recipient picker (GET) and the two-phase send flow (POST):
    - action=start: create pending AttestationSendLog rows for the
      selected participants, show the progress page.
    - action=batch: process the next BATCH_SIZE pending rows for this
      event and report progress as JSON, mirroring campaign_send's
      batching so a large participant list can't time out a single
      request.
    """
    event = get_object_or_404(Event, id=event_id)
    template = AttestationTemplate.objects.filter(event=event).first()

    if not template:
        messages.error(request, "Configurez d'abord un modèle d'attestation pour cet événement.")
        return redirect('dashboard:attestation_settings', event_id=event.id)

    if request.method == 'POST' and request.POST.get('action') == 'start':
        participant_ids = request.POST.getlist('participant_ids')
        if not participant_ids:
            messages.error(request, "Veuillez sélectionner au moins un participant.")
            return redirect('dashboard:attestation_send', event_id=event.id)

        participants = Participant.objects.filter(
            id__in=participant_ids,
            registrations__event=event,
        ).distinct()

        logs = [
            AttestationSendLog(event=event, participant=p, status='pending', sent_by=request.user)
            for p in participants
        ]
        AttestationSendLog.objects.bulk_create(logs)

        return render(request, 'dashboard/attestation/send_progress.html', {
            'event': event,
            'total': len(logs),
        })

    if request.method == 'POST' and request.POST.get('action') == 'batch':
        pending_qs = AttestationSendLog.objects.filter(event=event, status='pending').select_related('participant__user')
        batch = list(pending_qs[:BATCH_SIZE])

        if not batch:
            return JsonResponse({'success': True, 'done': True, 'sent_this_batch': 0, 'failed_this_batch': 0, 'remaining': 0})

        from .attestation_service import send_attestation_to_participant

        sent_count = 0
        failed_count = 0
        for log in batch:
            success, error = send_attestation_to_participant(template, log.participant, sent_by=request.user)
            log.status = 'sent' if success else 'failed'
            log.error_message = (error or '')[:500]
            log.save(update_fields=['status', 'error_message'])
            if success:
                sent_count += 1
            else:
                failed_count += 1

        if sent_count == 0 and failed_count > 0:
            # Whole batch failed -- likely a systemic outage (bad e-mail
            # credentials, API down), not per-recipient bounces. Put the
            # batch back to pending and stop instead of grinding through
            # the rest of the list marking everyone 'failed' for nothing.
            AttestationSendLog.objects.filter(
                id__in=[log.id for log in batch]
            ).update(status='pending', error_message='')
            return JsonResponse({
                'success': False,
                'done': True,
                'error': (
                    f"Échec de l'envoi : aucun des {failed_count} envoi(s) de ce lot n'a abouti. "
                    "Vérifiez la configuration d'envoi (e-mail) et réessayez."
                ),
            })

        remaining = AttestationSendLog.objects.filter(event=event, status='pending').count()
        return JsonResponse({
            'success': True,
            'done': remaining == 0,
            'sent_this_batch': sent_count,
            'failed_this_batch': failed_count,
            'remaining': remaining,
        })

    # GET -- recipient picker
    search = request.GET.get('search', '').strip()
    registrations = ParticipantEventRegistration.objects.filter(event=event).select_related('participant__user')
    if search:
        registrations = registrations.filter(
            Q(participant__user__first_name__icontains=search)
            | Q(participant__user__last_name__icontains=search)
            | Q(participant__user__email__icontains=search)
            | Q(participant__badge_id__icontains=search)
        )
    registrations = registrations.order_by('participant__user__first_name', 'participant__user__last_name')

    context = {
        'event': event,
        'template': template,
        'registrations': registrations,
        'search': search,
    }
    return render(request, 'dashboard/attestation/send_picker.html', context)


@never_cache
@login_required
@user_passes_test(is_staff_user)
def attestation_history(request, event_id):
    """Who already received (or failed to receive) their attestation for this event."""
    event = get_object_or_404(Event, id=event_id)
    logs = AttestationSendLog.objects.filter(event=event).exclude(status='pending').select_related(
        'participant__user', 'sent_by'
    ).order_by('-sent_at')[:500]

    context = {'event': event, 'logs': logs}
    return render(request, 'dashboard/attestation/history.html', context)
