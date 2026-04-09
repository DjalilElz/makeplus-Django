"""
Registration Helper Functions

Handles user creation, event assignment, and login code generation
for the registration form system.
"""

from django.contrib.auth.models import User
from events.models import UserEventAssignment, Participant, Event
from events.login_code_service import issue_email_login_code, invalidate_user_event_codes
from dashboard.models_form import FormSubmission
from dashboard.email_sender import send_email


def _ensure_registration_account(email, first_name, last_name, event):
    """
    Create or update user account for registration
    
    Args:
        email: User's email (unique identifier)
        first_name: User's first name
        last_name: User's last name
        event: Event instance
    
    Returns:
        tuple: (user: User, user_created: bool, participant: Participant)
    """
    # Get or create user
    user, user_created = User.objects.get_or_create(
        email=email,
        defaults={
            'username': email.split('@')[0],
            'first_name': first_name,
            'last_name': last_name,
        }
    )
    
    # If user exists, update their info with latest submission
    if not user_created:
        user.first_name = first_name
        user.last_name = last_name
        user.save(update_fields=['first_name', 'last_name'])
    
    # Set unusable password (passwordless authentication)
    if user_created or user.has_usable_password():
        user.set_unusable_password()
        user.save()
    
    # Create or get UserEventAssignment
    assignment, _ = UserEventAssignment.objects.get_or_create(
        user=user,
        event=event,
        defaults={'role': 'participant'}
    )
    
    # Create or get Participant
    from events.models import UserProfile
    qr_data = UserProfile.get_qr_for_user(user)
    
    participant, _ = Participant.objects.get_or_create(
        user=user,
        event=event,
        defaults={
            'badge_id': qr_data['badge_id'],
            'qr_code_data': qr_data
        }
    )
    
    return user, user_created, participant


def handle_re_registration(user, event, form_config):
    """
    Handle re-registration for same user+event
    
    - Deletes old FormSubmission
    - Invalidates old EmailLoginCode records
    - User info already updated by _ensure_registration_account
    
    Args:
        user: User instance
        event: Event instance
        form_config: FormConfiguration instance
    
    Returns:
        None
    """
    # Delete old form submission for this user+event
    FormSubmission.objects.filter(
        form=form_config,
        data__email=user.email
    ).delete()
    
    # Invalidate old login codes for this user+event
    invalidate_user_event_codes(user, event)


def send_registration_confirmation_email(user, event, login_code):
    """
    Send registration confirmation email with login code
    
    Args:
        user: User instance
        event: Event instance
        login_code: 6-digit login code (string)
    
    Returns:
        tuple: (success: bool, error: str or None, message_id: str or None)
    """
    subject = f"Registration Confirmed - {event.name}"
    
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #667eea;">Welcome, {user.first_name}!</h2>
            <p>Thank you for registering for <strong>{event.name}</strong>.</p>
            
            <div style="background: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0; text-align: center;">
                <h3 style="margin-top: 0; color: #667eea;">Your Login Code</h3>
                <div style="font-size: 48px; font-weight: bold; letter-spacing: 10px; color: #667eea; margin: 20px 0;">
                    {login_code}
                </div>
                <p style="color: #6c757d; font-size: 0.9em;">Use this code to log in to the mobile application</p>
            </div>
            
            <div style="background: #e7f3ff; padding: 15px; border-left: 4px solid #2196F3; margin: 20px 0;">
                <h4 style="margin-top: 0;">Event Details</h4>
                <p style="margin: 5px 0;"><strong>Event:</strong> {event.name}</p>
                <p style="margin: 5px 0;"><strong>Location:</strong> {event.location}</p>
                <p style="margin: 5px 0;"><strong>Date:</strong> {event.start_date.strftime("%B %d, %Y")}</p>
            </div>
            
            <div style="background: #fff3cd; padding: 15px; border-left: 4px solid #ffc107; margin: 20px 0;">
                <p style="margin: 0;"><strong>Important:</strong> This login code is specific to this event. Please save it securely.</p>
            </div>
            
            <p style="color: #6c757d; font-size: 0.9em; margin-top: 30px;">
                If you didn't register for this event, please contact us immediately.
            </p>
            
            <p style="margin-top: 30px;">
                Best regards,<br>
                <strong>MakePlus Team</strong>
            </p>
        </div>
    </body>
    </html>
    """
    
    return send_email(
        to_email=user.email,
        subject=subject,
        html_content=html_content,
        to_name=user.first_name,
        use_api=True  # Use Brevo API for tracking
    )
