"""
Attestation (certificate) generation views: admin uploads/configures a
per-event template, picks recipients, and the system generates + e-mails
a personalized PDF to each of them.
"""
import json
from types import SimpleNamespace

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q, Count
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.cache import never_cache

from events.models import Event, Participant, ParticipantEventRegistration
from .models_attestation import AttestationTemplate, AttestationSendLog, AttestationEmailTemplate, FONT_FILES
from .views import is_staff_user

BATCH_SIZE = 10


def _parse_fraction(post_data, key, default=0.5):
    try:
        return float(post_data.get(key, default))
    except (TypeError, ValueError):
        return default


def _parse_align(post_data, key, default='center'):
    value = post_data.get(key, default)
    return value if value in dict(AttestationTemplate.ALIGN_CHOICES) else default


def _parse_font_size(post_data, key, default):
    try:
        return max(8, min(300, int(post_data.get(key, default))))
    except (TypeError, ValueError):
        return default


def _parse_template_fields_from_post(post_data):
    """
    Shared field parsing/validation for the settings form -- used both
    when actually saving the template and when building a throwaway,
    unsaved preview object straight from the same submitted form (see
    attestation_preview_pdf). Never raises; falls back to safe defaults
    for anything missing or invalid.

    Covers all three independently-positioned text elements (name,
    ePoster title, ePoster co-authors) -- font_choice/font_weight/
    font_color stay shared across all three for one consistent
    certificate typography, matching the model.
    """
    font_choice = post_data.get('font_choice', 'playfair')
    if font_choice not in dict(AttestationTemplate.FONT_CHOICES):
        font_choice = 'playfair'

    font_weight = post_data.get('font_weight', 'regular')
    if font_weight not in dict(AttestationTemplate.WEIGHT_CHOICES):
        font_weight = 'regular'

    font_color = post_data.get('font_color', '#000000').strip()
    if not (len(font_color) == 7 and font_color.startswith('#')):
        font_color = '#000000'

    return {
        'text_x': _parse_fraction(post_data, 'text_x'),
        'text_y': _parse_fraction(post_data, 'text_y'),
        'text_align': _parse_align(post_data, 'text_align'),
        'font_size': _parse_font_size(post_data, 'font_size', 60),

        'title_x': _parse_fraction(post_data, 'title_x'),
        'title_y': _parse_fraction(post_data, 'title_y', 0.65),
        'title_align': _parse_align(post_data, 'title_align'),
        'title_font_size': _parse_font_size(post_data, 'title_font_size', 30),

        'co_authors_x': _parse_fraction(post_data, 'co_authors_x'),
        'co_authors_y': _parse_fraction(post_data, 'co_authors_y', 0.78),
        'co_authors_align': _parse_align(post_data, 'co_authors_align'),
        'co_authors_font_size': _parse_font_size(post_data, 'co_authors_font_size', 20),

        'font_choice': font_choice,
        'font_weight': font_weight,
        'font_color': font_color,
    }


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

        for field, value in _parse_template_fields_from_post(request.POST).items():
            setattr(template, field, value)

        template.save()
        messages.success(request, "Modèle d'attestation enregistré.")
        return redirect('dashboard:attestation_settings', event_id=event.id)

    context = {
        'event': event,
        'template': template,
        'font_choices': AttestationTemplate.FONT_CHOICES,
        'weight_choices': AttestationTemplate.WEIGHT_CHOICES,
        'align_choices': AttestationTemplate.ALIGN_CHOICES,
    }
    return render(request, 'dashboard/attestation/settings.html', context)


@never_cache
@login_required
@user_passes_test(is_staff_user)
def attestation_preview_pdf(request, event_id):
    """
    Renders a real sample PDF using the exact same Pillow pipeline as
    real sends -- submitted as a POST from the settings form itself
    (via formaction/formtarget="_blank" on the "Aperçu PDF" button, see
    the template) so it reflects whatever is CURRENTLY in the form,
    even unsaved changes, rather than only the last-saved template.

    That mismatch was the actual bug reported: the live click-to-position
    preview shows wherever you just clicked, but a plain link to this
    view always regenerated from the last SAVED position -- so clicking
    a new spot and previewing without saving first compared two
    different templates and looked "wrong" without anything really
    being broken.
    """
    event = get_object_or_404(Event, id=event_id)
    saved_template = AttestationTemplate.objects.filter(event=event).first()

    if request.method != 'POST':
        if not saved_template:
            messages.error(request, "Enregistrez d'abord un modèle d'attestation avant de prévisualiser.")
            return redirect('dashboard:attestation_settings', event_id=event.id)
        preview = saved_template
    else:
        image_file = request.FILES.get('template_image')
        if not image_file and not saved_template:
            messages.error(request, "Choisissez une image avant de prévisualiser.")
            return redirect('dashboard:attestation_settings', event_id=event.id)

        fields = _parse_template_fields_from_post(request.POST)
        preview = SimpleNamespace(
            template_image=image_file or saved_template.template_image,
            font_file_name=lambda: FONT_FILES[fields['font_choice']],
            **fields,
        )

    # The settings page previews both profiles (participant/ePoster) from
    # the same unsaved form state -- eposter_preview=1 requests the
    # ePoster sample text so the title/co-authors positions actually show
    # something; a plain participant preview passes neither.
    is_eposter_preview = request.POST.get('eposter_preview') == '1' if request.method == 'POST' else False

    from .attestation_service import generate_attestation_pdf
    try:
        pdf_bytes = generate_attestation_pdf(
            preview,
            "Jean Dupont",
            poster_title="Titre de l'étude scientifique présentée" if is_eposter_preview else None,
            co_authors_text="Amine Kaci, Sarah Belkacem, Yacine Meziane" if is_eposter_preview else None,
        )
    except Exception as e:
        messages.error(request, f"Erreur lors de la génération de l'aperçu : {e}")
        return redirect('dashboard:attestation_settings', event_id=event.id)

    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="apercu_attestation.pdf"'
    return response


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

        # Unlike campaign_send (whose recipient rows already exist as
        # 'pending' before a send is ever started, so re-running is
        # naturally a resume), this used to bulk_create a fresh 'pending'
        # row per participant every time -- so closing the progress tab
        # partway through a large send (closer to certain the bigger the
        # list is) and clicking "send" again re-queued everyone, including
        # people who'd already received their PDF, sending it twice.
        # Now: skip anyone already sent/pending, and retry (not duplicate)
        # anyone whose last attempt failed.
        existing_by_participant = {
            log.participant_id: log
            for log in AttestationSendLog.objects.filter(event=event, participant__in=participants)
        }

        new_logs = []
        retried = 0
        already_in_progress = 0
        for p in participants:
            existing = existing_by_participant.get(p.id)
            if existing is None:
                new_logs.append(AttestationSendLog(event=event, participant=p, status='pending', sent_by=request.user))
            elif existing.status == 'failed':
                existing.status = 'pending'
                existing.error_message = ''
                existing.sent_by = request.user
                existing.save(update_fields=['status', 'error_message', 'sent_by'])
                retried += 1
            else:
                already_in_progress += 1

        AttestationSendLog.objects.bulk_create(new_logs)
        total = len(new_logs) + retried

        if already_in_progress:
            messages.info(
                request,
                f"{already_in_progress} participant(s) avaient déjà reçu leur attestation (ou étaient déjà en cours d'envoi) et ont été ignorés."
            )

        if total == 0:
            messages.warning(request, "Tous les participants sélectionnés ont déjà reçu leur attestation.")
            return redirect('dashboard:attestation_send', event_id=event.id)

        return render(request, 'dashboard/attestation/send_progress.html', {
            'event': event,
            'total': total,
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
        'status': _attestation_status_counts(event),
    }
    return render(request, 'dashboard/attestation/send_picker.html', context)


def _attestation_status_counts(event):
    counts = AttestationSendLog.objects.filter(event=event).values('status').annotate(n=Count('id'))
    by_status = {row['status']: row['n'] for row in counts}
    sent = by_status.get('sent', 0)
    failed = by_status.get('failed', 0)
    pending = by_status.get('pending', 0)
    total = sent + failed + pending
    return {
        'sent': sent,
        'failed': failed,
        'pending': pending,
        'total': total,
        'done_pct': round(100 * (sent + failed) / total) if total else 0,
    }


@never_cache
@login_required
@user_passes_test(is_staff_user)
def attestation_history(request, event_id):
    """
    Who already received (or failed to receive) their attestation for
    this event, plus an overall status summary (sent/failed/pending
    counts and a progress bar) -- pending here means an interrupted send
    (closed tab, etc.) that "Reprendre l'envoi" can pick back up.
    """
    event = get_object_or_404(Event, id=event_id)
    logs = AttestationSendLog.objects.filter(event=event).exclude(status='pending').select_related(
        'participant__user', 'sent_by'
    ).order_by('-sent_at')[:500]

    context = {'event': event, 'logs': logs, 'status': _attestation_status_counts(event)}
    return render(request, 'dashboard/attestation/history.html', context)


@never_cache
@login_required
@user_passes_test(is_staff_user)
def attestation_send_resume(request, event_id):
    """
    Picks back up an interrupted send: attestation_send's 'batch' action
    already only cares that pending AttestationSendLog rows exist for
    this event, not how they got there -- so resuming is just reopening
    the same progress page against whatever's still pending, with no
    need to re-select participants.
    """
    event = get_object_or_404(Event, id=event_id)
    pending_count = AttestationSendLog.objects.filter(event=event, status='pending').count()

    if pending_count == 0:
        messages.info(request, "Aucun envoi en cours à reprendre.")
        return redirect('dashboard:attestation_send', event_id=event.id)

    return render(request, 'dashboard/attestation/send_progress.html', {
        'event': event,
        'total': pending_count,
    })


_EMAIL_TEMPLATE_DEFAULTS = {
    'participant': {
        'subject': "Votre attestation - {{event_name}}",
        'body_html': (
            "<p>Bonjour {{prenom}} {{nom}},</p>"
            "<p>Veuillez trouver ci-joint votre attestation de participation à <strong>{{event_name}}</strong>.</p>"
            "<p>Cordialement,<br>L'équipe organisatrice</p>"
        ),
    },
    'eposter': {
        'subject': "Votre attestation - {{event_name}}",
        'body_html': (
            "<p>Bonjour {{prenom}} {{nom}},</p>"
            "<p>Veuillez trouver ci-joint votre attestation de présentation ePoster à <strong>{{event_name}}</strong>"
            " pour le travail intitulé « {{titre}} ».</p>"
            "<p>Cordialement,<br>L'équipe organisatrice</p>"
        ),
    },
}


@never_cache
@login_required
@user_passes_test(is_staff_user)
def attestation_email_template_edit(request, event_id, recipient_type):
    """
    Edit the e-mail sent alongside the attestation PDF for one recipient
    profile ('participant' or 'eposter') -- get-or-create semantics, since
    there's always exactly one of each per event rather than an
    admin-managed list like the ePoster decision templates.
    """
    if recipient_type not in dict(AttestationEmailTemplate.RECIPIENT_TYPE_CHOICES):
        messages.error(request, "Type de destinataire invalide.")
        return redirect('dashboard:attestation_settings', event_id=event_id)

    event = get_object_or_404(Event, id=event_id)
    template = AttestationEmailTemplate.objects.filter(event=event, recipient_type=recipient_type).first()

    if request.method == 'POST':
        subject = request.POST.get('subject', '').strip()
        body_html = request.POST.get('body_html', '').strip()
        if not subject or not body_html:
            messages.error(request, "Le sujet et le contenu de l'e-mail sont obligatoires.")
            return redirect('dashboard:attestation_email_template_edit', event_id=event.id, recipient_type=recipient_type)

        try:
            design_json = json.loads(request.POST.get('design_json') or '{}')
        except (TypeError, ValueError):
            design_json = {}

        if not template:
            template = AttestationEmailTemplate(event=event, recipient_type=recipient_type, created_by=request.user)

        template.subject = subject
        template.body_html = body_html
        template.body_text = request.POST.get('body_text', '')
        template.design_json = design_json
        template.save()

        messages.success(request, "Modèle d'e-mail enregistré.")
        return redirect('dashboard:attestation_settings', event_id=event.id)

    defaults = _EMAIL_TEMPLATE_DEFAULTS[recipient_type]

    # Built here (as already-serialized JSON) rather than interpolated
    # into inline JS, so the literal "{{varname}}" placeholder strings
    # never pass through Django's own template engine -- embedding them
    # directly in a <script> block, as this page's ePoster counterpart
    # does, makes Django's engine treat {{prenom}} as ITS OWN (undefined)
    # template variable and silently render it as an empty string.
    merge_tags = {
        'prenom': {'name': 'Prénom', 'value': '{{prenom}}', 'sample': 'Jean'},
        'nom': {'name': 'Nom', 'value': '{{nom}}', 'sample': 'Dupont'},
        'event_name': {'name': "Nom de l'événement", 'value': '{{event_name}}', 'sample': event.name},
        'event_location': {'name': "Lieu de l'événement", 'value': '{{event_location}}', 'sample': 'Centre International de Conférences, Alger'},
        'event_start_date': {'name': 'Date de début', 'value': '{{event_start_date}}', 'sample': '15/06/2027'},
        'event_end_date': {'name': 'Date de fin', 'value': '{{event_end_date}}', 'sample': '17/06/2027'},
    }
    if recipient_type == 'eposter':
        merge_tags['titre'] = {'name': 'Titre du poster', 'value': '{{titre}}', 'sample': 'Étude sur les nouvelles approches thérapeutiques'}
        merge_tags['co_auteurs'] = {'name': 'Co-auteurs', 'value': '{{co_auteurs}}', 'sample': 'Amine Kaci, Sarah Belkacem, Yacine Meziane'}

    sample_values = {key: tag['sample'] for key, tag in merge_tags.items()}

    context = {
        'event': event,
        'template': template,
        'recipient_type': recipient_type,
        'recipient_type_label': dict(AttestationEmailTemplate.RECIPIENT_TYPE_CHOICES)[recipient_type],
        'defaults': defaults,
        'merge_tags_json': json.dumps(merge_tags),
        'sample_values_json': json.dumps(sample_values),
    }
    return render(request, 'dashboard/attestation/email_template_form.html', context)
