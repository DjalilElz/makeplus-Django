"""
Utility functions for the events app
"""

from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Custom exception handler that provides consistent error responses
    """
    response = exception_handler(exc, context)
    
    if response is not None:
        custom_response_data = {
            'error': True,
            'message': '',
            'details': {}
        }
        
        if isinstance(response.data, dict):
            if 'detail' in response.data:
                custom_response_data['message'] = response.data['detail']
            else:
                custom_response_data['details'] = response.data
                custom_response_data['message'] = 'Validation error'
        elif isinstance(response.data, list):
            custom_response_data['message'] = response.data[0] if response.data else 'An error occurred'
        else:
            custom_response_data['message'] = str(response.data)
        
        response.data = custom_response_data
    else:
        # Log unhandled exceptions
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return response


def generate_badge_id(event_id, participant_number):
    """
    Generate a unique badge ID for participant
    Format: EVT-{EVENT_SHORT_ID}-{PADDED_NUMBER}
    """
    event_short = str(event_id)[:8].upper()
    padded_number = str(participant_number).zfill(5)
    return f"EVT-{event_short}-{padded_number}"


def generate_qr_code_data(participant):
    """
    Generate unique QR code data for participant
    """
    import hashlib
    import uuid
    
    unique_string = f"{participant.id}_{participant.user.email}_{uuid.uuid4()}"
    return hashlib.sha256(unique_string.encode()).hexdigest()


def check_room_capacity(room, additional_count=1):
    """
    Check if room has capacity for additional participants
    Returns: (bool, str) - (has_capacity, message)
    """
    if room.capacity is None:
        return True, "Room has unlimited capacity"
    
    if room.current_participants + additional_count > room.capacity:
        return False, f"Room capacity exceeded. Current: {room.current_participants}/{room.capacity}"
    
    return True, "Room has capacity"


# Namespace for the event-selection token's signature. Changing this value
# invalidates every outstanding token, which is the intended kill switch.
EVENT_SELECTION_SALT = 'makeplus.auth.event-selection'

# How long a user has to pick an event before having to log in again.
EVENT_SELECTION_TOKEN_MAX_AGE = 600  # seconds


def make_event_selection_token(user):
    """
    Short-lived, opaque token proving "this person just authenticated and is
    choosing an event".

    Intentionally django.core.signing rather than a SimpleJWT token: a real
    AccessToken would be accepted by JWTAuthentication on every other
    endpoint, so a user who has not selected an event yet could call the
    whole API with it. This value carries no authentication weight anywhere
    except /auth/select-event/, which validates it by hand.
    """
    from django.core import signing

    return signing.dumps(
        {'user_id': user.id, 'purpose': 'event_selection'},
        salt=EVENT_SELECTION_SALT,
    )


def read_event_selection_token(token):
    """
    Validate an event-selection token and return its User, or None if the
    token is malformed, tampered with, expired, or not actually an
    event-selection token.
    """
    from django.contrib.auth.models import User
    from django.core import signing

    try:
        payload = signing.loads(
            token,
            salt=EVENT_SELECTION_SALT,
            max_age=EVENT_SELECTION_TOKEN_MAX_AGE,
        )
    except signing.BadSignature:
        return None

    if not isinstance(payload, dict) or payload.get('purpose') != 'event_selection':
        return None

    return User.objects.filter(id=payload.get('user_id'), is_active=True).first()


def resolve_role_for_event(user, event):
    """
    The user's role *in a specific event*, or None if they have no access to
    it at all.

    resolve_current_event() answers "which event should this user land on?";
    this answers "given they picked THIS event, what are they there?". Both
    membership models have to be checked for the same reason (staff-type
    roles get a UserEventAssignment row, plain participants never do).

    Returning None is the authorization check for event selection -- never
    mint a token for an event this returns None for.
    """
    from .models import UserEventAssignment, Participant

    assignment = UserEventAssignment.objects.filter(
        user=user, event=event, is_active=True
    ).first()
    if assignment:
        return assignment.role

    participant = Participant.objects.filter(user=user).first()
    if participant and participant.registrations.filter(event=event).exists():
        return 'participant'

    return None


def build_event_payload(event, request=None):
    """
    The JSON shape the mobile client's EventModel.fromJson expects.

    Shared by the login response, the event-selection response and the
    available_events list so all three stay identical -- the client parses
    them with the same code, and a field present in one but missing from
    another shows up as a blank event screen only in some flows.
    """
    if event is None:
        return None

    def _abs(file_field):
        if not file_field:
            return None
        return request.build_absolute_uri(file_field.url) if request else file_field.url

    return {
        'id': str(event.id),
        'name': event.name,
        'description': event.description,
        'start_date': event.start_date.isoformat() if event.start_date else None,
        'end_date': event.end_date.isoformat() if event.end_date else None,
        'location': event.location,
        'status': event.status,
        'logo': _abs(event.logo),
        'banner': _abs(event.banner),
        'primary_color': event.primary_color,
        'programme_file': _abs(event.programme_file),
        'guide_file': _abs(event.guide_file),
    }


def build_auth_payload(user, event, role, request=None):
    """
    Full authenticated response: tokens (with the event_id claim), user,
    role, event and QR badge.

    Used by both the normal single-event login and the post-selection
    token mint so the client receives byte-identical shapes either way.
    """
    from rest_framework_simplejwt.tokens import RefreshToken
    from .models import UserProfile

    refresh = RefreshToken.for_user(user)
    if event:
        # RefreshToken.access_token copies claims present on the refresh
        # token's payload at the time it's accessed, and TokenRefreshView
        # does the same on renewal -- so setting it here is enough for it
        # to survive refresh too, not just this login.
        refresh['event_id'] = str(event.id)

    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        'user': {
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
        },
        'role': role or 'participant',
        'event': build_event_payload(event, request),
        'qr_code': UserProfile.get_qr_for_user(user),
    }


def resolve_current_event(user):
    """
    Resolve the "current" (event, role) pair for a user.

    Staff-type roles (gestionnaire, controller, exposant, committee) get an
    UserEventAssignment row and that always wins. Plain participants never get
    one (signup creates none by design) — for them we fall back to their
    ParticipantEventRegistration rows, preferring an event that's currently
    'active', else the most recently registered one.

    Without this fallback, every plain participant — the majority of users —
    logs in with event=None: EventContextMiddleware never gets an event_id
    claim to put in the JWT, so anything gated on request.event_context
    (session Q&A, room statistics) silently fails for them, and the mobile
    client has nothing to show on the event/program screens either.

    Returns (event_or_None, role_or_None).
    """
    from .models import UserEventAssignment, Participant

    assignment = UserEventAssignment.objects.filter(
        user=user,
        is_active=True
    ).select_related('event').first()
    if assignment:
        return assignment.event, assignment.role

    participant = Participant.objects.filter(user=user).first()
    if participant:
        active_registration = (
            participant.registrations
            .filter(event__status='active')
            .select_related('event')
            .order_by('-registered_at')
            .first()
        )
        chosen = active_registration or (
            participant.registrations
            .select_related('event')
            .order_by('-registered_at')
            .first()
        )
        if chosen:
            return chosen.event, 'participant'

    return None, None


def get_accessible_event_ids(user):
    """
    Event IDs a user can access, combining both membership models: staff-type
    roles via UserEventAssignment, and plain participants via
    ParticipantEventRegistration (see resolve_current_event's docstring for
    why both are needed -- participants never get a UserEventAssignment row).

    Without this, any get_queryset() that only checks UserEventAssignment
    returns zero rows for every plain participant, even when they're
    genuinely registered for the event (sessions, rooms, etc. all
    silently empty on the mobile client).
    """
    from .models import UserEventAssignment, Participant

    assignment_event_ids = set(
        UserEventAssignment.objects.filter(user=user, is_active=True)
        .values_list('event_id', flat=True)
    )

    participant = Participant.objects.filter(user=user).first()
    registration_event_ids = set()
    if participant:
        registration_event_ids = set(
            participant.registrations.values_list('event_id', flat=True)
        )

    return assignment_event_ids | registration_event_ids


def get_assigned_room_ids(user):
    """
    Room IDs a gestionnaire_des_salles is assigned to, across every active
    UserEventAssignment they hold.

    Checked in the same order/priority as
    UserEventAssignmentSerializer.get_room_assignment() (events/serializers.py):
    the dashboard's own "assign a room" UI writes the room into
    UserEventAssignment.metadata['assigned_room_id'] -- that's the primary,
    actually-used mechanism today. The RoomAssignment table is only a
    fallback for older records that predate that; querying RoomAssignment
    alone (as an earlier version of the dashboard's session-questions
    feature did) misses every gestionnaire assigned the current way and
    wrongly reports them as having no room at all.
    """
    from .models import UserEventAssignment, RoomAssignment

    room_ids = set()
    assignments = UserEventAssignment.objects.filter(
        user=user, role='gestionnaire_des_salles', is_active=True
    )
    for assignment in assignments:
        room_id = None
        if assignment.metadata and assignment.metadata.get('assigned_room_id'):
            room_id = assignment.metadata['assigned_room_id']
        else:
            room_assignment = RoomAssignment.objects.filter(
                user=user, event=assignment.event, is_active=True
            ).first()
            if room_assignment:
                room_id = room_assignment.room_id
        if room_id:
            room_ids.add(str(room_id))
    return room_ids


def get_user_role_in_event(user, event):
    """
    Get user's role in a specific event
    Returns: str or None
    """
    from .models import UserEventAssignment
    
    assignment = UserEventAssignment.objects.filter(
        user=user,
        event=event,
        is_active=True
    ).first()
    
    return assignment.role if assignment else None


def is_user_authorized_for_event(user, event, required_roles=None):
    """
    Check if user is authorized for event with optional role check
    Args:
        user: User instance
        event: Event instance
        required_roles: list of roles or None (allows any role)
    Returns: bool
    """
    role = get_user_role_in_event(user, event)
    
    if role is None:
        return False
    
    if required_roles and role not in required_roles:
        return False
    
    return True


def format_session_time(session):
    """
    Format session time for display
    Returns: dict with formatted times
    """
    from django.utils import timezone
    
    return {
        'start_time': session.start_time.isoformat() if session.start_time else None,
        'end_time': session.end_time.isoformat() if session.end_time else None,
        'duration_minutes': session.duration_minutes(),
        'is_live': session.is_live,
        'status': session.status
    }


def send_notification(user, title, message, notification_type='info', related_object=None):
    """
    Send notification to user (placeholder for future implementation)
    """
    # TODO: Implement with actual notification system
    logger.info(f"Notification sent to {user.username}: {title} - {message}")
    return True


def validate_event_dates(start_date, end_date):
    """
    Validate event start and end dates
    Returns: (bool, str) - (is_valid, error_message)
    """
    from django.utils import timezone
    
    if start_date >= end_date:
        return False, "End date must be after start date"
    
    if start_date < timezone.now():
        return False, "Start date cannot be in the past"
    
    return True, ""


def validate_session_times(session, room=None):
    """
    Validate session times don't conflict with other sessions in the same room
    Returns: (bool, str) - (is_valid, error_message)
    """
    from .models import Session
    from django.db.models import Q
    
    if session.end_time <= session.start_time:
        return False, "End time must be after start time"
    
    if room is None:
        room = session.room
    
    # Check for overlapping sessions
    overlapping = Session.objects.filter(
        room=room,
        status__in=['scheduled', 'live']
    ).filter(
        Q(start_time__lt=session.end_time) & Q(end_time__gt=session.start_time)
    ).exclude(id=session.id if session.id else None)
    
    if overlapping.exists():
        conflicting_session = overlapping.first()
        return False, f"Session conflicts with '{conflicting_session.title}' ({conflicting_session.start_time} - {conflicting_session.end_time})"
    
    return True, ""