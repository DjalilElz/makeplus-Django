from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from events.models import Event, Participant


class EmailTemplate(models.Model):
    """Global email template that can be reused across events"""
    name = models.CharField(max_length=200, help_text="Template name for easy identification")
    subject = models.CharField(max_length=300, help_text="Email subject line")
    body = models.TextField(help_text="Email body content (supports HTML)")
    description = models.TextField(blank=True, help_text="Internal description of template purpose")
    
    # Available variables for template substitution
    # {{event_name}}, {{participant_name}}, {{event_date}}, {{event_location}}, etc.
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='email_templates_created')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Email Template"
        verbose_name_plural = "Email Templates"
        ordering = ['-created_at']
        
    def __str__(self):
        return self.name


class EventEmailTemplate(models.Model):
    """Event-specific customized email template"""
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='email_templates')
    base_template = models.ForeignKey(EmailTemplate, on_delete=models.SET_NULL, null=True, blank=True, 
                                      related_name='event_customizations',
                                      help_text="Original template this was based on")
    
    name = models.CharField(max_length=200, help_text="Customized template name")
    subject = models.CharField(max_length=300, help_text="Customized email subject")
    body = models.TextField(help_text="Customized email body (supports HTML)")
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='event_email_templates')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Event Email Template"
        verbose_name_plural = "Event Email Templates"
        ordering = ['-created_at']
        unique_together = ['event', 'name']
        
    def __str__(self):
        return f"{self.event.name} - {self.name}"


class EmailLog(models.Model):
    """Track sent emails"""
    TARGET_TYPE_CHOICES = [
        ('all_participants', 'All Event Participants'),
        ('attended', 'Participants Who Attended'),
        ('not_attended', 'Participants Who Did Not Attend'),
        ('paid', 'Participants Who Paid'),
        ('not_paid', 'Participants Who Did Not Pay'),
        ('custom', 'Custom Selection'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sending', 'Sending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
    ]
    
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='email_logs')
    template = models.ForeignKey(EventEmailTemplate, on_delete=models.SET_NULL, null=True, related_name='logs')
    
    subject = models.CharField(max_length=300)
    body = models.TextField()
    
    # Target settings
    target_type = models.CharField(max_length=50, choices=TARGET_TYPE_CHOICES)
    recipient_count = models.IntegerField(default=0, help_text="Number of recipients")
    recipients = models.ManyToManyField(Participant, related_name='received_emails', blank=True)
    
    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    sent_count = models.IntegerField(default=0, help_text="Number successfully sent")
    failed_count = models.IntegerField(default=0, help_text="Number failed to send")
    error_message = models.TextField(blank=True)
    
    # Metadata
    sent_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='emails_sent')
    created_at = models.DateTimeField(default=timezone.now)
    sent_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Email Log"
        verbose_name_plural = "Email Logs"
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.event.name} - {self.subject} ({self.status})"
