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

app_name = 'events'

urlpatterns = [
    # Router URLs
    path('', include(router.urls)),
    
    # Custom authentication endpoints
    path('auth/register/', views.RegisterView.as_view(), name='register'),
    path('auth/login/', views.CustomLoginView.as_view(), name='login'),
    path('auth/logout/', views.LogoutView.as_view(), name='logout'),
    path('auth/profile/', views.UserProfileView.as_view(), name='profile'),
    path('auth/change-password/', views.ChangePasswordView.as_view(), name='change-password'),
    
    # QR Code endpoints
    path('qr/verify/', views.QRVerificationView.as_view(), name='qr-verify'),
    path('qr/generate/', views.QRGenerateView.as_view(), name='qr-generate'),
    
    # Statistics endpoints
    path('dashboard/stats/', views.DashboardStatsView.as_view(), name='dashboard-stats'),
    
    # Notification endpoints
    path('notifications/', views.NotificationListView.as_view(), name='notification-list'),
    path('notifications/<uuid:pk>/', views.NotificationDetailView.as_view(), name='notification-detail'),
    path('notifications/<uuid:pk>/read/', views.MarkNotificationReadView.as_view(), name='notification-read'),
]