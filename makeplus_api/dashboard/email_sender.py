"""
Email Sender Module - Uses HTTP API for reliable cloud delivery

This module provides a unified interface for sending emails that works
reliably on cloud platforms like Render by using HTTP-based APIs
instead of direct SMTP connections which are often blocked.

Supports:
- SendGrid API (recommended for production)
- SMTP fallback (for local development)
"""

import json
import urllib.request
import urllib.error
from django.conf import settings
from django.core.mail import send_mail as django_send_mail


def send_email_via_sendgrid(to_email, subject, html_content, from_email=None):
    """
    Send email using SendGrid's HTTP API.
    
    Args:
        to_email: Recipient email address
        subject: Email subject line
        html_content: HTML body of the email
        from_email: Sender email (optional, uses DEFAULT_FROM_EMAIL)
    
    Returns:
        tuple: (success: bool, error_message: str or None)
    """
    api_key = getattr(settings, 'SENDGRID_API_KEY', '')
    
    if not api_key:
        return False, 'SendGrid API key not configured'
    
    from_address = from_email or settings.DEFAULT_FROM_EMAIL
    
    # SendGrid API v3 payload
    data = {
        "personalizations": [
            {
                "to": [{"email": to_email}],
                "subject": subject
            }
        ],
        "from": {"email": from_address},
        "content": [
            {
                "type": "text/html",
                "value": html_content
            }
        ]
    }
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    try:
        req = urllib.request.Request(
            'https://api.sendgrid.com/v3/mail/send',
            data=json.dumps(data).encode('utf-8'),
            headers=headers,
            method='POST'
        )
        
        with urllib.request.urlopen(req, timeout=30) as response:
            # SendGrid returns 202 Accepted on success
            if response.status in [200, 202]:
                return True, None
            else:
                return False, f'SendGrid returned status {response.status}'
                
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8') if e.fp else str(e)
        return False, f'SendGrid API error: {e.code} - {error_body}'
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


def send_email(to_email, subject, html_content, from_email=None):
    """
    Send email using the best available method.
    
    Tries SendGrid API first (works on cloud platforms),
    falls back to SMTP if SendGrid is not configured.
    
    Args:
        to_email: Recipient email address
        subject: Email subject line
        html_content: HTML body of the email
        from_email: Sender email (optional, uses DEFAULT_FROM_EMAIL)
    
    Returns:
        tuple: (success: bool, error_message: str or None)
    """
    # Try SendGrid first if API key is configured
    sendgrid_key = getattr(settings, 'SENDGRID_API_KEY', '')
    
    if sendgrid_key:
        success, error = send_email_via_sendgrid(to_email, subject, html_content, from_email)
        if success:
            return True, None
        # If SendGrid fails, try SMTP as fallback
        print(f"SendGrid failed: {error}, trying SMTP fallback...")
    
    # Try SMTP
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
