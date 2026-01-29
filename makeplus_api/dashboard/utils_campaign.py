"""
Email Campaign Management Utilities
Handles campaign creation, sending, and tracking
"""
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from .models_email import EmailCampaign, EmailRecipient, EmailLink
import re
from bs4 import BeautifulSoup


def process_email_links_for_tracking(html_content, campaign):
    """
    Process all links in email HTML to add tracking
    Returns modified HTML with tracked links
    """
    if not campaign.track_clicks:
        return html_content
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Find all <a> tags with href
    for link in soup.find_all('a', href=True):
        original_url = link['href']
        
        # Skip special URLs
        if original_url.startswith(('mailto:', 'tel:', '#')):
            continue
        
        # Get or create EmailLink for this URL
        email_link, created = EmailLink.objects.get_or_create(
            campaign=campaign,
            original_url=original_url
        )
        
        # Note: The actual tracking URL will be added per-recipient
        # We'll use a placeholder for now
        link['data-link-token'] = email_link.tracking_token
    
    return str(soup)


def add_recipient_tracking(html_content, recipient, campaign):
    """
    Add recipient-specific tracking to email HTML
    - Adds tracking pixel for opens
    - Adds recipient token to click tracking links
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Add tracking pixel for email opens
    if campaign.track_opens:
        tracking_url = f"{settings.SITE_URL}/track/email/open/{recipient.tracking_token}/"
        tracking_pixel = soup.new_tag('img', src=tracking_url, width="1", height="1", style="display:none")
        soup.body.append(tracking_pixel) if soup.body else soup.append(tracking_pixel)
    
    # Update link tracking with recipient token
    if campaign.track_clicks:
        for link in soup.find_all('a', href=True):
            if 'data-link-token' in link.attrs:
                link_token = link['data-link-token']
                tracking_url = f"{settings.SITE_URL}/track/email/click/{link_token}/{recipient.tracking_token}/"
                link['href'] = tracking_url
                del link['data-link-token']
    
    return str(soup)


def add_unsubscribe_link(html_content, recipient):
    """
    Add unsubscribe link to email footer
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    unsubscribe_url = f"{settings.SITE_URL}/track/email/unsubscribe/{recipient.tracking_token}/"
    
    # Create unsubscribe footer
    footer = soup.new_tag('div', style='text-align:center; margin-top:20px; padding:20px; font-size:11px; color:#999;')
    footer.string = 'If you no longer wish to receive these emails, you can '
    
    unsub_link = soup.new_tag('a', href=unsubscribe_url, style='color:#666;')
    unsub_link.string = 'unsubscribe here'
    footer.append(unsub_link)
    
    if soup.body:
        soup.body.append(footer)
    else:
        soup.append(footer)
    
    return str(soup)


def send_campaign_email(recipient):
    """
    Send email to a single recipient with tracking
    """
    campaign = recipient.campaign
    
    try:
        # Process email content with tracking
        html_content = campaign.body_html
        html_content = add_recipient_tracking(html_content, recipient, campaign)
        html_content = add_unsubscribe_link(html_content, recipient)
        
        # Create email message
        from_email = f"{campaign.from_name} <{campaign.from_email}>" if campaign.from_name else campaign.from_email
        
        message = EmailMultiAlternatives(
            subject=campaign.subject,
            body=campaign.body_text or "Please view this email in HTML format.",
            from_email=from_email,
            to=[recipient.email],
            reply_to=[campaign.reply_to] if campaign.reply_to else None
        )
        
        message.attach_alternative(html_content, "text/html")
        message.send()
        
        # Update recipient status
        recipient.status = 'sent'
        recipient.sent_at = timezone.now()
        recipient.save()
        
        # Update campaign stats
        campaign.total_sent += 1
        campaign.save(update_fields=['total_sent'])
        
        return True
        
    except Exception as e:
        # Update recipient with error
        recipient.status = 'failed'
        recipient.error_message = str(e)
        recipient.save()
        
        # Update campaign stats
        campaign.total_failed += 1
        campaign.save(update_fields=['total_failed'])
        
        return False


def send_campaign(campaign_id):
    """
    Send email campaign to all recipients
    This should be called in a background task (Celery)
    """
    from .models_email import EmailCampaign, EmailRecipient
    
    campaign = EmailCampaign.objects.get(id=campaign_id)
    
    # Update status
    campaign.status = 'sending'
    campaign.sent_at = timezone.now()
    campaign.save()
    
    # Process links for tracking
    campaign.body_html = process_email_links_for_tracking(campaign.body_html, campaign)
    campaign.save(update_fields=['body_html'])
    
    # Get all pending recipients
    recipients = EmailRecipient.objects.filter(
        campaign=campaign,
        status='pending'
    )
    
    success_count = 0
    for recipient in recipients:
        if send_campaign_email(recipient):
            success_count += 1
    
    # Update campaign status
    campaign.status = 'sent'
    campaign.completed_at = timezone.now()
    campaign.save()
    
    return {
        'total': recipients.count(),
        'success': success_count,
        'failed': campaign.total_failed
    }


def send_form_confirmation_email(form_config, submission_data, recipient_email):
    """
    Send automatic confirmation email after form submission
    """
    from .models_email import EmailTemplate
    from django.core.mail import EmailMultiAlternatives
    
    if not form_config.send_confirmation_email:
        return False
    
    if not form_config.confirmation_email_template:
        return False
    
    template = form_config.confirmation_email_template
    
    # Build context for template variables
    context = {
        'form_name': form_config.name,
        'event_name': form_config.event.name if form_config.event else '',
        'submission_date': timezone.now().strftime('%B %d, %Y %H:%M'),
    }
    context.update(submission_data)
    
    # Replace template variables
    subject = replace_template_variables(template.subject, context)
    body_html = replace_template_variables(template.body_html or template.body, context)
    
    # Send email
    try:
        from_email = template.from_email or settings.DEFAULT_FROM_EMAIL
        
        message = EmailMultiAlternatives(
            subject=subject,
            body="Please view this email in HTML format.",
            from_email=from_email,
            to=[recipient_email]
        )
        
        message.attach_alternative(body_html, "text/html")
        message.send()
        
        return True
        
    except Exception as e:
        print(f"Error sending confirmation email: {e}")
        return False


def replace_template_variables(text, context):
    """
    Replace template variables in text with values from context
    Example: {{first_name}} -> John
    """
    import re
    
    def replacer(match):
        var_name = match.group(1).strip()
        return str(context.get(var_name, match.group(0)))
    
    return re.sub(r'\{\{([^}]+)\}\}', replacer, text)

