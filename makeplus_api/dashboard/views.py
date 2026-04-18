"""
Views for MakePlus Dashboard - OPTIMIZED
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.db.models import Count, Q, Sum, Prefetch
from django.db import models
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.contrib.auth.models import User
from django.core.cache import cache
from django.views.decorators.cache import cache_page, never_cache
from datetime import timedelta
import json
import qrcode
import io
import base64

# Cache invalidation helper
def invalidate_event_cache(event_id):
    """Invalidate all caches related to an event by incrementing version"""
    from django.core.cache import cache
    
    # Get current versions before incrementing
    event_version_key = f'event_version_{event_id}'
    current_event_version = cache.get(event_version_key, 0)
    
    dashboard_version_key = 'dashboard_version'
    current_dashboard_version = cache.get(dashboard_version_key, 0)
    
    # Delete old cache entries explicitly (current version)
    old_event_cache_key = f'event_detail_{event_id}_v{current_event_version}'
    old_dashboard_cache_key = f'dashboard_home_v{current_dashboard_version}'
    cache.delete(old_event_cache_key)
    cache.delete(old_dashboard_cache_key)
    
    # Also delete potential future versions (in case of race conditions)
    # Delete up to 5 versions ahead to be safe
    for i in range(5):
        cache.delete(f'event_detail_{event_id}_v{current_event_version + i}')
        cache.delete(f'dashboard_home_v{current_dashboard_version + i}')
    
    # Increment the version numbers
    cache.set(event_version_key, current_event_version + 1, None)  # Never expires
    cache.set(dashboard_version_key, current_dashboard_version + 1, None)


def clear_all_caches():
    """Clear ALL caches - nuclear option for when edits are made"""
    from django.core.cache import cache
    cache.clear()
    print("DEBUG: ALL CACHES CLEARED")


def get_event_cache_version(event_id):
    """Get current cache version for an event"""
    from django.core.cache import cache
    version_key = f'event_version_{event_id}'
    return cache.get(version_key, 0)


def get_dashboard_cache_version():
    """Get current cache version for dashboard"""
    from django.core.cache import cache
    return cache.get('dashboard_version', 0)

from events.models import (
    Event, Room, Session, UserEventAssignment, Participant,
    SessionAccess, RoomAccess, ExposantScan, UserProfile,
    SessionQuestion, Annonce
)
from .forms import (
    EventDetailsForm, EventEditForm, RoomForm, SessionForm,
    UserCreationForm, QuickUserForm, RoomAssignmentForm
)
from .models_eposter import EPosterCommitteeMember


def is_staff_user(user):
    """Check if user is staff or committee member"""
    if user.is_staff or user.is_superuser:
        return True
    # Check if user is a committee member for any event
    return EPosterCommitteeMember.objects.filter(user=user, is_active=True).exists()


def is_committee_member(user):
    """Check if user is a committee member for any event"""
    return EPosterCommitteeMember.objects.filter(user=user, is_active=True).exists()


# ==================== Authentication Views ====================

def login_view(request):
    """Login page for dashboard"""
    if request.user.is_authenticated:
        return redirect('dashboard:home')
    
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        # DEBUG: Print what we received
        print(f"DEBUG Login attempt:")
        print(f"  Email received: '{email}' (length: {len(email) if email else 0})")
        print(f"  Password received: '{password}' (length: {len(password) if password else 0})")
        
        # Find user by email
        try:
            user_obj = User.objects.get(email=email)
            username = user_obj.username
            print(f"  Found user: {username}")
        except User.DoesNotExist:
            print(f"  User with email {email} not found")
            messages.error(request, 'Invalid email or password.')
            return render(request, 'dashboard/login.html')
        
        # Authenticate with username
        user = authenticate(request, username=username, password=password)
        
        print(f"  authenticate() returned: {user}")
        
        if user is not None:
            print(f"  User is_staff: {user.is_staff}, is_superuser: {user.is_superuser}")
            # Allow staff, superusers, and committee members
            is_committee = EPosterCommitteeMember.objects.filter(user=user, is_active=True).exists()
            if user.is_staff or user.is_superuser or is_committee:
                login(request, user)
                welcome_msg = f'Welcome back, {user.get_full_name() or user.email}!'
                if is_committee and not user.is_staff:
                    welcome_msg += ' (Committee Member)'
                messages.success(request, welcome_msg)
                
                # Redirect committee members directly to ePoster management
                if is_committee and not user.is_staff:
                    return redirect('dashboard:eposter_management_home')
                return redirect('dashboard:home')
            else:
                messages.error(request, 'You do not have permission to access the dashboard.')
        else:
            print(f"  Authentication FAILED")
            messages.error(request, 'Invalid email or password.')
    
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
    from django.core.cache import cache
    
    # Committee members should be redirected to their events page
    if not request.user.is_staff and not request.user.is_superuser:
        # Check if user is a committee member
        if EPosterCommitteeMember.objects.filter(user=request.user, is_active=True).exists():
            return redirect('dashboard:eposter_management_home')
    
    # Get cache version
    cache_version = get_dashboard_cache_version()
    cache_key = f'dashboard_home_v{cache_version}'
    
    # Try to get from cache
    cached_data = cache.get(cache_key)
    if cached_data:
        context = cached_data
    else:
        # Get recent events only (limit to 20 for performance)
        # Use prefetch to get counts efficiently
        events = list(Event.objects.select_related('created_by').prefetch_related(
            'registered_participants', 'rooms', 'sessions'
        ).order_by('-start_date')[:20])
        
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
        
        # Cache for 5 minutes
        cache.set(cache_key, context, 300)
    
    response = render(request, 'dashboard/home.html', context)
    
    # Allow browser to cache for 30 seconds
    response['Cache-Control'] = 'private, max-age=30'
    
    return response


# ==================== Event Detail View ====================

@login_required
@user_passes_test(is_staff_user)
def event_detail(request, event_id):
    """Comprehensive event detail view with all statistics - NO CACHING"""
    from django.core.cache import cache
    from django.db.models import Count, Sum, Q, Prefetch
    
    # NO CACHING - Always fetch fresh data
    event = get_object_or_404(Event.objects.select_related('created_by'), id=event_id)
    
    # Get event rooms (only fetch needed fields)
    rooms = list(Room.objects.filter(event=event).only(
        'id', 'name', 'capacity', 'location', 'description', 'current_participants'
    ))
    
    # Get event sessions (prefetch room to avoid N+1)
    sessions = list(Session.objects.filter(event=event).select_related('room').only(
        'id', 'title', 'session_type', 'start_time', 'end_time', 'speaker_name', 
        'speaker_title', 'is_paid', 'price', 'youtube_live_url', 'room__name', 'room__id'
    ))
    
    # Get unique session dates for filtering
    session_dates = list(Session.objects.filter(event=event).dates('start_time', 'day'))
    
    # Get all user assignments in ONE query with prefetch (includes profile for badge ID)
    all_assignments = list(UserEventAssignment.objects.filter(
        event=event,
        is_active=True
    ).select_related('user__profile', 'assigned_by').prefetch_related('user__participations'))
    
    # Separate by role in Python (faster than 4 separate queries)
    organisateurs = [a for a in all_assignments if a.role == 'organisateur']
    gestionnaires = [a for a in all_assignments if a.role == 'gestionnaire_des_salles']
    controleurs = [a for a in all_assignments if a.role == 'controlleur_des_badges']
    exposants = [a for a in all_assignments if a.role == 'exposant']
    
    # Get filter parameter for user list
    role_filter = request.GET.get('role', 'all')
    
    # Filter assignments for user list display
    if role_filter != 'all':
        filtered_assignments = [a for a in all_assignments if a.role == role_filter]
    else:
        filtered_assignments = list(all_assignments)
    
    # Get role counts
    role_counts = {
        'all': len(all_assignments),
        'organisateur': len(organisateurs),
        'gestionnaire_des_salles': len(gestionnaires),
        'controlleur_des_badges': len(controleurs),
        'exposant': len(exposants),
        'participant': len([a for a in all_assignments if a.role == 'participant']),
    }
    
    # Use aggregate for statistics (single query instead of multiple counts)
    # Count participants registered for this event via ParticipantEventRegistration
    from .models import ParticipantEventRegistration
    participant_stats = ParticipantEventRegistration.objects.filter(event=event).aggregate(
        total=Count('id'),
        checked_in=Count('id', filter=Q(is_checked_in=True))
    )
    
    session_stats = Session.objects.filter(event=event).aggregate(
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
    # Get all participants registered for this event
    participant_registrations = ParticipantEventRegistration.objects.filter(
        event=event
    ).select_related('participant__user')
    participants = [reg.participant for reg in participant_registrations]
    
    # Room access statistics (optimized)
    room_accesses = RoomAccess.objects.filter(room__event=event).count() if RoomAccess.objects.filter(room__event=event).exists() else 0
    
    # Exposant scans (optimized) - count scans for this event
    exposant_scans = ExposantScan.objects.filter(event=event).count()
    
    # Session questions (use aggregate with correct field name)
    question_stats = SessionQuestion.objects.filter(session__event=event).aggregate(
        total=Count('id'),
        answered=Count('id', filter=Q(is_answered=True))
    )
    total_questions = question_stats['total'] or 0
    answered_questions = question_stats['answered'] or 0
    
    # Get caisses with aggregated stats (MUCH faster than calling methods)
    from caisse.models import Caisse, CaisseTransaction, PayableItem
    caisses = list(Caisse.objects.filter(event=event).select_related('event'))
    
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
    
    # Get payable items for this event
    payable_items = PayableItem.objects.filter(
        event=event
    ).select_related('session').order_by('item_type', 'name')
    
    context = {
        'event': event,
        'rooms': rooms,
        'sessions': sessions,
        'session_dates': session_dates,
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
        'payable_items': payable_items,
        # User list data
        'event_users': filtered_assignments,
        'role_filter': role_filter,
        'role_counts': role_counts,
    }
    
    # NO CACHING - removed cache.set()
    
    response = render(request, 'dashboard/event_detail.html', context)
    
    # Prevent browser caching to ensure fresh data after edits
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    
    return response


# ==================== Multi-Step Event Creation ====================

@login_required
@user_passes_test(is_staff_user)
def event_create_step1(request):
    """Step 1: Event Details"""
    
    if request.method == 'POST':
        form = EventDetailsForm(request.POST, request.FILES)
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
            form = SessionForm(request.POST, event=event)
            # Make room and status fields not required since we set them manually
            form.fields['room'].required = False
            form.fields['status'].required = False
            if form.is_valid():
                session = form.save(commit=False)
                session.event = event
                session.room = current_room  # Force the current room
                session.status = 'pas_encore'  # Set default status
                session.created_by = request.user
                session.save()
                messages.success(request, f'Session "{session.title}" added to {current_room.name}!')
                return redirect('dashboard:event_create_step3')
            else:
                # Show form errors
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f'{field}: {error}')
        
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
    
    form = SessionForm(initial={'start_time': event.start_date, 'end_time': event.start_date}, event=event)
    # Hide/disable fields that are not in the template or set automatically
    form.fields['room'].widget = form.fields['room'].hidden_widget()
    form.fields['room'].required = False
    form.fields['status'].widget = form.fields['status'].hidden_widget()
    form.fields['status'].required = False
    # Make optional fields truly optional
    form.fields['speaker_bio'].required = False
    form.fields['speaker_photo_url'].required = False
    form.fields['cover_image_url'].required = False
    
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
    
    form = None  # Initialize form variable
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add_user':
            form = UserCreationForm(request.POST, event=event)
            if form.is_valid():
                # Create user
                user = form.save()
                
                # Get QR code
                qr_data = UserProfile.get_qr_for_user(user)
                
                # Assign to event
                role = form.cleaned_data['role']
                assignment = UserEventAssignment.objects.create(
                    user=user,
                    event=event,
                    role=role,
                    is_active=True,
                    assigned_by=request.user
                )
                
                # If role is committee, create EPosterCommitteeMember record
                if role == 'committee':
                    from .models_eposter import EPosterCommitteeMember
                    EPosterCommitteeMember.objects.create(
                        event=event,
                        user=user,
                        role='member',  # Default to 'member', can be changed later
                        is_active=True,
                        assigned_by=request.user
                    )
                    messages.success(request, f'Committee member "{user.get_full_name()}" created successfully!')
                
                # Assign room if role is gestionnaire_des_salles
                assigned_room = form.cleaned_data.get('assigned_room')
                if role == 'gestionnaire_des_salles' and assigned_room:
                    assignment.metadata = assignment.metadata or {}
                    assignment.metadata['assigned_room_id'] = str(assigned_room.id)
                    assignment.save()
                    messages.success(request, f'User "{user.get_full_name()}" created with role: {role} and assigned to room: {assigned_room.name}')
                else:
                    messages.success(request, f'User "{user.get_full_name()}" created with role: {role}')
                
                # Create participant profile
                Participant.objects.create(
                    user=user,
                    event=event,
                    badge_id=qr_data['badge_id'],
                    qr_code_data=qr_data
                )
                
                # Invalidate cache for this event
                invalidate_event_cache(event.id)
                
                return redirect('dashboard:event_create_step4')
            else:
                # Display form errors
                for field, errors in form.errors.items():
                    for error in errors:
                        if field == '__all__':
                            messages.error(request, f'{error}')
                        else:
                            messages.error(request, f'{field}: {error}')
                # Keep the form with errors to display
        
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
    
    # Create form for GET requests or if POST with errors
    if not form:
        form = UserCreationForm(event=event)
    
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
    """List all users with role and event filtering"""
    
    # Get filter parameters
    role_filter = request.GET.get('role', 'all')
    event_filter = request.GET.get('event', 'all')
    search_query = request.GET.get('search', '').strip()
    
    # Base query with optimizations
    users = User.objects.prefetch_related(
        'event_assignments__event',
        'profile',
        'participant_profile__events'  # Updated for new structure
    ).order_by('-date_joined')
    
    # Filter by role if specified
    if role_filter != 'all':
        users = users.filter(event_assignments__role=role_filter).distinct()
    
    # Filter by event if specified
    if event_filter != 'all':
        users = users.filter(event_assignments__event__id=event_filter).distinct()
    
    # Filter by search query
    if search_query:
        users = users.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query)
        )
    
    # Get counts for each role
    role_counts = {
        'all': User.objects.count(),
        'organisateur': UserEventAssignment.objects.filter(role='organisateur').values('user').distinct().count(),
        'gestionnaire_des_salles': UserEventAssignment.objects.filter(role='gestionnaire_des_salles').values('user').distinct().count(),
        'controlleur_des_badges': UserEventAssignment.objects.filter(role='controlleur_des_badges').values('user').distinct().count(),
        'exposant': UserEventAssignment.objects.filter(role='exposant').values('user').distinct().count(),
        'participant': UserEventAssignment.objects.filter(role='participant').values('user').distinct().count(),
    }
    
    # Get all events for filter dropdown
    events = Event.objects.all().order_by('-start_date')
    
    context = {
        'users': users,
        'role_filter': role_filter,
        'event_filter': event_filter,
        'search_query': search_query,
        'role_counts': role_counts,
        'events': events
    }
    
    return render(request, 'dashboard/user_list.html', context)


@login_required
@login_required
@user_passes_test(is_staff_user)
def user_create(request):
    """Quick user creation - behaves differently based on context"""
    from .models_eposter import EPosterCommitteeMember
    
    # Get event from query parameter (optional)
    event_id = request.GET.get('event')
    event = None
    from_event_page = False
    
    if event_id:
        event = get_object_or_404(Event, id=event_id)
        from_event_page = True
    
    # Get existing users for this event (only if accessed from event page)
    existing_users = []
    if from_event_page and event:
        existing_users = UserEventAssignment.objects.filter(
            event=event
        ).select_related('user')
    
    form = None
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'done':
            # Redirect back to event detail (only from event page)
            if event:
                return redirect('dashboard:event_detail', event_id=event.id)
            else:
                return redirect('dashboard:user_list')
        
        elif action == 'add_user':
            form = UserCreationForm(request.POST, event=event)
            if form.is_valid():
                # Create user
                user = form.save()
                
                # Get QR code
                qr_data = UserProfile.get_qr_for_user(user)
                
                # Get event (from form if not from event page)
                if not event:
                    event = form.cleaned_data.get('event')
                
                # Assign to event
                role = form.cleaned_data['role']
                assignment = UserEventAssignment.objects.create(
                    user=user,
                    event=event,
                    role=role,
                    is_active=True,
                    assigned_by=request.user
                )
                
                # If role is committee, create EPosterCommitteeMember record
                if role == 'committee':
                    EPosterCommitteeMember.objects.create(
                        event=event,
                        user=user,
                        role='member',  # Default to 'member', can be changed later
                        is_active=True,
                        assigned_by=request.user
                    )
                    messages.success(request, f'Committee member "{user.get_full_name()}" created successfully!')
                
                # Assign room if role is gestionnaire_des_salles
                assigned_room = form.cleaned_data.get('assigned_room')
                if role == 'gestionnaire_des_salles' and assigned_room:
                    assignment.metadata = assignment.metadata or {}
                    assignment.metadata['assigned_room_id'] = str(assigned_room.id)
                    assignment.save()
                    messages.success(request, f'User "{user.get_full_name()}" created with role: {role} and assigned to room: {assigned_room.name}')
                else:
                    messages.success(request, f'User "{user.get_full_name()}" created with role: {role}')
                
                # Create participant profile
                Participant.objects.create(
                    user=user,
                    event=event,
                    badge_id=qr_data['badge_id'],
                    qr_code_data=qr_data
                )
                
                # Invalidate cache for this event
                invalidate_event_cache(event.id)
                
                # Redirect based on context
                if from_event_page:
                    # Stay on same page to add more users
                    return redirect(f"{reverse('dashboard:user_create')}?event={event.id}")
                else:
                    # Go to user list
                    return redirect('dashboard:user_list')
            else:
                # Display form errors
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f'{field}: {error}')
    else:
        form = UserCreationForm(event=event)
    
    context = {
        'form': form,
        'event': event,
        'existing_users': existing_users,
        'from_event_page': from_event_page,
    }
    
    return render(request, 'dashboard/user_create.html', context)


@login_required
@user_passes_test(is_staff_user)
def user_detail(request, user_id):
    """User detail with comprehensive information"""
    from caisse.models import CaisseTransaction
    
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
    
    # Get user's event assignments with role details
    assignments = UserEventAssignment.objects.filter(
        user=user
    ).select_related('event', 'assigned_by').order_by('-assigned_at')
    
    # For each assignment, fetch assigned room if applicable
    assignments_with_rooms = []
    for assignment in assignments:
        assigned_room = None
        # Check if role is one that can have room assignment
        if assignment.role in ['organisateur', 'gestionnaire_des_salles', 'controlleur_des_badges']:
            # Get room ID from metadata
            room_id = assignment.metadata.get('assigned_room_id') if assignment.metadata else None
            if room_id:
                try:
                    assigned_room = Room.objects.get(id=room_id)
                except Room.DoesNotExist:
                    pass
        
        assignments_with_rooms.append({
            'assignment': assignment,
            'assigned_room': assigned_room
        })
    
    # Get participant profiles with detailed information
    participant_profiles = Participant.objects.filter(
        user=user
    ).select_related('event').prefetch_related('allowed_rooms')
    
    # For each participant profile, get their event data
    participant_data = []
    for participant in participant_profiles:
        event = participant.event
        
        # Get paid sessions (ateliers) for this participant in this event
        paid_sessions = Session.objects.filter(
            event=event,
            is_paid=True
        ).values('id', 'title', 'price', 'start_time', 'room__name')
        
        # Get transactions for this participant in this event
        transactions = CaisseTransaction.objects.filter(
            participant=participant
        ).select_related('caisse').order_by('-created_at')
        
        # Calculate total spent
        total_spent = transactions.aggregate(total=models.Sum('total_amount'))['total'] or 0
        
        # Get room access history
        room_accesses = RoomAccess.objects.filter(
            participant=participant
        ).select_related('room', 'session', 'verified_by').order_by('-accessed_at')
        
        # Get scans by exposants
        scans = ExposantScan.objects.filter(
            scanned_participant=participant
        ).select_related('exposant__user', 'event').order_by('-scanned_at')
        
        participant_data.append({
            'participant': participant,
            'event': event,
            'paid_sessions': paid_sessions,
            'transactions': transactions,
            'total_spent': total_spent,
            'room_accesses': room_accesses,
            'scans': scans,
            'transaction_count': transactions.count(),
            'scan_count': scans.count(),
            'room_access_count': room_accesses.count()
        })
    
    # Check if user has participant or committee role
    user_roles = list(assignments.values_list('role', flat=True))
    is_participant = 'participant' in user_roles
    is_committee = 'committee' in user_roles
    
    context = {
        'user': user,
        'qr_data': qr_data,
        'qr_image': qr_image,
        'assignments': assignments,
        'assignments_with_rooms': assignments_with_rooms,
        'participant_data': participant_data,
        'is_participant': is_participant,
        'is_committee': is_committee,
    }
    
    return render(request, 'dashboard/user_detail.html', context)


@login_required
@user_passes_test(is_staff_user)
def user_delete(request, user_id):
    """Delete a user and all their associated data"""
    
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        # Don't allow deleting superusers or current user
        if user.is_superuser:
            messages.error(request, 'Cannot delete superuser accounts.')
            return redirect('dashboard:user_detail', user_id=user.id)
        
        if user == request.user:
            messages.error(request, 'You cannot delete your own account.')
            return redirect('dashboard:user_detail', user_id=user.id)
        
        user_name = user.get_full_name() or user.username
        
        # Delete the user (cascading deletes will handle related objects)
        user.delete()
        
        messages.success(request, f'User "{user_name}" has been permanently deleted.')
        return redirect('dashboard:user_list')
    
    # If GET request, redirect to user detail
    messages.warning(request, 'Invalid request.')
    return redirect('dashboard:user_detail', user_id=user.id)


@login_required
@user_passes_test(is_staff_user)
def user_change_role(request, assignment_id):
    """Change user's role for a specific event"""
    
    assignment = get_object_or_404(UserEventAssignment, id=assignment_id)
    
    if request.method == 'POST':
        new_role = request.POST.get('role')
        
        # Validate role
        valid_roles = ['organisateur', 'gestionnaire_des_salles', 'controlleur_des_badges', 'exposant', 'participant']
        if new_role not in valid_roles:
            messages.error(request, 'Invalid role selected.')
            return redirect('dashboard:user_detail', user_id=assignment.user.id)
        
        old_role = assignment.get_role_display()
        assignment.role = new_role
        assignment.save()
        
        # Invalidate cache
        invalidate_event_cache(assignment.event.id)
        
        new_role_display = assignment.get_role_display()
        messages.success(request, f'User role changed from {old_role} to {new_role_display} for event "{assignment.event.name}".')
        return redirect('dashboard:user_detail', user_id=assignment.user.id)
    
    # If GET request, redirect to user detail
    messages.warning(request, 'Invalid request.')
    return redirect('dashboard:user_detail', user_id=assignment.user.id)


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


@login_required
@user_passes_test(is_staff_user)
def event_users(request, event_id):
    """Manage users for a specific event with role filtering"""
    from caisse.models import CaisseTransaction
    
    event = get_object_or_404(Event, id=event_id)
    
    # Get filter parameter
    role_filter = request.GET.get('role', 'all')
    
    # Get all user assignments for this event
    assignments = UserEventAssignment.objects.filter(
        event=event
    ).select_related('user', 'user__profile', 'assigned_by').order_by('-assigned_at')
    
    # Filter by role if specified
    if role_filter != 'all':
        assignments = assignments.filter(role=role_filter)
    
    # Get counts for each role in this event
    role_counts = {
        'all': UserEventAssignment.objects.filter(event=event).count(),
        'organisateur': UserEventAssignment.objects.filter(event=event, role='organisateur').count(),
        'gestionnaire_des_salles': UserEventAssignment.objects.filter(event=event, role='gestionnaire_des_salles').count(),
        'controlleur_des_badges': UserEventAssignment.objects.filter(event=event, role='controlleur_des_badges').count(),
        'exposant': UserEventAssignment.objects.filter(event=event, role='exposant').count(),
        'participant': UserEventAssignment.objects.filter(event=event, role='participant').count(),
    }
    
    # Get detailed stats for each user
    user_stats = []
    for assignment in assignments:
        user = assignment.user
        
        # Get participant profile if exists
        try:
            participant = Participant.objects.get(user=user)
            # Check if registered for this event
            from events.models import ParticipantEventRegistration
            event_registration = ParticipantEventRegistration.objects.filter(
                participant=participant,
                event=event
            ).first()
        except Participant.DoesNotExist:
            participant = None
            event_registration = None
        
        stats = {
            'assignment': assignment,
            'user': user,
            'participant': participant,
            'is_checked_in': event_registration.is_checked_in if event_registration else False,
            'checked_in_at': event_registration.checked_in_at if event_registration else None,
        }
        
        # If participant, get additional stats
        if participant and event_registration:
            # Total spent
            total_spent = CaisseTransaction.objects.filter(
                participant=participant
            ).aggregate(total=models.Sum('total_amount'))['total'] or 0
            
            # Transaction count
            transaction_count = CaisseTransaction.objects.filter(
                participant=participant
            ).count()
            
            # Room access count
            room_access_count = RoomAccess.objects.filter(
                participant=participant
            ).count()
            
            # Scan count
            scan_count = ExposantScan.objects.filter(
                scanned_participant=participant
            ).count()
            
            stats.update({
                'total_spent': total_spent,
                'transaction_count': transaction_count,
                'room_access_count': room_access_count,
                'scan_count': scan_count,
            })
        
        user_stats.append(stats)
    
    context = {
        'event': event,
        'user_stats': user_stats,
        'role_filter': role_filter,
        'role_counts': role_counts,
    }
    
    return render(request, 'dashboard/event_users.html', context)


@login_required
@user_passes_test(is_staff_user)
def event_user_delete(request, event_id, user_id):
    """Remove user from event (delete UserEventAssignment)"""
    
    event = get_object_or_404(Event, id=event_id)
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        # Get assignment
        assignment = get_object_or_404(UserEventAssignment, event=event, user=user)
        user_name = user.get_full_name() or user.username
        
        # Delete the assignment (this removes user from event)
        assignment.delete()
        
        # Invalidate cache
        invalidate_event_cache(event.id)
        
        messages.success(request, f'User "{user_name}" has been removed from this event.')
        return redirect('dashboard:event_detail', event_id=event.id)
    
    # If GET request, redirect to event detail
    messages.warning(request, 'Invalid request.')
    return redirect('dashboard:event_detail', event_id=event.id)


# ==================== Event Management ====================

@login_required
@user_passes_test(is_staff_user)
def event_edit(request, event_id):
    """Edit event details - COMPLETELY REWRITTEN"""
    from django.db import connection
    import time
    
    # Step 1: Close any existing connections and fetch fresh data
    connection.close()
    
    try:
        event = Event.objects.get(id=event_id)
    except Event.DoesNotExist:
        messages.error(request, 'Event not found.')
        return redirect('dashboard:home')
    
    if request.method == 'POST':
        # Step 2: Process the form
        form = EventEditForm(request.POST, request.FILES, instance=event)
        
        if form.is_valid():
            # Step 3: Save the event
            updated_event = form.save()
            
            # Step 4: CLEAR ALL CACHES (nuclear option)
            clear_all_caches()
            
            # Step 5: Close connection to force fresh queries
            connection.close()
            
            messages.success(request, f'Event "{updated_event.name}" updated successfully!')
            
            # Step 6: Redirect with timestamp to prevent browser cache
            return redirect(f"/dashboard/events/{updated_event.id}/?t={int(time.time())}")
        else:
            # Show form errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        # GET request - load the form
        # Close connection and fetch fresh data
        connection.close()
        event = Event.objects.get(id=event_id)
        
        form = EventEditForm(instance=event)
        
        # Format datetime fields
        if event.start_date:
            form.initial['start_date'] = event.start_date.strftime('%Y-%m-%dT%H:%M')
        if event.end_date:
            form.initial['end_date'] = event.end_date.strftime('%Y-%m-%dT%H:%M')
    
    context = {
        'form': form,
        'event': event,
        'is_edit': True
    }
    
    response = render(request, 'dashboard/event_edit.html', context)
    
    # Prevent ALL caching
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    
    return response


@login_required
@user_passes_test(is_staff_user)
def event_delete(request, event_id):
    """Delete event (POST only, called from modal)"""
    
    event = get_object_or_404(Event, id=event_id)
    
    if request.method == 'POST':
        event_name = event.name
        event.delete()
        # Invalidate cache
        invalidate_event_cache(event_id)
        cache.delete('dashboard_home')
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
    from django.db.models import Sum, Count, Q
    
    caisse = get_object_or_404(Caisse.objects.select_related('event'), id=caisse_id)
    
    # Filter parameters
    status_filter = request.GET.get('status', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    # Get transactions with filters
    transactions = CaisseTransaction.objects.filter(
        caisse=caisse
    ).select_related('participant__user').prefetch_related('items')
    
    # Apply filters
    if status_filter:
        transactions = transactions.filter(status=status_filter)
    if date_from:
        transactions = transactions.filter(created_at__date__gte=date_from)
    if date_to:
        transactions = transactions.filter(created_at__date__lte=date_to)
    
    transactions = transactions.order_by('-created_at')[:100]
    
    # Debug: Print transaction count
    print(f"DEBUG: Fetching transactions for caisse {caisse.id}")
    print(f"DEBUG: Total transactions found: {transactions.count()}")
    if transactions.exists():
        print(f"DEBUG: First transaction: {transactions[0].id} - {transactions[0].created_at}")
    
    # Statistics
    total_amount = caisse.get_total_amount()
    total_participants = caisse.get_total_participants()
    transaction_count = caisse.get_transaction_count()
    
    # Cancelled transactions stats
    cancelled_transactions = caisse.transactions.filter(status='cancelled')
    cancelled_count = cancelled_transactions.count()
    cancelled_amount = cancelled_transactions.aggregate(total=Sum('total_amount'))['total'] or 0
    
    # Get cancelled transactions with reasons
    cancelled_with_reasons = cancelled_transactions.select_related(
        'participant__user'
    ).prefetch_related('items').order_by('-cancelled_at')[:20]
    
    # Revenue by item type
    from caisse.models import PayableItem
    revenue_by_type = {}
    for transaction in caisse.transactions.filter(status='completed'):
        for item in transaction.items.all():
            item_type = item.get_item_type_display()
            if item_type not in revenue_by_type:
                revenue_by_type[item_type] = {'count': 0, 'amount': 0}
            revenue_by_type[item_type]['count'] += 1
            revenue_by_type[item_type]['amount'] += float(item.price)
    
    context = {
        'caisse': caisse,
        'transactions': transactions,
        'total_amount': total_amount,
        'total_participants': total_participants,
        'transaction_count': transaction_count,
        'cancelled_count': cancelled_count,
        'cancelled_amount': cancelled_amount,
        'cancelled_with_reasons': cancelled_with_reasons,
        'revenue_by_type': revenue_by_type,
        'status_filter': status_filter,
        'date_from': date_from,
        'date_to': date_to,
    }
    
    response = render(request, 'dashboard/caisse_detail.html', context)
    # Add cache control headers to prevent caching
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    
    return response


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
            return redirect('dashboard:event_detail', event_id=event.id)
    else:
        form = PayableItemForm(event=event)
    
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
            return redirect('dashboard:event_detail', event_id=item.event.id)
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
        return redirect('dashboard:event_detail', event_id=event_id)
    
    messages.warning(request, 'Invalid request.')
    return redirect('dashboard:event_detail', event_id=event_id)


@login_required
@user_passes_test(is_staff_user)
def sync_paid_sessions_ajax(request, event_id):
    """AJAX endpoint to sync paid sessions to payable items"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST method required'}, status=405)
    
    event = get_object_or_404(Event, id=event_id)
    
    try:
        from caisse.models import PayableItem
        
        # Get all paid sessions for this event
        paid_sessions = Session.objects.filter(
            event=event,
            is_paid=True,
            price__gt=0
        )
        
        created_count = 0
        updated_count = 0
        
        for session in paid_sessions:
            # Check if payable item already exists for this session
            item, created = PayableItem.objects.get_or_create(
                event=event,
                session=session,
                defaults={
                    'name': f"{session.get_session_type_display()} - {session.title}",
                    'description': f"Payment for {session.title}",
                    'price': session.price,
                    'item_type': 'session',
                    'is_active': True
                }
            )
            
            if created:
                created_count += 1
            else:
                # Update existing item
                item.name = f"{session.get_session_type_display()} - {session.title}"
                item.price = session.price
                item.is_active = True
                item.save()
                updated_count += 1
        
        return JsonResponse({
            'success': True,
            'created': created_count,
            'updated': updated_count,
            'total': paid_sessions.count()
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


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
    """Create multiple sessions for an event (similar to step 3 workflow)"""
    event = get_object_or_404(Event, id=event_id)
    
    # Get selected room from query param or session
    room_id_param = request.GET.get('room_id')
    if room_id_param:
        # Store in session when room is selected via GET
        request.session[f'session_create_room_{event_id}'] = room_id_param
    
    selected_room_id = request.session.get(f'session_create_room_{event_id}')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add_session':
            # Add a session to the selected room
            if not selected_room_id:
                messages.error(request, 'Please select a room first.')
                return redirect('dashboard:session_create', event_id=event_id)
            
            form = SessionForm(request.POST, event=event)
            if form.is_valid():
                session = form.save(commit=False)
                session.event = event
                session.room_id = selected_room_id
                session.save()
                invalidate_event_cache(event.id)
                messages.success(request, f'Session "{session.title}" added successfully!')
                # Stay on the same page to add more sessions
                return redirect('dashboard:session_create', event_id=event_id)
            else:
                # Show errors
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f'{field}: {error}')
        
        elif action == 'done':
            # User is done adding sessions
            # Clear the selected room from session
            if f'session_create_room_{event_id}' in request.session:
                del request.session[f'session_create_room_{event_id}']
            
            messages.success(request, 'Sessions added successfully!')
            return redirect('dashboard:event_detail', event_id=event_id)
        
        elif action == 'change_room':
            # User wants to change the room
            if f'session_create_room_{event_id}' in request.session:
                del request.session[f'session_create_room_{event_id}']
            return redirect('dashboard:session_create', event_id=event_id)
    
    # Get all rooms for this event
    rooms = Room.objects.filter(event=event, is_active=True).prefetch_related('sessions').order_by('name')
    
    # Get the selected room and its sessions
    selected_room = None
    existing_sessions = []
    if selected_room_id:
        try:
            selected_room = Room.objects.get(id=selected_room_id, event=event)
            existing_sessions = Session.objects.filter(room=selected_room).order_by('start_time')
        except Room.DoesNotExist:
            # Room doesn't exist, clear selection
            if f'session_create_room_{event_id}' in request.session:
                del request.session[f'session_create_room_{event_id}']
            selected_room_id = None
    
    # Create form
    if selected_room:
        form = SessionForm(event=event, initial={'room': selected_room.id})
    else:
        form = None
    
    context = {
        'event': event,
        'rooms': rooms,
        'selected_room': selected_room,
        'existing_sessions': existing_sessions,
        'form': form,
        'is_edit': False,
    }
    return render(request, 'dashboard/session_create_multi.html', context)


@login_required
@user_passes_test(is_staff_user)
def session_edit(request, session_id):
    """Edit an existing session - COMPLETELY REWRITTEN"""
    from django.db import connection
    import time
    
    # Step 1: Close any existing connections and fetch fresh data
    connection.close()
    
    try:
        session = Session.objects.get(id=session_id)
    except Session.DoesNotExist:
        messages.error(request, 'Session not found.')
        return redirect('dashboard:home')
    
    event = session.event
    
    if request.method == 'POST':
        # Step 2: Process the form
        form = SessionForm(request.POST, instance=session, event=event)
        
        if form.is_valid():
            # Step 3: Save the session
            updated_session = form.save()
            
            # Step 4: CLEAR ALL CACHES (nuclear option)
            clear_all_caches()
            
            # Step 5: Close connection to force fresh queries
            connection.close()
            
            messages.success(request, f'Session "{updated_session.title}" updated successfully!')
            
            # Step 6: Redirect with timestamp to prevent browser cache
            return redirect(f"/dashboard/events/{event.id}/?t={int(time.time())}")
        else:
            # Show form errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        # GET request - load the form
        # Close connection and fetch fresh data
        connection.close()
        session = Session.objects.get(id=session_id)
        
        form = SessionForm(instance=session, event=event)
    
    context = {
        'form': form,
        'event': event,
        'session': session,
        'is_edit': True,
    }
    
    response = render(request, 'dashboard/session_edit.html', context)
    
    # Prevent ALL caching
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    
    return response


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


# ==================== Event Registration Management ====================

@login_required
@user_passes_test(is_staff_user)
def event_registrations(request, event_id):
    """View and manage event registrations"""
    from events.models import EventRegistration
    
    event = get_object_or_404(Event, id=event_id)
    
    # Filter options
    filter_type = request.GET.get('filter', 'all')
    search_query = request.GET.get('search', '')
    
    registrations = EventRegistration.objects.filter(event=event).select_related('user', 'participant')
    
    # Apply filters
    if filter_type == 'confirmed':
        registrations = registrations.filter(is_confirmed=True)
    elif filter_type == 'not_confirmed':
        registrations = registrations.filter(is_confirmed=False)
    elif filter_type == 'spam':
        registrations = registrations.filter(is_spam=True)
    elif filter_type == 'no_account':
        registrations = registrations.filter(user__isnull=True)
    elif filter_type == 'with_account':
        registrations = registrations.filter(user__isnull=False)
    
    # Apply search
    if search_query:
        registrations = registrations.filter(
            Q(nom__icontains=search_query) |
            Q(prenom__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(telephone__icontains=search_query) |
            Q(etablissement__icontains=search_query)
        )
    
    registrations = registrations.order_by('-created_at')
    
    # Statistics
    stats = {
        'total': EventRegistration.objects.filter(event=event).count(),
        'confirmed': EventRegistration.objects.filter(event=event, is_confirmed=True).count(),
        'not_confirmed': EventRegistration.objects.filter(event=event, is_confirmed=False).count(),
        'spam': EventRegistration.objects.filter(event=event, is_spam=True).count(),
        'with_account': EventRegistration.objects.filter(event=event, user__isnull=False).count(),
        'no_account': EventRegistration.objects.filter(event=event, user__isnull=True).count(),
    }
    
    context = {
        'event': event,
        'registrations': registrations,
        'stats': stats,
        'filter_type': filter_type,
        'search_query': search_query,
    }
    
    return render(request, 'dashboard/event_registrations.html', context)


@login_required
@user_passes_test(is_staff_user)
def approve_registration(request, registration_id):
    """Approve registration and create user account"""
    from events.models import EventRegistration
    import uuid
    
    registration = get_object_or_404(EventRegistration, id=registration_id)
    
    if request.method == 'POST':
        if registration.user:
            messages.warning(request, 'User account already exists for this registration.')
            return redirect('dashboard:event_registrations', event_id=registration.event.id)
        
        try:
            # Create user account
            username = registration.email.split('@')[0] + str(uuid.uuid4().hex[:4])
            user = User.objects.create_user(
                username=username,
                email=registration.email,
                first_name=registration.prenom,
                last_name=registration.nom,
                password=User.objects.make_random_password(12)
            )
            
            # Get or create user profile with QR code
            qr_data = UserProfile.get_qr_for_user(user)
            
            # Create participant
            participant = Participant.objects.create(
                user=user,
                event=registration.event,
                badge_id=qr_data['badge_id'],
                qr_code_data=json.dumps(qr_data)
            )
            
            # Create user event assignment
            UserEventAssignment.objects.create(
                user=user,
                event=registration.event,
                role='participant',
                assigned_by=request.user
            )
            
            # Link registration to user and participant
            registration.user = user
            registration.participant = participant
            registration.is_confirmed = True
            registration.save()
            
            messages.success(request, f'User account created for {registration.get_full_name()}!')
            
        except Exception as e:
            messages.error(request, f'Error creating user account: {str(e)}')
        
        return redirect('dashboard:event_registrations', event_id=registration.event.id)
    
    messages.warning(request, 'Invalid request.')
    return redirect('dashboard:event_registrations', event_id=registration.event.id)


@login_required
@user_passes_test(is_staff_user)
def delete_registration(request, registration_id):
    """Delete a registration"""
    from events.models import EventRegistration
    
    registration = get_object_or_404(EventRegistration, id=registration_id)
    event_id = registration.event.id
    
    if request.method == 'POST':
        registration_name = registration.get_full_name()
        registration.delete()
        messages.success(request, f'Registration for {registration_name} deleted successfully!')
        return redirect('dashboard:event_registrations', event_id=event_id)
    
    messages.warning(request, 'Invalid request.')
    return redirect('dashboard:event_registrations', event_id=event_id)


# ==================== API Endpoints ====================

@login_required
def api_events_list(request):
    """API endpoint to get events with registration counts"""
    from events.models import EventRegistration
    
    events = Event.objects.all().order_by('-created_at')
    
    events_data = []
    for event in events:
        registration_count = EventRegistration.objects.filter(
            event=event,
            status='approved',
            is_spam=False
        ).count()
        
        events_data.append({
            'id': str(event.id),
            'name': event.name,
            'start_date': event.start_date.strftime('%Y-%m-%d') if event.start_date else None,
            'registration_count': registration_count
        })
    
    return JsonResponse({'events': events_data})


# ==================== Public Form Views ====================

def public_form_view(request, slug):
    """Public view for custom registration forms"""
    from dashboard.models_form import FormConfiguration, FormSubmission
    from django.utils import timezone
    from django.conf import settings
    from events.models import UserEventAssignment, Participant, UserProfile
    import secrets
    
    # Get form regardless of active status
    form_config = get_object_or_404(FormConfiguration, slug=slug)
    
    # Debug logging
    print(f"DEBUG: Form '{form_config.name}' is_active = {form_config.is_active}")
    
    # Check if form is inactive - MUST check before processing
    if not form_config.is_active:
        print(f"DEBUG: Form is INACTIVE, showing closed page")
        # Render "Form Closed" page
        context = {
            'form_config': form_config,
            'form_closed': True,
        }
        response = render(request, 'dashboard/public_form.html', context)
        # Prevent caching
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        return response
    
    print(f"DEBUG: Form is ACTIVE, processing normally")
    
    if request.method == 'POST':
        try:
            # Check if this is a verification code submission
            verification_code = request.POST.get('verification_code', '').strip()
            
            if verification_code:
                # Handle verification code submission
                email = request.POST.get('email', '').strip().lower()
                
                if not email or not verification_code:
                    context = {
                        'form_config': form_config,
                        'fields': form_config.fields_config,
                        'errors': ['Email and verification code are required'],
                        'show_verification': True,
                        'submitted_email': email,
                    }
                    return render(request, 'dashboard/public_form.html', context)
                
                # Verify code using service
                from events.form_validation_service import verify_form_registration
                
                ip_address = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0] if request.META.get('HTTP_X_FORWARDED_FOR') else request.META.get('REMOTE_ADDR')
                user_agent = request.META.get('HTTP_USER_AGENT', '')
                
                success, participant, message = verify_form_registration(
                    email=email,
                    form_slug=form_config.slug,
                    code=verification_code,
                    ip_address=ip_address,
                    user_agent=user_agent
                )
                
                if success:
                    # Show success page
                    context = {
                        'form_config': form_config,
                        'success': True,
                        'submitted_email': email,
                        'message': message,
                    }
                    return render(request, 'dashboard/public_form.html', context)
                else:
                    # Show error
                    context = {
                        'form_config': form_config,
                        'fields': form_config.fields_config,
                        'errors': [message],
                        'show_verification': True,
                        'submitted_email': email,
                    }
                    return render(request, 'dashboard/public_form.html', context)
            
            # CRITICAL: Re-check if form is still active before processing submission
            form_config.refresh_from_db()
            
            if not form_config.is_active:
                print(f"DEBUG: Form was deactivated while user had it open - showing closed page")
                context = {
                    'form_config': form_config,
                    'form_closed': True,
                    'show_submission_blocked_alert': True,
                }
                response = render(request, 'dashboard/public_form.html', context)
                response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                response['Pragma'] = 'no-cache'
                response['Expires'] = '0'
                return response
            
            # Collect form data
            form_data = {}
            email = None
            first_name = None
            last_name = None
            errors = []
            
            for field in form_config.fields_config:
                field_name = field.get('name')
                
                # Handle checkbox fields (multiple values)
                if field.get('type') == 'checkbox':
                    value = request.POST.getlist(field_name)
                else:
                    value = request.POST.get(field_name, '')
                
                # Validate required fields
                if field.get('required'):
                    if not value or (isinstance(value, list) and len(value) == 0):
                        errors.append(f'{field.get("label")} is required.')
                        continue
                
                form_data[field_name] = value
                
                # Extract user creation fields
                if field_name == 'email' or field.get('type') == 'email':
                    email = value.lower() if value else None
                elif field_name == 'first_name':
                    first_name = value
                elif field_name == 'last_name':
                    last_name = value
            
            # Validate required fields
            if not email:
                errors.append('Email is required.')
            if not first_name:
                errors.append('First name is required.')
            if not last_name:
                errors.append('Last name is required.')
            
            # Validate event is assigned to form
            if not form_config.event:
                errors.append('This form is not linked to an event.')
            elif not form_config.event.start_date:
                errors.append('Event configuration is incomplete (missing start date).')
                print(f"WARNING: Event {form_config.event.id} missing start_date")
            
            # Check if user exists
            from django.contrib.auth.models import User
            user_exists = User.objects.filter(email=email).exists() if email else False
            
            if email and not user_exists:
                errors.append('Please create an account first in the mobile app before registering for events.')
            
            # If there are errors, redisplay form with errors
            if errors:
                context = {
                    'form_config': form_config,
                    'fields': form_config.fields_config,
                    'errors': errors,
                    'form_data': form_data,
                }
                return render(request, 'dashboard/public_form.html', context)
            
            # Get IP address
            ip_address = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0] if request.META.get('HTTP_X_FORWARDED_FOR') else request.META.get('REMOTE_ADDR')
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            # Send validation code
            from events.form_validation_service import send_form_validation_code
            
            success, message, wait_seconds = send_form_validation_code(
                email=email,
                form_slug=form_config.slug,
                form_data=form_data,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            if not success:
                context = {
                    'form_config': form_config,
                    'fields': form_config.fields_config,
                    'errors': [message],
                    'form_data': form_data,
                    'wait_seconds': wait_seconds,
                }
                return render(request, 'dashboard/public_form.html', context)
            
            # Show verification code input page
            context = {
                'form_config': form_config,
                'show_verification': True,
                'submitted_email': email,
                'message': message,
            }
            return render(request, 'dashboard/public_form.html', context)
        
        except Exception as e:
            # Log the full error for debugging
            import traceback
            error_details = traceback.format_exc()
            print(f"=" * 80)
            print(f"ERROR in form submission for form: {form_config.name}")
            print(f"Error type: {type(e).__name__}")
            print(f"Error message: {str(e)}")
            print(f"Form data received: {request.POST.dict()}")
            print(f"Event: {form_config.event.name if form_config.event else 'None'}")
            print(f"Full traceback:\n{error_details}")
            print(f"=" * 80)
            
            # Show user-friendly error page
            context = {
                'form_config': form_config,
                'fields': form_config.fields_config,
                'errors': [f'An error occurred while processing your submission. Please try again or contact support. Error: {str(e)}'],
                'form_data': request.POST.dict(),
            }
            return render(request, 'dashboard/public_form.html', context)
    
    # GET request - display form
    context = {
        'form_config': form_config,
        'fields': form_config.fields_config,
        'success': False,
    }
    
    return render(request, 'dashboard/public_form.html', context)
