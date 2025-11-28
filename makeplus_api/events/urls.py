"""
Events app URL configuration - COMPLETE VERSION
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

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
    path('auth/register/', views.RegisterView.as_view(), name='register'),
    path('auth/login/', views.CustomLoginView.as_view(), name='login'),
    path('auth/logout/', views.LogoutView.as_view(), name='logout'),
    path('auth/profile/', views.UserProfileView.as_view(), name='profile'),
    path('auth/me/', views.UserProfileView.as_view(), name='user-me'),  # Flutter frontend alias
    path('auth/change-password/', views.ChangePasswordView.as_view(), name='change-password'),
    
    # Event selection endpoints (multi-event support)
    path('auth/select-event/', views.SelectEventView.as_view(), name='select-event'),
    path('auth/switch-event/', views.SwitchEventView.as_view(), name='switch-event'),
    path('auth/my-events/', views.MyEventsView.as_view(), name='my-events'),
    
    # QR Code endpoints
    path('qr/verify/', views.QRVerificationView.as_view(), name='qr-verify'),
    path('qr/generate/', views.QRGenerateView.as_view(), name='qr-generate'),
    
    # Statistics endpoints
    path('dashboard/stats/', views.DashboardStatsView.as_view(), name='dashboard-stats'),
    path('my-room/statistics/', views.MyRoomStatisticsView.as_view(), name='my-room-statistics'),
    
    # Notification endpoints
    path('notifications/', views.NotificationListView.as_view(), name='notification-list'),
    path('notifications/<uuid:pk>/', views.NotificationDetailView.as_view(), name='notification-detail'),
    path('notifications/<uuid:pk>/read/', views.MarkNotificationReadView.as_view(), name='notification-read'),
    
    # Session action aliases for Flutter frontend compatibility
    path('sessions/<uuid:pk>/start/', views.SessionViewSet.as_view({'post': 'mark_live'}), name='session-start'),
    path('sessions/<uuid:pk>/end/', views.SessionViewSet.as_view({'post': 'mark_completed'}), name='session-end'),
]