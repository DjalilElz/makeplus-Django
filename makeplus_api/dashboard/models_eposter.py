"""
Scientific Contributions Models - Committee Validation System
Supports: E-Poster, Communication Orale, Table Ronde, Atelier
"""
from django.db import models
from django.contrib.auth.models import User
from events.models import Event
import uuid


class ScientificContributionSubmission(models.Model):
    """
    Scientific Contribution Submission Model
    Stores all submission data from participants for:
    - E-Poster (requires final submission with code)
    - Communication Orale (requires final submission with code)
    - Table Ronde (no final submission)
    - Atelier (no final submission)
    """
    
    # Choices for various fields
    TYPE_PARTICIPATION_CHOICES = [
        ('e_poster', 'E-Poster'),
        ('communication_orale', 'Communication Orale'),
        ('table_ronde', 'Table Ronde'),
        ('atelier', 'Atelier'),
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
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='contribution_submissions')
    
    # --- PERSONAL INFORMATION ---
    nom = models.CharField(max_length=100, verbose_name="Nom")
    prenom = models.CharField(max_length=100, verbose_name="Prénom")
    email = models.EmailField(verbose_name="Email")
    telephone = models.CharField(max_length=20, verbose_name="Téléphone")
    genre = models.CharField(max_length=10, choices=GENRE_CHOICES, verbose_name="Genre", blank=True, null=True)
    
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
        upload_to='contributions/resumes/', 
        blank=True, 
        null=True, 
        verbose_name="Fichier résumé (optionnel)"
    )
    fichier_poster = models.FileField(
        upload_to='contributions/posters/', 
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
    
    # Code for final submission (generated when accepted)
    # Only for e_poster and communication_orale types
    contribution_code = models.CharField(max_length=50, blank=True, null=True, unique=True, verbose_name="Code de Contribution", db_column='eposter_code')
    
    # Metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    # Timestamps
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'dashboard_epostersubmission'  # Keep existing table name for data preservation
        ordering = ['-submitted_at']
        verbose_name = 'Scientific Contribution Submission'
        verbose_name_plural = 'Scientific Contribution Submissions'
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
        total_committee = self.event.contribution_committee_members.filter(is_active=True).count()
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
            # Generate contribution code if not already generated
            if not self.contribution_code:
                self.generate_contribution_code()
            self.save(update_fields=['status', 'contribution_code', 'updated_at'])
            return True
        
        # If more rejections than possible remaining approvals, reject
        total_committee = self.event.contribution_committee_members.filter(is_active=True).count()
        remaining_votes = total_committee - (approvals + rejections)
        if approvals + remaining_votes < self.validations_required:
            self.status = 'rejected'
            self.save(update_fields=['status', 'updated_at'])
            return True
        
        return False
    
    def generate_contribution_code(self):
        """
        Generate unique code for this event based on submission type.
        Only e_poster and communication_orale get codes (for final submission).
        Table_ronde and atelier do NOT get codes.
        """
        # Only generate codes for types that have final submission
        if self.type_participation not in ['e_poster', 'communication_orale']:
            return None
        
        # Separate number sequences for each type
        if self.type_participation == 'e_poster':
            prefix = 'EPOSTER'
        elif self.type_participation == 'communication_orale':
            prefix = 'COMORAL'
        else:
            return None
        
        # Get count of accepted submissions of this type for this event
        count = ScientificContributionSubmission.objects.filter(
            event=self.event,
            type_participation=self.type_participation,
            status='accepted'
        ).exclude(contribution_code='').count() + 1
        
        # Format: {PREFIX}-{EVENT_ID_SHORT}-{NUMBER}
        event_short = str(self.event.id)[:8].upper()
        code = f"{prefix}-{event_short}-{count:03d}"
        
        # Ensure uniqueness
        while ScientificContributionSubmission.objects.filter(contribution_code=code).exists():
            count += 1
            code = f"{prefix}-{event_short}-{count:03d}"
        
        self.contribution_code = code
        return code
    
    def requires_final_submission(self):
        """Check if this submission type requires a final submission"""
        return self.type_participation in ['e_poster', 'communication_orale']




class ScientificContributionFinalSubmission(models.Model):
    """
    Final Scientific Contribution Submission Model
    Only for E-Poster and Communication Orale types (after validation)
    Submitted by users who received validation and contribution code
    """
    
    SPECIALITE_CHOICES = [
        ('allerologie', 'Allerologie'),
        ('anatomique', 'Anatomique'),
        ('anesthesiologie', 'Anesthésiologie'),
        ('biologie', 'Biologie'),
        ('chirurgie_cardiaque', 'Chirurgie cardiaque'),
        ('dermatologie', 'Dermatologie'),
        ('diabetologie_endocrinologie', 'Diabétologie endocrinologie'),
        ('gastro_enterologie_hepatologie', 'Gastro-entérologie et hépatologie'),
        ('obstetrique_gynecologie', 'Obstétrique et gynécologie'),
        ('hematologie', 'Hématologie'),
        ('immunologie', 'Immunologie'),
        ('maladies_infectieuses', 'Maladies infectieuses'),
        ('medecine_travail', 'Médecine du travail'),
        ('medecine_interne', 'Médecine interne'),
        ('medecine_generale', 'Médecine générale'),
        ('nephrologie', 'Néphrologie'),
        ('oncologie', 'Oncologie'),
        ('ophtalmologie', 'Ophtalmologie'),
        ('orl', 'ORL'),
        ('professions_sante_alliees', 'Professions de santé alliées'),
        ('pediatrie', 'Pédiatrie'),
        ('pneumologie', 'Pneumologie'),
        ('pharmacie_hospitaliere', 'Pharmacie hospitalière'),
        ('pharmacien_officine', 'Pharmacien d\'officine'),
        ('medecine_soins_intensifs', 'Médecine de soins intensifs'),
        ('psychiatrie', 'Psychiatrie'),
        ('radiologie', 'Radiologie'),
        ('rhumatologie', 'Rhumatologie'),
        ('urologie', 'Urologie'),
        ('chirurgie_dentaire', 'Chirurgie dentaire'),
        ('chirurgie_pediatrique', 'Chirurgie pédiatrique'),
    ]
    
    DOMAINE_COMMUNICATION_CHOICES = [
        ('rhinologie', 'Rhinologie'),
        ('pathologie_cervico_facial', 'Pathologie cervico-facial'),
        ('thyroide_parathyroide', 'Thyroïde et parathyroïde'),
        ('orl_pediatrique', 'ORL pédiatrique'),
        ('laryngologie_trachee', 'Laryngologie trachée'),
        ('otologie', 'Otologie'),
        ('cancerologie', 'Cancérologie'),
        ('divers', 'Divers'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    original_submission = models.OneToOneField(
        'ScientificContributionSubmission',
        on_delete=models.CASCADE,
        related_name='final_submission',
        verbose_name="Soumission originale"
    )
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='contribution_final_submissions')
    
    # Form fields
    nom = models.CharField(max_length=100, verbose_name="Nom")
    email = models.EmailField(verbose_name="Email")
    telephone = models.CharField(max_length=20, verbose_name="Téléphone")
    specialite = models.CharField(max_length=100, choices=SPECIALITE_CHOICES, verbose_name="Spécialité")
    domaine_communication = models.CharField(
        max_length=100, 
        choices=DOMAINE_COMMUNICATION_CHOICES, 
        verbose_name="Domaine de communication"
    )
    contribution_number = models.CharField(max_length=50, verbose_name="Numéro de Contribution (Code)", db_column='poster_number')
    titre = models.CharField(max_length=500, verbose_name="Titre")
    auteurs = models.TextField(verbose_name="Auteurs")
    co_auteurs = models.TextField(blank=True, verbose_name="Co-auteurs")
    
    # PDF file
    abstract_file = models.FileField(
        upload_to='contributions/final_submissions/',
        verbose_name="Fichier Abstract (PDF)"
    )
    
    # Metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    # Timestamps
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'dashboard_eposterfinalsubmission'  # Keep existing table name
        ordering = ['-submitted_at']
        verbose_name = 'Scientific Contribution Final Submission'
        verbose_name_plural = 'Scientific Contribution Final Submissions'
        indexes = [
            models.Index(fields=['event', '-submitted_at']),
            models.Index(fields=['contribution_number']),
        ]
    
    def __str__(self):
        return f"{self.contribution_number} - {self.titre[:50]}..."


class ScientificContributionValidation(models.Model):
    """
    Individual validation by a committee member
    Supports real-time tracking of all committee votes
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    submission = models.ForeignKey(
        'ScientificContributionSubmission', 
        on_delete=models.CASCADE, 
        related_name='validations'
    )
    committee_member = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='contribution_validations'
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
        db_table = 'dashboard_epostervalidation'  # Keep existing table name
        unique_together = ('submission', 'committee_member')
        ordering = ['-validated_at']
        verbose_name = 'Scientific Contribution Validation'
        verbose_name_plural = 'Scientific Contribution Validations'
        indexes = [
            models.Index(fields=['submission', 'is_approved']),
            models.Index(fields=['committee_member', '-validated_at']),
        ]
    
    def __str__(self):
        status = "✓" if self.is_approved else "✗"
        return f"{status} {self.submission.titre_travail[:30]}... by {self.committee_member.username}"


class ScientificContributionCommitteeMember(models.Model):
    """
    Scientific Committee Member Assignment for Contribution Review
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(
        Event, 
        on_delete=models.CASCADE, 
        related_name='contribution_committee_members'
    )
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='contribution_committee_memberships'
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
        related_name='contribution_committee_assignments_made'
    )
    
    class Meta:
        db_table = 'dashboard_epostercommitteemember'  # Keep existing table name
        unique_together = ('event', 'user')
        ordering = ['-assigned_at']
        verbose_name = 'Scientific Contribution Committee Member'
        verbose_name_plural = 'Scientific Contribution Committee Members'
    
    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.event.name} ({self.get_role_display()})"
    
    def get_validations_count(self):
        """Get total validations made by this member for this event"""
        return ScientificContributionValidation.objects.filter(
            committee_member=self.user,
            submission__event=self.event
        ).count()
    
    def get_pending_submissions(self):
        """Get submissions this member hasn't reviewed yet"""
        reviewed_ids = ScientificContributionValidation.objects.filter(
            committee_member=self.user,
            submission__event=self.event
        ).values_list('submission_id', flat=True)
        
        return ScientificContributionSubmission.objects.filter(
            event=self.event,
            status='pending'
        ).exclude(id__in=reviewed_ids)


class ScientificContributionEmailTemplate(models.Model):
    """
    Email templates for Scientific Contribution notifications
    8 template types: 4 submission types × 2 decisions (accepted/rejected)
    """
    TYPE_CHOICES = [
        ('e_poster_accepted', 'E-Poster - Acceptation'),
        ('e_poster_rejected', 'E-Poster - Rejet'),
        ('communication_orale_accepted', 'Communication Orale - Acceptation'),
        ('communication_orale_rejected', 'Communication Orale - Rejet'),
        ('table_ronde_accepted', 'Table Ronde - Acceptation'),
        ('table_ronde_rejected', 'Table Ronde - Rejet'),
        ('atelier_accepted', 'Atelier - Acceptation'),
        ('atelier_rejected', 'Atelier - Rejet'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(
        Event, 
        on_delete=models.CASCADE, 
        related_name='contribution_email_templates'
    )
    
    template_type = models.CharField(max_length=35, choices=TYPE_CHOICES)
    subject = models.CharField(max_length=300)
    body_html = models.TextField(help_text="HTML content with placeholders: {{nom}}, {{prenom}}, {{titre}}, {{event_name}}, {{event_location}}, {{event_start_date}}, {{event_end_date}}, {{contribution_code}}, {{final_submission_url}}, {{type_participation}}, {{show_final_submission}}")
    body_text = models.TextField(blank=True, help_text="Plain text version (optional)")
    design_json = models.JSONField(default=dict, blank=True, help_text="Unlayer editor design JSON")
    
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        db_table = 'dashboard_eposteremailtemplate'  # Keep existing table name
        unique_together = ('event', 'template_type')
        ordering = ['template_type']
        verbose_name = 'Scientific Contribution Email Template'
        verbose_name_plural = 'Scientific Contribution Email Templates'
    
    def __str__(self):
        return f"{self.event.name} - {self.get_template_type_display()}"


class EventFormConfiguration(models.Model):
    """
    Tracks which type of form is enabled for each event.
    An event can have both participant and communicant forms.
    """
    FORM_TYPE_CHOICES = [
        ('participant', 'Participant Registration Form'),
        ('communicant', 'Call for Communicants Form'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(
        Event, 
        on_delete=models.CASCADE, 
        related_name='form_configurations'
    )
    form_type = models.CharField(max_length=20, choices=FORM_TYPE_CHOICES)
    
    is_active = models.BooleanField(default=True)
    
    # Form settings
    title = models.CharField(max_length=300, blank=True, help_text="Custom form title (optional)")
    description = models.TextField(blank=True, help_text="Form description/instructions")
    
    # Deadline settings
    submission_deadline = models.DateTimeField(null=True, blank=True)
    allow_late_submissions = models.BooleanField(default=False)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        unique_together = ('event', 'form_type')
        ordering = ['-created_at']
        verbose_name = 'Event Form Configuration'
        verbose_name_plural = 'Event Form Configurations'
    
    def __str__(self):
        return f"{self.event.name} - {self.get_form_type_display()}"


# Signals for automatic actions
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=ScientificContributionValidation)
def check_submission_status_after_validation(sender, instance, created, **kwargs):
    """
    After each validation, check if the submission status should be updated
    """
    if created:
        instance.submission.check_and_update_status()


# Legacy aliases for backward compatibility
EPosterSubmission = ScientificContributionSubmission
EPosterFinalSubmission = ScientificContributionFinalSubmission
EPosterValidation = ScientificContributionValidation
EPosterCommitteeMember = ScientificContributionCommitteeMember
EPosterEmailTemplate = ScientificContributionEmailTemplate
