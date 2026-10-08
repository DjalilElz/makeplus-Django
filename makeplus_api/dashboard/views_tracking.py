"""
Email Campaign and Form Tracking Views
Handles open/click tracking and form analytics
"""
from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden, JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models_email import EmailRecipient, EmailLink, EmailClick, EmailOpen, EmailCampaign
from .models_form import FormConfiguration, FormView, FormFieldInteraction, FormAnalytics
import base64
import json


# 1x1 transparent PNG pixel for email tracking
TRACKING_PIXEL = base64.b64decode(
    b'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=='
)


@require_http_methods(["GET"])
def track_email_open(request, token):
    """
    Track email open via tracking pixel
    Returns a 1x1 transparent pixel
    """
    try:
        recipient = EmailRecipient.objects.get(tracking_token=token)
        
        # Get user agent and IP
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        ip_address = get_client_ip(request)
        
        # Record the open
        recipient.record_open(user_agent=user_agent, ip_address=ip_address)
        
        # Create EmailOpen record
        EmailOpen.objects.create(
            recipient=recipient,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
    except EmailRecipient.DoesNotExist:
        pass  # Invalid token, but still return pixel
    except Exception:
        pass  # Don't break tracking for any error
    
    # Always return pixel regardless of success/failure
    return HttpResponse(TRACKING_PIXEL, content_type='image/png')


@require_http_methods(["GET"])
def track_link_click(request, link_token, recipient_token):
    """
    Track link click and redirect to original URL
    """
    try:
        link = EmailLink.objects.get(tracking_token=link_token)
        recipient = EmailRecipient.objects.get(tracking_token=recipient_token)
        
        # Get user agent and IP
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        ip_address = get_client_ip(request)
        referer = request.META.get('HTTP_REFERER', '')
        
        # Create click record (this will auto-update all stats via model save)
        EmailClick.objects.create(
            recipient=recipient,
            link=link,
            ip_address=ip_address,
            user_agent=user_agent,
            referer=referer
        )
        
        # Redirect to original URL
        return HttpResponseRedirect(link.original_url)
        
    except (EmailLink.DoesNotExist, EmailRecipient.DoesNotExist):
        # Invalid tokens, redirect to homepage
        return HttpResponseRedirect('/')


@require_http_methods(["GET", "POST"])
def unsubscribe_recipient(request, token):
    """
    Handle email unsubscribe
    """
    try:
        recipient = EmailRecipient.objects.get(tracking_token=token)
        recipient.status = 'unsubscribed'
        recipient.save()
        
        return HttpResponse("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Unsubscribed</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    max-width: 600px;
                    margin: 50px auto;
                    padding: 20px;
                    text-align: center;
                }
                .success {
                    background: #d4edda;
                    color: #155724;
                    padding: 20px;
                    border-radius: 5px;
                }
            </style>
        </head>
        <body>
            <div class="success">
                <h2>✓ Successfully Unsubscribed</h2>
                <p>You have been unsubscribed from this email campaign.</p>
                <p>Email: {}</p>
            </div>
        </body>
        </html>
        """.format(recipient.email))
        
    except EmailRecipient.DoesNotExist:
        return HttpResponse("Invalid unsubscribe link.", status=400)


def _postmark_webhook_authorized(request):
    """
    Postmark doesn't sign webhook payloads, so the recommended way to
    keep this endpoint from being spoofed is HTTP Basic Auth baked into
    the webhook URL itself (https://user:pass@host/...), which Postmark
    sends back as a normal Authorization header. If no credentials are
    configured, the check is skipped (webhook still only acts on
    messages whose MessageID matches a real EmailRecipient row).
    """
    expected_user = getattr(settings, 'POSTMARK_WEBHOOK_USERNAME', '')
    expected_password = getattr(settings, 'POSTMARK_WEBHOOK_PASSWORD', '')
    if not expected_user and not expected_password:
        return True

    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    if not auth_header.startswith('Basic '):
        return False
    try:
        decoded = base64.b64decode(auth_header[6:]).decode('utf-8')
        username, password = decoded.split(':', 1)
    except Exception:
        return False
    return username == expected_user and password == expected_password


@csrf_exempt
@require_http_methods(["POST"])
def postmark_webhook(request):
    """
    Receives Postmark's Delivery/Bounce/SpamComplaint/Open/Click events
    (configured in Postmark: Servers -> your server -> Webhooks) and
    updates the matching EmailRecipient's tracking fields in real time --
    replacing the old polling-based "sync stats" button.

    Events for a MessageID that isn't a campaign recipient (e.g. a plain
    transactional email like a password reset) are accepted and ignored;
    only EmailCampaign sends are tracked per-recipient.
    """
    if not _postmark_webhook_authorized(request):
        return HttpResponseForbidden('Invalid webhook credentials')

    try:
        payload = json.loads(request.body)
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    record_type = payload.get('RecordType', '')
    message_id = payload.get('MessageID', '')
    if not message_id:
        return JsonResponse({'success': True, 'ignored': True})

    recipient = EmailRecipient.objects.filter(external_id=message_id).select_related('campaign').first()
    if not recipient:
        return JsonResponse({'success': True, 'ignored': True})

    if record_type == 'Delivery':
        recipient.status = 'delivered'
        recipient.delivered_at = timezone.now()
        recipient.save(update_fields=['status', 'delivered_at'])
        campaign = recipient.campaign
        campaign.total_delivered = campaign.recipients.filter(status__in=['delivered', 'sent']).count()
        campaign.save(update_fields=['total_delivered'])

    elif record_type == 'Open':
        user_agent = (payload.get('Client') or {}).get('Name', '')
        recipient.record_open(user_agent=user_agent, ip_address=None)
        EmailOpen.objects.create(recipient=recipient, user_agent=user_agent)

    elif record_type == 'Click':
        original_url = payload.get('OriginalLink', '')
        if original_url:
            link, _ = EmailLink.objects.get_or_create(
                campaign=recipient.campaign, original_url=original_url,
            )
            user_agent = (payload.get('Client') or {}).get('Name', '')
            EmailClick.objects.create(recipient=recipient, link=link, user_agent=user_agent)
        else:
            recipient.record_click(original_url)

    elif record_type in ('Bounce', 'SpamComplaint'):
        recipient.status = 'bounced'
        recipient.error_message = (
            payload.get('Description') or payload.get('Type') or record_type
        )[:500]
        recipient.save(update_fields=['status', 'error_message'])

    return JsonResponse({'success': True})


@csrf_exempt
@require_http_methods(["POST"])
def track_form_view(request, form_id):
    """
    Track form view for analytics
    Expects JSON: {
        "session_id": "...",
        "device_type": "desktop|mobile|tablet",
        "browser": "chrome",
        "os": "windows",
        "referer": "...",
        "utm_source": "...",
        "utm_medium": "...",
        "utm_campaign": "..."
    }
    """
    try:
        form = FormConfiguration.objects.get(id=form_id)
        data = json.loads(request.body)
        
        # Get or create analytics
        analytics, created = FormAnalytics.objects.get_or_create(form=form)
        
        # Get user agent and IP
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        ip_address = get_client_ip(request)
        
        # Create form view
        form_view = FormView.objects.create(
            form=form,
            session_id=data.get('session_id', ''),
            ip_address=ip_address,
            user_agent=user_agent,
            device_type=data.get('device_type', ''),
            browser=data.get('browser', ''),
            os=data.get('os', ''),
            referer=data.get('referer', ''),
            utm_source=data.get('utm_source', ''),
            utm_medium=data.get('utm_medium', ''),
            utm_campaign=data.get('utm_campaign', '')
        )
        
        # Update analytics
        analytics.total_views += 1
        
        # Check if this is a unique view (new session)
        if not FormView.objects.filter(form=form, session_id=data.get('session_id')).exclude(id=form_view.id).exists():
            analytics.unique_views += 1
        
        analytics.update_conversion_rate()
        analytics.save()
        
        return JsonResponse({
            'success': True,
            'view_id': str(form_view.id)
        })
        
    except FormConfiguration.DoesNotExist:
        return JsonResponse({'error': 'Form not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["POST"])
def track_form_interaction(request, form_id):
    """
    Track form field interactions
    Expects JSON: {
        "view_id": "...",
        "fields_interacted": ["field1", "field2"],
        "time_on_page": 120,
        "completed": true
    }
    """
    try:
        data = json.loads(request.body)
        form_view = FormView.objects.get(id=data.get('view_id'))
        
        # Update form view
        form_view.time_on_page = data.get('time_on_page', 0)
        form_view.fields_interacted = data.get('fields_interacted', [])
        form_view.completed = data.get('completed', False)
        form_view.save()
        
        # Update analytics if completed
        if form_view.completed:
            analytics = FormAnalytics.objects.get(form=form_view.form)
            analytics.total_submissions += 1
            analytics.completed_submissions += 1
            analytics.update_conversion_rate()
            analytics.save()
        
        return JsonResponse({'success': True})
        
    except FormView.DoesNotExist:
        return JsonResponse({'error': 'Form view not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

