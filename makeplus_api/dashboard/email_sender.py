"""
Email Sender Module - Uses Brevo (Sendinblue) API for reliable cloud delivery

This module provides a unified interface for sending emails that works
reliably on cloud platforms by using HTTP-based APIs instead of direct
SMTP connections which are often blocked.

Priority Order:
1. Brevo API (recommended - handles tracking automatically)
2. SMTP (fallback for local development)
"""

from django.conf import settings
from django.core.mail import send_mail as django_send_mail
from .brevo_client import get_brevo_client


def send_email_via_brevo_api(to_email, subject, html_content, from_email=None, to_name=None, 
                              track_opens=True, track_clicks=True):
    """
    Send a single email using Brevo's API with tracking.
    
    Args:
        to_email: Recipient email address
        subject: Email subject line
        html_content: HTML body of the email
        from_email: Sender email (optional, uses DEFAULT_FROM_EMAIL)
        to_name: Recipient name (optional)
        track_opens: Enable open tracking (default: True)
        track_clicks: Enable click tracking (default: True)
    
    Returns:
        tuple: (success: bool, error_message: str or None, message_id: str or None)
    """
    try:
        client = get_brevo_client()
        
        recipient_name = to_name or to_email.split('@')[0]
        from_address = from_email or settings.DEFAULT_FROM_EMAIL
        
        response = client.send_transactional_email(
            to_email=to_email,
            to_name=recipient_name,
            subject=subject,
            html_content=html_content,
            from_email=from_address,
            from_name='MakePlus',
            track_opens=track_opens,
            track_clicks=track_clicks
        )
        
        message_id = response.get('messageId', '')
        return True, None, message_id
        
    except Exception as e:
        return False, str(e), None



def send_email_via_smtp(to_email, subject, html_content, from_email=None):
    """
    Send email using Django's SMTP backend.
    
    Args:
        to_email: Recipient email address
        subject: Email subject line
        html_content: HTML body of the email
        from_email: Sender email (optional, uses DEFAULT_FROM_EMAIL)
    
    Returns:
        tuple: (success: bool, error_message: str or None)
    """
    from_address = from_email or settings.DEFAULT_FROM_EMAIL
    
    try:
        result = django_send_mail(
            subject=subject,
            message='',  # Plain text version (empty, we use HTML)
            from_email=from_address,
            recipient_list=[to_email],
            html_message=html_content,
            fail_silently=False,
        )
        
        if result > 0:
            return True, None
        else:
            return False, 'Email was not sent (unknown reason)'
            
    except Exception as e:
        return False, str(e)


def send_email(to_email, subject, html_content, from_email=None, to_name=None, use_api=True):
    """
    Send email using the best available method.
    
    Priority:
    1. Brevo API (handles tracking automatically) - RECOMMENDED
    2. SMTP fallback (for local development)
    
    Args:
        to_email: Recipient email address
        subject: Email subject line
        html_content: HTML body of the email
        from_email: Sender email (optional, uses DEFAULT_FROM_EMAIL)
        to_name: Recipient name (optional)
        use_api: Use Brevo API (True) or SMTP (False) - default True
    
    Returns:
        tuple: (success: bool, error_message: str or None, message_id: str or None)
    """
    # Try Brevo API first (recommended for production)
    if use_api:
        brevo_api_key = getattr(settings, 'BREVO_API_KEY', '')
        
        if brevo_api_key:
            success, error, message_id = send_email_via_brevo_api(
                to_email, subject, html_content, from_email, to_name,
                track_opens=True, track_clicks=True
            )
            if success:
                return True, None, message_id
            # Log error but try SMTP fallback
            print(f"Brevo API failed: {error}, trying SMTP fallback...")
    
    # Try SMTP as fallback
    success, error = send_email_via_smtp(to_email, subject, html_content, from_email)
    return success, error, None


def send_bulk_emails(recipients_data, from_email=None, use_api=True):
    """
    Send emails to multiple recipients efficiently.
    
    Args:
        recipients_data: List of dicts with keys: 'email', 'subject', 'html_content', 'name' (optional)
        from_email: Sender email (optional)
        use_api: Use Brevo API (True) or SMTP (False) - default True
    
    Returns:
        tuple: (sent_count: int, failed_count: int, errors: list)
    """
    sent_count = 0
    failed_count = 0
    errors = []
    
    for recipient in recipients_data:
        success, error, message_id = send_email(
            to_email=recipient['email'],
            subject=recipient['subject'],
            html_content=recipient['html_content'],
            from_email=from_email,
            to_name=recipient.get('name'),
            use_api=use_api
        )
        
        if success:
            sent_count += 1
        else:
            failed_count += 1
            errors.append({
                'email': recipient['email'],
                'error': error
            })
    
    return sent_count, failed_count, errors
