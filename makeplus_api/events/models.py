# events/models.py - Complete Models for MakePlus

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
import uuid
import json


class UserProfile(models.Model):
    """
    User Profile - Stores user-level QR code (ONE per user across all events)
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    qr_code_data = models.JSONField(default=dict, blank=True, help_text="User's QR code data (used across all events)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"
    
    def __str__(self):
        return f"Profile: {self.user.username}"
    
    def get_or_create_qr_code(self):
        """Generate or return existing user-level QR code"""
        if not self.qr_code_data:
            # Generate unique badge ID for user
            badge_id = f"USER-{self.user.id}-{uuid.uuid4().hex[:8].upper()}"
            self.qr_code_data = {
                "user_id": self.user.id,
                "badge_id": badge_id
            }
            self.save()
        return self.qr_code_data
    
    @staticmethod
    def get_qr_for_user(user):
        """Get or create user profile and return QR code"""
        profile, created = UserProfile.objects.get_or_create(user=user)
        return profile.get_or_create_qr_code()


class Event(models.Model):
    """Main Event Model"""
    STATUS_CHOICES = [
        ('upcoming', 'Upcoming'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    location = models.CharField(max_length=200)
    location_details = models.TextField(blank=True)
    logo_url = models.URLField(blank=True)
    banner_url = models.URLField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='upcoming')
    
    # Event configuration
    settings = models.JSONField(default=dict, blank=True)
    themes = models.JSONField(default=list, blank=True)
    
    # Auto-calculated stats
    total_participants = models.IntegerField(default=0)
    total_exhibitors = models.IntegerField(default=0)
    total_rooms = models.IntegerField(default=0)
    
    organizer_contact = models.EmailField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    # Event files
    programme_file = models.FileField(upload_to='events/programmes/', blank=True, null=True, help_text="Event programme PDF")
    guide_file = models.FileField(upload_to='events/guides/', blank=True, null=True, help_text="Event guide PDF")
    
    # Event president
    president = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='presided_events', help_text="Event president")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_events')
    
    class Meta:
        ordering = ['-start_date']
        indexes = [
            models.Index(fields=['status', '-start_date']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.start_date.year})"


class UserEventAssignment(models.Model):
    """User-Event Role Assignment"""
    ROLE_CHOICES = [
        ('gestionnaire_des_salles', 'Gestionnaire des Salles'),
        ('controlleur_des_badges', 'Contrôleur des Badges'),
        ('participant', 'Participant'),
        ('exposant', 'Exposant'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='event_assignments')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='user_assignments')
    role = models.CharField(max_length=30, choices=ROLE_CHOICES)
    is_active = models.BooleanField(default=True)
    assigned_at = models.DateTimeField(auto_now_add=True)
    assigned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='assigned_users')
    
    class Meta:
        unique_together = ('user', 'event')
        indexes = [
            models.Index(fields=['event', 'role', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.event.name} ({self.role})"


class Room(models.Model):
    """Event Room/Hall"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='rooms')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    capacity = models.IntegerField(validators=[MinValueValidator(1)])
    location = models.CharField(max_length=200, help_text="Location within venue")
    
    # Current status
    current_participants = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['event', 'is_active']),
        ]
        unique_together = ('event', 'name')
    
    def __str__(self):
        return f"{self.event.name} - {self.name}"
    
    @property
    def occupancy_percentage(self):
        """Calculate room occupancy"""
        if self.capacity == 0:
            return 0
        return (self.current_participants / self.capacity) * 100


class Session(models.Model):
    """Event Session/Conference"""
    STATUS_CHOICES = [
        ('pas_encore', 'Pas Encore'),
        ('en_cours', 'En Cours'),
        ('termine', 'Terminé'),
    ]
    
    TYPE_CHOICES = [
        ('conference', 'Conférence'),
        ('atelier', 'Atelier'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='sessions')
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='sessions')
    
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    
    # Speaker info
    speaker_name = models.CharField(max_length=100, blank=True)
    speaker_title = models.CharField(max_length=100, blank=True)
    speaker_bio = models.TextField(blank=True)
    speaker_photo_url = models.URLField(blank=True)
    
    # Session type and status
    theme = models.CharField(max_length=100, blank=True)
    session_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='conference')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pas_encore')
    
    # Payment for ateliers
    is_paid = models.BooleanField(default=False, help_text="Paid atelier (participants must pay)")
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Price for paid ateliers")
    
    # Live streaming
    youtube_live_url = models.URLField(blank=True, help_text="YouTube live stream URL")
    
    # Cover image
    cover_image_url = models.URLField(blank=True)
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        ordering = ['start_time']
        indexes = [
            models.Index(fields=['event', 'start_time']),
            models.Index(fields=['room', 'start_time']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.event.name} - {self.title}"
    
    @property
    def is_live(self):
        return self.status == 'en_cours'
    
    def duration_minutes(self):
        """Calculate session duration in minutes"""
        return int((self.end_time - self.start_time).total_seconds() / 60)


class Participant(models.Model):
    """Event Participant"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='participations')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='participants')
    
    # Participant details
    badge_id = models.CharField(max_length=100, unique=True)
    qr_code_data = models.TextField(help_text="QR code content")
    
    # Status
    is_checked_in = models.BooleanField(default=False)
    checked_in_at = models.DateTimeField(null=True, blank=True)
    
    # Access
    allowed_rooms = models.ManyToManyField(Room, blank=True, related_name='allowed_participants')
    
    # Exposant plan (PDF file for exposants only)
    plan_file = models.FileField(upload_to='exposants/plans/', blank=True, null=True, help_text="Plan PDF for exposants")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('user', 'event')
        indexes = [
            models.Index(fields=['event', 'is_checked_in']),
            models.Index(fields=['badge_id']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.event.name}"


class RoomAccess(models.Model):
    """Track room access/check-ins"""
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE, related_name='room_accesses')
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='accesses')
    session = models.ForeignKey(Session, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Access details
    accessed_at = models.DateTimeField(auto_now_add=True)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, help_text="Controller who verified")
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=[('granted', 'Granted'), ('denied', 'Denied')],
        default='granted'
    )
    denial_reason = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-accessed_at']
        indexes = [
            models.Index(fields=['room', '-accessed_at']),
            models.Index(fields=['participant', '-accessed_at']),
        ]
    
    def __str__(self):
        return f"{self.participant.user.username} - {self.room.name} - {self.accessed_at}"


class SessionAccess(models.Model):
    """Track participant access to paid ateliers"""
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE, related_name='session_accesses')
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='participant_accesses')
    
    # Access and payment
    has_access = models.BooleanField(default=False)
    payment_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'En Attente'),
            ('paid', 'Payé'),
            ('free', 'Gratuit')
        ],
        default='pending'
    )
    paid_at = models.DateTimeField(null=True, blank=True)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('participant', 'session')
        verbose_name = 'Session Access'
        verbose_name_plural = 'Session Accesses'
        indexes = [
            models.Index(fields=['session', 'payment_status']),
            models.Index(fields=['participant', 'has_access']),
        ]
    
    def __str__(self):
        return f"{self.participant.user.username} - {self.session.title} ({self.payment_status})"


class Annonce(models.Model):
    """Event announcements targeted to specific user groups"""
    TARGET_CHOICES = [
        ('all', 'Tous'),
        ('participants', 'Participants'),
        ('exposants', 'Exposants'),
        ('controlleurs', 'Contrôleurs'),
        ('gestionnaires', 'Gestionnaires'),
    ]
    
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='annonces')
    title = models.CharField(max_length=200)
    description = models.TextField()
    target = models.CharField(max_length=20, choices=TARGET_CHOICES)
    
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_annonces')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Annonce'
        verbose_name_plural = 'Annonces'
        indexes = [
            models.Index(fields=['event', 'target', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.event.name} ({self.target})"


class SessionQuestion(models.Model):
    """Questions asked by participants during sessions"""
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='questions')
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE, related_name='questions')
    
    question_text = models.TextField()
    
    # Answer
    is_answered = models.BooleanField(default=False)
    answer_text = models.TextField(blank=True)
    answered_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='answered_questions')
    answered_at = models.DateTimeField(null=True, blank=True)
    
    asked_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['asked_at']
        verbose_name = 'Session Question'
        verbose_name_plural = 'Session Questions'
        indexes = [
            models.Index(fields=['session', 'asked_at']),
            models.Index(fields=['is_answered']),
        ]
    
    def __str__(self):
        return f"Q: {self.question_text[:50]}... - {self.session.title}"


class RoomAssignment(models.Model):
    """Assign gestionnaires/controllers to specific rooms at specific times"""
    ROLE_CHOICES = [
        ('gestionnaire_des_salles', 'Gestionnaire des Salles'),
        ('controlleur_des_badges', 'Contrôleur des Badges'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='room_assignments')
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='assigned_staff')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='room_assignments')
    
    role = models.CharField(max_length=30, choices=ROLE_CHOICES)
    
    # Time slot for assignment
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    
    is_active = models.BooleanField(default=True)
    assigned_at = models.DateTimeField(auto_now_add=True)
    assigned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='room_assignments_made')
    
    class Meta:
        ordering = ['start_time']
        verbose_name = 'Room Assignment'
        verbose_name_plural = 'Room Assignments'
        indexes = [
            models.Index(fields=['user', 'room', 'start_time']),
            models.Index(fields=['event', 'is_active']),
            models.Index(fields=['room', 'start_time', 'end_time']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.room.name} ({self.start_time.date()})"
    
    def clean(self):
        """Validate that end_time is after start_time"""
        from django.core.exceptions import ValidationError
        if self.end_time and self.start_time and self.end_time <= self.start_time:
            raise ValidationError({'end_time': 'End time must be after start time'})


class ExposantScan(models.Model):
    """Track exposant scanning participant QR codes (for booth visits)"""
    exposant = models.ForeignKey(Participant, on_delete=models.CASCADE, related_name='scanned_participants')
    scanned_participant = models.ForeignKey(Participant, on_delete=models.CASCADE, related_name='exposant_scans')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='exposant_scans')
    
    scanned_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, help_text="Optional notes about the visit")
    
    class Meta:
        ordering = ['-scanned_at']
        verbose_name = 'Exposant Scan'
        verbose_name_plural = 'Exposant Scans'
        indexes = [
            models.Index(fields=['exposant', '-scanned_at']),
            models.Index(fields=['event', '-scanned_at']),
            models.Index(fields=['scanned_participant', '-scanned_at']),
        ]
    
    def __str__(self):
        return f"{self.exposant.user.username} scanned {self.scanned_participant.user.username}"


# Signals to auto-update statistics
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

@receiver([post_save, post_delete], sender=Room)
def update_event_room_count(sender, instance, **kwargs):
    """Auto-update event's total_rooms count"""
    event = instance.event
    event.total_rooms = event.rooms.filter(is_active=True).count()
    event.save(update_fields=['total_rooms'])

@receiver([post_save, post_delete], sender=RoomAccess)
def update_room_participant_count(sender, instance, **kwargs):
    """Auto-update room's current_participants count"""
    room = instance.room
    room.current_participants = room.accesses.filter(
        status='granted',
        accessed_at__date=room.event.start_date.date()
    ).values('participant').distinct().count()
    room.save(update_fields=['current_participants'])