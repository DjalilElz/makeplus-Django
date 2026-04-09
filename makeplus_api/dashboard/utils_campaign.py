"""
Campaign Utilities - Variable Replacement System

Handles dynamic variable replacement in email campaigns based on
registration form data and participant information.
"""

from django.conf import settings
from .models_form import FormSubmission
from events.models import Participant


def build_recipient_context(recipient_email, event):
    """
    Build context dictionary for variable replacement
    
    Fetches data from FormSubmission by email and creates a context
    with all available variables for replacement.
    
    Args:
        recipient_email: Recipient's email address
        event: Event instance
    
    Returns:
        dict: Context with all variables
    """
    context = {
        # Event info
        'event_name': event.name if event else '',
        'event_location': event.location if event else '',
        'event_start_date': event.start_date.strftime('%Y-%m-%d') if event and event.start_date else '',
        'event_end_date': event.end_date.strftime('%Y-%m-%d') if event and event.end_date else '',
        'event_description': event.description if event else '',
        
        # Default user info
        'email': recipient_email,
        'first_name': '',
        'last_name': '',
        'username': recipient_email.split('@')[0],
        
        # Participant data
        'badge_id': '',
        'qr_code_url': '',
        'is_checked_in': 'No',
        
        # System links
        'unsubscribe_url': f"{settings.SITE_URL}/unsubscribe/",
        'view_online_url': f"{settings.SITE_URL}/view-email/",
    }
    
    # Try to get form submission data
    if event:
        try:
            # Get the registration form for this event
            from .models_form import FormConfiguration
            form_config = FormConfiguration.objects.filter(event=event).first()
            
            if form_config:
                # Get the form submission by email
                submission = FormSubmission.objects.filter(
                    form=form_config,
                    data__email=recipient_email
                ).first()
                
                if submission and submission.data:
                    # Add all form fields to context
                    form_data = submission.data
                    
                    # Update basic fields
                    context['first_name'] = form_data.get('first_name', form_data.get('prenom', ''))
                    context['last_name'] = form_data.get('last_name', form_data.get('nom', ''))
                    context['email'] = form_data.get('email', recipient_email)
                    
                    # Add all custom fields (field_0, field_1, etc.)
                    for key, value in form_data.items():
                        if key.startswith('field_'):
                            context[key] = value
                        else:
                            # Also add non-field keys directly
                            context[key] = value
        except Exception as e:
            print(f"Error fetching form submission: {e}")
    
    # Try to get participant data
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        user = User.objects.filter(email=recipient_email).first()
        if user and event:
            participant = Participant.objects.filter(
                user=user,
                event=event
            ).first()
            
            if participant:
                context['badge_id'] = participant.badge_id or ''
                context['qr_code_url'] = participant.qr_code.url if participant.qr_code else ''
                context['is_checked_in'] = 'Yes' if participant.is_checked_in else 'No'
    except Exception as e:
        print(f"Error fetching participant data: {e}")
    
    return context


def replace_variables(content, context):
    """
    Replace variables in content with actual values
    
    Args:
        content: HTML or text content with {{variable}} placeholders
        context: Dictionary with variable values
    
    Returns:
        str: Content with variables replaced
    """
    if not content:
        return content
    
    print(f"Replacing variables in content (length: {len(content)})")
    print(f"Context keys: {list(context.keys())}")
    
    for key, value in context.items():
        placeholder = f"{{{{{key}}}}}"
        if placeholder in content:
            print(f"  Replacing {placeholder} with '{value}'")
            content = content.replace(placeholder, str(value) if value else '')
        else:
            print(f"  Placeholder {placeholder} not found in content")
    
    return content


def send_campaign_email(recipient, campaign):
    """
    Send campaign email with variable replacement
    
    Args:
        recipient: EmailRecipient instance
        campaign: EmailCampaign instance
    
    Returns:
        tuple: (success: bool, error: str or None, message_id: str or None)
    """
    from .email_sender import send_email
    
    # Build context for this recipient
    context = build_recipient_context(recipient.email, campaign.event)
    
    # Replace variables in subject and body
    subject = replace_variables(campaign.subject, context)
    html_content = replace_variables(campaign.body_html, context)
    
    # Send email via Brevo API
    success, error, message_id = send_email(
        to_email=recipient.email,
        subject=subject,
        html_content=html_content,
        from_email=campaign.from_email,
        to_name=recipient.name or context.get('first_name', ''),
        use_api=True  # Always use Brevo API for campaigns
    )
    
    return success, error, message_id
