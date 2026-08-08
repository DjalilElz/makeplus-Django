"""
Password Reset Service - Handle self-service password reset with email verification
"""

from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import PasswordResetVerification
from dashboard.email_sender import send_email


def request_password_reset(email, new_password, ip_address=None, user_agent=''):
    """
    Send a verification code to reset a real account's password.

    Args:
        email: Account email
        new_password: The password to apply once the code is verified
        ip_address: IP address of request
        user_agent: User agent string

    Returns:
        tuple: (success: bool, message: str, wait_seconds: int or None)
    """
    # A placeholder account (created by event registration, no usable
    # password yet) has nothing to "reset" -- that email needs to go
    # through signup instead, same boundary signup_service enforces in
    # the other direction.
    user = User.objects.filter(email=email).first()
    if not user or not user.has_usable_password():
        return False, "Aucun compte trouvé avec cet email", None

    try:
        validate_password(new_password, user=user)
    except ValidationError as e:
        return False, ', '.join(e.messages), None

    can_resend, wait_seconds = PasswordResetVerification.can_resend(email)
    if not can_resend:
        return False, f"Veuillez patienter {wait_seconds} secondes avant de demander un nouveau code", wait_seconds

    code, verification = PasswordResetVerification.create_verification(
        email=email,
        new_password_hash=make_password(new_password),
        ip_address=ip_address,
        user_agent=user_agent
    )

    subject = "Réinitialisation de votre mot de passe MakePlus"
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #667eea;">Réinitialisation de mot de passe</h2>
            <p>Bonjour {user.first_name or ''},</p>
            <p>Utilisez le code ci-dessous pour réinitialiser votre mot de passe MakePlus :</p>

            <div style="background: #f8f9fa; padding: 20px; border-radius: 5px; text-align: center; margin: 20px 0;">
                <div style="font-size: 48px; font-weight: bold; letter-spacing: 10px; color: #667eea; margin: 20px 0;">
                    {code}
                </div>
                <p style="color: #6c757d; font-size: 0.9em;">Ce code expire dans 3 minutes</p>
            </div>

            <div style="background: #fff3cd; padding: 15px; border-left: 4px solid #ffc107; margin: 20px 0;">
                <p style="margin: 0;"><strong>Important :</strong> Si vous n'êtes pas à l'origine de cette demande, ignorez cet email -- votre mot de passe restera inchangé.</p>
            </div>

            <p style="margin-top: 30px;">
                Cordialement,<br>
                <strong>L'équipe MakePlus</strong>
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
        return True, "Code de vérification envoyé à votre email", None
    else:
        return False, f"Échec de l'envoi de l'email : {error}", None


def verify_password_reset(email, code, ip_address=None, user_agent=''):
    """
    Verify the reset code and apply the new password stored alongside it.

    Args:
        email: Account email
        code: 6-digit verification code
        ip_address: IP address of request
        user_agent: User agent string

    Returns:
        tuple: (success: bool, message: str)
    """
    user = User.objects.filter(email=email).first()
    if not user or not user.has_usable_password():
        return False, "Aucun compte trouvé avec cet email"

    code_hash = PasswordResetVerification.hash_code(code)
    verification = PasswordResetVerification.objects.filter(
        email=email,
        code_hash=code_hash,
        is_used=False
    ).order_by('-created_at').first()

    if not verification:
        return False, "Code invalide ou expiré"

    is_valid, message = verification.verify_code(code)
    if not is_valid:
        return False, message

    if not verification.new_password_hash:
        return False, "Données de réinitialisation invalides. Veuillez recommencer."

    user.password = verification.new_password_hash  # Already hashed
    user.save(update_fields=['password'])

    verification.mark_as_used(ip_address=ip_address, user_agent=user_agent)

    # Proving control of the account is exactly the moment to kill any
    # session issued before it -- otherwise a stolen refresh token from
    # before the reset keeps working after it.
    from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
    for outstanding in OutstandingToken.objects.filter(user=user):
        BlacklistedToken.objects.get_or_create(token=outstanding)

    return True, "Mot de passe réinitialisé avec succès"


def resend_password_reset_code(email, new_password, ip_address=None, user_agent=''):
    """
    Resend verification code for password reset

    Returns:
        tuple: (success: bool, message: str, wait_seconds: int or None)
    """
    return request_password_reset(email, new_password, ip_address, user_agent)
