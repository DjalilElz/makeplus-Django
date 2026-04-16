# events/serializers.py - DRF Serializers

from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import (
    Event, Room, Session, Participant, RoomAccess, UserEventAssignment,
    SessionAccess, Annonce, SessionQuestion, RoomAssignment, ExposantScan
)


class UserSerializer(serializers.ModelSerializer):
    """User serializer - username is internal only"""
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name']
        read_only_fields = ['id']


class EventSerializer(serializers.ModelSerializer):
    """Event serializer"""
    created_by = UserSerializer(read_only=True)
    president = UserSerializer(read_only=True)
    dynamic_status = serializers.SerializerMethodField()
    
    def get_dynamic_status(self, obj):
        """Get dynamic status based on dates"""
        return obj.get_dynamic_status()
    
    class Meta:
        model = Event
        fields = [
            'id', 'name', 'description', 'start_date', 'end_date',
            'location', 'location_url', 'location_details', 'logo', 'banner',
            'status', 'dynamic_status', 'settings', 'themes', 'total_participants',
            'total_exhibitors', 'total_rooms', 'organizer_contact',
            'metadata', 'programme_file', 'guide_file', 'president',
            'created_at', 'updated_at', 'created_by'
        ]
        read_only_fields = ['id', 'total_participants', 'total_exhibitors', 'total_rooms', 'created_at', 'updated_at']


class RoomSerializer(serializers.ModelSerializer):
    """Room serializer"""
    event_name = serializers.CharField(source='event.name', read_only=True)
    
    class Meta:
        model = Room
        fields = [
            'id', 'event', 'event_name', 'name', 'capacity',
            'location', 'current_participants', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'current_participants', 'created_at', 'updated_at']


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
            'speaker_bio', 'speaker_photo_url', 'theme', 'session_type',
            'status', 'is_paid', 'price', 'youtube_live_url',
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
        return data


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
            'is_checked_in', 'checked_in_at', 'allowed_rooms', 'plan_file',
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


# ============================================
# Authentication Serializers - Added for JWT
# ============================================

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom token serializer that accepts email instead of username
    and includes user data and role
    """
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove username field requirement
        self.fields.pop('username', None)
    
    def validate(self, attrs):
        # Get email and password from attrs
        email = attrs.get('email')
        password = attrs.get('password')
        
        if not email or not password:
            raise serializers.ValidationError('Email and password are required')
        
        # Find user by email
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError('No active account found with the given credentials')
        
        # Check if user is active
        if not user.is_active:
            raise serializers.ValidationError('User account is disabled')
        
        # Verify password
        if not user.check_password(password):
            raise serializers.ValidationError('Invalid credentials')
        
        # Generate tokens manually
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)
        
        data = {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }
        
        # Add custom claims
        data['user'] = {
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
        }
        
        # Get user role from active assignments
        assignment = UserEventAssignment.objects.filter(
            user=user,
            is_active=True
        ).first()
        
        if assignment:
            data['role'] = assignment.role
            data['event'] = {
                'id': str(assignment.event.id),
                'name': assignment.event.name,
                'start_date': assignment.event.start_date.isoformat() if assignment.event.start_date else None,
                'end_date': assignment.event.end_date.isoformat() if assignment.event.end_date else None,
                'location': assignment.event.location,
                'status': assignment.event.status,
            }
        else:
            data['role'] = 'participant'  # Default role
            data['event'] = None
        
        return data


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    User registration serializer with password confirmation
    Username is auto-generated from email
    """
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password2 = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    email = serializers.EmailField(required=True)
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    
    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'password', 'password2')
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({
                "password": "Password fields didn't match."
            })
        
        # Check if email already exists
        if User.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError({
                "email": "A user with this email already exists."
            })
        
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password2')
        
        # Auto-generate username from email
        email = validated_data['email']
        username = email  # Use email as username
        
        # If username exists, append a number
        counter = 1
        original_username = username
        while User.objects.filter(username=username).exists():
            username = f"{original_username}{counter}"
            counter += 1
        
        user = User.objects.create_user(
            username=username,
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            password=validated_data['password']
        )
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    """
    User profile serializer for viewing and updating profile
    """
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'full_name')
        read_only_fields = ('id',)
    
    def get_full_name(self, obj):
        return obj.get_full_name() or obj.email


class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer for password change endpoint
    """
    old_password = serializers.CharField(required=True, style={'input_type': 'password'})
    new_password = serializers.CharField(
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    new_password2 = serializers.CharField(required=True, style={'input_type': 'password'})
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError({
                "new_password": "Password fields didn't match."
            })
        return attrs
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value

# =================================================================
# NEW MODEL SERIALIZERS - Added for restructure
# =================================================================

class SessionAccessSerializer(serializers.ModelSerializer):
    """SessionAccess serializer for paid ateliers"""
    participant_name = serializers.CharField(source='participant.user.get_full_name', read_only=True)
    session_title = serializers.CharField(source='session.title', read_only=True)
    session_type = serializers.CharField(source='session.session_type', read_only=True)
    
    class Meta:
        model = SessionAccess
        fields = [
            'id', 'participant', 'participant_name', 'session', 'session_title',
            'session_type', 'has_access', 'payment_status', 'paid_at',
            'amount_paid', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class AnnonceSerializer(serializers.ModelSerializer):
    """Annonce serializer for event announcements"""
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    event_name = serializers.CharField(source='event.name', read_only=True)
    
    class Meta:
        model = Annonce
        fields = [
            'id', 'event', 'event_name', 'title', 'description', 'target',
            'created_by', 'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']


class SessionQuestionSerializer(serializers.ModelSerializer):
    """SessionQuestion serializer for participant questions"""
    participant_name = serializers.CharField(source='participant.user.get_full_name', read_only=True)
    session_title = serializers.CharField(source='session.title', read_only=True)
    answered_by_name = serializers.CharField(source='answered_by.get_full_name', read_only=True)
    
    class Meta:
        model = SessionQuestion
        fields = [
            'id', 'session', 'session_title', 'participant', 'participant_name',
            'question_text', 'is_answered', 'answer_text', 'answered_by',
            'answered_by_name', 'asked_at', 'answered_at'
        ]
        read_only_fields = ['id', 'asked_at', 'answered_at']


class RoomAssignmentSerializer(serializers.ModelSerializer):
    """RoomAssignment serializer for staff assignments"""
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    room_name = serializers.CharField(source='room.name', read_only=True)
    event_name = serializers.CharField(source='event.name', read_only=True)
    assigned_by_name = serializers.CharField(source='assigned_by.get_full_name', read_only=True)
    
    class Meta:
        model = RoomAssignment
        fields = [
            'id', 'user', 'user_name', 'room', 'room_name', 'event', 'event_name',
            'role', 'start_time', 'end_time', 'is_active', 'assigned_at',
            'assigned_by', 'assigned_by_name'
        ]
        read_only_fields = ['id', 'assigned_at']
    
    def validate(self, data):
        """Validate that end_time is after start_time"""
        if data.get('end_time') and data.get('start_time'):
            if data['end_time'] <= data['start_time']:
                raise serializers.ValidationError({
                    'end_time': 'End time must be after start time'
                })
        return data


class ExposantScanSerializer(serializers.ModelSerializer):
    """ExposantScan serializer for tracking exposant scans"""
    exposant_name = serializers.CharField(source='exposant.user.get_full_name', read_only=True)
    scanned_participant_name = serializers.CharField(source='scanned_participant.user.get_full_name', read_only=True)
    scanned_participant_email = serializers.CharField(source='scanned_participant.user.email', read_only=True)
    event_name = serializers.CharField(source='event.name', read_only=True)
    
    class Meta:
        model = ExposantScan
        fields = [
            'id', 'exposant', 'exposant_name', 'scanned_participant',
            'scanned_participant_name', 'scanned_participant_email',
            'event', 'event_name', 'scanned_at', 'notes'
        ]
        read_only_fields = ['id', 'scanned_at']



# Custom view for email-based token authentication
from rest_framework_simplejwt.views import TokenObtainPairView

class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom token view that uses email instead of username
    """
    serializer_class = CustomTokenObtainPairSerializer
