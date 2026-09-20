"""
Attestation (certificate) generation: an admin uploads one background
image per event, positions where the participant's name goes on it
(plus font/weight/size/color), then generates + e-mails a personalized
single-page PDF to any number of selected participants.

Two recipient profiles share one template image: a plain participant
gets only their name drawn; an ePoster presenter (detected by matching
their e-mail against an accepted ScientificContributionSubmission for
the event -- see attestation_service.find_eposter_submission) also gets
the poster's title and its co-authors drawn, each independently
positioned via its own click on the settings page, same as the name.
"""
from django.db import models
from django.contrib.auth.models import User
from events.models import Event, Participant
import uuid

# Shared with views_attestation.py's live-preview endpoint, which builds
# a throwaway (unsaved) stand-in for this model out of the settings
# form's current values -- both need the exact same font_choice ->
# filename mapping, so it lives here once rather than duplicated.
#
# Each of these files is actually a variable font (confirmed via
# Pillow's get_variation_names()), so one file covers every weight --
# attestation_service.WEIGHT_NAMES selects the instance at render time.
# Great Vibes has no weight axis (it's a single-style script font); its
# weight selection is silently a no-op there.
FONT_FILES = {
    'great_vibes': 'GreatVibes-Regular.ttf',
    'playfair': 'PlayfairDisplay-Regular.ttf',
    'montserrat': 'Montserrat-Regular.ttf',
}


class AttestationTemplate(models.Model):
    """
    One attestation design per event. Every *_x/*_y is stored as a
    fraction (0-1) of the image's width/height -- not pixels -- so the
    position stays correct no matter what size image is uploaded or how
    it's displayed in the position-picker preview.

    font_choice/font_weight/font_color are shared across all three text
    elements (name, poster title, co-authors) for one consistent
    certificate typography; only position, alignment and size are set
    per element, matching what's actually click-positioned per element
    on the settings page.
    """
    FONT_CHOICES = [
        ('great_vibes', 'Great Vibes (élégant, cursif)'),
        ('playfair', 'Playfair Display (serif élégant)'),
        ('montserrat', 'Montserrat (moderne, sans-serif)'),
    ]
    WEIGHT_CHOICES = [
        ('regular', 'Normal'),
        ('medium', 'Medium'),
        ('bold', 'Gras'),
    ]
    ALIGN_CHOICES = [
        ('left', 'Gauche'),
        ('center', 'Centré'),
        ('right', 'Droite'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.OneToOneField(Event, on_delete=models.CASCADE, related_name='attestation_template')

    # max_length=255, not Django's default 100 -- a real uploaded filename
    # plus the upload_to prefix routinely exceeds 100 characters (this
    # broke in production with a real descriptive filename), and Postgres
    # enforces the column's varchar length strictly.
    template_image = models.ImageField(upload_to='events/attestation_templates/', max_length=255, verbose_name="Image du modèle")

    text_x = models.FloatField(default=0.5, verbose_name="Position X (fraction de la largeur)")
    text_y = models.FloatField(default=0.5, verbose_name="Position Y (fraction de la hauteur)")
    text_align = models.CharField(max_length=10, choices=ALIGN_CHOICES, default='center')
    font_size = models.PositiveIntegerField(default=60)

    # ePoster-only: poster title, positioned independently of the name.
    title_x = models.FloatField(default=0.5, verbose_name="Titre - Position X")
    title_y = models.FloatField(default=0.65, verbose_name="Titre - Position Y")
    title_align = models.CharField(max_length=10, choices=ALIGN_CHOICES, default='center')
    title_font_size = models.PositiveIntegerField(default=30)

    # ePoster-only: co-authors, drawn as one comma-separated line, pulled
    # verbatim from the submission's author list -- positioned
    # independently of both the name and the title.
    co_authors_x = models.FloatField(default=0.5, verbose_name="Co-auteurs - Position X")
    co_authors_y = models.FloatField(default=0.78, verbose_name="Co-auteurs - Position Y")
    co_authors_align = models.CharField(max_length=10, choices=ALIGN_CHOICES, default='center')
    co_authors_font_size = models.PositiveIntegerField(default=20)

    font_choice = models.CharField(max_length=30, choices=FONT_CHOICES, default='playfair')
    font_weight = models.CharField(max_length=10, choices=WEIGHT_CHOICES, default='regular')
    font_color = models.CharField(max_length=7, default='#000000', verbose_name="Couleur (hex)")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        db_table = 'dashboard_attestationtemplate'
        verbose_name = 'Attestation Template'
        verbose_name_plural = 'Attestation Templates'

    def __str__(self):
        return f"Attestation - {self.event.name}"

    def font_file_name(self):
        return FONT_FILES[self.font_choice]


class AttestationEmailTemplate(models.Model):
    """
    The e-mail sent alongside the attestation PDF -- editable per event,
    per recipient profile (plain participant vs. ePoster presenter, since
    only the latter has {{titre}}/{{co_auteurs}} available), using the
    same Unlayer visual builder and {{variable}} convention already used
    for event/campaign/ePoster-decision e-mails elsewhere in this app.
    """
    RECIPIENT_TYPE_CHOICES = [
        ('participant', 'Participant'),
        ('eposter', 'Présentateur ePoster'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='attestation_email_templates')
    recipient_type = models.CharField(max_length=20, choices=RECIPIENT_TYPE_CHOICES)

    subject = models.CharField(max_length=300)
    body_html = models.TextField(help_text="HTML content with placeholders: {{prenom}}, {{nom}}, {{event_name}}, {{event_location}}, {{event_start_date}}, {{event_end_date}}, {{titre}}, {{co_auteurs}}")
    body_text = models.TextField(blank=True, help_text="Plain text version (optional)")
    design_json = models.JSONField(default=dict, blank=True, help_text="Unlayer editor design JSON")

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        db_table = 'dashboard_attestationemailtemplate'
        unique_together = ('event', 'recipient_type')
        verbose_name = 'Attestation Email Template'
        verbose_name_plural = 'Attestation Email Templates'

    def __str__(self):
        return f"{self.event.name} - {self.get_recipient_type_display()}"


class AttestationSendLog(models.Model):
    """
    One row per participant an attestation was generated/sent for --
    lets the admin see who already received theirs and who failed
    (network/e-mail error), mirroring the status-tracking pattern used
    for bulk email campaign recipients.
    """
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('sent', 'Envoyé'),
        ('failed', 'Échoué'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='attestation_sends')
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE, related_name='attestation_sends')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    error_message = models.CharField(max_length=500, blank=True)
    sent_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'dashboard_attestationsendlog'
        ordering = ['-sent_at']
        verbose_name = 'Attestation Send Log'
        verbose_name_plural = 'Attestation Send Logs'
        indexes = [
            models.Index(fields=['event', '-sent_at']),
            models.Index(fields=['participant']),
        ]

    def __str__(self):
        return f"{self.participant} - {self.status} - {self.sent_at}"
