"""
ePoster API URL Configuration
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views_eposter

# Create router
router = DefaultRouter()
router.register(r'submissions', views_eposter.EPosterSubmissionViewSet, basename='eposter-submission')
router.register(r'validations', views_eposter.EPosterValidationViewSet, basename='eposter-validation')
router.register(r'committee', views_eposter.EPosterCommitteeMemberViewSet, basename='eposter-committee')
router.register(r'email-templates', views_eposter.EPosterEmailTemplateViewSet, basename='eposter-email-template')

urlpatterns = [
    # ViewSet routes
    path('', include(router.urls)),
    
    # Public submission endpoint
    path('<uuid:event_id>/submit/', views_eposter.public_eposter_submit, name='eposter-public-submit'),
    
    # Real-time validation status
    path('submissions/<uuid:submission_id>/realtime/', views_eposter.realtime_validation_status, name='eposter-realtime-status'),
]
