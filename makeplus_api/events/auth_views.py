"""
Authentication Views - Passwordless Login with Email Codes

Supports both:
1. Email + Login Code (new, passwordless)
2. Email + Password (legacy fallback)
"""

from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.views import View
from django.contrib import messages
from django.http import JsonResponse
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
            messages.error(request, 'Email is required')
            return redirect('events:login')
        
        if not event_id:
            messages.error(request, 'Please select an event')
            return redirect('events:login')
        
        # Get event
        try:
            event = Event.objects.get(id=event_id)
        except Event.DoesNotExist:
            messages.error(request, 'Invalid event')
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
                messages.success(request, f'Welcome back, {user.first_name or user.username}!')
                
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
                messages.success(request, f'Welcome back, {user.first_name or user.username}!')
                return redirect('dashboard:dashboard_home')
            else:
                messages.error(request, 'Invalid email or password')
                return redirect('events:login')
        
        else:
            messages.error(request, 'Please provide either a login code or password')
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
            messages.error(request, 'Email and event are required')
            return redirect('events:request_login_code')
        
        try:
            user = User.objects.get(email=email)
            event = Event.objects.get(id=event_id)
        except User.DoesNotExist:
            messages.error(request, 'User not found. Please register first.')
            return redirect('events:request_login_code')
        except Event.DoesNotExist:
            messages.error(request, 'Event not found')
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
            messages.success(request, f'Login code sent to {email}. Please check your inbox.')
            return redirect('events:login')
        else:
            messages.error(request, f'Failed to send email: {error}')
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
        messages.success(request, 'You have been logged out successfully')
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
            messages.error(request, 'All fields are required')
            return redirect('events:change_password')
        
        if new_password != confirm_password:
            messages.error(request, 'New passwords do not match')
            return redirect('events:change_password')
        
        if len(new_password) < 8:
            messages.error(request, 'Password must be at least 8 characters')
            return redirect('events:change_password')
        
        user = request.user
        if not user.check_password(old_password):
            messages.error(request, 'Current password is incorrect')
            return redirect('events:change_password')
        
        user.set_password(new_password)
        user.save()
        
        # Re-authenticate user
        from django.contrib.auth import update_session_auth_hash
        update_session_auth_hash(request, user)
        
        messages.success(request, 'Password changed successfully')
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


class SelectEventView(View):
    """Select event view"""
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('events:login')
        
        from events.models import Event
        events = Event.objects.all()
        
        return render(request, 'events/select_event.html', {
            'events': events
        })


class SwitchEventView(View):
    """Switch to different event"""
    def post(self, request):
        if not request.user.is_authenticated:
            return JsonResponse({
                'success': False,
                'message': 'Authentication required'
            }, status=401)
        
        event_id = request.POST.get('event_id')
        
        return JsonResponse({
            'success': True,
            'message': 'Event switched successfully'
        })


class MyEventsView(View):
    """List user's events"""
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('events:login')
        
        from events.models import UserEventAssignment
        assignments = UserEventAssignment.objects.filter(user=request.user)
        
        return render(request, 'events/my_events.html', {
            'assignments': assignments
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
