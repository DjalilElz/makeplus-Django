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
        """Get value for a specific field"""
        return self.data.get(field_name, '')
