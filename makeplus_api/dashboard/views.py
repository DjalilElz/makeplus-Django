"""
Views for MakePlus Dashboard - OPTIMIZED
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.db.models import Count, Q, Sum, Prefetch
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.contrib.auth.models import User
from django.core.cache import cache
from django.views.decorators.cache import cache_page
from datetime import timedelta
import json
import qrcode
import io
import base64

# Cache invalidation helper
def invalidate_event_cache(event_id):
    """Invalidate all caches related to an event"""
    cache_keys = [
        f'event_detail_{event_id}',
        'dashboard_home',
    ]
    cache.delete_many(cache_keys)

from events.models import (
    Event, Room, Session, UserEventAssignment, Participant,
    SessionAccess, RoomAccess, ExposantScan, UserProfile,
    SessionQuestion, Annonce
)
from .forms import (
    EventDetailsForm, RoomForm, SessionForm, UserCreationForm,
    QuickUserForm, RoomAssignmentForm
)


def is_staff_user(user):
    """Check if user is staff"""
    return user.is_staff or user.is_superuser


# ==================== Authentication Views ====================

def login_view(request):
    """Login page for dashboard"""
    if request.user.is_authenticated:
        return redirect('dashboard:home')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # DEBUG: Print what we received
        print(f"DEBUG Login attempt:")
        print(f"  Username received: '{username}' (length: {len(username) if username else 0})")
        print(f"  Password received: '{password}' (length: {len(password) if password else 0})")
        
        user = authenticate(request, username=username, password=password)
        
        print(f"  authenticate() returned: {user}")
        
        if user is not None:
            print(f"  User is_staff: {user.is_staff}, is_superuser: {user.is_superuser}")
            if user.is_staff or user.is_superuser:
                login(request, user)
                messages.success(request, f'Welcome back, {user.get_full_name() or user.username}!')
                return redirect('dashboard:home')
            else:
                messages.error(request, 'You do not have permission to access the dashboard.')
        else:
            print(f"  Authentication FAILED")
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'dashboard/login.html')


@login_required
def logout_view(request):
    """Logout"""
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('dashboard:login')


# ==================== Dashboard Home ====================

@login_required
@user_passes_test(is_staff_user)
def dashboard_home(request):
    """Main dashboard with statistics and event list"""
    
    # Get recent events only (limit to 20 for performance)
    # Use prefetch to get counts efficiently
    events = Event.objects.select_related('created_by').prefetch_related(
        'participants', 'rooms', 'sessions'
    ).order_by('-start_date')[:20]
    
    # Calculate overall statistics using aggregate (single query)
    from django.db.models import Q
    stats = Event.objects.aggregate(
        total=Count('id'),
        active=Count('id', filter=Q(status='active')),
        upcoming=Count('id', filter=Q(status='upcoming')),
        completed=Count('id', filter=Q(status='completed'))
    )
    
    total_events = stats['total']
    active_events = stats['active']
    upcoming_events = stats['upcoming']
    completed_events = stats['completed']
    
    # Simple counts (cached values from Event model where possible)
    total_participants = Participant.objects.count()
    total_users = User.objects.count()
    total_sessions = Session.objects.count()
    
    # Skip recent activity for performance (or make it optional)
    recent_room_accesses = 0
    recent_scans = 0
    
    context = {
        'events': events,
        'total_events': total_events,
        'active_events': active_events,
        'upcoming_events': upcoming_events,
        'completed_events': completed_events,
        'total_participants': total_participants,
        'total_users': total_users,
        'total_sessions': total_sessions,
        'recent_room_accesses': recent_room_accesses,
        'recent_scans': recent_scans,
    }
    
    return render(request, 'dashboard/home.html', context)


# ==================== Event Detail View ====================

@login_required
@user_passes_test(is_staff_user)
def event_detail(request, event_id):
    """Comprehensive event detail view with all statistics - OPTIMIZED"""
    from django.core.cache import cache
    from django.db.models import Count, Sum, Q, Prefetch
    
    # Try to get from cache first (cache for 2 minutes)
    cache_key = f'event_detail_{event_id}'
    cached_data = cache.get(cache_key)
    
    if cached_data and not request.GET.get('refresh'):
        return render(request, 'dashboard/event_detail.html', cached_data)
    
    event = get_object_or_404(Event.objects.select_related('created_by'), id=event_id)
    
    # Get event rooms (only fetch needed fields)
    rooms = Room.objects.filter(event=event).only(
        'id', 'name', 'capacity', 'location', 'description', 'current_participants'
    )
    
    # Get event sessions (prefetch room to avoid N+1)
    sessions = Session.objects.filter(event=event).select_related('room').only(
        'id', 'title', 'session_type', 'start_time', 'end_time', 'speaker_name', 
        'speaker_title', 'is_paid', 'price', 'youtube_live_url', 'room__name', 'room__id'
    )
    
    # Get all user assignments in ONE query with prefetch
    all_assignments = UserEventAssignment.objects.filter(
        event=event,
        is_active=True
    ).select_related('user').only('role', 'user__username', 'user__first_name', 'user__last_name')
    
    # Separate by role in Python (faster than 4 separate queries)
    organisateurs = [a for a in all_assignments if a.role == 'organisateur']
    gestionnaires = [a for a in all_assignments if a.role == 'gestionnaire_des_salles']
    controleurs = [a for a in all_assignments if a.role == 'controlleur_des_badges']
    exposants = [a for a in all_assignments if a.role == 'exposant']
    
    # Use aggregate for statistics (single query instead of multiple counts)
    participant_stats = Participant.objects.filter(event=event).aggregate(
        total=Count('id'),
        checked_in=Count('id', filter=Q(is_checked_in=True))
    )
    
    session_stats = sessions.aggregate(
        total=Count('id'),
        conferences=Count('id', filter=Q(session_type='conference')),
        ateliers=Count('id', filter=Q(session_type='atelier'))
    )
    
    total_participants = participant_stats['total']
    checked_in_participants = participant_stats['checked_in'] or 0
    total_sessions = session_stats['total']
    conferences = session_stats['conferences'] or 0
    ateliers = session_stats['ateliers'] or 0
    
    # Get participants queryset for template (but don't iterate here)
    participants = Participant.objects.filter(event=event).select_related('user')
    
    # Room access statistics (optimized)
    room_accesses = RoomAccess.objects.filter(room__event=event).count() if RoomAccess.objects.filter(room__event=event).exists() else 0
    
    # Exposant scans (optimized) - use correct field name 'scanned_participant'
    exposant_scans = ExposantScan.objects.filter(scanned_participant__event=event).count() if ExposantScan.objects.filter(scanned_participant__event=event).exists() else 0
    
    # Session questions (use aggregate with correct field name)
    question_stats = SessionQuestion.objects.filter(session__event=event).aggregate(
        total=Count('id'),
        answered=Count('id', filter=Q(is_answered=True))
    )
    total_questions = question_stats['total'] or 0
    answered_questions = question_stats['answered'] or 0
    
    # Get caisses with aggregated stats (MUCH faster than calling methods)
    from caisse.models import Caisse, CaisseTransaction
    caisses = Caisse.objects.filter(event=event).select_related('event')
    
    # Get all transaction stats in ONE query
    caisse_transaction_stats = CaisseTransaction.objects.filter(
        caisse__event=event
    ).values('caisse_id').annotate(
        total_amount=Sum('total_amount'),
        transaction_count=Count('id'),
        total_participants=Count('participant_id', distinct=True)
    )
    
    # Create lookup dict for fast access
    stats_lookup = {stat['caisse_id']: stat for stat in caisse_transaction_stats}
    
    caisse_stats = []
    for caisse in caisses:
        stats = stats_lookup.get(caisse.id, {})
        caisse_stats.append({
            'caisse': caisse,
            'total_amount': stats.get('total_amount', 0) or 0,
            'total_participants': stats.get('total_participants', 0) or 0,
            'transaction_count': stats.get('transaction_count', 0) or 0
        })
    
    context = {
        'event': event,
        'rooms': rooms,
        'sessions': sessions,
        'participants': participants,
        'organisateurs': organisateurs,
        'gestionnaires': gestionnaires,
        'controleurs': controleurs,
        'exposants': exposants,
        'total_participants': total_participants,
        'checked_in_participants': checked_in_participants,
        'total_sessions': total_sessions,
        'conferences': conferences,
        'ateliers': ateliers,
        'workshops': 0,
        'room_accesses': room_accesses,
        'exposant_scans': exposant_scans,
        'total_questions': total_questions,
        'answered_questions': answered_questions,
        'caisses': caisses,
        'caisse_stats': caisse_stats,
    }
    
    # Cache the context for 2 minutes
    cache.set(cache_key, context, 120)

    
    return render(request, 'dashboard/event_detail.html', context)


# ==================== Multi-Step Event Creation ====================

@login_required
@user_passes_test(is_staff_user)
def event_create_step1(request):
    """Step 1: Event Details"""
    
    if request.method == 'POST':
        form = EventDetailsForm(request.POST)
        if form.is_valid():
            # Save event
            event = form.save(commit=False)
            event.created_by = request.user
            event.save()
            
            # Store number of rooms in session
            request.session['event_id'] = str(event.id)
            request.session['number_of_rooms'] = form.cleaned_data['number_of_rooms']
            request.session['current_room'] = 0
            request.session['rooms_data'] = []
            
            messages.success(request, f'Event "{event.name}" created! Now let\'s add rooms.')
            return redirect('dashboard:event_create_step2')
        else:
            # Show validation errors
            messages.error(request, 'Please fix the errors below.')
    else:
        form = EventDetailsForm()
    
    context = {
        'form': form,
        'step': 1,
        'step_title': 'Event Details'
    }
    
    return render(request, 'dashboard/event_create_step1.html', context)


@login_required
@user_passes_test(is_staff_user)
def event_create_step2(request):
    """Step 2: Room Details (multiple forms based on number_of_rooms)"""
    
    event_id = request.session.get('event_id')
    if not event_id:
        messages.error(request, 'Please start from Step 1.')
        return redirect('dashboard:event_create_step1')
    
    event = get_object_or_404(Event, id=event_id)
    number_of_rooms = request.session.get('number_of_rooms', 1)
    current_room = request.session.get('current_room', 0)
    rooms_data = request.session.get('rooms_data', [])
    
    if request.method == 'POST':
        form = RoomForm(request.POST)
        if form.is_valid():
            # Save room
            room = form.save(commit=False)
            room.event = event
            room.created_by = request.user
            room.save()
            
            # Store room ID
            rooms_data.append(str(room.id))
            request.session['rooms_data'] = rooms_data
            
            # Check if we need more rooms
            if len(rooms_data) < number_of_rooms:
                request.session['current_room'] = len(rooms_data)
                messages.success(request, f'Room "{room.name}" added! ({len(rooms_data)}/{number_of_rooms})')
                return redirect('dashboard:event_create_step2')
            else:
                # All rooms added, move to sessions
                request.session['current_room_for_sessions'] = 0
                messages.success(request, 'All rooms added! Now let\'s add sessions.')
                return redirect('dashboard:event_create_step3')
    else:
        form = RoomForm()
    
    context = {
        'form': form,
        'event': event,
        'step': 2,
        'step_title': f'Room {len(rooms_data) + 1} of {number_of_rooms}',
        'current_room': len(rooms_data) + 1,
        'total_rooms': number_of_rooms,
        'progress': int((len(rooms_data) / number_of_rooms) * 100)
    }
    
    return render(request, 'dashboard/event_create_step2.html', context)


@login_required
@user_passes_test(is_staff_user)
def event_create_step3(request):
    """Step 3: Sessions for each room"""
    
    event_id = request.session.get('event_id')
    rooms_data = request.session.get('rooms_data', [])
    
    if not event_id or not rooms_data:
        messages.error(request, 'Please complete previous steps.')
        return redirect('dashboard:event_create_step1')
    
    event = get_object_or_404(Event, id=event_id)
    current_room_index = request.session.get('current_room_for_sessions', 0)
    
    # Check if we're done with all rooms
    if current_room_index >= len(rooms_data):
        messages.success(request, 'All sessions added! Now let\'s add users.')
        return redirect('dashboard:event_create_step4')
    
    current_room_id = rooms_data[current_room_index]
    current_room = get_object_or_404(Room, id=current_room_id)
    
    # Get existing sessions for this room
    existing_sessions = Session.objects.filter(room=current_room)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add_session':
            form = SessionForm(request.POST)
            if form.is_valid():
                session = form.save(commit=False)
                session.event = event
                session.room = current_room
                session.save()
                messages.success(request, f'Session "{session.title}" added to {current_room.name}!')
                return redirect('dashboard:event_create_step3')
        
        elif action == 'next_room':
            # Move to next room or finish
            request.session['current_room_for_sessions'] = current_room_index + 1
            
            if current_room_index + 1 >= len(rooms_data):
                messages.success(request, 'All sessions configured!')
                return redirect('dashboard:event_create_step4')
            else:
                messages.info(request, f'Moving to next room...')
                return redirect('dashboard:event_create_step3')
        
        elif action == 'skip_room':
            # Skip this room
            request.session['current_room_for_sessions'] = current_room_index + 1
            messages.info(request, f'Skipped sessions for {current_room.name}')
            return redirect('dashboard:event_create_step3')
    
    form = SessionForm(initial={'start_time': event.start_date, 'end_time': event.start_date})
    
    context = {
        'form': form,
        'event': event,
        'current_room': current_room,
        'existing_sessions': existing_sessions,
        'room_number': current_room_index + 1,
        'total_rooms': len(rooms_data),
        'step': 3,
        'step_title': f'Sessions for {current_room.name}',
        'progress': int(((current_room_index + 1) / len(rooms_data)) * 100)
    }
    
    return render(request, 'dashboard/event_create_step3.html', context)


@login_required
@user_passes_test(is_staff_user)
def event_create_step4(request):
    """Step 4: Add users and assign roles"""
    
    event_id = request.session.get('event_id')
    if not event_id:
        messages.error(request, 'Please complete previous steps.')
        return redirect('dashboard:event_create_step1')
    
    event = get_object_or_404(Event, id=event_id)
    
    # Get existing users for this event
    existing_users = UserEventAssignment.objects.filter(
        event=event
    ).select_related('user')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add_user':
            form = UserCreationForm(request.POST)
            if form.is_valid():
                # Create user
                user = form.save()
                
                # Get QR code
                qr_data = UserProfile.get_qr_for_user(user)
                
                # Assign to event
                role = form.cleaned_data['role']
                UserEventAssignment.objects.create(
                    user=user,
                    event=event,
                    role=role,
                    is_active=True,
                    assigned_by=request.user
                )
                
                # Create participant profile
                Participant.objects.create(
                    user=user,
                    event=event,
                    badge_id=qr_data['badge_id'],
                    qr_code_data=qr_data
                )
                
                messages.success(request, f'User "{user.get_full_name()}" created with role: {role}')
                return redirect('dashboard:event_create_step4')
        
        elif action == 'finish':
            # Clear session data
            request.session.pop('event_id', None)
            request.session.pop('number_of_rooms', None)
            request.session.pop('current_room', None)
            request.session.pop('rooms_data', None)
            request.session.pop('current_room_for_sessions', None)
            
            messages.success(request, f'Event "{event.name}" created successfully! 🎉')
            return redirect('dashboard:event_detail', event_id=event.id)
        
        elif action == 'skip':
            # Skip user creation
            request.session.pop('event_id', None)
            request.session.pop('number_of_rooms', None)
            request.session.pop('current_room', None)
            request.session.pop('rooms_data', None)
            request.session.pop('current_room_for_sessions', None)
            
            messages.info(request, 'Event created! You can add users later.')
            return redirect('dashboard:event_detail', event_id=event.id)
    else:
        form = UserCreationForm()
    
    context = {
        'form': form,
        'event': event,
        'existing_users': existing_users,
        'step': 4,
        'step_title': 'Add Users & Assign Roles'
    }
    
    return render(request, 'dashboard/event_create_step4.html', context)


# ==================== User Management ====================

@login_required
@user_passes_test(is_staff_user)
def user_list(request):
    """List all users"""
    
    users = User.objects.all().prefetch_related('userassignments', 'profile')
    
    context = {
        'users': users
    }
    
    return render(request, 'dashboard/user_list.html', context)


@login_required
@user_passes_test(is_staff_user)
def user_create(request):
    """Quick user creation"""
    
    if request.method == 'POST':
        form = QuickUserForm(request.POST)
        if form.is_valid():
            # Create user
            email = form.cleaned_data['email']
            username = email.split('@')[0]
            
            user = User.objects.create_user(
                username=username,
                email=email,
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
                password=form.cleaned_data['password']
            )
            
            # Get QR code
            qr_data = UserProfile.get_qr_for_user(user)
            
            # Assign to event
            event = form.cleaned_data['event']
            role = form.cleaned_data['role']
            
            UserEventAssignment.objects.create(
                user=user,
                event=event,
                role=role,
                is_active=True,
                assigned_by=request.user
            )
            
            # Create participant profile
            Participant.objects.create(
                user=user,
                event=event,
                badge_id=qr_data['badge_id'],
                qr_code_data=qr_data
            )
            
            messages.success(request, f'User "{user.get_full_name()}" created successfully!')
            return redirect('dashboard:user_detail', user_id=user.id)
    else:
        form = QuickUserForm()
    
    context = {
        'form': form
    }
    
    return render(request, 'dashboard/user_create.html', context)


@login_required
@user_passes_test(is_staff_user)
def user_detail(request, user_id):
    """User detail with QR code"""
    
    user = get_object_or_404(User, id=user_id)
    
    # Get QR code
    qr_data = UserProfile.get_qr_for_user(user)
    
    # Generate QR code image
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(json.dumps(qr_data))
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    qr_image = base64.b64encode(buffer.getvalue()).decode()
    
    # Get user's event assignments
    assignments = UserEventAssignment.objects.filter(
        user=user
    ).select_related('event')
    
    # Get participant profiles
    participant_profiles = Participant.objects.filter(
        user=user
    ).select_related('event')
    
    context = {
        'user': user,
        'qr_data': qr_data,
        'qr_image': qr_image,
        'assignments': assignments,
        'participant_profiles': participant_profiles
    }
    
    return render(request, 'dashboard/user_detail.html', context)


@login_required
@user_passes_test(is_staff_user)
def download_qr_code(request, user_id):
    """Download QR code as PNG"""
    
    user = get_object_or_404(User, id=user_id)
    qr_data = UserProfile.get_qr_for_user(user)
    
    # Generate QR code
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(json.dumps(qr_data))
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    response = HttpResponse(buffer.getvalue(), content_type='image/png')
    response['Content-Disposition'] = f'attachment; filename="{user.username}_qr_code.png"'
    
    return response


# ==================== Event Management ====================

@login_required
@user_passes_test(is_staff_user)
@login_required
@user_passes_test(is_staff_user)
def event_edit(request, event_id):
    """Edit event details"""
    
    event = get_object_or_404(Event, id=event_id)
    
    if request.method == 'POST':
        # Don't include number_of_rooms in edit form
        form = EventDetailsForm(request.POST, instance=event)
        if form.is_valid():
            form.save()
            messages.success(request, f'Event "{event.name}" updated successfully!')
            return redirect('dashboard:event_detail', event_id=event.id)
    else:
        form = EventDetailsForm(instance=event)
    
    context = {
        'form': form,
        'event': event,
        'is_edit': True
    }
    
    return render(request, 'dashboard/event_edit.html', context)


@login_required
@user_passes_test(is_staff_user)
def event_delete(request, event_id):
    """Delete event (POST only, called from modal)"""
    
    event = get_object_or_404(Event, id=event_id)
    
    if request.method == 'POST':
        event_name = event.name
        event.delete()
        messages.success(request, f'Event "{event_name}" deleted successfully!')
        return redirect('dashboard:home')
    
    # If accessed via GET (shouldn't happen with modal), redirect to event detail
    messages.warning(request, 'Invalid request. Use the delete button to delete an event.')
    return redirect('dashboard:event_detail', event_id=event.id)


# ==================== Caisse Management Views ====================

@login_required
@user_passes_test(is_staff_user)
def caisse_list(request):
    """List all caisses"""
    from caisse.models import Caisse
    
    event_id = request.GET.get('event')
    caisses = Caisse.objects.select_related('event').all()
    
    if event_id:
        caisses = caisses.filter(event_id=event_id)
    
    # Get statistics for each caisse
    caisse_stats = []
    for caisse in caisses:
        caisse_stats.append({
            'caisse': caisse,
            'total_amount': caisse.get_total_amount(),
            'total_participants': caisse.get_total_participants(),
            'transaction_count': caisse.get_transaction_count()
        })
    
    events = Event.objects.all().order_by('-start_date')
    
    context = {
        'caisse_stats': caisse_stats,
        'events': events,
        'selected_event': event_id
    }
    
    return render(request, 'dashboard/caisse_list.html', context)


@login_required
@user_passes_test(is_staff_user)
def caisse_create(request):
    """Create new caisse"""
    from .forms import CaisseForm
    
    # Get event from query parameter
    event_id = request.GET.get('event')
    initial_data = {}
    redirect_url = 'dashboard:caisse_list'
    
    if event_id:
        try:
            event = Event.objects.get(id=event_id)
            initial_data['event'] = event
            redirect_url = f'dashboard:event_detail'
            redirect_event_id = event_id
        except Event.DoesNotExist:
            pass
    
    if request.method == 'POST':
        form = CaisseForm(request.POST)
        if form.is_valid():
            caisse = form.save()
            messages.success(request, f'Caisse "{caisse.name}" created successfully!')
            if event_id:
                return redirect('dashboard:event_detail', event_id=event_id)
            return redirect('dashboard:caisse_list')
    else:
        form = CaisseForm(initial=initial_data)
    
    context = {
        'form': form,
        'is_edit': False,
        'event_id': event_id
    }
    
    return render(request, 'dashboard/caisse_form.html', context)


@login_required
@user_passes_test(is_staff_user)
def caisse_edit(request, caisse_id):
    """Edit caisse"""
    from caisse.models import Caisse
    from .forms import CaisseForm
    
    caisse = get_object_or_404(Caisse, id=caisse_id)
    
    if request.method == 'POST':
        form = CaisseForm(request.POST, instance=caisse)
        if form.is_valid():
            form.save()
            messages.success(request, f'Caisse "{caisse.name}" updated successfully!')
            return redirect('dashboard:caisse_list')
    else:
        form = CaisseForm(instance=caisse)
    
    context = {
        'form': form,
        'caisse': caisse,
        'is_edit': True
    }
    
    return render(request, 'dashboard/caisse_form.html', context)


@login_required
@user_passes_test(is_staff_user)
def caisse_delete(request, caisse_id):
    """Delete caisse"""
    from caisse.models import Caisse
    
    caisse = get_object_or_404(Caisse, id=caisse_id)
    
    if request.method == 'POST':
        caisse_name = caisse.name
        caisse.delete()
        messages.success(request, f'Caisse "{caisse_name}" deleted successfully!')
        return redirect('dashboard:caisse_list')
    
    messages.warning(request, 'Invalid request.')
    return redirect('dashboard:caisse_list')


@login_required
@user_passes_test(is_staff_user)
def caisse_detail(request, caisse_id):
    """View caisse details and statistics"""
    from caisse.models import Caisse, CaisseTransaction
    
    caisse = get_object_or_404(Caisse.objects.select_related('event'), id=caisse_id)
    
    # Get transactions
    transactions = CaisseTransaction.objects.filter(
        caisse=caisse
    ).select_related('participant__user').prefetch_related('items').order_by('-created_at')[:50]
    
    # Statistics
    total_amount = caisse.get_total_amount()
    total_participants = caisse.get_total_participants()
    transaction_count = caisse.get_transaction_count()
    cancelled_count = caisse.transactions.filter(status='cancelled').count()
    
    context = {
        'caisse': caisse,
        'transactions': transactions,
        'total_amount': total_amount,
        'total_participants': total_participants,
        'transaction_count': transaction_count,
        'cancelled_count': cancelled_count
    }
    
    return render(request, 'dashboard/caisse_detail.html', context)


@login_required
@user_passes_test(is_staff_user)
def payable_items_list(request, event_id):
    """List payable items for an event"""
    from caisse.models import PayableItem
    
    event = get_object_or_404(Event, id=event_id)
    items = PayableItem.objects.filter(event=event).select_related('session').order_by('item_type', 'name')
    
    context = {
        'event': event,
        'items': items
    }
    
    return render(request, 'dashboard/payable_items_list.html', context)


@login_required
@user_passes_test(is_staff_user)
def payable_item_create(request, event_id):
    """Create new payable item"""
    from .forms import PayableItemForm
    
    event = get_object_or_404(Event, id=event_id)
    
    if request.method == 'POST':
        form = PayableItemForm(request.POST, event=event)
        if form.is_valid():
            item = form.save()
            messages.success(request, f'Item "{item.name}" created successfully!')
            return redirect('dashboard:payable_items_list', event_id=event.id)
    else:
        form = PayableItemForm(initial={'event': event}, event=event)
    
    context = {
        'form': form,
        'event': event,
        'is_edit': False
    }
    
    return render(request, 'dashboard/payable_item_form.html', context)


@login_required
@user_passes_test(is_staff_user)
def payable_item_edit(request, item_id):
    """Edit payable item"""
    from caisse.models import PayableItem
    from .forms import PayableItemForm
    
    item = get_object_or_404(PayableItem, id=item_id)
    
    if request.method == 'POST':
        form = PayableItemForm(request.POST, instance=item, event=item.event)
        if form.is_valid():
            form.save()
            messages.success(request, f'Item "{item.name}" updated successfully!')
            return redirect('dashboard:payable_items_list', event_id=item.event.id)
    else:
        form = PayableItemForm(instance=item, event=item.event)
    
    context = {
        'form': form,
        'item': item,
        'event': item.event,
        'is_edit': True
    }
    
    return render(request, 'dashboard/payable_item_form.html', context)


@login_required
@user_passes_test(is_staff_user)
def payable_item_delete(request, item_id):
    """Delete payable item"""
    from caisse.models import PayableItem
    
    item = get_object_or_404(PayableItem, id=item_id)
    event_id = item.event.id
    
    if request.method == 'POST':
        item_name = item.name
        item.delete()
        messages.success(request, f'Item "{item_name}" deleted successfully!')
        return redirect('dashboard:payable_items_list', event_id=event_id)
    
    messages.warning(request, 'Invalid request.')
    return redirect('dashboard:payable_items_list', event_id=event_id)


# Room CRUD Views
@login_required
@user_passes_test(is_staff_user)
def room_create(request, event_id):
    """Create a new room for an event"""
    event = get_object_or_404(Event, id=event_id)
    
    if request.method == 'POST':
        form = RoomForm(request.POST)
        if form.is_valid():
            room = form.save(commit=False)
            room.event = event
            room.save()
            invalidate_event_cache(event.id)
            messages.success(request, f'Room "{room.name}" created successfully!')
            return redirect('dashboard:event_detail', event_id=event.id)
    else:
        form = RoomForm()
    
    context = {
        'form': form,
        'event': event,
        'is_edit': False,
    }
    return render(request, 'dashboard/room_edit.html', context)


@login_required
@user_passes_test(is_staff_user)
def room_edit(request, room_id):
    """Edit an existing room"""
    room = get_object_or_404(Room, id=room_id)
    event = room.event
    
    if request.method == 'POST':
        form = RoomForm(request.POST, instance=room)
        if form.is_valid():
            form.save()
            invalidate_event_cache(event.id)
            messages.success(request, f'Room "{room.name}" updated successfully!')
            return redirect('dashboard:event_detail', event_id=event.id)
    else:
        form = RoomForm(instance=room)
    
    context = {
        'form': form,
        'event': event,
        'room': room,
        'is_edit': True,
    }
    return render(request, 'dashboard/room_edit.html', context)


@login_required
@user_passes_test(is_staff_user)
def room_delete(request, room_id):
    """Delete a room"""
    try:
        room = Room.objects.get(id=room_id)
    except Room.DoesNotExist:
        messages.error(request, 'Room not found or already deleted.')
        # Try to redirect back, or go to dashboard home
        referer = request.META.get('HTTP_REFERER')
        if referer and '/events/' in referer:
            # Extract event_id from referer if possible
            import re
            match = re.search(r'/events/([0-9a-f-]+)/', referer)
            if match:
                return redirect('dashboard:event_detail', event_id=match.group(1))
        return redirect('dashboard:home')
    
    event_id = room.event.id
    
    if request.method == 'POST':
        room_name = room.name
        room.delete()
        invalidate_event_cache(event_id)
        messages.success(request, f'Room "{room_name}" deleted successfully!')
        return redirect('dashboard:event_detail', event_id=event_id)
    
    messages.warning(request, 'Invalid request.')
    return redirect('dashboard:event_detail', event_id=event_id)


# Session CRUD Views
@login_required
@user_passes_test(is_staff_user)
def session_create(request, event_id):
    """Create a new session for an event"""
    event = get_object_or_404(Event, id=event_id)
    
    if request.method == 'POST':
        form = SessionForm(request.POST, event=event)
        if form.is_valid():
            session = form.save(commit=False)
            session.event = event
            session.save()
            invalidate_event_cache(event.id)
            messages.success(request, f'Session "{session.title}" created successfully!')
            return redirect('dashboard:event_detail', event_id=event.id)
    else:
        form = SessionForm(event=event)
    
    context = {
        'form': form,
        'event': event,
        'is_edit': False,
    }
    return render(request, 'dashboard/session_edit.html', context)


@login_required
@user_passes_test(is_staff_user)
def session_edit(request, session_id):
    """Edit an existing session"""
    session = get_object_or_404(Session, id=session_id)
    event = session.event
    
    if request.method == 'POST':
        form = SessionForm(request.POST, instance=session, event=event)
        if form.is_valid():
            form.save()
            invalidate_event_cache(event.id)
            messages.success(request, f'Session "{session.title}" updated successfully!')
            return redirect('dashboard:event_detail', event_id=event.id)
    else:
        form = SessionForm(instance=session, event=event)
    
    context = {
        'form': form,
        'event': event,
        'session': session,
        'is_edit': True,
    }
    return render(request, 'dashboard/session_edit.html', context)


@login_required
@user_passes_test(is_staff_user)
def session_delete(request, session_id):
    """Delete a session"""
    try:
        session = Session.objects.get(id=session_id)
    except Session.DoesNotExist:
        messages.error(request, 'Session not found or already deleted.')
        # Try to redirect back
        referer = request.META.get('HTTP_REFERER')
        if referer and '/events/' in referer:
            import re
            match = re.search(r'/events/([0-9a-f-]+)/', referer)
            if match:
                return redirect('dashboard:event_detail', event_id=match.group(1))
        return redirect('dashboard:home')
    
    event_id = session.event.id
    
    if request.method == 'POST':
        session_title = session.title
        session.delete()
        invalidate_event_cache(event_id)
        messages.success(request, f'Session "{session_title}" deleted successfully!')
        return redirect('dashboard:event_detail', event_id=event_id)
    
    messages.warning(request, 'Invalid request.')
    return redirect('dashboard:event_detail', event_id=event_id)
