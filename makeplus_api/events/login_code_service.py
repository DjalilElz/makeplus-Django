"""
Login Code Service - Passwordless Authentication

Handles generation, validation, and management of email-based login codes.
Codes are event-scoped with practically infinite expiry.
"""

import secrets
from django.contrib.auth.models import User
from django.utils import timezone
from .models import EmailLoginCode, Event


def generate_6_digit_code():
    """Generate a random 6-digit code"""
    return ''.join([str(secrets.randbelow(10)) for _ in range(6)])


def issue_email_login_code(user, event, invalidate_old=True):
    """
    Generate and store a new login code for user+event
    
    Args:
        user: User instance
        event: Event instance
        invalidate_old: If True, invalidate all old codes for this user+event
    
    Returns:
        tuple: (code: str, login_code_instance: EmailLoginCode)
    """
    # Generate 6-digit code
    code = generate_6_digit_code()
    
    # Invalidate old codes for this user+event if requested
    if invalidate_old:
        EmailLoginCode.objects.filter(
            user=user,
            event=event,
            is_used=False
        ).update(is_used=True, used_at=timezone.now())
    
    # Create new login code
    login_code = EmailLoginCode.objects.create(
        user=user,
        event=event,
        code_hash=EmailLoginCode.hash_code(code)
    )
    
    return code, login_code


def verify_login_code(email, code, event):
    """
    Verify a login code for a user+event
    
    Args:
        email: User's email address
        code: 6-digit code to verify
        event: Event instance
    
    Returns:
        tuple: (success: bool, user: User or None, message: str)
    """
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return False, None, "User not found"
    
    # Find valid login code
    code_hash = EmailLoginCode.hash_code(code)
    
    try:
        login_code = EmailLoginCode.objects.get(
            user=user,
            event=event,
            code_hash=code_hash,
            is_used=False
        )
        
        # Code is valid
        return True, user, "Code verified successfully"
        
    except EmailLoginCode.DoesNotExist:
        return False, None, "Invalid or expired code"
    except EmailLoginCode.MultipleObjectsReturned:
        # Should not happen, but handle gracefully
        return False, None, "Multiple codes found - please request a new code"


def mark_code_as_used(email, code, event, ip_address=None, user_agent=''):
    """
    Mark a login code as used after successful login
    
    Args:
        email: User's email address
        code: 6-digit code
        event: Event instance
        ip_address: IP address of login attempt
        user_agent: User agent string
    
    Returns:
        bool: True if code was marked as used, False otherwise
    """
    try:
        user = User.objects.get(email=email)
        code_hash = EmailLoginCode.hash_code(code)
        
        login_code = EmailLoginCode.objects.get(
            user=user,
            event=event,
            code_hash=code_hash,
            is_used=False
        )
        
        login_code.mark_as_used(ip_address=ip_address, user_agent=user_agent)
        return True
        
    except (User.DoesNotExist, EmailLoginCode.DoesNotExist):
        return False


def invalidate_user_event_codes(user, event):
    """
    Invalidate all login codes for a specific user+event
    Used when user re-registers for the same event
    
    Args:
        user: User instance
        event: Event instance
    
    Returns:
        int: Number of codes invalidated
    """
    count = EmailLoginCode.objects.filter(
        user=user,
        event=event,
        is_used=False
    ).update(is_used=True, used_at=timezone.now())
    
    return count


def get_active_code_count(user, event):
    """
    Get count of active (unused) codes for user+event
    
    Args:
        user: User instance
        event: Event instance
    
    Returns:
        int: Count of active codes
    """
    return EmailLoginCode.objects.filter(
        user=user,
        event=event,
        is_used=False
    ).count()


def cleanup_old_codes(days=90):
    """
    Clean up old used codes (optional maintenance task)
    
    Args:
        days: Delete codes older than this many days
    
    Returns:
        int: Number of codes deleted
    """
    from datetime import timedelta
    cutoff_date = timezone.now() - timedelta(days=days)
    
    count, _ = EmailLoginCode.objects.filter(
        is_used=True,
        used_at__lt=cutoff_date
    ).delete()
    
    return count
