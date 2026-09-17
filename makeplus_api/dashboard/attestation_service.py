"""
Attestation (certificate) generation and sending.

Draws a participant's name onto a fresh copy of the event's uploaded
template image, exports it as a single-page PDF, and e-mails it as an
attachment -- following the same per-recipient try/except + status
logging pattern used by bulk email campaigns (see
views_email.py::campaign_send).
"""
import io
import os
from django.conf import settings
from PIL import Image, ImageDraw, ImageFont

FONTS_DIR = os.path.join(settings.BASE_DIR, 'dashboard', 'static', 'dashboard', 'fonts', 'attestation')


def get_participant_full_name(participant):
    user = participant.user
    return user.get_full_name() or user.username


def _load_font(template):
    font_path = os.path.join(FONTS_DIR, template.font_file_name())
    return ImageFont.truetype(font_path, template.font_size)


def generate_attestation_pdf(template, full_name):
    """
    Returns the bytes of a single-page PDF: the event's template image
    with `full_name` drawn at the configured position/font/size/color.

    template_image.open()/img.load() (not template_image.path) is used
    deliberately -- .path raises on non-filesystem storage backends
    (this project switches to an HTTP-based cPanel storage in
    production), while .open() works uniformly on any Django Storage.
    """
    with template.template_image.open('rb') as f:
        img = Image.open(f)
        img.load()
    img = img.convert('RGB')

    draw = ImageDraw.Draw(img)
    font = _load_font(template)

    x = template.text_x * img.width
    y = template.text_y * img.height

    # Center the drawn text's own ink bounding box on (x, y), not its
    # (0,0)-relative origin -- fonts have ascent/descent offsets that
    # would otherwise throw off vertical centering, and long names need
    # to shrink left from the anchor for 'center'/'right' alignment.
    bbox = draw.textbbox((0, 0), full_name, font=font)
    mid_x = (bbox[0] + bbox[2]) / 2
    mid_y = (bbox[1] + bbox[3]) / 2

    if template.text_align == 'center':
        draw_x = x - mid_x
    elif template.text_align == 'right':
        draw_x = x - bbox[2]
    else:
        draw_x = x - bbox[0]
    draw_y = y - mid_y

    draw.text((draw_x, draw_y), full_name, font=font, fill=template.font_color)

    buffer = io.BytesIO()
    img.save(buffer, format='PDF')
    buffer.seek(0)
    return buffer.read()


def send_attestation_to_participant(template, participant, sent_by=None):
    """
    Generates and e-mails one participant's attestation. Always returns
    (success: bool, error_message: str or None) -- never raises, so a
    caller looping over many participants can keep going after one
    failure (matches campaign_send's per-recipient try/except).
    """
    full_name = get_participant_full_name(participant)
    event = template.event

    if not participant.user.email:
        return False, "Ce participant n'a pas d'adresse e-mail."

    try:
        pdf_bytes = generate_attestation_pdf(template, full_name)
    except Exception as e:
        return False, f"Erreur de génération du PDF : {e}"

    html_content = f"""
    <p>Bonjour {full_name},</p>
    <p>Veuillez trouver ci-joint votre attestation de participation à <strong>{event.name}</strong>.</p>
    <p>Cordialement,<br>L'équipe organisatrice</p>
    """
    safe_filename = "attestation_" + "_".join(full_name.split()) + ".pdf"

    from .email_sender import send_email
    success, error, _message_id = send_email(
        to_email=participant.user.email,
        subject=f"Votre attestation - {event.name}",
        html_content=html_content,
        to_name=full_name,
        use_api=True,
        attachments=[{'name': safe_filename, 'content': pdf_bytes, 'mimetype': 'application/pdf'}],
    )
    return success, error
