# events/serializers.py - DRF Serializers

from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Event, Room, Session, Participant, RoomAccess, UserEventAssignment

class UserSerializer(serializers.ModelSerializer):
    """User serializer"""
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = ['id']


class EventSerializer(serializers.ModelSerializer):
    """Event serializer"""
    created_by = UserSerializer(read_only=True)
    
    class Meta:
        model = Event
        fields = [
            'id', 'name', 'description', 'start_date', 'end_date',
            'location', 'location_details', 'logo_url', 'banner_url',
            'status', 'settings', 'themes', 'total_participants',
            'total_exhibitors', 'total_rooms', 'organizer_contact',
            'metadata', 'created_at', 'updated_at', 'created_by'
        ]
        read_only_fields = ['id', 'total_participants', 'total_exhibitors', 'total_rooms', 'created_at', 'updated_at']


class SessionSerializer(serializers.ModelSerializer):
    """Session serializer"""
    is_live = serializers.ReadOnlyField()
    duration_minutes = serializers.SerializerMethodField()
    room_name = serializers.CharField(source='room.name', read_only=True)
    
    class Meta:
        model = Session
        fields = [
            'id', 'event', 'room', 'room_name', 'title', 'description',
            'start_time', 'end_time', 'speaker_name', 'speaker_title',
            'speaker_bio', 'speaker_photo_url', 'theme', 'status',
            'cover_image_url', 'metadata', 'is_live', 'duration_minutes',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'is_live']
    
    def get_duration_minutes(self, obj):
        return obj.duration_minutes()
    
    def validate(self, data):
        """Validate session times"""
        if data.get('end_time') and data.get('start_time'):
            if data['end_time'] <= data['start_time']:
                raise serializers.ValidationError({
                    'end_time': 'End time must be after start time'
                })
        
        # Check room availability (if updating/creating)
        room = data.get('room')
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        
        if room and start_time and end_time:
            # Get session id if updating
            session_id = self.instance.id if self.instance else None
            
            # Check for overlapping sessions
            overlapping = Session.objects.filter(
                room=room,
                start_time__lt=end_time,
                end_time__gt=start_time,
                status__in=['scheduled', 'live']
            ).exclude(id=session_id)
            
            if overlapping.exists():
                raise serializers.ValidationError({
                    'start_time': 'Room is already booked for this time slot'
                })
        
        return data


class RoomSerializer(serializers.ModelSerializer):
    """Room serializer with sessions"""
    sessions = SessionSerializer(many=True, read_only=True)
    occupancy_percentage = serializers.ReadOnlyField()
    event_name = serializers.CharField(source='event.name', read_only=True)
    
    class Meta:
        model = Room
        fields = [
            'id', 'event', 'event_name', 'name', 'description', 'capacity',
            'location', 'current_participants', 'is_active', 'sessions',
            'occupancy_percentage', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'current_participants', 'created_at', 'updated_at', 'occupancy_percentage']
    
    def validate_capacity(self, value):
        """Validate capacity is positive"""
        if value < 1:
            raise serializers.ValidationError("Capacity must be at least 1")
        return value


class RoomListSerializer(serializers.ModelSerializer):
    """Lightweight room serializer for lists"""
    event_name = serializers.CharField(source='event.name', read_only=True)
    session_count = serializers.SerializerMethodField()
    next_session = serializers.SerializerMethodField()
    
    class Meta:
        model = Room
        fields = [
            'id', 'event', 'event_name', 'name', 'capacity',
            'location', 'current_participants', 'is_active',
            'session_count', 'next_session'
        ]
    
    def get_session_count(self, obj):
        return obj.sessions.filter(status__in=['scheduled', 'live']).count()
    
    def get_next_session(self, obj):
        from django.utils import timezone
        next_session = obj.sessions.filter(
            start_time__gte=timezone.now(),
            status='scheduled'
        ).order_by('start_time').first()
        
        if next_session:
            return {
                'id': str(next_session.id),
                'title': next_session.title,
                'start_time': next_session.start_time,
                'speaker_name': next_session.speaker_name
            }
        return None


class ParticipantSerializer(serializers.ModelSerializer):
    """Participant serializer"""
    user = UserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='user',
        write_only=True
    )
    
    class Meta:
        model = Participant
        fields = [
            'id', 'user', 'user_id', 'event', 'badge_id', 'qr_code_data',
            'is_checked_in', 'checked_in_at', 'allowed_rooms',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class RoomAccessSerializer(serializers.ModelSerializer):
    """Room access/check-in serializer"""
    participant_name = serializers.CharField(source='participant.user.get_full_name', read_only=True)
    room_name = serializers.CharField(source='room.name', read_only=True)
    session_title = serializers.CharField(source='session.title', read_only=True)
    verified_by_name = serializers.CharField(source='verified_by.get_full_name', read_only=True)
    
    class Meta:
        model = RoomAccess
        fields = [
            'id', 'participant', 'participant_name', 'room', 'room_name',
            'session', 'session_title', 'accessed_at', 'verified_by',
            'verified_by_name', 'status', 'denial_reason'
        ]
        read_only_fields = ['id', 'accessed_at']


class UserEventAssignmentSerializer(serializers.ModelSerializer):
    """User event assignment serializer"""
    user = UserSerializer(read_only=True)
    event = EventSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='user',
        write_only=True
    )
    event_id = serializers.PrimaryKeyRelatedField(
        queryset=Event.objects.all(),
        source='event',
        write_only=True
    )
    
    class Meta:
        model = UserEventAssignment
        fields = [
            'id', 'user', 'user_id', 'event', 'event_id', 'role',
            'is_active', 'assigned_at', 'assigned_by'
        ]
        read_only_fields = ['id', 'assigned_at']


class QRVerificationSerializer(serializers.Serializer):
    """Serializer for QR code verification"""
    qr_data = serializers.CharField(required=True)
    room_id = serializers.UUIDField(required=True)
    session_id = serializers.UUIDField(required=False, allow_null=True)
    
    def validate(self, data):
        """Validate QR data and room"""
        from .models import Room
        
        # Check room exists
        try:
            room = Room.objects.get(id=data['room_id'])
            data['room'] = room
        except Room.DoesNotExist:
            raise serializers.ValidationError({'room_id': 'Room not found'})
        
        # Check session if provided
        if data.get('session_id'):
            try:
                session = Session.objects.get(id=data['session_id'])
                data['session'] = session
            except Session.DoesNotExist:
                raise serializers.ValidationError({'session_id': 'Session not found'})
        
        return data