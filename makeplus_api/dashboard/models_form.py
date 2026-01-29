"""
Form Configuration Models
"""
from django.db import models
from django.contrib.auth.models import User
from events.models import Event
import uuid


class FormConfiguration(models.Model):
    """Custom registration form configuration"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    slug = models.SlugField(max_length=255, unique=True)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, null=True, blank=True, related_name='custom_forms')
    
    # Banner image for the form (optional)
    banner_image = models.ImageField(upload_to='forms/banners/', blank=True, null=True, help_text="Optional banner image for the form. If not set, will use event banner if form is linked to an event.")
    
    # JSON field to store form fields configuration
    # Structure: [{"name": "field_name", "label": "Field Label", "type": "text|email|tel|textarea|select", "required": true, "options": [...]}]
    fields_config = models.JSONField(default=list)
    
    # Settings
    is_active = models.BooleanField(default=True)
    allow_multiple_submissions = models.BooleanField(default=False)
    show_on_event_page = models.BooleanField(default=True)
    
    # Success message after submission
    success_message = models.TextField(default="Thank you for your registration! We will contact you soon.")
    
    # Email notification settings
    send_confirmation_email = models.BooleanField(default=True)
    confirmation_email_template = models.ForeignKey(
        'EmailTemplate', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='form_confirmations'
    )
    
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_forms')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Statistics
    submission_count = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Form Configuration'
        verbose_name_plural = 'Form Configurations'
    
    def __str__(self):
        return self.name
    
    def get_public_url(self):
        """Get the public URL for this form"""
        return f"/forms/{self.slug}/"
    
    def increment_submission_count(self):
        """Increment submission count"""
        self.submission_count += 1
        self.save(update_fields=['submission_count'])


class FormSubmission(models.Model):
    """Store form submissions"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    form = models.ForeignKey(FormConfiguration, on_delete=models.CASCADE, related_name='submissions')
    
    # Store all form data as JSON
    # Structure: {"field_name": "value", ...}
    data = models.JSONField(default=dict)
    
    # Participant info (if provided)
    email = models.EmailField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    # Status
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('spam', 'Marked as Spam'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Admin notes
    admin_notes = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_submissions')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    submitted_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-submitted_at']
        verbose_name = 'Form Submission'
        verbose_name_plural = 'Form Submissions'
    
    def __str__(self):
        return f"Submission for {self.form.name} at {self.submitted_at}"
    
    def get_field_value(self, field_name):
        """Get the value of a specific field"""
        return self.data.get(field_name, '')


class FormAnalytics(models.Model):
    """Track form analytics and statistics"""
    form = models.OneToOneField(FormConfiguration, on_delete=models.CASCADE, related_name='analytics')
    
    # View statistics
    total_views = models.IntegerField(default=0, help_text="Total number of form views")
    unique_views = models.IntegerField(default=0, help_text="Unique visitors")
    
    # Submission statistics
    total_submissions = models.IntegerField(default=0)
    completed_submissions = models.IntegerField(default=0)
    abandoned_submissions = models.IntegerField(default=0)
    
    # Conversion tracking
    conversion_rate = models.FloatField(default=0.0, help_text="Percentage of views that resulted in submissions")
    average_completion_time = models.IntegerField(default=0, help_text="Average time to complete form in seconds")
    
    # Field-level analytics (JSON structure)
    # {"field_name": {"interactions": 10, "completion_rate": 95.5, "average_time": 15}}
    field_analytics = models.JSONField(default=dict, blank=True)
    
    # Traffic sources
    traffic_sources = models.JSONField(default=dict, blank=True, help_text="Breakdown of traffic sources")
    
    # Device/Browser breakdown
    device_breakdown = models.JSONField(default=dict, blank=True)
    browser_breakdown = models.JSONField(default=dict, blank=True)
    
    # Time-based analytics
    hourly_stats = models.JSONField(default=dict, blank=True, help_text="Submissions by hour")
    daily_stats = models.JSONField(default=dict, blank=True, help_text="Submissions by day")
    
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Form Analytics'
        verbose_name_plural = 'Form Analytics'
    
    def __str__(self):
        return f"Analytics for {self.form.name}"
    
    def update_conversion_rate(self):
        """Recalculate conversion rate"""
        if self.total_views > 0:
            self.conversion_rate = round((self.total_submissions / self.total_views) * 100, 2)
        else:
            self.conversion_rate = 0.0
        self.save(update_fields=['conversion_rate'])


class FormView(models.Model):
    """Track individual form views for analytics"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    form = models.ForeignKey(FormConfiguration, on_delete=models.CASCADE, related_name='views')
    
    # Session tracking
    session_id = models.CharField(max_length=100, db_index=True)
    
    # Visitor info
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    device_type = models.CharField(max_length=50, blank=True)  # mobile, tablet, desktop
    browser = models.CharField(max_length=50, blank=True)
    os = models.CharField(max_length=50, blank=True)
    
    # Referrer info
    referer = models.TextField(blank=True)
    utm_source = models.CharField(max_length=100, blank=True)
    utm_medium = models.CharField(max_length=100, blank=True)
    utm_campaign = models.CharField(max_length=100, blank=True)
    
    # Engagement
    time_on_page = models.IntegerField(default=0, help_text="Time spent on form in seconds")
    fields_interacted = models.JSONField(default=list, help_text="List of field names user interacted with")
    completed = models.BooleanField(default=False, help_text="Did user submit the form")
    
    viewed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-viewed_at']
        verbose_name = 'Form View'
        verbose_name_plural = 'Form Views'
        indexes = [
            models.Index(fields=['form', 'session_id']),
            models.Index(fields=['viewed_at']),
        ]
    
    def __str__(self):
        return f"View of {self.form.name} at {self.viewed_at}"


class FormFieldInteraction(models.Model):
    """Track interactions with individual form fields"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    form_view = models.ForeignKey(FormView, on_delete=models.CASCADE, related_name='field_interactions')
    
    field_name = models.CharField(max_length=100)
    
    # Interaction tracking
    focused_at = models.DateTimeField(null=True, blank=True)
    blurred_at = models.DateTimeField(null=True, blank=True)
    time_spent = models.IntegerField(default=0, help_text="Time spent on this field in seconds")
    
    # Value tracking
    initial_value = models.TextField(blank=True)
    final_value = models.TextField(blank=True)
    changes_count = models.IntegerField(default=0, help_text="Number of times value was changed")
    
    # Completion
    completed = models.BooleanField(default=False, help_text="Did user complete this field")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
        verbose_name = 'Form Field Interaction'
        verbose_name_plural = 'Form Field Interactions'
    
    def __str__(self):
        return f"{self.field_name} interaction"

        """Get value for a specific field"""
        return self.data.get(field_name, '')
