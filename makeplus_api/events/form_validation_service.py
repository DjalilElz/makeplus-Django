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
    event_or_form_name = form.event.name if form.event else form.name
    subject = f"Vérifiez votre inscription - {event_or_form_name}"
    html_content = f"""
    <html>
    <body style="margin:0; padding:0; background-color:#ffffff; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color:#1a1a1a;">
        <div style="max-width: 480px; margin: 0 auto; padding: 48px 24px;">
            <h1 style="font-size: 20px; font-weight: 600; margin: 0 0 24px 0; color:#1a1a1a;">Vérifiez votre inscription</h1>

            <p style="font-size: 15px; line-height: 1.6; margin: 0 0 16px 0;">Bonjour {greeting_name},</p>
            <p style="font-size: 15px; line-height: 1.6; margin: 0 0 32px 0;">
                Merci de vous être inscrit(e) à <strong>{event_or_form_name}</strong>. Utilisez le code ci-dessous pour terminer votre inscription :
            </p>

            <div style="text-align: center; padding: 28px 0; margin: 0 0 16px 0; border: 1px solid #e5e5e5; border-radius: 8px;">
                <div style="font-size: 36px; font-weight: 700; letter-spacing: 8px; color:#1a1a1a;">{code}</div>
            </div>

            <p style="font-size: 13px; color: #767676; margin: 0 0 32px 0; text-align:center;">Ce code expire dans 3 minutes</p>

            <p style="font-size: 14px; line-height: 1.6; color:#4a4a4a; margin: 0 0 40px 0;">
                Entrez ce code sur la page d'inscription pour terminer votre inscription.
            </p>

            <p style="font-size: 14px; color:#767676; margin: 0; border-top: 1px solid #e5e5e5; padding-top: 24px;">
                Cordialement,<br>L'équipe MakePlus
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

    # Checking existence up front (instead of routing everything through
    # get_or_create_qr_code's full lookup chain, as this used to) means an
    # already-registered user -- the common case for repeat/admin-added
    # registrations and every row of a bulk import after their first
    # event -- costs one query here instead of the five-plus hidden
    # inside get_qr_for_user (assignment/participant/registration/
    # CaisseTransaction, none of which can change anything for a
    # Participant that already exists). Only a genuinely new participant
    # pays for QR generation at all, via the cheaper build_initial_qr_data.
    try:
        participant = Participant.objects.get(user=user)
    except Participant.DoesNotExist:
        qr_data = UserProfile.build_initial_qr_data(user)
        participant = Participant.objects.create(
            user=user, badge_id=qr_data['badge_id'], qr_code_data=qr_data, role='participant',
        )
    ParticipantEventRegistration.objects.get_or_create(participant=participant, event=event)
    UserEventAssignment.objects.get_or_create(user=user, event=event, defaults={'role': 'participant'})
    return participant


def send_registration_confirmation_email(user, event):
    """
    Best-effort confirmation email sent right after a registration is
    finalized (free flow immediately, paid flow once the order is
    reserved -- both already grant the participant role, see
    create_participant_for_event's docstring): a minimal "you're
    confirmed" message with the participant's QR code embedded inline,
    to present at check-in. Failures are logged, never raised -- a
    delivery hiccup here must not undo or block a registration that
    already succeeded.

    Fire-and-forget: the actual work (a QR lookup, rendering a PNG, a
    live Postmark API call) used to run inline in the caller's request --
    the self-registration flow, the event owner's manual "Nouvelle
    inscription" page, and each row of the bulk import's email phase all
    had the person who just finished registering sit through it. None of
    those callers use this function's return value or need it to have
    finished before they respond, so it's safe to hand off to a
    background thread instead. This app has no task queue (Celery/etc.),
    so a plain daemon thread is the pragmatic option at this scale.
    """
    import threading
    threading.Thread(
        target=_send_registration_confirmation_email_now, args=(user, event), daemon=True,
    ).start()


def _send_registration_confirmation_email_now(user, event):
    """The actual send for send_registration_confirmation_email -- runs
    off the request thread, so it manages its own DB connection: Django
    only auto-closes connections at the end of a *request*, which this
    thread is not, so an explicit close() is needed once done with it
    (not finishing one isn't catastrophic for a short-lived daemon thread
    that exits right after, but leaves the connection open longer than
    necessary otherwise)."""
    import io
    import logging
    import qrcode
    from django.db import connection

    try:
        qr_data = UserProfile.get_qr_for_user(user)
        # Same plain user_id payload as every other badge QR in the app
        # (see dashboard.views._qr_display_payload) -- scanners only need
        # the id to look the participant up.
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(str(qr_data.get('user_id')))
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        qr_png_bytes = buffer.getvalue()

        full_name = user.get_full_name() or user.email
        event_name = event.name if event else ''
        intro = f'votre inscription à <strong>{event_name}</strong> est confirmée.' if event_name else 'votre inscription est confirmée.'

        subject = f"Inscription confirmée - {event_name}" if event_name else "Inscription confirmée"
        html_content = f"""
        <html>
        <body style="margin:0; padding:0; background-color:#ffffff; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color:#1a1a1a;">
            <div style="max-width: 480px; margin: 0 auto; padding: 48px 24px;">
                <h1 style="font-size: 20px; font-weight: 600; margin: 0 0 24px 0; color:#1a1a1a;">Inscription confirmée</h1>

                <p style="font-size: 15px; line-height: 1.6; margin: 0 0 32px 0;">
                    Bonjour {full_name}, {intro}
                </p>

                <div style="text-align: center; padding: 24px 0; margin: 0 0 16px 0; border: 1px solid #e5e5e5; border-radius: 8px;">
                    <img src="cid:qrcode" alt="QR code" width="200" height="200" style="display:block; margin:0 auto; width:200px; height:200px;">
                </div>

                <p style="font-size: 14px; line-height: 1.6; color:#4a4a4a; margin: 0 0 40px 0; text-align:center;">
                    Présentez ce code QR à l'accueil pour le contrôle d'accès.
                </p>

                <p style="font-size: 14px; color:#767676; margin: 0; border-top: 1px solid #e5e5e5; padding-top: 24px;">
                    Cordialement,<br>L'équipe MakePlus
                </p>
            </div>
        </body>
        </html>
        """

        send_email(
            to_email=user.email,
            subject=subject,
            html_content=html_content,
            to_name=full_name,
            use_api=True,
            attachments=[{
                'name': 'qr-code.png',
                'content': qr_png_bytes,
                'mimetype': 'image/png',
                'content_id': 'qrcode',
            }],
        )
    except Exception:
        logging.getLogger(__name__).exception(
            "Failed to send registration confirmation email to %s", user.email,
        )
    finally:
        connection.close()


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


def get_or_create_user_for_manual_registration(email, first_name='', last_name=''):
    """
    Like get_or_create_user_by_email, but for the event owner's own manual
    "Nouvelle inscription" entry, where the same email is routinely shared
    by many genuinely different attendees -- a sponsor's guest list, a
    receptionist's inbox used for walk-ins without their own email, etc.
    get_or_create_user_by_email's plain email lookup would silently merge
    every one of them into whichever person happened to be entered first
    under that email (Participant/badge/UserEventAssignment are all keyed
    off the User account, not the name on the order), which is exactly
    what made every later registration under a shared email invisible at
    the caisse -- their name only ever existed on their own order, never
    on the account caisse actually searches/displays.

    Only treated as the same returning person (reusing their account and
    badge) when BOTH the email and the name already match; a different
    name under the same email always gets its own account.
    """
    existing = User.objects.filter(
        email__iexact=email, first_name__iexact=first_name, last_name__iexact=last_name,
    ).first()
    if existing:
        return existing

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
        # Lost a race against a concurrent submission for the same
        # email+name -- the username loop above already avoided a plain
        # username collision, so this means someone else just created
        # the exact same person.
        return User.objects.filter(
            email__iexact=email, first_name__iexact=first_name, last_name__iexact=last_name,
        ).first()


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
            send_registration_confirmation_email(user, form.event)
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

        send_registration_confirmation_email(user, form.event)

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
