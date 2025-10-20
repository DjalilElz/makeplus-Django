# events/models.py - Complete Models for MakePlus

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
import uuid

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
        ('organizer', 'Organizer'),
        ('controller', 'Controller'),
        ('participant', 'Participant'),
        ('exhibitor', 'Exhibitor'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='event_assignments')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='user_assignments')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
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
        ('scheduled', 'Scheduled'),
        ('live', 'Live'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
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
    
    theme = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    
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
        return self.status == 'live'
    
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