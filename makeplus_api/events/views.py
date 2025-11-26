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
    MarkNotificationReadView,
    SelectEventView, SwitchEventView, MyEventsView
)
from .models import (
    Event, Room, Session, Participant, RoomAccess, UserEventAssignment,
    SessionAccess, Annonce, SessionQuestion, RoomAssignment, ExposantScan
)
from .serializers import (
    EventSerializer, RoomSerializer, RoomListSerializer, SessionSerializer,
    ParticipantSerializer, RoomAccessSerializer, UserEventAssignmentSerializer,
    QRVerificationSerializer, SessionAccessSerializer, AnnonceSerializer,
    SessionQuestionSerializer, RoomAssignmentSerializer, ExposantScanSerializer
)
from .permissions import IsGestionnaireOrReadOnly, IsGestionnaire, IsController, IsExposant, IsAnnonceOwner


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
            'live_sessions': event.sessions.filter(status='en_cours').count(),
            'completed_sessions': event.sessions.filter(status='termine').count(),
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
    permission_classes = [IsAuthenticated, IsGestionnaireOrReadOnly]
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
    permission_classes = [IsAuthenticated, IsGestionnaireOrReadOnly]
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
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsGestionnaire])
    def mark_live(self, request, pk=None):
        """Mark session as live"""
        session = self.get_object()
        session.status = 'en_cours'
        session.save(update_fields=['status'])
        
        serializer = self.get_serializer(session)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsGestionnaire])
    def mark_completed(self, request, pk=None):
        """Mark session as completed"""
        session = self.get_object()
        session.status = 'termine'
        session.save(update_fields=['status'])
        
        serializer = self.get_serializer(session)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsGestionnaire])
    def cancel(self, request, pk=None):
        """Cancel session (reset to not started)"""
        session = self.get_object()
        session.status = 'pas_encore'
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

class SessionAccessViewSet(viewsets.ModelViewSet):
    """
    Session access management for paid ateliers
    """
    queryset = SessionAccess.objects.all()
    serializer_class = SessionAccessSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['participant', 'session', 'payment_status', 'has_access']
    
    def get_queryset(self):
        """Filter by participant or session"""
        queryset = SessionAccess.objects.select_related('participant__user', 'session')
        
        participant_id = self.request.query_params.get('participant_id')
        if participant_id:
            queryset = queryset.filter(participant_id=participant_id)
        
        session_id = self.request.query_params.get('session_id')
        if session_id:
            queryset = queryset.filter(session_id=session_id)
        
        return queryset


class AnnonceViewSet(viewsets.ModelViewSet):
    """
    Event announcements with targeting
    """
    queryset = Annonce.objects.all()
    serializer_class = AnnonceSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['event', 'target', 'created_by']
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter annonces by user role and event"""
        user = self.request.user
        queryset = Annonce.objects.select_related('event', 'created_by')
        
        # Filter by event
        event_id = self.request.query_params.get('event_id')
        if event_id:
            queryset = queryset.filter(event_id=event_id)
        
        # Filter by target based on user role (even for staff/admins)
        # Only superusers see all announcements
        if not user.is_superuser:
            # Get user's role in events
            user_assignments = UserEventAssignment.objects.filter(user=user, is_active=True)
            user_roles = {assignment.event_id: assignment.role for assignment in user_assignments}
            
            # Filter annonces targeted to user's roles or 'all' OR created by user
            role_filters = Q(target='all') | Q(created_by=user)
            for event_id, role in user_roles.items():
                if role == 'participant':
                    role_filters |= Q(event_id=event_id, target='participants')
                elif role == 'exposant':
                    role_filters |= Q(event_id=event_id, target='exposants')
                elif role == 'controlleur_des_badges':
                    role_filters |= Q(event_id=event_id, target='controlleurs')
                elif role == 'gestionnaire_des_salles':
                    role_filters |= Q(event_id=event_id, target='gestionnaires')
            
            queryset = queryset.filter(role_filters)
        
        return queryset
    
    def perform_create(self, serializer):
        """Set created_by on creation"""
        serializer.save(created_by=self.request.user)
    
    def get_permissions(self):
        """Only annonce owner or gestionnaire can update/delete"""
        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsAnnonceOwner()]
        return [IsAuthenticated()]


class SessionQuestionViewSet(viewsets.ModelViewSet):
    """
    Session questions (Q&A)
    """
    queryset = SessionQuestion.objects.all()
    serializer_class = SessionQuestionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['session', 'participant', 'is_answered']
    ordering_fields = ['asked_at', 'answered_at']
    ordering = ['asked_at']
    
    def get_queryset(self):
        """Filter by session"""
        queryset = SessionQuestion.objects.select_related('session', 'participant__user', 'answered_by')
        
        session_id = self.request.query_params.get('session_id')
        if session_id:
            queryset = queryset.filter(session_id=session_id)
        
        return queryset
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsGestionnaire])
    def answer(self, request, pk=None):
        """Answer a question"""
        question = self.get_object()
        answer_text = request.data.get('answer_text')
        
        if not answer_text:
            return Response({'error': 'answer_text is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        question.answer_text = answer_text
        question.is_answered = True
        question.answered_by = request.user
        question.answered_at = timezone.now()
        question.save()
        
        serializer = self.get_serializer(question)
        return Response(serializer.data)


class RoomAssignmentViewSet(viewsets.ModelViewSet):
    """
    Room assignments for gestionnaires and controllers
    """
    queryset = RoomAssignment.objects.all()
    serializer_class = RoomAssignmentSerializer
    permission_classes = [IsAuthenticated, IsGestionnaire]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['user', 'room', 'event', 'role', 'is_active']
    ordering_fields = ['start_time', 'end_time']
    ordering = ['start_time']
    
    def get_queryset(self):
        """Filter by room, user, or event"""
        queryset = RoomAssignment.objects.select_related('user', 'room', 'event', 'assigned_by')
        
        room_id = self.request.query_params.get('room_id')
        if room_id:
            queryset = queryset.filter(room_id=room_id)
        
        user_id = self.request.query_params.get('user_id')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        event_id = self.request.query_params.get('event_id')
        if event_id:
            queryset = queryset.filter(event_id=event_id)
        
        # Get current assignments
        current_only = self.request.query_params.get('current')
        if current_only:
            now = timezone.now()
            queryset = queryset.filter(start_time__lte=now, end_time__gte=now, is_active=True)
        
        return queryset
    
    def perform_create(self, serializer):
        """Set assigned_by on creation"""
        serializer.save(assigned_by=self.request.user)


class ExposantScanViewSet(viewsets.ModelViewSet):
    """
    Exposant scanning participant QR codes (booth visits)
    """
    queryset = ExposantScan.objects.all()
    serializer_class = ExposantScanSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['exposant', 'scanned_participant', 'event']
    ordering_fields = ['scanned_at']
    ordering = ['-scanned_at']
    
    def get_queryset(self):
        """Filter by exposant or event"""
        queryset = ExposantScan.objects.select_related(
            'exposant__user', 'scanned_participant__user', 'event'
        )
        
        exposant_id = self.request.query_params.get('exposant_id')
        if exposant_id:
            queryset = queryset.filter(exposant_id=exposant_id)
        
        event_id = self.request.query_params.get('event_id')
        if event_id:
            queryset = queryset.filter(event_id=event_id)
        
        return queryset
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, IsExposant])
    def my_scans(self, request):
        """Get scans for the current exposant"""
        try:
            # Find exposant participant record for current user
            event_id = request.query_params.get('event_id')
            if not event_id:
                return Response({'error': 'event_id is required'}, status=status.HTTP_400_BAD_REQUEST)
            
            exposant = Participant.objects.get(user=request.user, event_id=event_id)
            scans = self.get_queryset().filter(exposant=exposant)
            
            # Get statistics
            total_scans = scans.count()
            today_scans = scans.filter(scanned_at__date=timezone.now().date()).count()
            
            serializer = self.get_serializer(scans, many=True)
            
            return Response({
                'total_visits': total_scans,
                'today_visits': today_scans,
                'scans': serializer.data
            })
        except Participant.DoesNotExist:
            return Response({'error': 'Exposant participant record not found'}, status=status.HTTP_404_NOT_FOUND)
