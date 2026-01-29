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
import time
from django.conf import settings
from django.core.mail import send_mail as django_send_mail


def send_email_via_mailerlite(to_email, subject, html_content, from_email=None, to_name=None):
    """
    Send a single email using MailerLite's API.
    
    Note: For bulk sending, use send_bulk_via_mailerlite() instead.
    
    IMPORTANT: from_email MUST be from a verified domain in MailerLite.
    Set MAILERLITE_FROM_EMAIL in your environment variables.
    
    Args:
        to_email: Recipient email address
        subject: Email subject line
        html_content: HTML body of the email
        from_email: Sender email (must be verified in MailerLite!)
        to_name: Recipient name (optional)
    
    Returns:
        tuple: (success: bool, error_message: str or None)
    """
    api_token = getattr(settings, 'MAILERLITE_API_TOKEN', '')
    
    if not api_token:
        return False, 'MailerLite API token not configured'
    
    # IMPORTANT: Must use a verified email in MailerLite
    # Priority: 1) MAILERLITE_FROM_EMAIL, 2) from_email param, 3) DEFAULT_FROM_EMAIL
    mailerlite_from = getattr(settings, 'MAILERLITE_FROM_EMAIL', '')
    from_address = mailerlite_from or from_email or settings.DEFAULT_FROM_EMAIL
    
    recipient_name = to_name or to_email.split('@')[0]
    
    headers = {
        'Authorization': f'Bearer {api_token}',
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    # Step 1: Add subscriber to MailerLite
    subscriber_data = {
        'email': to_email,
        'fields': {
            'name': recipient_name,
        },
        'status': 'active'
    }
    
    try:
        req = urllib.request.Request(
            'https://connect.mailerlite.com/api/subscribers',
            data=json.dumps(subscriber_data).encode('utf-8'),
            headers=headers,
            method='POST'
        )
        urllib.request.urlopen(req, timeout=30)
    except urllib.error.HTTPError as e:
        if e.code not in [422, 409]:  # 422/409 = already exists, which is fine
            error_body = e.read().decode('utf-8') if e.fp else str(e)
            return False, f'Failed to add subscriber: {e.code} - {error_body}'
    except Exception as e:
        # Continue anyway - subscriber might already exist
        pass
    
    # Step 2: Create a unique group for this send
    group_name = f'send_{int(time.time())}_{to_email[:10].replace("@","_")}'
    group_data = {'name': group_name}
    
    group_id = None
    try:
        req = urllib.request.Request(
            'https://connect.mailerlite.com/api/groups',
            data=json.dumps(group_data).encode('utf-8'),
            headers=headers,
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=30) as response:
            resp_data = json.loads(response.read().decode('utf-8'))
            group_id = resp_data.get('data', {}).get('id')
    except Exception as e:
        return False, f'Failed to create group: {str(e)}'
    
    if not group_id:
        return False, 'Failed to create group - no ID returned'
    
    # Step 3: Add subscriber to the group
    try:
        req = urllib.request.Request(
            f'https://connect.mailerlite.com/api/subscribers/{to_email}/groups/{group_id}',
            headers=headers,
            method='POST'
        )
        urllib.request.urlopen(req, timeout=30)
    except Exception as e:
        return False, f'Failed to add subscriber to group: {str(e)}'
    
    # Step 4: Create campaign
    campaign_data = {
        'name': group_name,
        'type': 'regular',
        'emails': [{
            'subject': subject,
            'from_name': 'MakePlus',
            'from': from_address,
            'content': html_content,
        }]
    }
    
    try:
        req = urllib.request.Request(
            'https://connect.mailerlite.com/api/campaigns',
            data=json.dumps(campaign_data).encode('utf-8'),
            headers=headers,
            method='POST'
        )
        
        with urllib.request.urlopen(req, timeout=60) as response:
            resp_data = json.loads(response.read().decode('utf-8'))
            campaign_id = resp_data.get('data', {}).get('id')
            
            if not campaign_id:
                return False, 'Failed to create campaign - no ID returned'
            
            # Step 5: Schedule campaign to the group
            schedule_data = {
                'delivery': 'instant',
                'groups': [group_id]
            }
            
            req2 = urllib.request.Request(
                f'https://connect.mailerlite.com/api/campaigns/{campaign_id}/schedule',
                data=json.dumps(schedule_data).encode('utf-8'),
                headers=headers,
                method='POST'
            )
            
            urllib.request.urlopen(req2, timeout=60)
            return True, None
                
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8') if e.fp else str(e)
        try:
            error_json = json.loads(error_body)
            error_msg = error_json.get('message', str(error_json))
        except:
            error_msg = error_body
        return False, f'MailerLite API error: {e.code} - {error_msg}'
    except Exception as e:
        return False, f'Unexpected error: {str(e)}'


def send_bulk_via_mailerlite(recipients, subject_template, html_template, from_email=None, campaign_name=None):
    """
    Send emails to multiple recipients efficiently using ONE MailerLite campaign.
    
    This is the efficient way to send bulk emails:
    1. Create all subscribers
    2. Create ONE group with all subscribers
    3. Create ONE campaign
    4. Send to the group
    
    IMPORTANT: from_email MUST be from a verified domain in MailerLite!
    Set MAILERLITE_FROM_EMAIL in environment variables.
    
    Args:
        recipients: List of dicts with 'email', 'name', 'context' (for variable replacement)
        subject_template: Subject line (can contain {name}, {email} variables)
        html_template: HTML content (can contain {name}, {email} variables)
        from_email: Sender email (must be verified in MailerLite!)
        campaign_name: Optional campaign name
    
    Returns:
        tuple: (success: bool, error_message: str or None, sent_count: int)
    """
    api_token = getattr(settings, 'MAILERLITE_API_TOKEN', '')
    
    if not api_token:
        return False, 'MailerLite API token not configured', 0
    
    if not recipients:
        return False, 'No recipients provided', 0
    
    # IMPORTANT: Must use a verified email in MailerLite
    # Priority: 1) MAILERLITE_FROM_EMAIL, 2) from_email param, 3) DEFAULT_FROM_EMAIL
    mailerlite_from = getattr(settings, 'MAILERLITE_FROM_EMAIL', '')
    from_address = mailerlite_from or from_email or settings.DEFAULT_FROM_EMAIL
    
    headers = {
        'Authorization': f'Bearer {api_token}',
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    # Step 1: Create a unique group for this campaign
    group_name = campaign_name or f'campaign_{int(time.time())}'
    group_data = {'name': group_name}
    
    try:
        req = urllib.request.Request(
            'https://connect.mailerlite.com/api/groups',
            data=json.dumps(group_data).encode('utf-8'),
            headers=headers,
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=30) as response:
            resp_data = json.loads(response.read().decode('utf-8'))
            group_id = resp_data.get('data', {}).get('id')
    except Exception as e:
        return False, f'Failed to create group: {str(e)}', 0
    
    if not group_id:
        return False, 'Failed to create group - no ID returned', 0
    
    # Step 2: Add all subscribers to the group
    added_count = 0
    for recipient in recipients:
        email = recipient.get('email')
        name = recipient.get('name', email.split('@')[0])
        
        subscriber_data = {
            'email': email,
            'fields': {'name': name},
            'groups': [group_id],
            'status': 'active'
        }
        
        try:
            req = urllib.request.Request(
                'https://connect.mailerlite.com/api/subscribers',
                data=json.dumps(subscriber_data).encode('utf-8'),
                headers=headers,
                method='POST'
            )
            urllib.request.urlopen(req, timeout=30)
            added_count += 1
        except urllib.error.HTTPError as e:
            if e.code in [422, 409]:  # Already exists
                # Add existing subscriber to group
                try:
                    req = urllib.request.Request(
                        f'https://connect.mailerlite.com/api/subscribers/{email}/groups/{group_id}',
                        headers=headers,
                        method='POST'
                    )
                    urllib.request.urlopen(req, timeout=30)
                    added_count += 1
                except:
                    pass
        except:
            pass
    
    if added_count == 0:
        return False, 'Failed to add any subscribers', 0
    
    # Step 3: Create and send campaign
    campaign_data = {
        'name': group_name,
        'type': 'regular',
        'emails': [{
            'subject': subject_template,
            'from_name': 'MakePlus',
            'from': from_address,
            'content': html_template,
        }]
    }
    
    try:
        req = urllib.request.Request(
            'https://connect.mailerlite.com/api/campaigns',
            data=json.dumps(campaign_data).encode('utf-8'),
            headers=headers,
            method='POST'
        )
        
        with urllib.request.urlopen(req, timeout=60) as response:
            resp_data = json.loads(response.read().decode('utf-8'))
            campaign_id = resp_data.get('data', {}).get('id')
            
            if not campaign_id:
                return False, 'Failed to create campaign', 0
            
            # Schedule to group
            schedule_data = {
                'delivery': 'instant',
                'groups': [group_id]
            }
            
            req2 = urllib.request.Request(
                f'https://connect.mailerlite.com/api/campaigns/{campaign_id}/schedule',
                data=json.dumps(schedule_data).encode('utf-8'),
                headers=headers,
                method='POST'
            )
            
            urllib.request.urlopen(req2, timeout=60)
            return True, None, added_count
                
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8') if e.fp else str(e)
        return False, f'MailerLite API error: {e.code} - {error_body}', 0
    except Exception as e:
        return False, f'Error: {str(e)}', 0


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
