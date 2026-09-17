"""
Attestation (certificate) generation: an admin uploads one background
image per event, positions where the participant's name goes on it
(plus font/size/color), then generates + e-mails a personalized
single-page PDF to any number of selected participants.
"""
from django.db import models
from django.contrib.auth.models import User
from events.models import Event, Participant
import uuid


class AttestationTemplate(models.Model):
    """
    One attestation design per event. text_x/text_y are stored as a
    fraction (0-1) of the image's width/height -- not pixels -- so the
    position stays correct no matter what size image is uploaded or how
    it's displayed in the position-picker preview.
    """
    FONT_CHOICES = [
        ('great_vibes', 'Great Vibes (élégant, cursif)'),
        ('playfair', 'Playfair Display (serif élégant)'),
        ('montserrat', 'Montserrat (moderne, sans-serif)'),
    ]
    ALIGN_CHOICES = [
        ('left', 'Gauche'),
        ('center', 'Centré'),
        ('right', 'Droite'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.OneToOneField(Event, on_delete=models.CASCADE, related_name='attestation_template')

    template_image = models.ImageField(upload_to='events/attestation_templates/', verbose_name="Image du modèle")

    text_x = models.FloatField(default=0.5, verbose_name="Position X (fraction de la largeur)")
    text_y = models.FloatField(default=0.5, verbose_name="Position Y (fraction de la hauteur)")
    text_align = models.CharField(max_length=10, choices=ALIGN_CHOICES, default='center')

    font_choice = models.CharField(max_length=30, choices=FONT_CHOICES, default='playfair')
    font_size = models.PositiveIntegerField(default=60)
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
        return {
            'great_vibes': 'GreatVibes-Regular.ttf',
            'playfair': 'PlayfairDisplay-Regular.ttf',
            'montserrat': 'Montserrat-Regular.ttf',
        }[self.font_choice]


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
