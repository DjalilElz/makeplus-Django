"""
Attestation (certificate) generation and sending.

Draws a participant's name (and, for an ePoster presenter, the poster
title and its co-authors) onto a fresh copy of the event's uploaded
template image, exports it as a single-page PDF, and e-mails it as an
attachment -- following the same per-recipient try/except + status
logging pattern used by bulk email campaigns (see
views_email.py::campaign_send).
"""
import io
import os
from datetime import timedelta
from django.conf import settings
from django.template import Template, Context
from PIL import Image, ImageDraw, ImageFont, ImageOps

FONTS_DIR = os.path.join(settings.BASE_DIR, 'dashboard', 'static', 'dashboard', 'fonts', 'attestation')

# Every bundled font file is actually a variable font (confirmed via
# Pillow's get_variation_names()), so one file covers every weight.
# Without explicitly selecting an instance, Montserrat in particular
# defaults to its Thin (100) axis position, not Regular -- so this is
# applied even for the 'regular' choice, never left as "whatever the
# file's own default is".
WEIGHT_NAMES = {
    'regular': 'Regular',
    'medium': 'Medium',
    'bold': 'Bold',
}


def get_participant_full_name(participant):
    user = participant.user
    return user.get_full_name() or user.username


def find_eposter_submission(participant, event):
    """
    An ePoster presenter isn't a distinct participant type in this
    app -- there's no FK linking a Participant to their submission, so
    detection is by matching the participant's e-mail against an
    *accepted* e_poster submission for this event. Returns the
    submission, or None for a plain participant (or an e-poster
    submitter who was never accepted).
    """
    if not participant.user.email:
        return None

    from .models_eposter import ScientificContributionSubmission
    return ScientificContributionSubmission.objects.filter(
        event=event,
        email__iexact=participant.user.email,
        type_participation='e_poster',
        status='accepted',
    ).first()


def format_co_authors(submission):
    """
    submission.auteurs is stored verbatim as [{"nom", "prenom",
    "affiliation"}, ...] from the submission form -- rendered here
    exactly as submitted (no de-duplication against the presenter's own
    name), joined into one comma-separated line.
    """
    if not submission or not submission.auteurs:
        return ''
    names = []
    for author in submission.auteurs:
        name = f"{author.get('prenom', '')} {author.get('nom', '')}".strip()
        if name:
            names.append(name)
    return ', '.join(names)


def _load_font(template, font_size):
    font_path = os.path.join(FONTS_DIR, template.font_file_name())
    font = ImageFont.truetype(font_path, font_size)
    weight_name = WEIGHT_NAMES.get(template.font_weight, 'Regular')
    try:
        font.set_variation_by_name(weight_name)
    except OSError:
        pass  # single-weight font (e.g. Great Vibes) -- nothing to select.
    return font


def _draw_positioned_text(draw, img, template, text, x_frac, y_frac, align, font_size):
    """
    Shared centering math for every text element on the certificate
    (name, poster title, co-authors): centers the drawn text's own ink
    bounding box on (x_frac * width, y_frac * height), not its
    (0,0)-relative origin -- fonts have ascent/descent offsets that
    would otherwise throw off vertical centering, and long text needs
    to shrink left from the anchor for 'center'/'right' alignment.
    """
    if not text:
        return

    font = _load_font(template, font_size)
    x = x_frac * img.width
    y = y_frac * img.height

    bbox = draw.textbbox((0, 0), text, font=font)
    mid_x = (bbox[0] + bbox[2]) / 2
    mid_y = (bbox[1] + bbox[3]) / 2

    if align == 'center':
        draw_x = x - mid_x
    elif align == 'right':
        draw_x = x - bbox[2]
    else:
        draw_x = x - bbox[0]
    draw_y = y - mid_y

    draw.text((draw_x, draw_y), text, font=font, fill=template.font_color)


# Template image bytes by stored file name. Production media storage is
# a slow HTTP server (a 1.2 MB template took ~25-30 s to download, close
# to its 30 s timeout), and every attestation used to download the same
# image again. A new upload always gets a new file name, so a cached
# entry can never be stale; only a few events' templates are kept.
_TEMPLATE_CACHE = {}
_TEMPLATE_CACHE_MAX = 4


def _template_image_bytes(template):
    from django.db.models.fields.files import FieldFile
    image = template.template_image
    if not isinstance(image, FieldFile):
        # Live preview of a not-yet-saved upload: its name is just the
        # user's filename, not a unique stored name -- never cache it.
        image.seek(0)
        return image.read()
    name = image.name
    data = _TEMPLATE_CACHE.get(name)
    if data is None:
        with template.template_image.open('rb') as f:
            data = f.read()
        if len(_TEMPLATE_CACHE) >= _TEMPLATE_CACHE_MAX:
            _TEMPLATE_CACHE.pop(next(iter(_TEMPLATE_CACHE)))
        _TEMPLATE_CACHE[name] = data
    return data


def generate_attestation_pdf(template, full_name, poster_title=None, co_authors_text=None):
    """
    Returns the bytes of a single-page PDF: the event's template image
    with `full_name` drawn at the configured position/font/size/color,
    plus -- only when given -- the poster title and co-authors, each at
    their own independently configured position (ePoster presenters
    only; a plain participant call passes neither).

    template_image.open()/img.load() (not template_image.path) is used
    deliberately -- .path raises on non-filesystem storage backends
    (this project switches to an HTTP-based cPanel storage in
    production), while .open() works uniformly on any Django Storage.
    """
    img = Image.open(io.BytesIO(_template_image_bytes(template)))
    img.load()

    # Browsers auto-rotate a displayed <img> per its EXIF orientation tag,
    # but Pillow does not -- without this, a template photo with an
    # orientation tag (common from phones/exports) keeps its raw,
    # unrotated width/height here while text_x/text_y were picked against
    # the browser's rotated dimensions, throwing off both position and
    # apparent font size relative to the image.
    img = ImageOps.exif_transpose(img)
    img = img.convert('RGB')

    draw = ImageDraw.Draw(img)

    _draw_positioned_text(draw, img, template, full_name, template.text_x, template.text_y, template.text_align, template.font_size)
    _draw_positioned_text(draw, img, template, poster_title, template.title_x, template.title_y, template.title_align, template.title_font_size)
    _draw_positioned_text(draw, img, template, co_authors_text, template.co_authors_x, template.co_authors_y, template.co_authors_align, template.co_authors_font_size)

    buffer = io.BytesIO()
    img.save(buffer, format='PDF')
    buffer.seek(0)
    return buffer.read()


def _build_email_context(participant, event, full_name, submission=None):
    first_name, _, last_name = full_name.partition(' ')
    return {
        'prenom': first_name,
        'nom': last_name,
        'event_name': event.name,
        'event_location': event.location or '',
        'event_start_date': event.start_date.strftime('%d/%m/%Y') if event.start_date else '',
        'event_end_date': event.end_date.strftime('%d/%m/%Y') if event.end_date else '',
        'titre': submission.titre_travail if submission else '',
        'co_auteurs': format_co_authors(submission) if submission else '',
    }


def _default_email_content(recipient_type):
    """Used when the admin hasn't customized this event's attestation e-mail yet."""
    if recipient_type == 'eposter':
        return (
            "Votre attestation - {{event_name}}",
            "<p>Bonjour {{prenom}} {{nom}},</p>"
            "<p>Veuillez trouver ci-joint votre attestation de présentation ePoster à <strong>{{event_name}}</strong>"
            " pour le travail intitulé « {{titre}} ».</p>"
            "<p>Cordialement,<br>L'équipe organisatrice</p>"
        )
    return (
        "Votre attestation - {{event_name}}",
        "<p>Bonjour {{prenom}} {{nom}},</p>"
        "<p>Veuillez trouver ci-joint votre attestation de participation à <strong>{{event_name}}</strong>.</p>"
        "<p>Cordialement,<br>L'équipe organisatrice</p>"
    )


def send_attestation_to_participant(template, participant, sent_by=None):
    """
    Generates and e-mails one participant's attestation. Always returns
    (success: bool, error_message: str or None) -- never raises, so a
    caller looping over many participants can keep going after one
    failure (matches campaign_send's per-recipient try/except).

    Detects an ePoster presenter by e-mail match (find_eposter_submission)
    and, only for them, draws the poster title/co-authors and picks the
    'eposter' e-mail template instead of 'participant' -- a plain
    participant is completely unaffected by any of this.
    """
    full_name = get_participant_full_name(participant)
    event = template.event

    if not participant.user.email:
        return False, "Ce participant n'a pas d'adresse e-mail."

    submission = find_eposter_submission(participant, event)
    recipient_type = 'eposter' if submission else 'participant'

    try:
        pdf_bytes = generate_attestation_pdf(
            template,
            full_name,
            poster_title=submission.titre_travail if submission else None,
            co_authors_text=format_co_authors(submission) if submission else None,
        )
    except Exception as e:
        return False, f"Erreur de génération du PDF : {e}"

    from .models_attestation import AttestationEmailTemplate
    email_template = AttestationEmailTemplate.objects.filter(
        event=event, recipient_type=recipient_type, is_active=True
    ).first()

    context = Context(_build_email_context(participant, event, full_name, submission))
    if email_template:
        subject = Template(email_template.subject).render(context)
        html_content = Template(email_template.body_html).render(context)
    else:
        default_subject, default_body = _default_email_content(recipient_type)
        subject = Template(default_subject).render(context)
        html_content = Template(default_body).render(context)

    safe_filename = "attestation_" + "_".join(full_name.split()) + ".pdf"

    from .email_sender import send_email
    success, error, _message_id = send_email(
        to_email=participant.user.email,
        subject=subject,
        html_content=html_content,
        to_name=full_name,
        use_api=True,
        attachments=[{'name': safe_filename, 'content': pdf_bytes, 'mimetype': 'application/pdf'}],
    )
    return success, error


def _send_presence_attestation_now(log_id):
    """Background worker for queue_presence_attestation: sends one queued
    attestation and records the outcome on its AttestationSendLog row."""
    from django.db import connection
    from .models_attestation import AttestationSendLog, AttestationTemplate
    try:
        log = AttestationSendLog.objects.select_related('participant__user', 'event').get(id=log_id)
        if log.status != 'pending':
            return
        template = AttestationTemplate.objects.filter(event=log.event).first()
        if not template:
            success, error = False, "Aucun modèle d'attestation pour cet événement."
        else:
            success, error = send_attestation_to_participant(template, log.participant)
        log.status = 'sent' if success else 'failed'
        log.error_message = (error or '')[:500]
        log.save(update_fields=['status', 'error_message'])
    except Exception as e:  # never let a background send crash silently mid-way
        import logging
        logging.getLogger(__name__).exception("[ATTESTATION] presence send failed for log %s: %s", log_id, e)
        AttestationSendLog.objects.filter(id=log_id, status='pending').update(
            status='failed', error_message=str(e)[:500]
        )
    finally:
        connection.close()


PRESENCE_SEND_STALE_AFTER = timedelta(minutes=15)


def queue_presence_attestation(participant, event):
    """
    Called when the caisse marks a participant present for the first time.
    If the event opted in (AttestationTemplate.auto_send_on_presence), queue
    their attestation and send it in the background so the cashier is never
    kept waiting on PDF generation or the e-mail provider.

    Uses the same AttestationSendLog rows as the dashboard's bulk send, so a
    participant never gets it twice: anyone already sent (or in progress) is
    skipped, a previous failure is retried. Returns True if a send was queued.
    """
    from django.db import transaction
    from .models_attestation import AttestationSendLog, AttestationTemplate

    if not AttestationTemplate.objects.filter(event=event, auto_send_on_presence=True).exists():
        return False
    if not participant.user.email:
        return False

    from django.utils import timezone

    existing = AttestationSendLog.objects.filter(event=event, participant=participant).order_by('-sent_at').first()
    if existing:
        # Skip only what presence itself already did (sent_by NULL): a
        # manual send from the dashboard made *before* the person arrived
        # (a test, an early send) must not swallow the arrival e-mail.
        if existing.status == 'sent' and existing.sent_by_id is None:
            return False
        # A send in progress -- unless it is stale (the background worker
        # was killed mid-way, e.g. a server restart), which would otherwise
        # leave this person 'pending' forever and never retried.
        if existing.status == 'pending' and existing.sent_at >= timezone.now() - PRESENCE_SEND_STALE_AFTER:
            return False
        existing.status = 'pending'
        existing.error_message = ''
        existing.sent_by = None
        existing.sent_at = timezone.now()
        existing.save(update_fields=['status', 'error_message', 'sent_by', 'sent_at'])
        log = existing
    else:
        log = AttestationSendLog.objects.create(event=event, participant=participant, status='pending')

    import threading
    log_id = log.id
    # After commit: the caller may be inside a transaction (a caisse
    # payment), and the worker must see the committed rows.
    transaction.on_commit(
        lambda: threading.Thread(target=_send_presence_attestation_now, args=(log_id,), daemon=True).start()
    )
    return True
