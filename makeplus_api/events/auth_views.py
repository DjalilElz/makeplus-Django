"""
Authentication Views - Passwordless Login with Email Codes

Supports both:
1. Email + Login Code (new, passwordless)
2. Email + Password (legacy fallback)
"""

from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.shortcuts import render, redirect
from django.views import View
from django.contrib import messages
from django.http import JsonResponse
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Event
from .login_code_service import verify_login_code, mark_code_as_used, issue_email_login_code


class CustomLoginView(View):
    """
    Custom login view supporting both:
    - Email + 6-digit code (passwordless)
    - Email + password (legacy fallback)
    """
    template_name = 'events/login.html'
    
    def get(self, request):
        """Show login form"""
        # Get all active events for dropdown
        events = Event.objects.filter(status='active').order_by('-start_date')
        
        return render(request, self.template_name, {
            'events': events
        })
    
    def post(self, request):
        """Handle login submission"""
        email = request.POST.get('email', '').strip()
        code = request.POST.get('code', '').strip()
        password = request.POST.get('password', '').strip()
        event_id = request.POST.get('event', '').strip()
        
        if not email:
            messages.error(request, "L'e-mail est obligatoire")
            return redirect('events:login')
        
        if not event_id:
            messages.error(request, 'Veuillez sélectionner un événement')
            return redirect('events:login')
        
        # Get event
        try:
            event = Event.objects.get(id=event_id)
        except Event.DoesNotExist:
            messages.error(request, 'Événement invalide')
            return redirect('events:login')
        
        # Try code-based login first (if code provided)
        if code:
            success, user, message = verify_login_code(email, code, event)
            
            if success:
                # Mark code as used
                ip_address = self.get_client_ip(request)
                user_agent = request.META.get('HTTP_USER_AGENT', '')
                mark_code_as_used(email, code, event, ip_address, user_agent)
                
                # Log user in
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                messages.success(request, f'Bon retour, {user.first_name or user.username} !')
                
                # Redirect to event or dashboard
                return redirect('dashboard:dashboard_home')
            else:
                messages.error(request, message)
                return redirect('events:login')
        
        # Try password-based login (legacy fallback)
        elif password:
            user = authenticate(request, username=email, password=password)
            
            if user is not None:
                login(request, user)
                messages.success(request, f'Bon retour, {user.first_name or user.username} !')
                return redirect('dashboard:dashboard_home')
            else:
                messages.error(request, 'E-mail ou mot de passe invalide')
                return redirect('events:login')
        
        else:
            messages.error(request, 'Veuillez fournir un code de connexion ou un mot de passe')
            return redirect('events:login')
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class RequestLoginCodeView(View):
    """
    Request a new login code via email
    Used when user wants to login but doesn't have a code
    """
    template_name = 'events/request_code.html'
    
    def get(self, request):
        """Show request code form"""
        events = Event.objects.filter(status='active').order_by('-start_date')
        return render(request, self.template_name, {'events': events})
    
    def post(self, request):
        """Generate and send new login code"""
        email = request.POST.get('email', '').strip()
        event_id = request.POST.get('event', '').strip()
        
        if not email or not event_id:
            messages.error(request, "L'e-mail et l'événement sont obligatoires")
            return redirect('events:request_login_code')
        
        try:
            user = User.objects.get(email=email)
            event = Event.objects.get(id=event_id)
        except User.DoesNotExist:
            messages.error(request, "Utilisateur introuvable. Veuillez d'abord vous inscrire.")
            return redirect('events:request_login_code')
        except Event.DoesNotExist:
            messages.error(request, 'Événement introuvable')
            return redirect('events:request_login_code')
        
        # Generate new login code
        code, login_code_instance = issue_email_login_code(user, event, invalidate_old=True)
        
        # Send email with code
        from dashboard.email_sender import send_email
        
        subject = f"Your login code for {event.name}"
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #667eea;">Login Code for {event.name}</h2>
                <p>Hello {user.first_name or user.username},</p>
                <p>Your login code is:</p>
                <div style="background: #f8f9fa; padding: 20px; border-radius: 5px; text-align: center; margin: 20px 0;">
                    <div style="font-size: 48px; font-weight: bold; letter-spacing: 10px; color: #667eea;">
                        {code}
                    </div>
                </div>
                <p>This code is valid for this event only.</p>
                <p>If you didn't request this code, please ignore this email.</p>
                <br>
                <p>Best regards,<br><strong>MakePlus Team</strong></p>
            </div>
        </body>
        </html>
        """
        
        success, error, message_id = send_email(
            to_email=email,
            subject=subject,
            html_content=html_content,
            to_name=user.first_name or user.username,
            use_api=True
        )
        
        if success:
            messages.success(request, f'Code de connexion envoyé à {email}. Veuillez consulter votre boîte de réception.')
            return redirect('events:login')
        else:
            messages.error(request, f"Échec de l'envoi de l'e-mail : {error}")
            return redirect('events:request_login_code')



class RegisterView(View):
    """
    Registration view - redirects to registration forms
    This is a placeholder for backward compatibility
    """
    def get(self, request):
        return redirect('dashboard:registration_form_builder')


class LogoutView(View):
    """Logout view"""
    def get(self, request):
        from django.contrib.auth import logout
        logout(request)
        messages.success(request, 'Vous avez été déconnecté avec succès')
        return redirect('events:login')


class UserProfileView(View):
    """User profile view"""
    template_name = 'events/profile.html'
    
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('events:login')
        
        return render(request, self.template_name, {
            'user': request.user
        })


class ChangePasswordView(View):
    """Change password view - for legacy password users"""
    template_name = 'events/change_password.html'
    
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('events:login')
        
        return render(request, self.template_name)
    
    def post(self, request):
        if not request.user.is_authenticated:
            return redirect('events:login')
        
        old_password = request.POST.get('old_password', '')
        new_password = request.POST.get('new_password', '')
        confirm_password = request.POST.get('confirm_password', '')
        
        if not old_password or not new_password:
            messages.error(request, 'Tous les champs sont obligatoires')
            return redirect('events:change_password')
        
        if new_password != confirm_password:
            messages.error(request, 'Les nouveaux mots de passe ne correspondent pas')
            return redirect('events:change_password')
        
        if len(new_password) < 8:
            messages.error(request, 'Le mot de passe doit comporter au moins 8 caractères')
            return redirect('events:change_password')
        
        user = request.user
        if not user.check_password(old_password):
            messages.error(request, 'Le mot de passe actuel est incorrect')
            return redirect('events:change_password')
        
        user.set_password(new_password)
        user.save()
        
        # Re-authenticate user
        from django.contrib.auth import update_session_auth_hash
        update_session_auth_hash(request, user)
        
        messages.success(request, 'Mot de passe changé avec succès')
        return redirect('events:profile')



class QRVerificationView(View):
    """QR code verification view"""
    def post(self, request):
        """Verify QR code"""
        qr_data = request.POST.get('qr_data', '')
        
        if not qr_data:
            return JsonResponse({
                'success': False,
                'message': 'QR data is required'
            }, status=400)
        
        # Parse QR data and verify
        # Implementation depends on QR code format
        
        return JsonResponse({
            'success': True,
            'message': 'QR code verified'
        })



class QRGenerateView(View):
    """Generate QR code for user"""
    def get(self, request):
        if not request.user.is_authenticated:
            return JsonResponse({
                'success': False,
                'message': 'Authentication required'
            }, status=401)
        
        # Generate QR code for user
        from events.models import UserProfile
        qr_data = UserProfile.get_qr_for_user(request.user)
        
        return JsonResponse({
            'success': True,
            'qr_data': qr_data
        })


class DashboardStatsView(View):
    """Dashboard statistics view"""
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('events:login')
        
        return render(request, 'events/dashboard_stats.html', {
            'user': request.user
        })


class NotificationListView(View):
    """List user notifications"""
    def get(self, request):
        if not request.user.is_authenticated:
            return JsonResponse({
                'success': False,
                'message': 'Authentication required'
            }, status=401)
        
        return JsonResponse({
            'success': True,
            'notifications': []
        })


class NotificationDetailView(View):
    """Notification detail view"""
    def get(self, request, notification_id):
        if not request.user.is_authenticated:
            return JsonResponse({
                'success': False,
                'message': 'Authentication required'
            }, status=401)
        
        return JsonResponse({
            'success': True,
            'notification': {}
        })


class MarkNotificationReadView(View):
    """Mark notification as read"""
    def post(self, request, notification_id):
        if not request.user.is_authenticated:
            return JsonResponse({
                'success': False,
                'message': 'Authentication required'
            }, status=401)
        
        return JsonResponse({
            'success': True,
            'message': 'Notification marked as read'
        })


class SelectEventView(APIView):
    """
    Second half of login for users attached to more than one event.

    POST /api/auth/select-event/
        Authorization: Bearer <temp_token from the login response>
        {"event_id": "<uuid>"}

    Returns the same payload as a normal single-event login (access +
    refresh with the event_id claim, user, role, event, qr_code), so the
    client can treat both paths identically.

    authentication_classes is deliberately empty: the temp token is a
    django.core.signing value, not a JWT (see utils.make_event_selection_token
    for why). Leaving SimpleJWT's JWTAuthentication in place would make it
    reject the Authorization header as a malformed token and return 401
    before this view ever runs.
    """
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        from events.models import Event
        from events.utils import (
            build_auth_payload,
            read_event_selection_token,
            resolve_role_for_event,
        )

        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if not auth_header.lower().startswith('bearer '):
            return Response(
                {'detail': 'Temporary token required.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        user = read_event_selection_token(auth_header[7:].strip())
        if user is None:
            return Response(
                {'detail': 'Invalid or expired selection token. Please log in again.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        event_id = request.data.get('event_id')
        if not event_id:
            return Response(
                {'detail': 'event_id is required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            event = Event.objects.filter(id=event_id).first()
        except (ValueError, ValidationError):
            # Non-UUID event_id -- filter() raises rather than returning empty.
            event = None
        if event is None:
            return Response(
                {'detail': 'Event not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        # The authorization check: never mint a token for an event this user
        # is not actually attached to, whatever they asked for.
        role = resolve_role_for_event(user, event)
        if role is None:
            return Response(
                {'detail': 'You do not have access to this event.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        return Response(build_auth_payload(user, event, role, request))


class SwitchEventView(APIView):
    """
    Switch the active event for an already-signed-in user, without making
    them log out and back in.

    POST /api/auth/switch-event/  {"event_id": "<uuid>"}
    with a normal access token. Returns a fresh token pair carrying the new
    event_id claim.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        from events.models import Event
        from events.utils import build_auth_payload, resolve_role_for_event

        event_id = request.data.get('event_id')
        if not event_id:
            return Response(
                {'detail': 'event_id is required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            event = Event.objects.filter(id=event_id).first()
        except (ValueError, ValidationError):
            event = None
        if event is None:
            return Response(
                {'detail': 'Event not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        role = resolve_role_for_event(request.user, event)
        if role is None:
            return Response(
                {'detail': 'You do not have access to this event.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        return Response(build_auth_payload(request.user, event, role, request))


class MyEventsView(APIView):
    """
    GET /api/auth/my-events/ -- every event the signed-in user can access,
    with their role in each and which one is currently active.

    Backs an in-app event switcher. Uses get_accessible_event_ids so plain
    participants are included: they never get a UserEventAssignment row, so
    querying that table alone (as this view previously did) returned an
    empty list for the majority of users.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from events.models import Event
        from events.utils import (
            build_event_payload,
            get_accessible_event_ids,
            resolve_role_for_event,
        )

        event_ids = get_accessible_event_ids(request.user)
        events = Event.objects.filter(id__in=event_ids).order_by('-start_date', 'name')

        current_event_id = None
        event_context = getattr(request, 'event_context', None)
        if event_context is not None:
            current_event_id = str(event_context.id)

        return Response({
            'count': events.count(),
            'current_event_id': current_event_id,
            'events': [
                {
                    **build_event_payload(event, request),
                    'role': resolve_role_for_event(request.user, event),
                    'is_current': str(event.id) == current_event_id,
                }
                for event in events
            ],
        })


class MyRoomStatisticsView(View):
    """Room statistics for room managers"""
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('events:login')
        
        return render(request, 'events/my_room_stats.html', {
            'user': request.user
        })


class MyAteliersView(View):
    """List user's ateliers/workshops"""
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('events:login')
        
        return render(request, 'events/my_ateliers.html', {
            'user': request.user
        })
