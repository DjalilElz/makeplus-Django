"""
Authentication Views - JWT Implementation with EMAIL LOGIN
"""

from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .serializers import (
    UserSerializer, UserRegistrationSerializer,
    UserProfileSerializer, ChangePasswordSerializer,
    CustomTokenObtainPairSerializer
)
from .models import UserEventAssignment


class CustomLoginView(APIView):
    """
    Custom login view - USES EMAIL instead of username
    """
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        operation_description="Login with email and password",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['email', 'password'],
            properties={
                'email': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='User email address',
                    example='organizer@makeplus.com'
                ),
                'password': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format=openapi.FORMAT_PASSWORD,
                    description='User password',
                    example='test123'
                ),
            },
        ),
        responses={
            200: openapi.Response(
                description="Login successful",
                examples={
                    "application/json": {
                        "tokens": {
                            "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                            "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
                        },
                        "user": {
                            "id": 1,
                            "username": "organizer",
                            "email": "organizer@makeplus.com",
                            "first_name": "Ahmed",
                            "last_name": "Benali"
                        },
                        "role": "organizer",
                        "event": {
                            "id": "123e4567-e89b-12d3-a456-426614174000",
                            "name": "MakePlus 2025"
                        }
                    }
                }
            ),
            400: "Bad request - Missing email or password",
            401: "Unauthorized - Invalid credentials"
        }
    )
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        
        if not email or not password:
            return Response({
                'detail': 'Email and password are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Get user by email
            user = User.objects.get(email=email)
            
            # Authenticate using username (Django internal requirement)
            authenticated_user = authenticate(
                request,
                username=user.username,
                password=password
            )
            
            if authenticated_user is None:
                return Response({
                    'detail': 'Invalid credentials'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            if not authenticated_user.is_active:
                return Response({
                    'detail': 'Account is inactive'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            # Get user's role
            assignment = UserEventAssignment.objects.filter(
                user=authenticated_user,
                is_active=True
            ).select_related('event').first()
            
            role = assignment.role if assignment else 'participant'
            event = assignment.event if assignment else None
            
            # Generate tokens
            refresh = RefreshToken.for_user(authenticated_user)
            
            return Response({
                'tokens': {
                    'access': str(refresh.access_token),
                    'refresh': str(refresh),
                },
                'user': {
                    'id': authenticated_user.id,
                    'username': authenticated_user.username,
                    'email': authenticated_user.email,
                    'first_name': authenticated_user.first_name,
                    'last_name': authenticated_user.last_name,
                    'is_active': authenticated_user.is_active,
                },
                'role': role,
                'event': {
                    'id': str(event.id),
                    'name': event.name,
                    'start_date': event.start_date.isoformat() if event.start_date else None,
                    'end_date': event.end_date.isoformat() if event.end_date else None,
                    'location': event.location,
                } if event else None
            }, status=status.HTTP_200_OK)
            
        except User.DoesNotExist:
            return Response({
                'detail': 'No active account found with the given credentials'
            }, status=status.HTTP_401_UNAUTHORIZED)


class RegisterView(APIView):
    """
    User registration endpoint - USES EMAIL
    """
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        operation_description="Register new user with email",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['email', 'password', 'password2'],
            properties={
                'email': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format=openapi.FORMAT_EMAIL,
                    description='User email address',
                    example='newuser@makeplus.com'
                ),
                'password': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format=openapi.FORMAT_PASSWORD,
                    description='Password (min 6 characters)',
                    example='password123'
                ),
                'password2': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format=openapi.FORMAT_PASSWORD,
                    description='Confirm password',
                    example='password123'
                ),
                'first_name': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='First name',
                    example='John'
                ),
                'last_name': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Last name',
                    example='Doe'
                ),
            },
        ),
        responses={
            201: "User created successfully",
            400: "Bad request - Validation error"
        }
    )
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        password2 = request.data.get('password2')
        first_name = request.data.get('first_name', '')
        last_name = request.data.get('last_name', '')
        
        # Validation
        if not email or not password:
            return Response({
                'detail': 'Email and password are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if password != password2:
            return Response({
                'detail': 'Passwords do not match'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if len(password) < 6:
            return Response({
                'detail': 'Password must be at least 6 characters'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if email exists
        if User.objects.filter(email=email).exists():
            return Response({
                'detail': 'User with this email already exists'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Generate username from email
        username = email.split('@')[0]
        base_username = username
        counter = 1
        
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1
        
        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        
        # Generate tokens
        refresh = RefreshToken.for_user(user)
        
        # Get user role from assignments (default to 'participant')
        role = 'participant'
        assignment = UserEventAssignment.objects.filter(
            user=user,
            is_active=True
        ).first()
        if assignment:
            role = assignment.role
        
        return Response({
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
            },
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            },
            'role': role,
            'message': 'User registered successfully'
        }, status=status.HTTP_201_CREATED)


class LogoutView(APIView):
    """
    Logout endpoint - blacklist refresh token
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Logout and blacklist refresh token",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['refresh_token'],
            properties={
                'refresh_token': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Refresh token to blacklist'
                ),
            },
        ),
        responses={
            205: "Successfully logged out",
            400: "Bad request"
        }
    )
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh_token')
            if not refresh_token:
                return Response(
                    {'error': 'Refresh token is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            return Response({
                'message': 'Successfully logged out'
            }, status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    Get and update user profile
    GET: Retrieve current user profile
    PUT/PATCH: Update user profile
    """
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        return self.request.user
    
    def retrieve(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = self.get_serializer(user)
        
        # Get user role and events
        assignments = UserEventAssignment.objects.filter(
            user=user,
            is_active=True
        )
        
        data = serializer.data
        data['assignments'] = [{
            'event_id': str(assignment.event.id),
            'event_name': assignment.event.name,
            'role': assignment.role,
            'assigned_at': assignment.assigned_at
        } for assignment in assignments]
        
        return Response(data)


class ChangePasswordView(APIView):
    """
    Change user password
    POST: Change password with old password verification
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        request_body=ChangePasswordSerializer,
        responses={
            200: "Password changed successfully",
            400: "Bad request - Validation error"
        }
    )
    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            
            return Response({
                'message': 'Password changed successfully'
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class QRVerificationView(APIView):
    """
    Verify QR code for participant access
    POST: Verify QR code and grant/deny access
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['qr_data', 'room_id'],
            properties={
                'qr_data': openapi.Schema(type=openapi.TYPE_STRING),
                'room_id': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_UUID),
                'session_id': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_UUID),
            },
        )
    )
    def post(self, request):
        from .serializers import QRVerificationSerializer
        from .models import Participant, RoomAccess
        
        serializer = QRVerificationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        qr_data = serializer.validated_data['qr_data']
        room = serializer.validated_data['room']
        session = serializer.validated_data.get('session')
        
        try:
            # Find participant by QR code
            participant = Participant.objects.get(qr_code_data=qr_data)
            
            # Check if participant is allowed in this room
            if room.id not in participant.allowed_rooms and participant.allowed_rooms:
                access = RoomAccess.objects.create(
                    participant=participant,
                    room=room,
                    session=session,
                    verified_by=request.user,
                    status='denied',
                    denial_reason='Not authorized for this room'
                )
                
                return Response({
                    'status': 'denied',
                    'message': 'Participant not authorized for this room',
                    'participant': {
                        'id': str(participant.id),
                        'name': participant.user.get_full_name(),
                        'badge_id': participant.badge_id
                    }
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Grant access
            access = RoomAccess.objects.create(
                participant=participant,
                room=room,
                session=session,
                verified_by=request.user,
                status='granted'
            )
            
            return Response({
                'status': 'granted',
                'message': 'Access granted successfully',
                'participant': {
                    'id': str(participant.id),
                    'name': participant.user.get_full_name(),
                    'email': participant.user.email,
                    'badge_id': participant.badge_id,
                    'photo_url': getattr(participant.user.profile, 'photo_url', None) if hasattr(participant.user, 'profile') else None
                },
                'access': {
                    'id': str(access.id),
                    'accessed_at': access.accessed_at,
                    'room_name': room.name
                }
            }, status=status.HTTP_200_OK)
            
        except Participant.DoesNotExist:
            return Response({
                'status': 'invalid',
                'message': 'Invalid QR code or participant not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class QRGenerateView(APIView):
    """
    Generate QR code data for participant
    POST: Generate unique QR code data
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['participant_id'],
            properties={
                'participant_id': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format=openapi.FORMAT_UUID,
                    description='Participant ID'
                ),
            },
        )
    )
    def post(self, request):
        import uuid
        import hashlib
        
        participant_id = request.data.get('participant_id')
        if not participant_id:
            return Response(
                {'error': 'participant_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from .models import Participant
            participant = Participant.objects.get(id=participant_id)
            
            # Generate unique QR data if not exists
            if not participant.qr_code_data:
                unique_string = f"{participant.id}_{participant.user.email}_{uuid.uuid4()}"
                qr_data = hashlib.sha256(unique_string.encode()).hexdigest()
                participant.qr_code_data = qr_data
                participant.save()
            
            return Response({
                'qr_code_data': participant.qr_code_data,
                'badge_id': participant.badge_id,
                'participant': {
                    'id': str(participant.id),
                    'name': participant.user.get_full_name(),
                    'email': participant.user.email
                }
            }, status=status.HTTP_200_OK)
            
        except Participant.DoesNotExist:
            return Response(
                {'error': 'Participant not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class DashboardStatsView(APIView):
    """
    Get dashboard statistics based on user role
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'event_id',
                openapi.IN_QUERY,
                description="Event ID to get stats for",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_UUID
            )
        ]
    )
    def get(self, request):
        from .models import Event, Room, Session, Participant, RoomAccess
        from django.db.models import Count, Q
        from django.utils import timezone
        
        user = request.user
        event_id = request.query_params.get('event_id')
        
        # Get user's events
        user_assignments = UserEventAssignment.objects.filter(
            user=user,
            is_active=True
        )
        
        if event_id:
            user_assignments = user_assignments.filter(event_id=event_id)
        
        if not user_assignments.exists():
            return Response({
                'message': 'No events assigned to this user'
            }, status=status.HTTP_200_OK)
        
        assignment = user_assignments.first()
        event = assignment.event
        role = assignment.role
        
        stats = {
            'event': {
                'id': str(event.id),
                'name': event.name,
                'status': event.status
            },
            'role': role
        }
        
        # Role-specific statistics
        if role == 'organizer':
            stats.update({
                'total_rooms': event.rooms.filter(is_active=True).count(),
                'total_sessions': event.sessions.count(),
                'live_sessions': event.sessions.filter(status='live').count(),
                'total_participants': Participant.objects.filter(event=event).count(),
                'checked_in_participants': Participant.objects.filter(
                    event=event,
                    is_checked_in=True
                ).count(),
                'total_access_logs': RoomAccess.objects.filter(
                    room__event=event
                ).count()
            })
        
        elif role == 'controller':
            stats.update({
                'scans_today': RoomAccess.objects.filter(
                    verified_by=user,
                    accessed_at__date=timezone.now().date()
                ).count(),
                'granted_access': RoomAccess.objects.filter(
                    verified_by=user,
                    status='granted'
                ).count(),
                'denied_access': RoomAccess.objects.filter(
                    verified_by=user,
                    status='denied'
                ).count()
            })
        
        elif role == 'participant':
            try:
                participant = Participant.objects.get(user=user, event=event)
                stats.update({
                    'is_checked_in': participant.is_checked_in,
                    'sessions_attended': RoomAccess.objects.filter(
                        participant=participant,
                        status='granted'
                    ).count(),
                    'favorite_exhibitors': 0  # TODO: Implement favorites
                })
            except Participant.DoesNotExist:
                pass
        
        return Response(stats, status=status.HTTP_200_OK)


class NotificationListView(generics.ListAPIView):
    """
    List notifications for current user
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # TODO: Implement notification model and logic
        return Response({
            'notifications': [],
            'unread_count': 0
        }, status=status.HTTP_200_OK)


class NotificationDetailView(generics.RetrieveAPIView):
    """
    Get notification detail
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, pk):
        # TODO: Implement notification model and logic
        return Response({
            'message': 'Notification not found'
        }, status=status.HTTP_404_NOT_FOUND)


class MarkNotificationReadView(APIView):
    """
    Mark notification as read
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, pk):
        # TODO: Implement notification model and logic
        return Response({
            'message': 'Notification marked as read'
        }, status=status.HTTP_200_OK)