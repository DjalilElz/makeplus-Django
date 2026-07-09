"""
Form Registration Validation Service
"""

from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.utils import timezone
from .models import FormRegistrationVerification, UserEventAssignment, Participant, UserProfile
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
    # No account is required to register -- if one doesn't exist yet, a
    # placeholder gets created once the code is verified (see
    # get_or_create_user_by_email). Greet by the name given on the form.
    greeting_name = form_data.get('first_name', '')

    # Get form
    try:
        form = FormConfiguration.objects.get(slug=form_slug)
    except FormConfiguration.DoesNotExist:
        return False, "Formulaire introuvable", None

    # Check if form is active
    if not form.is_active:
        return False, "Ce formulaire n'accepte plus de soumissions", None

    # Check if can resend
    can_resend, wait_seconds = FormRegistrationVerification.can_resend(email, form)
    if not can_resend:
        return False, f"Veuillez patienter {wait_seconds} secondes avant de demander un nouveau code", wait_seconds
    
    # Create verification code
    code, verification = FormRegistrationVerification.create_verification(
        email=email,
        form=form,
        form_data=form_data,
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    # Send email
    subject = f"Vérifiez votre inscription - {form.event.name if form.event else form.name}"
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #667eea;">Vérifiez votre inscription</h2>
            <p>Bonjour {greeting_name},</p>
            <p>Merci de vous être inscrit(e) à <strong>{form.event.name if form.event else form.name}</strong>.</p>
            <p>Veuillez utiliser le code de vérification ci-dessous pour terminer votre inscription :</p>

            <div style="background: #f8f9fa; padding: 20px; border-radius: 5px; text-align: center; margin: 20px 0;">
                <div style="font-size: 48px; font-weight: bold; letter-spacing: 10px; color: #667eea; margin: 20px 0;">
                    {code}
                </div>
                <p style="color: #6c757d; font-size: 0.9em;">Ce code expire dans 3 minutes</p>
            </div>

            <div style="background: #e7f3ff; padding: 15px; border-left: 4px solid #2196F3; margin: 20px 0;">
                <p style="margin: 0;"><strong>Étape suivante :</strong> Entrez ce code sur la page d'inscription pour terminer votre inscription.</p>
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
        to_name=greeting_name,
        use_api=True
    )
    
    if success:
        return True, "Code de vérification envoyé à votre e-mail", None
    else:
        return False, f"Échec de l'envoi de l'e-mail : {error}", None


def create_participant_for_event(user, event):
    """
    Get-or-create the Participant/registration/assignment records that grant
    a user the 'participant' role for an event. Shared by the free-flow
    email verification (immediate) and admin approval of paid registrations.
    """
    from .models import ParticipantEventRegistration

    participant, _ = Participant.objects.get_or_create(
        user=user,
        defaults={
            'badge_id': UserProfile.get_qr_for_user(user)['badge_id'],
            'qr_code_data': UserProfile.get_qr_for_user(user),
            'role': 'participant'
        }
    )
    ParticipantEventRegistration.objects.get_or_create(participant=participant, event=event)
    UserEventAssignment.objects.get_or_create(user=user, event=event, defaults={'role': 'participant'})
    return participant


def get_or_create_user_by_email(email, first_name='', last_name=''):
    """
    Get the account for this email, or create a placeholder one (unusable
    password) if they haven't signed up in the mobile app yet -- lets
    someone register for an event before creating an account. When they
    later use the app's normal "Sign Up" with the same email,
    verify_signup_code() claims this placeholder (sets a real password)
    instead of refusing or creating a duplicate.
    """
    user = User.objects.filter(email=email).first()
    if user:
        return user

    username = email.split('@')[0]
    original_username = username
    counter = 1
    while User.objects.filter(username=username).exists():
        username = f"{original_username}{counter}"
        counter += 1

    try:
        with transaction.atomic():
            user = User.objects.create(
                username=username,
                email=email,
                first_name=first_name or '',
                last_name=last_name or '',
            )
            user.set_unusable_password()
            user.save(update_fields=['password'])
        return user
    except IntegrityError:
        # Lost a race against a concurrent submission/signup for the same email.
        return User.objects.filter(email=email).first()


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
    # Get form
    try:
        form = FormConfiguration.objects.get(slug=form_slug)
    except FormConfiguration.DoesNotExist:
        return False, None, "Formulaire introuvable"

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
            return False, None, "Code invalide ou expiré"
        
        # Verify code
        is_valid, message = verification.verify_code(code)
        if not is_valid:
            return False, None, message

        # They've now proven ownership of the email -- get their account,
        # or create a placeholder one if they haven't signed up in the app.
        user = get_or_create_user_by_email(
            email,
            first_name=verification.form_data.get('first_name', ''),
            last_name=verification.form_data.get('last_name', ''),
        )

        # Paid (blocs) registrations were staged at submit time -- the
        # RegistrationOrder is created now as "reserved". The participant
        # role is granted right away (same trust level as the free flow);
        # the caisse operator does the real payment validation on event day.
        if verification.form_data.get('__paid_meta__'):
            from dashboard.views_blocs import finalize_paid_registration
            ok, result_message = finalize_paid_registration(verification, form, user)
            if not ok:
                return False, None, result_message
            verification.mark_as_used(ip_address=ip_address, user_agent=user_agent)
            participant = Participant.objects.filter(user=user).first()
            return True, participant, result_message

        # Free (no-blocs) flow: grant the participant role immediately,
        # since there's no payment for an admin to review.
        participant = create_participant_for_event(user, form.event) if form.event else None

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

        return True, participant, "Inscription terminée avec succès"

    except Exception as e:
        return False, None, f"Erreur lors de la finalisation de l'inscription : {str(e)}"


def resend_form_validation_code(email, form_slug, form_data=None, ip_address=None, user_agent=''):
    """
    Resend validation code for form registration.

    Args:
        email: User's email
        form_slug: Form slug
        form_data: Form submission data. Pass explicitly when the caller has
            it on hand (e.g. the mobile app). If omitted, the data staged by
            the most recent verification attempt for this email/form is
            reused -- the public registration page's "Resend Code" button
            only has the email available, not the original answers/receipt.
        ip_address: IP address of request
        user_agent: User agent string

    Returns:
        tuple: (success: bool, message: str, wait_seconds: int or None)
    """
    if form_data is None:
        try:
            form = FormConfiguration.objects.get(slug=form_slug)
        except FormConfiguration.DoesNotExist:
            return False, "Formulaire introuvable", None

        previous = FormRegistrationVerification.objects.filter(
            email=email, form=form
        ).order_by('-created_at').first()
        if not previous:
            return False, "Aucune inscription précédente trouvée pour cet e-mail. Veuillez remplir le formulaire à nouveau.", None
        form_data = previous.form_data

    return send_form_validation_code(email, form_slug, form_data, ip_address, user_agent)
