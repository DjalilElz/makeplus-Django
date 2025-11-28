"""
Authentication Views - JWT Implementation with EMAIL LOGIN
"""

from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.utils import timezone
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .serializers import (
    UserSerializer, UserRegistrationSerializer,
    UserProfileSerializer, ChangePasswordSerializer,
    CustomTokenObtainPairSerializer
)
from .models import UserEventAssignment, Event, Participant
import jwt
from django.conf import settings
from datetime import timedelta


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
            
            # Get all events user is assigned to
            assignments = UserEventAssignment.objects.filter(
                user=authenticated_user,
                is_active=True
            ).select_related('event').order_by('-event__start_date')
            
            # Build available events list
            available_events = []
            for assignment in assignments:
                event = assignment.event
                
                # Get badge info if user is participant/exposant
                badge_info = None
                if assignment.role in ['participant', 'exposant']:
                    try:
                        participant = Participant.objects.get(user=authenticated_user, event=event)
                        badge_info = {
                            'badge_id': participant.badge_id,
                            'qr_code_data': participant.qr_code_data,
                            'is_checked_in': participant.is_checked_in
                        }
                    except Participant.DoesNotExist:
                        pass
                
                available_events.append({
                    'id': str(event.id),
                    'name': event.name,
                    'role': assignment.role,
                    'start_date': event.start_date.isoformat(),
                    'end_date': event.end_date.isoformat(),
                    'status': event.status,
                    'location': event.location,
                    'badge': badge_info
                })
            
            # If user has NO events
            if len(available_events) == 0:
                return Response({
                    'detail': 'User is not assigned to any events'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # If user has only ONE event - auto-select it
            if len(available_events) == 1:
                selected_event = available_events[0]
                
                # Generate tokens with event context
                refresh = RefreshToken.for_user(authenticated_user)
                refresh['event_id'] = selected_event['id']
                refresh['role'] = selected_event['role']
                
                return Response({
                    'access': str(refresh.access_token),
                    'refresh': str(refresh),
                    'user': {
                        'id': authenticated_user.id,
                        'username': authenticated_user.username,
                        'email': authenticated_user.email,
                        'first_name': authenticated_user.first_name,
                        'last_name': authenticated_user.last_name,
                    },
                    'current_event': selected_event,
                    'requires_event_selection': False
                }, status=status.HTTP_200_OK)
            
            # If user has MULTIPLE events - return list and temp token
            else:
                # Create temporary token (valid for 5 minutes, no event context)
                temp_refresh = RefreshToken.for_user(authenticated_user)
                temp_refresh['is_temp']: True
                temp_refresh.set_exp(lifetime=timedelta(minutes=5))
                
                return Response({
                    'user': {
                        'id': authenticated_user.id,
                        'username': authenticated_user.username,
                        'email': authenticated_user.email,
                        'first_name': authenticated_user.first_name,
                        'last_name': authenticated_user.last_name,
                    },
                    'requires_event_selection': True,
                    'available_events': available_events,
                    'temp_token': str(temp_refresh.access_token)
                }, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response({
                'detail': 'No active account found with the given credentials'
            }, status=status.HTTP_401_UNAUTHORIZED)
        except Exception as e:
            print(f"Login error: {str(e)}")
            return Response({
                'detail': f'An error occurred during login'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
        ).select_related('event')
        
        data = serializer.data
        data['assignments'] = [{
            'event_id': str(assignment.event.id),
            'event_name': assignment.event.name,
            'event_location': assignment.event.location,
            'event_start_date': assignment.event.start_date.strftime('%Y-%m-%d'),
            'event_end_date': assignment.event.end_date.strftime('%Y-%m-%d'),
            'event_status': assignment.event.status,
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


class SelectEventView(APIView):
    """
    Select event after login (for users with multiple events)
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Select event to access (after login with multiple events)",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['event_id'],
            properties={
                'event_id': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='UUID of the event to access',
                    example='550e8400-e29b-41d4-a716-446655440000'
                ),
            },
        ),
        responses={
            200: "Event selected successfully, returns full JWT tokens",
            400: "Bad request",
            403: "User not assigned to this event",
            404: "Event not found"
        }
    )
    def post(self, request):
        event_id = request.data.get('event_id')
        
        if not event_id:
            return Response({
                'detail': 'event_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Verify user has access to this event
            assignment = UserEventAssignment.objects.select_related('event').get(
                user=request.user,
                event_id=event_id,
                is_active=True
            )
            
            event = assignment.event
            
            # Get badge info if applicable
            badge_info = None
            if assignment.role in ['participant', 'exposant']:
                try:
                    participant = Participant.objects.get(user=request.user, event=event)
                    badge_info = {
                        'badge_id': participant.badge_id,
                        'qr_code_data': participant.qr_code_data,
                        'is_checked_in': participant.is_checked_in,
                        'checked_in_at': participant.checked_in_at.isoformat() if participant.checked_in_at else None
                    }
                except Participant.DoesNotExist:
                    pass
            
            # Generate new tokens with event context
            refresh = RefreshToken.for_user(request.user)
            refresh['event_id'] = str(event.id)
            refresh['role'] = assignment.role
            
            # Determine permissions based on role
            permissions = []
            if assignment.role == 'organisateur':
                permissions = ['full_control', 'manage_event', 'manage_rooms', 'manage_sessions', 'manage_participants', 'verify_qr']
            elif assignment.role == 'controlleur_des_badges':
                permissions = ['verify_qr', 'grant_access', 'view_participants']
            elif assignment.role == 'participant':
                permissions = ['view_sessions', 'access_rooms', 'check_in']
            elif assignment.role == 'exposant':
                permissions = ['view_sessions', 'access_rooms', 'check_in', 'manage_booth']
            
            return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': {
                    'id': request.user.id,
                    'username': request.user.username,
                    'email': request.user.email,
                    'first_name': request.user.first_name,
                    'last_name': request.user.last_name,
                },
                'current_event': {
                    'id': str(event.id),
                    'name': event.name,
                    'role': assignment.role,
                    'start_date': event.start_date.isoformat(),
                    'end_date': event.end_date.isoformat(),
                    'status': event.status,
                    'location': event.location,
                    'logo_url': event.logo_url,
                    'banner_url': event.banner_url,
                    'badge': badge_info,
                    'permissions': permissions
                }
            }, status=status.HTTP_200_OK)
            
        except UserEventAssignment.DoesNotExist:
            return Response({
                'detail': 'You do not have access to this event'
            }, status=status.HTTP_403_FORBIDDEN)
        except Event.DoesNotExist:
            return Response({
                'detail': 'Event not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f"Event selection error: {str(e)}")
            return Response({
                'detail': 'An error occurred while selecting the event'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SwitchEventView(APIView):
    """
    Switch to a different event (for already logged-in users)
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Switch to a different event without re-login",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['event_id'],
            properties={
                'event_id': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='UUID of the event to switch to',
                    example='550e8400-e29b-41d4-a716-446655440000'
                ),
            },
        ),
        responses={
            200: "Event switched successfully, returns new tokens",
            400: "Bad request",
            403: "User not assigned to this event",
            404: "Event not found"
        }
    )
    def post(self, request):
        # Reuse the same logic as SelectEventView
        return SelectEventView().post(request)


class MyEventsView(APIView):
    """
    Get all events the current user has access to
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Get list of all events user is assigned to",
        responses={
            200: openapi.Response(
                description="List of events",
                examples={
                    "application/json": {
                        "events": [
                            {
                                "id": "550e8400-e29b-41d4-a716-446655440000",
                                "name": "TechSummit Algeria 2025",
                                "role": "participant",
                                "is_current": True,
                                "status": "active",
                                "start_date": "2025-12-19T09:00:00Z",
                                "badge": {"badge_id": "TECH-XXX"}
                            }
                        ],
                        "total": 1
                    }
                }
            )
        }
    )
    def get(self, request):
        try:
            # Get current event_id from token if available
            current_event_id = None
            auth_header = request.META.get('HTTP_AUTHORIZATION', '')
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
                try:
                    decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
                    current_event_id = decoded.get('event_id')
                except:
                    pass
            
            # Get all user's events
            assignments = UserEventAssignment.objects.filter(
                user=request.user,
                is_active=True
            ).select_related('event').order_by('-event__start_date')
            
            events_list = []
            for assignment in assignments:
                event = assignment.event
                
                # Get badge info if applicable
                badge_info = None
                if assignment.role in ['participant', 'exposant']:
                    try:
                        participant = Participant.objects.get(user=request.user, event=event)
                        badge_info = {
                            'badge_id': participant.badge_id,
                            'is_checked_in': participant.is_checked_in
                        }
                    except Participant.DoesNotExist:
                        pass
                
                events_list.append({
                    'id': str(event.id),
                    'name': event.name,
                    'role': assignment.role,
                    'is_current': str(event.id) == current_event_id,
                    'status': event.status,
                    'start_date': event.start_date.isoformat(),
                    'end_date': event.end_date.isoformat(),
                    'location': event.location,
                    'logo_url': event.logo_url,
                    'badge': badge_info
                })
            
            return Response({
                'events': events_list,
                'total': len(events_list)
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            print(f"Error fetching user events: {str(e)}")
            return Response({
                'detail': 'An error occurred while fetching events'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MyRoomStatisticsView(APIView):
    """
    Get statistics for the controller's assigned room
    Only accessible by controllers (controlleur_des_badges)
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Get statistics for the controller's assigned room",
        responses={
            200: openapi.Response(
                description="Room statistics retrieved successfully",
                examples={
                    "application/json": {
                        "room": {
                            "id": "uuid",
                            "name": "Salle Principale",
                            "capacity": 100
                        },
                        "statistics": {
                            "total_scans": 45,
                            "today_scans": 12,
                            "granted": 38,
                            "denied": 7,
                            "unique_participants": 25,
                            "unique_participants_today": 8
                        },
                        "recent_scans": [
                            {
                                "id": "uuid",
                                "participant": {
                                    "id": "uuid",
                                    "name": "John Doe",
                                    "email": "john@example.com",
                                    "badge_id": "BADGE123"
                                },
                                "session": "Innovation et Startups",
                                "status": "granted",
                                "accessed_at": "2025-11-28T14:30:00Z",
                                "verified_by": "controller_username"
                            }
                        ]
                    }
                }
            ),
            403: "Forbidden - User is not a controller or has no room assignment",
            404: "Not found - No event context or room assignment"
        }
    )
    def get(self, request):
        user = request.user
        event_context = getattr(request, 'event_context', None)
        
        if not event_context:
            return Response(
                {'detail': 'No event context found. Please select an event first.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if user is a controller
        assignment = UserEventAssignment.objects.filter(
            user=user,
            event=event_context,
            role='controlleur_des_badges',
            is_active=True
        ).first()
        
        if not assignment:
            return Response(
                {'detail': 'You must be a controller to access room statistics.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get the room assigned to this controller
        from .models import RoomAssignment, RoomAccess
        room_assignment = RoomAssignment.objects.filter(
            user=user,
            event=event_context,
            is_active=True
        ).select_related('room').first()
        
        if not room_assignment:
            return Response(
                {'detail': 'You have no room assigned. Please contact the administrator.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        room = room_assignment.room
        today = timezone.now().date()
        
        # Total scans (all time)
        total_scans = RoomAccess.objects.filter(room=room).count()
        
        # Today's scans
        today_scans = RoomAccess.objects.filter(
            room=room,
            accessed_at__date=today
        ).count()
        
        # Granted vs Denied
        granted_count = RoomAccess.objects.filter(
            room=room,
            status='granted'
        ).count()
        
        denied_count = RoomAccess.objects.filter(
            room=room,
            status='denied'
        ).count()
        
        # Unique participants (all time)
        unique_participants = RoomAccess.objects.filter(
            room=room,
            status='granted'
        ).values('participant').distinct().count()
        
        # Unique participants today
        unique_today = RoomAccess.objects.filter(
            room=room,
            accessed_at__date=today,
            status='granted'
        ).values('participant').distinct().count()
        
        # Recent scans (last 20)
        recent_scans = RoomAccess.objects.filter(
            room=room
        ).select_related('participant__user', 'session', 'verified_by').order_by('-accessed_at')[:20]
        
        recent_data = [{
            'id': str(scan.id),
            'participant': {
                'id': str(scan.participant.id),
                'name': scan.participant.user.get_full_name() or scan.participant.user.username,
                'email': scan.participant.user.email,
                'badge_id': scan.participant.badge_id
            },
            'session': scan.session.title if scan.session else None,
            'status': scan.status,
            'accessed_at': scan.accessed_at.isoformat(),
            'verified_by': scan.verified_by.username if scan.verified_by else None
        } for scan in recent_scans]
        
        return Response({
            'room': {
                'id': str(room.id),
                'name': room.name,
                'capacity': room.capacity
            },
            'statistics': {
                'total_scans': total_scans,
                'today_scans': today_scans,
                'granted': granted_count,
                'denied': denied_count,
                'unique_participants': unique_participants,
                'unique_participants_today': unique_today
            },
            'recent_scans': recent_data
        }, status=status.HTTP_200_OK)


class MyAteliersView(APIView):
    """
    Get all paid ateliers for the authenticated participant
    Returns complete atelier information with payment status
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get participant's paid ateliers with full details"""
        from .models import SessionAccess, Participant
        
        user = request.user
        
        # Get event context from JWT token
        event_context = getattr(request, 'event_context', None)
        if not event_context:
            return Response(
                {'detail': 'No event context found. Please select an event first.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            # Get participant profile
            participant = Participant.objects.get(
                user=user,
                event=event_context
            )
        except Participant.DoesNotExist:
            return Response(
                {'detail': 'Participant profile not found for this event.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get all session access records for this participant (paid ateliers)
        session_accesses = SessionAccess.objects.filter(
            participant=participant,
            session__session_type='atelier',
            session__is_paid=True
        ).select_related(
            'session',
            'session__room',
            'session__event'
        ).order_by('-created_at')
        
        # Build response with full atelier details
        ateliers_data = []
        total_paid = 0
        total_pending = 0
        
        for access in session_accesses:
            session = access.session
            
            atelier_data = {
                'id': str(access.id),
                'session_id': str(session.id),
                'title': session.title,
                'description': session.description,
                'speaker_name': session.speaker_name,
                'speaker_title': session.speaker_title,
                'speaker_bio': session.speaker_bio,
                'speaker_photo_url': session.speaker_photo_url,
                'theme': session.theme,
                'room': {
                    'id': str(session.room.id),
                    'name': session.room.name,
                    'capacity': session.room.capacity
                } if session.room else None,
                'start_time': session.start_time.isoformat(),
                'end_time': session.end_time.isoformat(),
                'price': float(session.price),
                'payment_status': access.payment_status,
                'has_access': access.has_access,
                'amount_paid': float(access.amount_paid),
                'paid_at': access.paid_at.isoformat() if access.paid_at else None,
                'registered_at': access.created_at.isoformat()
            }
            
            ateliers_data.append(atelier_data)
            
            # Calculate totals
            if access.payment_status == 'paid':
                total_paid += float(access.amount_paid)
            elif access.payment_status == 'pending':
                total_pending += float(session.price)
        
        # Build summary
        paid_count = sum(1 for a in ateliers_data if a['payment_status'] == 'paid')
        pending_count = sum(1 for a in ateliers_data if a['payment_status'] == 'pending')
        
        response_data = {
            'participant': {
                'id': str(participant.id),
                'name': user.get_full_name() or user.username,
                'email': user.email,
                'badge_id': participant.badge_id
            },
            'summary': {
                'total_ateliers': len(ateliers_data),
                'paid_count': paid_count,
                'pending_count': pending_count,
                'total_paid': total_paid,
                'total_pending': total_pending,
                'total_amount': total_paid + total_pending
            },
            'ateliers': ateliers_data
        }
        
        return Response(response_data, status=status.HTTP_200_OK)