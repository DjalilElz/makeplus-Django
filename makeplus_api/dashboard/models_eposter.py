"""
ePoster Models for Scientific Committee Validation System
"""
from django.db import models
from django.contrib.auth.models import User
from events.models import Event
import uuid


class EPosterSubmission(models.Model):
    """
    ePoster Submission Model
    Stores all submission data from participants
    """
    
    # Choices for various fields
    TYPE_PARTICIPATION_CHOICES = [
        ('communication_orale', 'Communication Orale'),
        ('poster', 'Poster'),
        ('e_poster', 'E-Poster'),
    ]
    
    GENRE_CHOICES = [
        ('homme', 'Homme'),
        ('femme', 'Femme'),
    ]
    
    GRADE_CHOICES = [
        ('professeur', 'Professeur'),
        ('maitre_de_conference', 'Maître de conférence'),
        ('maitre_assistant', 'Maître assistant'),
        ('specialiste', 'Spécialiste'),
        ('resident', 'Résident'),
        ('doctorant', 'Doctorant'),
        ('autre', 'Autre'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'En attente de validation'),
        ('accepted', 'Accepté'),
        ('rejected', 'Rejeté'),
        ('revision_requested', 'Révision demandée'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='eposter_submissions')
    
    # --- PERSONAL INFORMATION ---
    nom = models.CharField(max_length=100, verbose_name="Nom")
    prenom = models.CharField(max_length=100, verbose_name="Prénom")
    email = models.EmailField(verbose_name="Email")
    telephone = models.CharField(max_length=20, verbose_name="Téléphone")
    genre = models.CharField(max_length=10, choices=GENRE_CHOICES, verbose_name="Genre")
    
    # --- PROFESSIONAL INFORMATION ---
    grade = models.CharField(max_length=50, choices=GRADE_CHOICES, verbose_name="Grade")
    grade_autre = models.CharField(max_length=100, blank=True, verbose_name="Autre grade (si autre)")
    service = models.CharField(max_length=200, verbose_name="Service")
    etablissement = models.CharField(max_length=200, verbose_name="Établissement")
    wilaya = models.CharField(max_length=100, verbose_name="Wilaya")
    
    # --- SUBMISSION DETAILS ---
    type_participation = models.CharField(
        max_length=30, 
        choices=TYPE_PARTICIPATION_CHOICES, 
        verbose_name="Type de participation"
    )
    theme = models.CharField(max_length=300, verbose_name="Thème")
    titre_travail = models.CharField(max_length=500, verbose_name="Titre du travail")
    
    # --- AUTHORS ---
    # Store as JSON array: [{"nom": "", "prenom": "", "affiliation": ""}, ...]
    auteurs = models.JSONField(default=list, verbose_name="Liste des auteurs")
    
    # --- ABSTRACT ---
    introduction = models.TextField(verbose_name="Introduction")
    materiels_methodes = models.TextField(verbose_name="Matériels et méthodes")
    resultats = models.TextField(verbose_name="Résultats")
    conclusion = models.TextField(verbose_name="Conclusion")
    
    # --- OPTIONAL ATTACHMENTS ---
    fichier_resume = models.FileField(
        upload_to='eposters/resumes/', 
        blank=True, 
        null=True, 
        verbose_name="Fichier résumé (optionnel)"
    )
    fichier_poster = models.FileField(
        upload_to='eposters/posters/', 
        blank=True, 
        null=True, 
        verbose_name="Fichier poster (optionnel)"
    )
    
    # --- VALIDATION STATUS ---
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Number of validations needed (configurable per event)
    validations_required = models.IntegerField(default=1, verbose_name="Nombre de validations requises")
    
    # Final decision fields
    final_decision_date = models.DateTimeField(null=True, blank=True)
    final_decision_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='eposter_final_decisions'
    )
    rejection_reason = models.TextField(blank=True, verbose_name="Raison du rejet")
    
    # Email tracking
    acceptance_email_sent = models.BooleanField(default=False)
    rejection_email_sent = models.BooleanField(default=False)
    
    # Metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    # Timestamps
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-submitted_at']
        verbose_name = 'ePoster Submission'
        verbose_name_plural = 'ePoster Submissions'
        indexes = [
            models.Index(fields=['event', 'status', '-submitted_at']),
            models.Index(fields=['email']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.titre_travail[:50]}... - {self.nom} {self.prenom}"
    
    def get_full_name(self):
        return f"{self.prenom} {self.nom}"
    
    def get_validations_count(self):
        """Get count of positive validations"""
        return self.validations.filter(is_approved=True).count()
    
    def get_rejections_count(self):
        """Get count of rejections"""
        return self.validations.filter(is_approved=False).count()
    
    def get_pending_validations_count(self):
        """Get count of committee members who haven't voted yet"""
        total_committee = self.event.eposter_committee_members.filter(is_active=True).count()
        voted = self.validations.count()
        return total_committee - voted
    
    def check_and_update_status(self):
        """
        Check validations and update status automatically
        Returns True if status changed
        """
        if self.status not in ['pending']:
            return False
        
        approvals = self.get_validations_count()
        rejections = self.get_rejections_count()
        
        # If enough approvals, mark as accepted
        if approvals >= self.validations_required:
            self.status = 'accepted'
            self.save(update_fields=['status', 'updated_at'])
            return True
        
        # If more rejections than possible remaining approvals, reject
        total_committee = self.event.eposter_committee_members.filter(is_active=True).count()
        remaining_votes = total_committee - (approvals + rejections)
        if approvals + remaining_votes < self.validations_required:
            self.status = 'rejected'
            self.save(update_fields=['status', 'updated_at'])
            return True
        
        return False


class EPosterValidation(models.Model):
    """
    Individual validation by a committee member
    Supports real-time tracking of all committee votes
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    submission = models.ForeignKey(
        EPosterSubmission, 
        on_delete=models.CASCADE, 
        related_name='validations'
    )
    committee_member = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='eposter_validations'
    )
    
    # Vote
    is_approved = models.BooleanField(verbose_name="Approuvé")
    
    # Comments/feedback
    comments = models.TextField(blank=True, verbose_name="Commentaires")
    
    # Rating (optional, 1-5)
    rating = models.IntegerField(
        null=True, 
        blank=True, 
        choices=[(i, str(i)) for i in range(1, 6)],
        verbose_name="Note (1-5)"
    )
    
    # Timestamps
    validated_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('submission', 'committee_member')
        ordering = ['-validated_at']
        verbose_name = 'ePoster Validation'
        verbose_name_plural = 'ePoster Validations'
        indexes = [
            models.Index(fields=['submission', 'is_approved']),
            models.Index(fields=['committee_member', '-validated_at']),
        ]
    
    def __str__(self):
        status = "✓" if self.is_approved else "✗"
        return f"{status} {self.submission.titre_travail[:30]}... by {self.committee_member.username}"


class EPosterCommitteeMember(models.Model):
    """
    Scientific Committee Member Assignment for ePoster Review
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(
        Event, 
        on_delete=models.CASCADE, 
        related_name='eposter_committee_members'
    )
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='eposter_committee_memberships'
    )
    
    # Role in committee
    ROLE_CHOICES = [
        ('member', 'Membre'),
        ('president', 'Président du comité'),
        ('secretary', 'Secrétaire'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    
    # Specialty/expertise area
    specialty = models.CharField(max_length=200, blank=True, verbose_name="Spécialité")
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Assignment info
    assigned_at = models.DateTimeField(auto_now_add=True)
    assigned_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='eposter_committee_assignments_made'
    )
    
    class Meta:
        unique_together = ('event', 'user')
        ordering = ['-assigned_at']
        verbose_name = 'ePoster Committee Member'
        verbose_name_plural = 'ePoster Committee Members'
    
    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.event.name} ({self.get_role_display()})"
    
    def get_validations_count(self):
        """Get total validations made by this member for this event"""
        return EPosterValidation.objects.filter(
            committee_member=self.user,
            submission__event=self.event
        ).count()
    
    def get_pending_submissions(self):
        """Get submissions this member hasn't reviewed yet"""
        reviewed_ids = EPosterValidation.objects.filter(
            committee_member=self.user,
            submission__event=self.event
        ).values_list('submission_id', flat=True)
        
        return EPosterSubmission.objects.filter(
            event=self.event,
            status='pending'
        ).exclude(id__in=reviewed_ids)


class EPosterEmailTemplate(models.Model):
    """
    Email templates for ePoster notifications
    """
    TYPE_CHOICES = [
        ('submission_received', 'Soumission reçue'),
        ('accepted', 'Acceptation'),
        ('rejected', 'Rejet'),
        ('revision_requested', 'Révision demandée'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(
        Event, 
        on_delete=models.CASCADE, 
        related_name='eposter_email_templates'
    )
    
    template_type = models.CharField(max_length=30, choices=TYPE_CHOICES)
    subject = models.CharField(max_length=300)
    body_html = models.TextField(help_text="HTML content with placeholders: {{nom}}, {{prenom}}, {{titre}}, {{event_name}}")
    body_text = models.TextField(blank=True, help_text="Plain text version (optional)")
    
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        unique_together = ('event', 'template_type')
        ordering = ['template_type']
        verbose_name = 'ePoster Email Template'
        verbose_name_plural = 'ePoster Email Templates'
    
    def __str__(self):
        return f"{self.event.name} - {self.get_template_type_display()}"


# Signals for automatic actions
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=EPosterValidation)
def check_submission_status_after_validation(sender, instance, created, **kwargs):
    """
    After each validation, check if the submission status should be updated
    """
    if created:
        instance.submission.check_and_update_status()
