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
    with template.template_image.open('rb') as f:
        img = Image.open(f)
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
