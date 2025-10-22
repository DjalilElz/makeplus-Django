# events/views.py - Complete Views with Permissions

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db.models import Q, Count
from .auth_views import (
    RegisterView, CustomLoginView, LogoutView,
    UserProfileView, ChangePasswordView,
    QRVerificationView, QRGenerateView,
    DashboardStatsView,
    NotificationListView, NotificationDetailView,
    MarkNotificationReadView
)
from .models import Event, Room, Session, Participant, RoomAccess, UserEventAssignment
from .serializers import (
    EventSerializer, RoomSerializer, RoomListSerializer, SessionSerializer,
    ParticipantSerializer, RoomAccessSerializer, UserEventAssignmentSerializer,
    QRVerificationSerializer
)
from .permissions import IsOrganizerOrReadOnly, IsOrganizer, IsController


class EventViewSet(viewsets.ModelViewSet):
    """
    Event CRUD operations
    Only organizers/admins can create/update
    """
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status']
    search_fields = ['name', 'location']
    ordering_fields = ['start_date', 'created_at']
    ordering = ['-start_date']
    
    def get_queryset(self):
        """Filter events based on user access"""
        user = self.request.user
        
        # Admin sees all
        if user.is_staff:
            return Event.objects.all()
        
        # Users see events they're assigned to
        user_events = UserEventAssignment.objects.filter(
            user=user,
            is_active=True
        ).values_list('event_id', flat=True)
        
        return Event.objects.filter(id__in=user_events)
    
    def perform_create(self, serializer):
        """Set created_by on creation"""
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """Get event statistics"""
        event = self.get_object()
        
        stats = {
            'total_rooms': event.rooms.filter(is_active=True).count(),
            'total_sessions': event.sessions.count(),
            'total_participants': event.participants.count(),
            'checked_in_count': event.participants.filter(is_checked_in=True).count(),
            'live_sessions': event.sessions.filter(status='live').count(),
            'completed_sessions': event.sessions.filter(status='completed').count(),
        }
        
        return Response(stats)


class RoomViewSet(viewsets.ModelViewSet):
    """
    Room CRUD operations
    GET: List/retrieve rooms (filtered by event)
    POST: Create room (organizer only)
    PUT/PATCH: Update room (organizer only)
    DELETE: Delete room (organizer only)
    """
    queryset = Room.objects.all()
    permission_classes = [IsAuthenticated, IsOrganizerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['event', 'is_active']
    search_fields = ['name', 'location']
    ordering_fields = ['name', 'capacity', 'current_participants']
    ordering = ['name']
    
    def get_serializer_class(self):
        """Use lightweight serializer for list"""
        if self.action == 'list':
            return RoomListSerializer
        return RoomSerializer
    
    def get_queryset(self):
        """Filter rooms by event"""
        queryset = Room.objects.select_related('event').prefetch_related('sessions')
        
        # Filter by event if provided
        event_id = self.request.query_params.get('event_id')
        if event_id:
            queryset = queryset.filter(event_id=event_id)
        
        # Filter by user's accessible events
        user = self.request.user
        if not user.is_staff:
            user_events = UserEventAssignment.objects.filter(
                user=user,
                is_active=True
            ).values_list('event_id', flat=True)
            queryset = queryset.filter(event_id__in=user_events)
        
        return queryset
    
    def perform_create(self, serializer):
        """Set created_by on creation"""
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['get'])
    def sessions(self, request, pk=None):
        """Get all sessions for this room"""
        room = self.get_object()
        sessions = room.sessions.all().order_by('start_time')
        serializer = SessionSerializer(sessions, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def participants(self, request, pk=None):
        """Get participants currently in room"""
        room = self.get_object()
        today = timezone.now().date()
        
        # Get participants who accessed today
        accesses = RoomAccess.objects.filter(
            room=room,
            accessed_at__date=today,
            status='granted'
        ).select_related('participant__user').distinct('participant')
        
        data = [{
            'id': access.participant.id,
            'name': access.participant.user.get_full_name() or access.participant.user.username,
            'email': access.participant.user.email,
            'accessed_at': access.accessed_at,
            'session': access.session.title if access.session else None
        } for access in accesses]
        
        return Response(data)
    
    @action(detail=True, methods=['post'])
    def verify_access(self, request, pk=None):
        """Verify QR code for room access"""
        room = self.get_object()
        serializer = QRVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        qr_data = serializer.validated_data['qr_data']
        
        try:
            # Find participant by QR code
            participant = Participant.objects.get(
                qr_code_data=qr_data,
                event=room.event
            )
            
            # Check if participant is allowed
            allowed_rooms = participant.allowed_rooms.all()
            if allowed_rooms.exists() and room not in allowed_rooms:
                # Create denied access record
                RoomAccess.objects.create(
                    participant=participant,
                    room=room,
                    session=serializer.validated_data.get('session'),
                    verified_by=request.user,
                    status='denied',
                    denial_reason='Not authorized for this room'
                )
                
                return Response({
                    'status': 'denied',
                    'message': 'Participant not authorized for this room',
                    'participant': {
                        'id': participant.id,
                        'name': participant.user.get_full_name(),
                        'badge_id': participant.badge_id
                    }
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Grant access
            access = RoomAccess.objects.create(
                participant=participant,
                room=room,
                session=serializer.validated_data.get('session'),
                verified_by=request.user,
                status='granted'
            )
            
            return Response({
                'status': 'granted',
                'message': 'Access granted',
                'participant': {
                    'id': participant.id,
                    'name': participant.user.get_full_name(),
                    'email': participant.user.email,
                    'badge_id': participant.badge_id
                },
                'access_id': access.id,
                'accessed_at': access.accessed_at
            })
            
        except Participant.DoesNotExist:
            return Response({
                'status': 'invalid',
                'message': 'Invalid QR code or participant not found'
            }, status=status.HTTP_404_NOT_FOUND)


class SessionViewSet(viewsets.ModelViewSet):
    """
    Session CRUD operations
    Includes session status management (live, completed)
    """
    queryset = Session.objects.all()
    serializer_class = SessionSerializer
    permission_classes = [IsAuthenticated, IsOrganizerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['event', 'room', 'status', 'theme']
    search_fields = ['title', 'speaker_name', 'description']
    ordering_fields = ['start_time', 'created_at']
    ordering = ['start_time']
    
    def get_queryset(self):
        """Filter sessions by event and user access"""
        queryset = Session.objects.select_related('event', 'room')
        
        # Filter by event
        event_id = self.request.query_params.get('event_id')
        if event_id:
            queryset = queryset.filter(event_id=event_id)
        
        # Filter by room
        room_id = self.request.query_params.get('room_id')
        if room_id:
            queryset = queryset.filter(room_id=room_id)
        
        # Filter by user's accessible events
        user = self.request.user
        if not user.is_staff:
            user_events = UserEventAssignment.objects.filter(
                user=user,
                is_active=True
            ).values_list('event_id', flat=True)
            queryset = queryset.filter(event_id__in=user_events)
        
        return queryset
    
    def perform_create(self, serializer):
        """Set created_by on creation"""
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsOrganizer])
    def mark_live(self, request, pk=None):
        """Mark session as live"""
        session = self.get_object()
        session.status = 'live'
        session.save(update_fields=['status'])
        
        serializer = self.get_serializer(session)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsOrganizer])
    def mark_completed(self, request, pk=None):
        """Mark session as completed"""
        session = self.get_object()
        session.status = 'completed'
        session.save(update_fields=['status'])
        
        serializer = self.get_serializer(session)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsOrganizer])
    def cancel(self, request, pk=None):
        """Cancel session"""
        session = self.get_object()
        session.status = 'cancelled'
        session.save(update_fields=['status'])
        
        serializer = self.get_serializer(session)
        return Response(serializer.data)


class ParticipantViewSet(viewsets.ModelViewSet):
    """
    Participant management
    """
    queryset = Participant.objects.all()
    serializer_class = ParticipantSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['event', 'is_checked_in']
    search_fields = ['user__username', 'user__email', 'user__first_name', 'user__last_name', 'badge_id']
    
    def get_queryset(self):
        """Filter by event and user access"""
        queryset = Participant.objects.select_related('user', 'event')
        
        event_id = self.request.query_params.get('event_id')
        if event_id:
            queryset = queryset.filter(event_id=event_id)
        
        return queryset


class RoomAccessViewSet(viewsets.ModelViewSet):
    """
    Room access log/history
    """
    queryset = RoomAccess.objects.all()
    serializer_class = RoomAccessSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['room', 'participant', 'status']
    ordering_fields = ['accessed_at']
    ordering = ['-accessed_at']
    
    def get_queryset(self):
        """Filter by room/participant"""
        queryset = RoomAccess.objects.select_related('participant__user', 'room', 'session', 'verified_by')
        
        room_id = self.request.query_params.get('room_id')
        if room_id:
            queryset = queryset.filter(room_id=room_id)
        
        participant_id = self.request.query_params.get('participant_id')
        if participant_id:
            queryset = queryset.filter(participant_id=participant_id)
        
        return queryset
    
    def perform_create(self, serializer):
        """Set verified_by on creation"""
        serializer.save(verified_by=self.request.user)


class UserEventAssignmentViewSet(viewsets.ModelViewSet):
    """
    User-Event assignments (Admin only)
    """
    queryset = UserEventAssignment.objects.all()
    serializer_class = UserEventAssignmentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['user', 'event', 'role', 'is_active']
    
    def perform_create(self, serializer):
        """Set assigned_by on creation"""
        serializer.save(assigned_by=self.request.user)