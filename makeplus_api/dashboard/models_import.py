"""
Bulk participant import from Excel.

An admin downloads a template generated for one specific event (its
exact form fields + whichever blocs it has enabled), fills it in, and
uploads it back. Rows are parsed and validated into a batch *before*
anything is created -- the admin reviews the per-row report (which
rows are valid, which have an error, which are skipped as already
registered) and only then confirms, at which point rows are processed
in small batches (same pattern as attestation_send/campaign_send) so a
large file can't time out a single request.
"""
import uuid

from django.conf import settings
from django.db import models

from events.models import Event


class ParticipantImportBatch(models.Model):
    STATUS_CHOICES = [
        ('validating', 'Validation en cours'),
        ('ready', 'Prêt à importer'),
        ('processing', 'Importation en cours'),
        ('done', 'Terminé'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='import_batches')
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    original_filename = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='validating')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'dashboard_participantimportbatch'
        verbose_name = 'Participant Import Batch'
        verbose_name_plural = 'Participant Import Batches'
        ordering = ['-created_at']

    def __str__(self):
        return f"Import {self.event.name} - {self.created_at:%d/%m/%Y %H:%M}"


class ParticipantImportRow(models.Model):
    STATUS_CHOICES = [
        ('valid', 'Valide'),
        ('error', 'Erreur'),
        ('skipped_duplicate', 'Ignoré (déjà inscrit)'),
        ('created', 'Créé'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    batch = models.ForeignKey(ParticipantImportBatch, on_delete=models.CASCADE, related_name='rows')
    row_number = models.IntegerField(help_text="Excel row number, for error reporting")

    # Raw cell values keyed by column header, exactly as uploaded --
    # kept verbatim (not just the resolved form_data) so the preview can
    # show the admin exactly what was typed, including for error rows.
    raw_data = models.JSONField(default=dict)

    # Resolved during validation, consumed during processing:
    email = models.EmailField(blank=True)
    full_name = models.CharField(max_length=255, blank=True)
    form_data = models.JSONField(default=dict, blank=True, help_text="Mapped onto FormConfiguration.fields_config")
    resolved_item_ids = models.JSONField(default=list, blank=True, help_text="Matched BlocItem ids (status/restauration/social_event)")
    resolved_session_ids = models.JSONField(default=list, blank=True, help_text="Matched Session ids (workshops)")

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='valid')
    error_message = models.CharField(max_length=500, blank=True)

    participant = models.ForeignKey(
        'events.Participant', on_delete=models.SET_NULL, null=True, blank=True, related_name='import_rows'
    )

    class Meta:
        db_table = 'dashboard_participantimportrow'
        verbose_name = 'Participant Import Row'
        verbose_name_plural = 'Participant Import Rows'
        ordering = ['row_number']
        indexes = [
            models.Index(fields=['batch', 'status']),
        ]

    def __str__(self):
        return f"Row {self.row_number} - {self.email or '?'} ({self.status})"
