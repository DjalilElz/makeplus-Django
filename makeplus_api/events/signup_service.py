"""
Sign Up Service - Handle user registration with email verification
"""

from django.contrib.auth.models import User
from django.utils import timezone
from .models import SignUpVerification
from dashboard.email_sender import send_email


def send_signup_verification_code(email, first_name, password, last_name, ip_address=None, user_agent=''):
    """
    Send verification code for sign up
    
    Args:
        email: User's email
        first_name: User's first name (for email personalization)
        password: User's password (will be hashed and stored temporarily)
        last_name: User's last name
        ip_address: IP address of request
        user_agent: User agent string
    
    Returns:
        tuple: (success: bool, message: str, wait_seconds: int or None)
    """
    from django.contrib.auth.hashers import make_password
    
    # Check if user already exists
    if User.objects.filter(email=email).exists():
        return False, "Email already registered", None
    
    # Check if can resend
    can_resend, wait_seconds = SignUpVerification.can_resend(email)
    if not can_resend:
        return False, f"Please wait {wait_seconds} seconds before requesting a new code", wait_seconds
    
    # Hash the password for temporary storage
    password_hash = make_password(password)
    
    # Create verification code with signup data
    code, verification = SignUpVerification.create_verification(
        email=email,
        signup_data={
            'first_name': first_name,
            'last_name': last_name,
            'password_hash': password_hash
        },
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    # Send email
    subject = "Verify Your MakePlus Account"
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #667eea;">Welcome to MakePlus!</h2>
            <p>Hello {first_name},</p>
            <p>Thank you for signing up. Please use the verification code below to complete your registration:</p>
            
            <div style="background: #f8f9fa; padding: 20px; border-radius: 5px; text-align: center; margin: 20px 0;">
                <div style="font-size: 48px; font-weight: bold; letter-spacing: 10px; color: #667eea; margin: 20px 0;">
                    {code}
                </div>
                <p style="color: #6c757d; font-size: 0.9em;">This code expires in 3 minutes</p>
            </div>
            
            <div style="background: #fff3cd; padding: 15px; border-left: 4px solid #ffc107; margin: 20px 0;">
                <p style="margin: 0;"><strong>Important:</strong> If you didn't request this code, please ignore this email.</p>
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
        to_name=first_name,
        use_api=True
    )
    
    if success:
        return True, "Verification code sent to your email", None
    else:
        return False, f"Failed to send email: {error}", None


def verify_signup_code(email, code, ip_address=None, user_agent=''):
    """
    Verify sign up code and create user account
    
    Args:
        email: User's email
        code: 6-digit verification code
        ip_address: IP address of request
        user_agent: User agent string
    
    Returns:
        tuple: (success: bool, user: User or None, message: str)
    """
    # Check if user already exists
    if User.objects.filter(email=email).exists():
        return False, None, "Email already registered"
    
    # Find valid verification code
    code_hash = SignUpVerification.hash_code(code)
    
    try:
        verification = SignUpVerification.objects.filter(
            email=email,
            code_hash=code_hash,
            is_used=False
        ).order_by('-created_at').first()
        
        if not verification:
            return False, None, "Invalid or expired code"
        
        # Verify code
        is_valid, message = verification.verify_code(code)
        if not is_valid:
            return False, None, message
        
        # Get stored signup data
        signup_data = verification.signup_data
        first_name = signup_data.get('first_name', '')
        last_name = signup_data.get('last_name', '')
        password_hash = signup_data.get('password_hash', '')
        
        if not all([first_name, last_name, password_hash]):
            return False, None, "Invalid verification data. Please request a new code."
        
        # Create user account
        username = email.split('@')[0]
        counter = 1
        original_username = username
        while User.objects.filter(username=username).exists():
            username = f"{original_username}{counter}"
            counter += 1
        
        user = User.objects.create(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            password=password_hash  # Already hashed
        )
        
        # Create Participant profile automatically
        from .models import Participant, UserProfile
        qr_data = UserProfile.get_qr_for_user(user)
        
        Participant.objects.create(
            user=user,
            badge_id=qr_data['badge_id'],
            qr_code_data=qr_data,
            role='participant'
        )
        
        # Mark code as used
        verification.mark_as_used(ip_address=ip_address, user_agent=user_agent)
        
        return True, user, "Account created successfully"
        
    except Exception as e:
        return False, None, f"Error creating account: {str(e)}"


def resend_signup_code(email, first_name, password, last_name, ip_address=None, user_agent=''):
    """
    Resend verification code for sign up
    
    Args:
        email: User's email
        first_name: User's first name
        password: User's password
        last_name: User's last name
        ip_address: IP address of request
        user_agent: User agent string
    
    Returns:
        tuple: (success: bool, message: str, wait_seconds: int or None)
    """
    return send_signup_verification_code(email, first_name, password, last_name, ip_address, user_agent)
