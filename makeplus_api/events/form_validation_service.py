"""
Form Registration Validation Service
"""

from django.contrib.auth.models import User
from django.utils import timezone
from .models_verification import FormRegistrationVerification
from .models import UserEventAssignment, Participant, UserProfile
from dashboard.models_form import FormConfiguration, FormSubmission
from dashboard.email_sender import send_email


def send_form_validation_code(email, form_slug, form_data, ip_address=None, user_agent=''):
    """
    Send validation code for form registration
    
    Args:
        email: User's email
        form_slug: Form slug
        form_data: Form submission data
        ip_address: IP address of request
        user_agent: User agent string
    
    Returns:
        tuple: (success: bool, message: str, wait_seconds: int or None)
    """
    # Check if user exists
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return False, "Please create an account first in the mobile app", None
    
    # Get form
    try:
        form = FormConfiguration.objects.get(slug=form_slug)
    except FormConfiguration.DoesNotExist:
        return False, "Form not found", None
    
    # Check if form is active
    if not form.is_active:
        return False, "This form is no longer accepting submissions", None
    
    # Check if can resend
    can_resend, wait_seconds = FormRegistrationVerification.can_resend(email, form)
    if not can_resend:
        return False, f"Please wait {wait_seconds} seconds before requesting a new code", wait_seconds
    
    # Create verification code
    code, verification = FormRegistrationVerification.create_verification(
        email=email,
        form=form,
        form_data=form_data,
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    # Send email
    subject = f"Verify Your Registration - {form.event.name if form.event else form.name}"
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #667eea;">Verify Your Registration</h2>
            <p>Hello {user.first_name},</p>
            <p>Thank you for registering for <strong>{form.event.name if form.event else form.name}</strong>.</p>
            <p>Please use the verification code below to complete your registration:</p>
            
            <div style="background: #f8f9fa; padding: 20px; border-radius: 5px; text-align: center; margin: 20px 0;">
                <div style="font-size: 48px; font-weight: bold; letter-spacing: 10px; color: #667eea; margin: 20px 0;">
                    {code}
                </div>
                <p style="color: #6c757d; font-size: 0.9em;">This code expires in 3 minutes</p>
            </div>
            
            <div style="background: #e7f3ff; padding: 15px; border-left: 4px solid #2196F3; margin: 20px 0;">
                <p style="margin: 0;"><strong>Next Step:</strong> Enter this code on the registration page to complete your registration.</p>
            </div>
            
            <p style="margin-top: 30px;">
                Best regards,<br>
                <strong>MakePlus Team</strong>
            </p>
        </div>
    </body>
    </html>
    """
    
    success, error, message_id = send_email(
        to_email=email,
        subject=subject,
        html_content=html_content,
        to_name=user.first_name,
        use_api=True
    )
    
    if success:
        return True, "Verification code sent to your email", None
    else:
        return False, f"Failed to send email: {error}", None


def verify_form_registration(email, form_slug, code, ip_address=None, user_agent=''):
    """
    Verify form registration code and create participant record
    
    Args:
        email: User's email
        form_slug: Form slug
        code: 6-digit verification code
        ip_address: IP address of request
        user_agent: User agent string
    
    Returns:
        tuple: (success: bool, participant: Participant or None, message: str)
    """
    # Get user
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return False, None, "User not found"
    
    # Get form
    try:
        form = FormConfiguration.objects.get(slug=form_slug)
    except FormConfiguration.DoesNotExist:
        return False, None, "Form not found"
    
    # Find valid verification code
    code_hash = FormRegistrationVerification.hash_code(code)
    
    try:
        verification = FormRegistrationVerification.objects.filter(
            email=email,
            form=form,
            code_hash=code_hash,
            is_used=False
        ).order_by('-created_at').first()
        
        if not verification:
            return False, None, "Invalid or expired code"
        
        # Verify code
        is_valid, message = verification.verify_code(code)
        if not is_valid:
            return False, None, message
        
        # Check if user already registered for this event
        if form.event:
            existing_participant = Participant.objects.filter(
                user=user,
                event=form.event
            ).first()
            
            if existing_participant:
                # Update existing participant
                participant = existing_participant
            else:
                # Create participant record
                qr_data = UserProfile.get_qr_for_user(user)
                
                participant = Participant.objects.create(
                    user=user,
                    event=form.event,
                    badge_id=qr_data['badge_id'],
                    qr_code_data=qr_data
                )
                
                # Create or update user event assignment
                UserEventAssignment.objects.get_or_create(
                    user=user,
                    event=form.event,
                    defaults={'role': 'participant'}
                )
        else:
            participant = None
        
        # Create form submission
        FormSubmission.objects.create(
            form=form,
            email=email,
            data=verification.form_data,
            ip_address=ip_address,
            user_agent=user_agent,
            status='approved'
        )
        
        # Increment submission count
        form.increment_submission_count()
        
        # Mark code as used
        verification.mark_as_used(ip_address=ip_address, user_agent=user_agent)
        
        return True, participant, "Registration completed successfully"
        
    except Exception as e:
        return False, None, f"Error completing registration: {str(e)}"


def resend_form_validation_code(email, form_slug, form_data, ip_address=None, user_agent=''):
    """
    Resend validation code for form registration
    
    Args:
        email: User's email
        form_slug: Form slug
        form_data: Form submission data
        ip_address: IP address of request
        user_agent: User agent string
    
    Returns:
        tuple: (success: bool, message: str, wait_seconds: int or None)
    """
    return send_form_validation_code(email, form_slug, form_data, ip_address, user_agent)
