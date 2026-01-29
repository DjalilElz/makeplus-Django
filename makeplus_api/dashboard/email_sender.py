"""
Email Sender Module - Uses MailerLite API for reliable cloud delivery

This module provides a unified interface for sending emails that works
reliably on cloud platforms like Render by using HTTP-based APIs
instead of direct SMTP connections which are often blocked.

Priority Order:
1. MailerLite API (recommended - handles tracking automatically)
2. SendGrid API (fallback)
3. SMTP (local development only)
"""

import json
import urllib.request
import urllib.error
from django.conf import settings
from django.core.mail import send_mail as django_send_mail


def send_email_via_mailerlite(to_email, subject, html_content, from_email=None, to_name=None):
    """
    Send email using MailerLite's API.
    
    MailerLite automatically handles:
    - Open tracking (adds tracking pixel)
    - Click tracking (rewrites links)
    - Bounce handling
    - Unsubscribe management
    
    Args:
        to_email: Recipient email address
        subject: Email subject line
        html_content: HTML body of the email
        from_email: Sender email (optional, uses DEFAULT_FROM_EMAIL)
        to_name: Recipient name (optional)
    
    Returns:
        tuple: (success: bool, error_message: str or None)
    """
    api_token = getattr(settings, 'MAILERLITE_API_TOKEN', '')
    
    if not api_token:
        return False, 'MailerLite API token not configured'
    
    from_address = from_email or settings.DEFAULT_FROM_EMAIL
    recipient_name = to_name or to_email.split('@')[0]
    
    # MailerLite API v2 - Send transactional email
    data = {
        'from': {
            'email': from_address,
            'name': 'MakePlus'
        },
        'to': [{
            'email': to_email,
            'name': recipient_name
        }],
        'subject': subject,
        'html': html_content,
        'settings': {
            'track_opens': True,
            'track_clicks': True
        }
    }
    
    headers = {
        'Authorization': f'Bearer {api_token}',
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    try:
        req = urllib.request.Request(
            'https://connect.mailerlite.com/api/campaigns/send',
            data=json.dumps(data).encode('utf-8'),
            headers=headers,
            method='POST'
        )
        
        with urllib.request.urlopen(req, timeout=60) as response:
            if response.status in [200, 201, 202]:
                return True, None
            else:
                return False, f'MailerLite returned status {response.status}'
                
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8') if e.fp else str(e)
        try:
            error_json = json.loads(error_body)
            error_msg = error_json.get('message', error_body)
        except:
            error_msg = error_body
        return False, f'MailerLite API error: {e.code} - {error_msg}'
    except urllib.error.URLError as e:
        return False, f'Network error: {str(e.reason)}'
    except Exception as e:
        return False, f'Unexpected error: {str(e)}'


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


def send_email(to_email, subject, html_content, from_email=None, to_name=None):
    """
    Send email using the best available method.
    
    Priority:
    1. MailerLite API (handles tracking automatically)
    2. SMTP fallback (for local development)
    
    Args:
        to_email: Recipient email address
        subject: Email subject line
        html_content: HTML body of the email
        from_email: Sender email (optional, uses DEFAULT_FROM_EMAIL)
        to_name: Recipient name (optional)
    
    Returns:
        tuple: (success: bool, error_message: str or None)
    """
    # Try MailerLite first (recommended for production)
    mailerlite_token = getattr(settings, 'MAILERLITE_API_TOKEN', '')
    
    if mailerlite_token:
        success, error = send_email_via_mailerlite(to_email, subject, html_content, from_email, to_name)
        if success:
            return True, None
        # Log error but try SMTP fallback
        print(f"MailerLite failed: {error}, trying SMTP fallback...")
    
    # Try SMTP as fallback
    return send_email_via_smtp(to_email, subject, html_content, from_email)


def send_bulk_emails(recipients_data, from_email=None):
    """
    Send emails to multiple recipients efficiently.
    
    Args:
        recipients_data: List of dicts with keys: 'email', 'subject', 'html_content'
        from_email: Sender email (optional)
    
    Returns:
        tuple: (sent_count: int, failed_count: int, errors: list)
    """
    sent_count = 0
    failed_count = 0
    errors = []
    
    for recipient in recipients_data:
        success, error = send_email(
            to_email=recipient['email'],
            subject=recipient['subject'],
            html_content=recipient['html_content'],
            from_email=from_email
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
