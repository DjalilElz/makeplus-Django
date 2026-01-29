from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from events.models import Event, Participant
import uuid
import hashlib


class EmailTemplate(models.Model):
    """Global email template that can be reused across events"""
    TYPE_CHOICES = [
        ('invitation', 'Invitation'),
        ('confirmation', 'Confirmation'),
        ('reminder', 'Reminder'),
        ('follow_up', 'Follow-up'),
        ('announcement', 'Announcement'),
        ('custom', 'Custom'),
    ]
    
    name = models.CharField(max_length=200, help_text="Template name for easy identification")
    subject = models.CharField(max_length=300, help_text="Email subject line")
    from_email = models.EmailField(max_length=200, blank=True, help_text="Sender email address (leave blank to use default)")
    body = models.TextField(help_text="Email body content (supports HTML)")
    body_html = models.TextField(blank=True, help_text="Visual builder HTML output")
    description = models.TextField(blank=True, help_text="Internal description of template purpose")
    
    template_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='custom', help_text="Type of email template")
    
    # Visual builder configuration (stores builder state)
    builder_config = models.JSONField(default=dict, blank=True, help_text="Visual email builder configuration")
    
    # Available variables for template substitution
    # {{event_name}}, {{participant_name}}, {{first_name}}, {{last_name}}, 
    # {{event_date}}, {{event_location}}, {{badge_id}}, {{qr_code_url}}, etc.
    
    is_active = models.BooleanField(default=True)
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='email_templates_created')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Email Template"
        verbose_name_plural = "Email Templates"
        ordering = ['-created_at']
        
    def __str__(self):
        return self.name
    
    def duplicate(self, new_name=None):
        """Create a duplicate of this template"""
        duplicate = EmailTemplate.objects.create(
            name=new_name or f"{self.name} (Copy)",
            subject=self.subject,
            body=self.body,
            body_html=self.body_html,
            description=self.description,
            template_type=self.template_type,
            builder_config=self.builder_config,
            created_by=self.created_by
        )
        return duplicate


class EventEmailTemplate(models.Model):
    """Event-specific customized email template"""
    TYPE_CHOICES = [
        ('invitation', 'Invitation'),
        ('confirmation', 'Confirmation'),
        ('reminder', 'Reminder'),
        ('follow_up', 'Follow-up'),
        ('announcement', 'Announcement'),
        ('registration_confirmation', 'Registration Confirmation'),
        ('custom', 'Custom'),
    ]
    
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='email_templates')
    base_template = models.ForeignKey(EmailTemplate, on_delete=models.SET_NULL, null=True, blank=True, 
                                      related_name='event_customizations',
                                      help_text="Original template this was based on")
    
    name = models.CharField(max_length=200, help_text="Customized template name")
    subject = models.CharField(max_length=300, help_text="Customized email subject")
    body = models.TextField(help_text="Customized email body (supports HTML)")
    body_html = models.TextField(blank=True, help_text="Visual builder HTML output")
    
    template_type = models.CharField(max_length=30, choices=TYPE_CHOICES, default='custom', help_text="Type of email template")
    
    # Visual builder configuration
    builder_config = models.JSONField(default=dict, blank=True, help_text="Visual email builder configuration")
    
    is_active = models.BooleanField(default=True)
    
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
    
    def duplicate(self, new_name=None):
        """Create a duplicate of this template for the same event"""
        duplicate = EventEmailTemplate.objects.create(
            event=self.event,
            base_template=self.base_template,
            name=new_name or f"{self.name} (Copy)",
            subject=self.subject,
            body=self.body,
            body_html=self.body_html,
            template_type=self.template_type,
            builder_config=self.builder_config,
            created_by=self.created_by
        )
        return duplicate


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
    
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='email_logs', null=True, blank=True)
    # Store template info as text to avoid relationship constraints
    template_name = models.CharField(max_length=200, blank=True)
    
    subject = models.CharField(max_length=300)
    body = models.TextField()
    recipient_email = models.EmailField(max_length=200, blank=True, help_text="For test emails")
    
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

class EmailCampaign(models.Model):
    """Email campaign with detailed tracking like Mailerlite"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('sending', 'Sending'),
        ('sent', 'Sent'),
        ('paused', 'Paused'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, help_text="Internal campaign name")
    event = models.ForeignKey(Event, on_delete=models.CASCADE, null=True, blank=True, related_name='email_campaigns')
    
    # Email content
    email_template = models.ForeignKey(EmailTemplate, on_delete=models.SET_NULL, null=True, blank=True)
    subject = models.CharField(max_length=300)
    from_email = models.EmailField(max_length=200)
    from_name = models.CharField(max_length=100, blank=True)
    reply_to = models.EmailField(max_length=200, blank=True)
    body_html = models.TextField()
    body_text = models.TextField(blank=True, help_text="Plain text version")
    
    # Tracking
    track_opens = models.BooleanField(default=True, help_text="Track email opens")
    track_clicks = models.BooleanField(default=True, help_text="Track link clicks")
    
    # Recipients
    recipient_count = models.IntegerField(default=0)
    
    # Statistics (auto-updated)
    total_sent = models.IntegerField(default=0)
    total_delivered = models.IntegerField(default=0)
    total_failed = models.IntegerField(default=0)
    total_opened = models.IntegerField(default=0)
    total_clicked = models.IntegerField(default=0)
    unique_opens = models.IntegerField(default=0)
    unique_clicks = models.IntegerField(default=0)
    
    # Scheduling
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    scheduled_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='campaigns_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Email Campaign'
        verbose_name_plural = 'Email Campaigns'
    
    def __str__(self):
        return f"{self.name} ({self.status})"
    
    def get_open_rate(self):
        """Calculate open rate percentage"""
        if self.total_delivered > 0:
            return round((self.unique_opens / self.total_delivered) * 100, 2)
        return 0
    
    def get_click_rate(self):
        """Calculate click rate percentage"""
        if self.total_delivered > 0:
            return round((self.unique_clicks / self.total_delivered) * 100, 2)
        return 0
    
    def get_click_to_open_rate(self):
        """Calculate click-to-open rate"""
        if self.unique_opens > 0:
            return round((self.unique_clicks / self.unique_opens) * 100, 2)
        return 0


class EmailRecipient(models.Model):
    """Individual recipient in a campaign with tracking"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
        ('bounced', 'Bounced'),
        ('unsubscribed', 'Unsubscribed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    campaign = models.ForeignKey(EmailCampaign, on_delete=models.CASCADE, related_name='recipients')
    
    # Recipient info
    email = models.EmailField(max_length=200)
    name = models.CharField(max_length=200, blank=True)
    participant = models.ForeignKey(Participant, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Tracking tokens
    tracking_token = models.CharField(max_length=64, unique=True, db_index=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True)
    
    # Engagement tracking
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    first_opened_at = models.DateTimeField(null=True, blank=True)
    last_opened_at = models.DateTimeField(null=True, blank=True)
    open_count = models.IntegerField(default=0)
    click_count = models.IntegerField(default=0)
    
    # Device/Location info
    user_agent = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Email Recipient'
        verbose_name_plural = 'Email Recipients'
        unique_together = ['campaign', 'email']
        indexes = [
            models.Index(fields=['campaign', 'status']),
            models.Index(fields=['tracking_token']),
        ]
    
    def __str__(self):
        return f"{self.email} - {self.campaign.name}"
    
    def save(self, *args, **kwargs):
        if not self.tracking_token:
            # Generate unique tracking token
            data = f"{self.campaign.id}{self.email}{timezone.now().isoformat()}"
            self.tracking_token = hashlib.sha256(data.encode()).hexdigest()
        super().save(*args, **kwargs)
    
    def record_open(self, user_agent='', ip_address=None):
        """Record an email open"""
        now = timezone.now()
        if not self.first_opened_at:
            self.first_opened_at = now
            # Update campaign unique opens
            self.campaign.unique_opens += 1
            self.campaign.save(update_fields=['unique_opens'])
        
        self.last_opened_at = now
        self.open_count += 1
        self.user_agent = user_agent
        self.ip_address = ip_address
        self.save(update_fields=['first_opened_at', 'last_opened_at', 'open_count', 'user_agent', 'ip_address'])
        
        # Update campaign total opens
        self.campaign.total_opened += 1
        self.campaign.save(update_fields=['total_opened'])
    
    def record_click(self, link_url):
        """Record a link click"""
        if not self.first_opened_at:
            # First click also counts as open
            self.record_open()
        
        self.click_count += 1
        self.save(update_fields=['click_count'])


class EmailLink(models.Model):
    """Track individual links in email campaigns"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    campaign = models.ForeignKey(EmailCampaign, on_delete=models.CASCADE, related_name='tracked_links')
    
    # Original URL
    original_url = models.TextField()
    
    # Tracking token for this link
    tracking_token = models.CharField(max_length=64, unique=True, db_index=True)
    
    # Statistics
    total_clicks = models.IntegerField(default=0)
    unique_clicks = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-total_clicks']
        verbose_name = 'Email Link'
        verbose_name_plural = 'Email Links'
        unique_together = ['campaign', 'original_url']
    
    def __str__(self):
        return f"{self.original_url[:50]} ({self.total_clicks} clicks)"
    
    def save(self, *args, **kwargs):
        if not self.tracking_token:
            # Generate unique tracking token for link
            data = f"{self.campaign.id}{self.original_url}{timezone.now().isoformat()}"
            self.tracking_token = hashlib.sha256(data.encode()).hexdigest()[:32]
        super().save(*args, **kwargs)
    
    def get_click_rate(self):
        """Calculate click rate for this link"""
        if self.campaign.total_delivered > 0:
            return round((self.unique_clicks / self.campaign.total_delivered) * 100, 2)
        return 0


class EmailClick(models.Model):
    """Track individual link clicks"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient = models.ForeignKey(EmailRecipient, on_delete=models.CASCADE, related_name='clicks')
    link = models.ForeignKey(EmailLink, on_delete=models.CASCADE, related_name='clicks')
    
    # Click details
    clicked_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    referer = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-clicked_at']
        verbose_name = 'Email Click'
        verbose_name_plural = 'Email Clicks'
        indexes = [
            models.Index(fields=['recipient', 'link']),
            models.Index(fields=['clicked_at']),
        ]
    
    def __str__(self):
        return f"{self.recipient.email} clicked {self.link.original_url[:50]}"
    
    def save(self, *args, **kwargs):
        # Check if this is a new record by seeing if it exists in the database
        is_new = not EmailClick.objects.filter(pk=self.pk).exists()
        super().save(*args, **kwargs)
        
        if is_new:
            # Update link statistics
            self.link.total_clicks += 1
            # Check if this is first click from this recipient for this link
            if not EmailClick.objects.filter(recipient=self.recipient, link=self.link).exclude(pk=self.pk).exists():
                self.link.unique_clicks += 1
            self.link.save(update_fields=['total_clicks', 'unique_clicks'])
            
            # Update recipient click count
            self.recipient.record_click(self.link.original_url)
            
            # Update campaign statistics
            campaign = self.recipient.campaign
            campaign.total_clicked += 1
            # Check if this is first click from this recipient in campaign
            if self.recipient.click_count == 1:
                campaign.unique_clicks += 1
            campaign.save(update_fields=['total_clicked', 'unique_clicks'])


class EmailOpen(models.Model):
    """Track individual email opens"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient = models.ForeignKey(EmailRecipient, on_delete=models.CASCADE, related_name='opens')
    
    opened_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-opened_at']
        verbose_name = 'Email Open'
        verbose_name_plural = 'Email Opens'
        indexes = [
            models.Index(fields=['recipient', 'opened_at']),
        ]
    
    def __str__(self):
        return f"{self.recipient.email} opened at {self.opened_at}"