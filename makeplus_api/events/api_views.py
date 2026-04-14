"""
REST API Views for Mobile App
These views return JSON responses, not HTML templates
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.db.models import Count, Q
from django.utils import timezone
from .models import (
    UserEventAssignment, RoomAssignment, Session, RoomAccess,
    Participant, Event
)
from .serializers import EventSerializer


class MyRoomStatisticsAPIView(APIView):
    """
    REST API: Get statistics for rooms assigned to current user (controller/gestionnaire)
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        # Get user's role and event
        assignment = UserEventAssignment.objects.filter(
            user=user,
            is_active=True
        ).first()
        
        if not assignment:
            return Response({
                'error': 'No active event assignment found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get rooms assigned to this user
        room_assignments = RoomAssignment.objects.filter(
            user=user,
            event=assignment.event,
            is_active=True
        ).select_related('room')
        
        if not room_assignments.exists():
            return Response({
                'assigned_rooms': 0,
                'total_sessions_today': 0,
                'current_participants': 0,
                'total_check_ins_today': 0,
                'rooms': []
            })
        
        # Get assigned rooms
        assigned_rooms = [ra.room for ra in room_assignments]
        room_ids = [room.id for room in assigned_rooms]
        
        # Get today's date range
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start.replace(hour=23, minute=59, second=59)
        
        # Count sessions today in assigned rooms
        sessions_today = Session.objects.filter(
            room_id__in=room_ids,
            start_time__gte=today_start,
            start_time__lte=today_end
        ).count()
        
        # Count check-ins today in assigned rooms
        check_ins_today = RoomAccess.objects.filter(
            room_id__in=room_ids,
            accessed_at__gte=today_start,
            accessed_at__lte=today_end,
            status='granted'
        ).count()
        
        # Count current participants (checked in today)
        current_participants = RoomAccess.objects.filter(
            room_id__in=room_ids,
            accessed_at__gte=today_start,
            status='granted'
        ).values('participant').distinct().count()
        
        # Room details
        rooms_data = []
        for room in assigned_rooms:
            room_sessions = Session.objects.filter(
                room=room,
                start_time__gte=today_start,
                start_time__lte=today_end
            ).count()
            
            room_check_ins = RoomAccess.objects.filter(
                room=room,
                accessed_at__gte=today_start,
                status='granted'
            ).count()
            
            rooms_data.append({
                'id': str(room.id),
                'name': room.name,
                'capacity': room.capacity,
                'sessions_today': room_sessions,
                'check_ins_today': room_check_ins
            })
        
        return Response({
            'assigned_rooms': len(assigned_rooms),
            'total_sessions_today': sessions_today,
            'current_participants': current_participants,
            'total_check_ins_today': check_ins_today,
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
