"""
Events app URL configuration - COMPLETE VERSION
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import views_registration
from . import auth_views
from . import api_views  # REST API views for mobile app
from . import signup_views  # Sign up views
from . import form_validation_views  # Form validation views

# Create router and register viewsets
router = DefaultRouter()
router.register(r'events', views.EventViewSet, basename='event')
router.register(r'rooms', views.RoomViewSet, basename='room')
router.register(r'sessions', views.SessionViewSet, basename='session')
router.register(r'participants', views.ParticipantViewSet, basename='participant')
router.register(r'room-access', views.RoomAccessViewSet, basename='room-access')
router.register(r'user-assignments', views.UserEventAssignmentViewSet, basename='user-assignment')
router.register(r'session-access', views.SessionAccessViewSet, basename='session-access')
router.register(r'annonces', views.AnnonceViewSet, basename='annonce')
router.register(r'session-questions', views.SessionQuestionViewSet, basename='session-question')
router.register(r'room-assignments', views.RoomAssignmentViewSet, basename='room-assignment')
router.register(r'exposant-scans', views.ExposantScanViewSet, basename='exposant-scan')

app_name = 'events'

urlpatterns = [
    # Router URLs
    path('', include(router.urls)),
    
    # Custom authentication endpoints
    path('auth/register/', auth_views.RegisterView.as_view(), name='register'),
    path('auth/login/', auth_views.CustomLoginView.as_view(), name='login'),
    path('auth/logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('auth/request-code/', auth_views.RequestLoginCodeView.as_view(), name='request_login_code'),
    
    # Sign up endpoints (mobile app)
    path('auth/signup/request/', signup_views.SignUpRequestView.as_view(), name='signup_request'),
    path('auth/signup/verify/', signup_views.SignUpVerifyView.as_view(), name='signup_verify'),
    path('auth/signup/resend/', signup_views.SignUpResendView.as_view(), name='signup_resend'),
    
    # Form validation endpoints
    path('forms/validate/', form_validation_views.FormValidationVerifyView.as_view(), name='form_validate'),
    path('forms/validate/resend/', form_validation_views.FormValidationResendView.as_view(), name='form_validate_resend'),
    
    path('auth/me/', api_views.UserProfileAPIView.as_view(), name='user-me'),  # REST API for mobile
    path('auth/profile/', auth_views.UserProfileView.as_view(), name='profile'),  # Template view for web
    path('auth/change-password/', auth_views.ChangePasswordView.as_view(), name='change-password'),
    
    # Event selection endpoints (multi-event support)
    path('auth/select-event/', views.SelectEventView.as_view(), name='select-event'),
    path('auth/switch-event/', views.SwitchEventView.as_view(), name='switch-event'),
    path('auth/my-events/', views.MyEventsView.as_view(), name='my-events'),
    
    # QR Code endpoints
    path('qr/verify/', views.QRVerificationView.as_view(), name='qr-verify'),
    path('qr/generate/', views.QRGenerateView.as_view(), name='qr-generate'),
    
    # Statistics endpoints (REST API for mobile)
    path('dashboard/stats/', api_views.DashboardStatsAPIView.as_view(), name='dashboard-stats'),
    path('my-room/statistics/', api_views.MyRoomStatisticsAPIView.as_view(), name='my-room-statistics'),
    
    # User endpoints (REST API for mobile)
    path('my-events/', api_views.MyEventsAPIView.as_view(), name='my-events'),
    path('my-ateliers/', api_views.MyAteliersAPIView.as_view(), name='my-ateliers'),
    
    # Notification endpoints
    path('notifications/', views.NotificationListView.as_view(), name='notification-list'),
    path('notifications/<uuid:pk>/', views.NotificationDetailView.as_view(), name='notification-detail'),
    path('notifications/<uuid:pk>/read/', views.MarkNotificationReadView.as_view(), name='notification-read'),
    
    # Session action aliases for Flutter frontend compatibility
    path('sessions/<uuid:pk>/start/', views.SessionViewSet.as_view({'post': 'mark_live'}), name='session-start'),
    path('sessions/<uuid:pk>/end/', views.SessionViewSet.as_view({'post': 'mark_completed'}), name='session-end'),
    
    # Public Event Registration URLs
    path('events/<uuid:event_id>/register/', views_registration.event_registration_page, name='event_registration'),
    path('events/<uuid:event_id>/register/submit/', views_registration.event_registration_submit, name='event_registration_submit'),
    path('registration/success/<uuid:registration_id>/', views_registration.registration_success, name='registration_success'),
    
    # API endpoint for event registration (JSON)
    path('api/events/<uuid:event_id>/register/', views_registration.event_registration_api, name='event_registration_api'),
]