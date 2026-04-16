"""
REST API Views for Mobile App
These views return JSON responses, not HTML templates
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.renderers import JSONRenderer
from django.db.models import Count, Q
from django.utils import timezone
from .models import (
    UserEventAssignment, Session, RoomAccess, Room,
    Participant, Event
)
from .serializers import EventSerializer


class MyRoomStatisticsAPIView(APIView):
    """
    REST API: Get statistics for check-ins performed by current controller
    Each controller sees only their own scans/check-ins
    """
    permission_classes = [IsAuthenticated]
    renderer_classes = [JSONRenderer]  # Force JSON only
    
    def get(self, request):
        user = request.user
        
        # Get user's assignment with event in one query
        assignment = UserEventAssignment.objects.select_related('event').filter(
            user=user,
            is_active=True
        ).first()
        
        if not assignment:
            return Response({
                'error': 'No active event assignment found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get all active rooms in the event
        rooms = Room.objects.filter(
            event=assignment.event,
            is_active=True
        )
        
        if not rooms.exists():
            return Response({
                'total_rooms': 0,
                'total_sessions_today': 0,
                'my_check_ins_today': 0,
                'rooms': []
            })
        
        # Get today's date range
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start.replace(hour=23, minute=59, second=59)
        
        # Get room IDs for queries
        room_ids = [room.id for room in rooms]
        
        # Count sessions today in all rooms
        sessions_today = Session.objects.filter(
            room_id__in=room_ids,
            start_time__gte=today_start,
            start_time__lte=today_end
        ).count()
        
        # Count check-ins performed by THIS controller today
        my_check_ins_today = RoomAccess.objects.filter(
            verified_by=user,  # Only this controller's scans
            accessed_at__gte=today_start,
            accessed_at__lte=today_end,
            status='granted'
        ).count()
        
        # Build room details with this controller's check-ins per room
        rooms_data = []
        for room in rooms:
            room_sessions = Session.objects.filter(
                room=room,
                start_time__gte=today_start,
                start_time__lte=today_end
            ).count()
            
            # Check-ins by THIS controller in this room
            my_room_check_ins = RoomAccess.objects.filter(
                room=room,
                verified_by=user,  # Only this controller's scans
                accessed_at__gte=today_start,
                status='granted'
            ).count()
            
            rooms_data.append({
                'id': str(room.id),
                'name': room.name,
                'capacity': room.capacity,
                'sessions_today': room_sessions,
                'my_check_ins_today': my_room_check_ins
            })
        
        # Build response
        return Response({
            'total_rooms': len(rooms),
            'total_sessions_today': sessions_today,
            'my_check_ins_today': my_check_ins_today,
            'rooms': rooms_data,
            'role': assignment.role,
            'event': {
                'id': str(assignment.event.id),
                'name': assignment.event.name
            }
        })


class DashboardStatsAPIView(APIView):
    """
    REST API: Get dashboard statistics for current user
    """
    permission_classes = [IsAuthenticated]
    renderer_classes = [JSONRenderer]  # Force JSON only
    
    def get(self, request):
        user = request.user
        
        # Get user's active assignment
        assignment = UserEventAssignment.objects.filter(
            user=user,
            is_active=True
        ).first()
        
        if not assignment:
            return Response({
                'error': 'No active event assignment found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        event = assignment.event
        role = assignment.role
        
        # Base stats
        stats = {
            'role': role,
            'event': {
                'id': str(event.id),
                'name': event.name,
                'status': event.status
            }
        }
        
        # Role-specific stats
        if role == 'gestionnaire':
            # Room manager stats
            assigned_rooms = RoomAssignment.objects.filter(
                user=user,
                event=event,
                is_active=True
            ).count()
            
            stats['assigned_rooms'] = assigned_rooms
            
        elif role == 'controller':
            # Controller stats
            today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
            
            check_ins_today = RoomAccess.objects.filter(
                verified_by=user,
                accessed_at__gte=today_start,
                status='granted'
            ).count()
            
            stats['check_ins_today'] = check_ins_today
            
        elif role == 'exposant':
            # Exhibitor stats
            from .models import ExposantScan
            
            participant = Participant.objects.filter(
                user=user,
                event=event
            ).first()
            
            if participant:
                scans_count = ExposantScan.objects.filter(
                    exposant=participant
                ).count()
                
                stats['total_scans'] = scans_count
        
        # Common stats
        stats['total_participants'] = event.total_participants
        stats['total_rooms'] = event.total_rooms
        
        return Response(stats)


class MyEventsAPIView(APIView):
    """
    REST API: Get list of events assigned to current user
    """
    permission_classes = [IsAuthenticated]
    renderer_classes = [JSONRenderer]  # Force JSON only
    
    def get(self, request):
        user = request.user
        
        # Get all active assignments for this user
        assignments = UserEventAssignment.objects.filter(
            user=user,
            is_active=True
        ).select_related('event')
        
        events_data = []
        for assignment in assignments:
            event = assignment.event
            events_data.append({
                'assignment_id': str(assignment.id),
                'role': assignment.role,
                'event': EventSerializer(event).data,
                'assigned_at': assignment.assigned_at
            })
        
        return Response({
            'count': len(events_data),
            'results': events_data
        })


class MyAteliersAPIView(APIView):
    """
    REST API: Get list of workshops/ateliers for current user
    """
    permission_classes = [IsAuthenticated]
    renderer_classes = [JSONRenderer]  # Force JSON only
    
    def get(self, request):
        user = request.user
        
        # Get user's participant record
        participant = Participant.objects.filter(user=user).first()
        
        if not participant:
            return Response({
                'count': 0,
                'results': []
            })
        
        # Get sessions user has access to
        from .models import SessionAccess
        from .serializers import SessionSerializer
        
        session_accesses = SessionAccess.objects.filter(
            participant=participant,
            has_access=True
        ).select_related('session')
        
        sessions_data = []
        for access in session_accesses:
            session = access.session
            session_data = SessionSerializer(session).data
            session_data['payment_status'] = access.payment_status
            session_data['amount_paid'] = float(access.amount_paid) if access.amount_paid else 0
            sessions_data.append(session_data)
        
        return Response({
            'count': len(sessions_data),
            'results': sessions_data
        })


class UserProfileAPIView(APIView):
    """
    REST API: Get current user profile
    Returns JSON only (no HTML)
    """
    permission_classes = [IsAuthenticated]
    renderer_classes = [JSONRenderer]  # Force JSON only, no HTML
    
    def get(self, request):
        user = request.user
        
        # Get user's active assignment
        assignment = UserEventAssignment.objects.filter(
            user=user,
            is_active=True
        ).first()
        
        profile_data = {
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'full_name': user.get_full_name() or user.email
        }
        
        # Add role and event if user has assignment
        if assignment:
            profile_data['role'] = assignment.role
            profile_data['event'] = {
                'id': str(assignment.event.id),
                'name': assignment.event.name,
                'status': assignment.event.status
            }
        else:
            profile_data['role'] = None
            profile_data['event'] = None
        
        return Response(profile_data)
