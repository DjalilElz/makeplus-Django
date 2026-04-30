# events/models.py - Complete Models for MakePlus

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.utils import timezone
from datetime import timedelta
import uuid
import json
import hashlib
import secrets


class EmailLoginCode(models.Model):
    """
    Email-based login codes for passwordless authentication
    Event-scoped, practically infinite expiry
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='login_codes')
    event = models.ForeignKey('Event', on_delete=models.CASCADE, related_name='login_codes')
    
    # Hashed code (6-digit code is hashed before storage)
    code_hash = models.CharField(max_length=64, db_index=True)
    
    # Status
    is_used = models.BooleanField(default=False, help_text="True if code has been used or invalidated")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    used_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Email Login Code'
        verbose_name_plural = 'Email Login Codes'
        indexes = [
            models.Index(fields=['user', 'event', 'is_used']),
            models.Index(fields=['code_hash']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.event.name} - {'Used' if self.is_used else 'Active'}"
    
    @staticmethod
    def hash_code(code):
        """Hash a 6-digit code for secure storage"""
        return hashlib.sha256(code.encode()).hexdigest()
    
    def verify_code(self, code):
        """Verify if provided code matches this record"""
        return self.code_hash == self.hash_code(code) and not self.is_used
    
    def mark_as_used(self, ip_address=None, user_agent=''):
        """Mark code as used"""
        self.is_used = True
        self.used_at = timezone.now()
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.save(update_fields=['is_used', 'used_at', 'ip_address', 'user_agent'])


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
        """Generate or return existing user-level QR code with full participant info"""
        # Always regenerate to get latest data
        user = self.user
        
        # Get user's active event assignment
        from .models import UserEventAssignment, Participant, SessionAccess, RoomAccess
        assignment = UserEventAssignment.objects.filter(
            user=user,
            is_active=True
        ).select_related('event').first()
        
        # Get participant to reuse existing badge_id
        try:
            participant = Participant.objects.get(user=user)
            badge_id = participant.badge_id  # Reuse existing badge_id
        except Participant.DoesNotExist:
            # Generate new badge_id only if participant doesn't exist yet
            badge_id = f"USER-{user.id}-{uuid.uuid4().hex[:8].upper()}"
            participant = None
        
        qr_data = {
            "user_id": user.id,
            "badge_id": badge_id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "full_name": user.get_full_name() or user.email,
        }
        
        # Add event and role info if user has assignment
        if assignment:
            qr_data["role"] = assignment.role
            qr_data["event"] = {
                "id": str(assignment.event.id),
                "name": assignment.event.name,
                "start_date": assignment.event.start_date.isoformat() if assignment.event.start_date else None,
                "end_date": assignment.event.end_date.isoformat() if assignment.event.end_date else None,
            }
            
            if participant:
                # Get event registration for this specific event
                from .models import ParticipantEventRegistration
                event_registration = ParticipantEventRegistration.objects.filter(
                    participant=participant,
                    event=assignment.event
                ).first()
                
                qr_data["participant_id"] = str(participant.id)
                
                # Check-in status is per-event
                if event_registration:
                    qr_data["is_checked_in"] = event_registration.is_checked_in
                    qr_data["checked_in_at"] = event_registration.checked_in_at.isoformat() if event_registration.checked_in_at else None
                else:
                    qr_data["is_checked_in"] = False
                    qr_data["checked_in_at"] = None
                
                # Get ALL paid items from CaisseTransaction (sessions, access, dinner, other)
                paid_items = []
                seen_items = set()  # Track unique items
                
                # Query all completed transactions for this participant
                from caisse.models import CaisseTransaction
                import logging
                logger = logging.getLogger(__name__)
                
                completed_transactions = CaisseTransaction.objects.filter(
                    participant=participant,
                    status='completed'
                ).prefetch_related('items', 'items__session')
                
                logger.info(f"[QR GEN] Generating QR code for {user.email}")
                logger.info(f"[QR GEN] Found {completed_transactions.count()} completed transactions")
                
                # Fetch all paid items from transactions
                for transaction in completed_transactions:
                    logger.info(f"[QR GEN]   Transaction {transaction.id}: status={transaction.status}, items={transaction.items.count()}")
                    
                    for item in transaction.items.all():
                        # Create unique key for this item
                        if item.session:
                            unique_key = f"session-{item.session.id}"
                        else:
                            unique_key = f"{item.item_type}-{item.id}"
                        
                        # Skip if already added
                        if unique_key in seen_items:
                            continue
                        
                        seen_items.add(unique_key)
                        
                        # Build paid item data
                        paid_item = {
                            "type": item.item_type,  # 'session', 'access', 'dinner', 'other'
                            "id": str(item.session.id) if item.session else str(item.id),
                            "title": item.name,
                            "is_paid": True,
                            "payment_status": "paid",
                            "amount_paid": float(item.price),
                            "has_access": True
                        }
                        
                        paid_items.append(paid_item)
                        logger.info(f"[QR GEN]     Added: {item.name} ({item.item_type})")
                
                logger.info(f"[QR GEN] Total paid items: {len(paid_items)}")
                
                qr_data["paid_items"] = paid_items
                qr_data["total_paid_items"] = len([item for item in paid_items if item['is_paid']])
                
                # Summary for quick check
                qr_data["access_summary"] = {
                    "total_sessions": len([item for item in paid_items if item['type'] == 'session']),
                    "paid_sessions": len([item for item in paid_items if item['type'] == 'session' and item['is_paid']]),
                    "total_rooms": len([item for item in paid_items if item['type'] == 'room']),
                    "has_any_paid_access": any(item['is_paid'] for item in paid_items)
                }
        
        self.qr_code_data = qr_data
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
    location_url = models.URLField(blank=True, null=True, help_text="Google Maps URL for event location")
    location_details = models.TextField(blank=True)
    logo = models.ImageField(upload_to='events/logos/', blank=True, null=True, help_text="Event logo image")
    banner = models.ImageField(upload_to='events/banners/', blank=True, null=True, help_text="Event banner image")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='upcoming')
    
    # Registration settings
    registration_enabled = models.BooleanField(default=True, help_text="Enable public registration for this event")
    registration_description = models.TextField(blank=True, help_text="Custom registration page description")
    registration_fields_config = models.JSONField(default=dict, blank=True, help_text="Configuration for which fields are enabled/required")
    
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
    
    def get_dynamic_status(self):
        """Calculate status based on dates"""
        from django.utils import timezone
        now = timezone.now()
        
        if self.status == 'cancelled':
            return 'cancelled'
        
        if now < self.start_date:
            return 'upcoming'
        elif now > self.end_date:
            return 'completed'
        else:
            return 'active'

    def get_dynamic_status(self):
        """Calculate status based on dates"""
        from django.utils import timezone
        now = timezone.now()

        if self.status == 'cancelled':
            return 'cancelled'

        if now < self.start_date:
            return 'upcoming'
        elif now > self.end_date:
            return 'completed'
        else:
            return 'active'


class UserEventAssignment(models.Model):
    """User-Event Role Assignment"""
    ROLE_CHOICES = [
        ('gestionnaire_des_salles', 'Gestionnaire de Salle'),
        ('controlleur_des_badges', 'Contrôleur'),
        ('exposant', 'Exposant'),
        ('committee', 'Committee'),
        ('participant', 'Participant'),  # Auto-created via registration form, not by admin
    ]
    
    # Roles that admin can create manually
    ADMIN_CREATABLE_ROLES = [
        ('gestionnaire_des_salles', 'Gestionnaire de Salle'),
        ('controlleur_des_badges', 'Contrôleur'),
        ('exposant', 'Exposant'),
        ('committee', 'Committee'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='event_assignments')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='user_assignments')
    role = models.CharField(max_length=30, choices=ROLE_CHOICES)
    is_active = models.BooleanField(default=True)
    assigned_at = models.DateTimeField(auto_now_add=True)
    assigned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='assigned_users')
    metadata = models.JSONField(default=dict, blank=True, help_text="Additional data like assigned_room_id")
    
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
        ('communication', 'Communication'),
        ('table_ronde', 'Table ronde'),
        ('lunch_symposium', 'Lunch symposium'),
        ('symposium', 'Symposium'),
        ('session_photo', 'Session photo de communication'),
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
    max_participants = models.IntegerField(null=True, blank=True, help_text="Maximum number of participants (leave empty for unlimited)")
    
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
    """Event Participant - One participant per user, can register for multiple events"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='participant_profile')
    events = models.ManyToManyField(Event, through='ParticipantEventRegistration', related_name='registered_participants')
    
    # Participant details
    badge_id = models.CharField(max_length=100, unique=True)
    qr_code_data = models.JSONField(default=dict, blank=True, help_text="QR code content as JSON")
    
    # Role (always participant for users who sign up via mobile app)
    role = models.CharField(max_length=30, default='participant', editable=False)
    
    # Exposant plan (PDF file for exposants only)
    plan_file = models.FileField(upload_to='exposants/plans/', blank=True, null=True, help_text="Plan PDF for exposants")
    
    # Additional data
    metadata = models.JSONField(default=dict, blank=True, help_text="Additional data like profile_picture_url")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['badge_id']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - Participant"
    
    def get_registered_events(self):
        """Get all events this participant is registered for"""
        return self.events.all()
    
    def is_registered_for_event(self, event):
        """Check if participant is registered for a specific event"""
        return self.events.filter(id=event.id).exists()


class ParticipantEventRegistration(models.Model):
    """Through model for Participant-Event relationship"""
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE, related_name='registrations')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='participant_registrations')
    
    # Registration status
    is_checked_in = models.BooleanField(default=False)
    checked_in_at = models.DateTimeField(null=True, blank=True)
    
    # Access control for this specific event
    allowed_rooms = models.ManyToManyField(Room, blank=True, related_name='allowed_participants')
    
    # Registration metadata
    registered_at = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(default=dict, blank=True, help_text="Event-specific data")
    
    class Meta:
        unique_together = ('participant', 'event')
        indexes = [
            models.Index(fields=['event', 'is_checked_in']),
            models.Index(fields=['participant', 'event']),
        ]
    
    def __str__(self):
        return f"{self.participant.user.username} - {self.event.name}"


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
    notes = models.TextField(blank=True, null=True, help_text="Optional notes about the visit")
    
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


class EventRegistration(models.Model):
    """Public event registration submissions"""
    SECTEUR_CHOICES = [
        ('prive', 'Privé'),
        ('public', 'Public'),
    ]
    
    PAYS_CHOICES = [
        ('algerie', 'Algérie'),
        ('maroc', 'Maroc'),
        ('tunisie', 'Tunisie'),
        ('autre', 'Autre'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='registrations')
    
    # Personal Information (Ordered as per requirements)
    nom = models.CharField(max_length=100, help_text="Last name")
    prenom = models.CharField(max_length=100, help_text="First name")
    email = models.EmailField(help_text="Email address")
    telephone = models.CharField(max_length=20, help_text="Phone number")
    
    # Location
    pays = models.CharField(max_length=100, default='algerie', help_text="Country")
    wilaya = models.CharField(max_length=100, blank=True, help_text="Wilaya (for Algeria)")
    
    # Professional Information
    secteur = models.CharField(max_length=20, choices=SECTEUR_CHOICES, help_text="Sector: Private or Public")
    etablissement = models.CharField(max_length=200, help_text="Institution/Organization")
    specialite = models.CharField(max_length=200, blank=True, help_text="Specialty/Field")
    
    # Workshop Selection (stored as JSON: {day: [workshop_ids]})
    ateliers_selected = models.JSONField(default=dict, blank=True, help_text="Selected workshops per day")
    
    # Status
    is_confirmed = models.BooleanField(default=False, help_text="Email confirmation status")
    confirmation_sent_at = models.DateTimeField(null=True, blank=True)
    
    # User account (created after confirmation)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='event_registrations')
    participant = models.ForeignKey(Participant, on_delete=models.SET_NULL, null=True, blank=True, related_name='registration')
    
    # Anti-spam
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    spam_score = models.IntegerField(default=0, help_text="Higher score = more likely spam")
    is_spam = models.BooleanField(default=False)
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Event Registration'
        verbose_name_plural = 'Event Registrations'
        indexes = [
            models.Index(fields=['event', '-created_at']),
            models.Index(fields=['email', 'event']),
            models.Index(fields=['is_confirmed']),
            models.Index(fields=['is_spam']),
        ]
    
    def __str__(self):
        return f"{self.prenom} {self.nom} - {self.event.name}"
    
    def get_full_name(self):
        """Return full name"""
        return f"{self.prenom} {self.nom}"



# ============================================
# Verification Models for Sign Up and Form Registration
# ============================================

class SignUpVerification(models.Model):
    """
    Email verification codes for user sign up
    Expires after 3 minutes
    """
    email = models.EmailField(db_index=True)
    code_hash = models.CharField(max_length=64, db_index=True)
    
    # Store signup data temporarily until verified
    signup_data = models.JSONField(default=dict, blank=True, help_text="Temporary storage for first_name, last_name, password_hash")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    expires_at = models.DateTimeField(db_index=True)
    
    # Status
    is_used = models.BooleanField(default=False, db_index=True)
    used_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Sign Up Verification'
        verbose_name_plural = 'Sign Up Verifications'
        indexes = [
            models.Index(fields=['email', 'is_used', '-created_at']),
            models.Index(fields=['code_hash', 'is_used']),
            models.Index(fields=['expires_at', 'is_used']),
        ]
    
    def __str__(self):
        return f"{self.email} - {'Used' if self.is_used else 'Active'}"
    
    @staticmethod
    def hash_code(code):
        """Hash a 6-digit code for secure storage"""
        return hashlib.sha256(code.encode()).hexdigest()
    
    @staticmethod
    def generate_code():
        """Generate a random 6-digit code"""
        return ''.join([str(secrets.randbelow(10)) for _ in range(6)])
    
    def is_expired(self):
        """Check if code has expired"""
        return timezone.now() > self.expires_at
    
    def verify_code(self, code):
        """Verify if provided code matches and is valid"""
        if self.is_used:
            return False, "Code already used"
        if self.is_expired():
            return False, "Code expired"
        if self.code_hash != self.hash_code(code):
            return False, "Invalid code"
        return True, "Code verified"
    
    def mark_as_used(self, ip_address=None, user_agent=''):
        """Mark code as used"""
        self.is_used = True
        self.used_at = timezone.now()
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.save(update_fields=['is_used', 'used_at', 'ip_address', 'user_agent'])
    
    @classmethod
    def create_verification(cls, email, signup_data=None, ip_address=None, user_agent=''):
        """Create a new verification code"""
        code = cls.generate_code()
        expires_at = timezone.now() + timedelta(minutes=3)
        
        verification = cls.objects.create(
            email=email,
            code_hash=cls.hash_code(code),
            signup_data=signup_data or {},
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return code, verification
    
    @classmethod
    def can_resend(cls, email):
        """Check if user can request a new code (3 minutes since last request)"""
        last_code = cls.objects.filter(email=email).order_by('-created_at').first()
        if not last_code:
            return True, None
        
        time_since_last = timezone.now() - last_code.created_at
        if time_since_last < timedelta(minutes=3):
            wait_seconds = int((timedelta(minutes=3) - time_since_last).total_seconds())
            return False, wait_seconds
        
        return True, None


class FormRegistrationVerification(models.Model):
    """
    Verification codes for event registration form validation
    Expires after 3 minutes
    """
    email = models.EmailField(db_index=True)
    form = models.ForeignKey('dashboard.FormConfiguration', on_delete=models.CASCADE, related_name='verifications')
    code_hash = models.CharField(max_length=64, db_index=True)
    
    # Form submission data (stored temporarily until verified)
    form_data = models.JSONField(default=dict)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    expires_at = models.DateTimeField(db_index=True)
    
    # Status
    is_used = models.BooleanField(default=False, db_index=True)
    used_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Form Registration Verification'
        verbose_name_plural = 'Form Registration Verifications'
        indexes = [
            models.Index(fields=['email', 'form', 'is_used', '-created_at']),
            models.Index(fields=['code_hash', 'is_used']),
            models.Index(fields=['expires_at', 'is_used']),
        ]
    
    def __str__(self):
        return f"{self.email} - {self.form.name} - {'Used' if self.is_used else 'Active'}"
    
    @staticmethod
    def hash_code(code):
        """Hash a 6-digit code for secure storage"""
        return hashlib.sha256(code.encode()).hexdigest()
    
    @staticmethod
    def generate_code():
        """Generate a random 6-digit code"""
        return ''.join([str(secrets.randbelow(10)) for _ in range(6)])
    
    def is_expired(self):
        """Check if code has expired"""
        return timezone.now() > self.expires_at
    
    def verify_code(self, code):
        """Verify if provided code matches and is valid"""
        if self.is_used:
            return False, "Code already used"
        if self.is_expired():
            return False, "Code expired"
        if self.code_hash != self.hash_code(code):
            return False, "Invalid code"
        return True, "Code verified"
    
    def mark_as_used(self, ip_address=None, user_agent=''):
        """Mark code as used"""
        self.is_used = True
        self.used_at = timezone.now()
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.save(update_fields=['is_used', 'used_at', 'ip_address', 'user_agent'])
    
    @classmethod
    def create_verification(cls, email, form, form_data, ip_address=None, user_agent=''):
        """Create a new verification code"""
        code = cls.generate_code()
        expires_at = timezone.now() + timedelta(minutes=3)
        
        verification = cls.objects.create(
            email=email,
            form=form,
            code_hash=cls.hash_code(code),
            form_data=form_data,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return code, verification
    
    @classmethod
    def can_resend(cls, email, form):
        """Check if user can request a new code (3 minutes since last request)"""
        last_code = cls.objects.filter(
            email=email,
            form=form
        ).order_by('-created_at').first()
        
        if not last_code:
            return True, None
        
        time_since_last = timezone.now() - last_code.created_at
        if time_since_last < timedelta(minutes=3):
            wait_seconds = int((timedelta(minutes=3) - time_since_last).total_seconds())
            return False, wait_seconds
        
        return True, None


class ControllerScan(models.Model):
    """Track controller badge scans (for statistics and audit trail)"""
    controller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='controller_scans', help_text="Controller who scanned")
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='controller_scans')
    
    # Participant info (denormalized for performance and history)
    participant_user_id = models.IntegerField(help_text="User ID of scanned participant")
    badge_id = models.CharField(max_length=100, help_text="Badge ID scanned")
    participant_name = models.CharField(max_length=255, help_text="Participant full name")
    participant_email = models.EmailField(help_text="Participant email")
    
    # Scan details
    scanned_at = models.DateTimeField(auto_now_add=True, db_index=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('success', 'Success'),
            ('error', 'Error'),
            ('not_registered', 'Not Registered'),
        ],
        default='success'
    )
    error_message = models.TextField(blank=True, help_text="Error message if scan failed")
    
    # Metadata
    total_paid_items = models.IntegerField(default=0, help_text="Number of paid items at scan time")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Total amount paid")
    
    class Meta:
        ordering = ['-scanned_at']
        indexes = [
            models.Index(fields=['controller', '-scanned_at']),
            models.Index(fields=['event', '-scanned_at']),
            models.Index(fields=['controller', 'event', '-scanned_at']),
        ]
    
    def __str__(self):
        return f"{self.controller.username} scanned {self.participant_name} at {self.scanned_at}"
