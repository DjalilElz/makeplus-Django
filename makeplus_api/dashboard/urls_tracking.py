"""
URL configuration for tracking email opens, clicks, and form analytics.
Handles tracking pixel and click tracking for email campaigns.
"""
from django.urls import path
from . import views_tracking

app_name = 'tracking'

urlpatterns = [
    # Email open tracking (tracking pixel)
    path('email/open/<str:token>/', views_tracking.track_email_open, name='track_email_open'),
    
    # Link click tracking
    path('email/click/<str:link_token>/<str:recipient_token>/', views_tracking.track_link_click, name='track_link_click'),
    
    # Unsubscribe
    path('email/unsubscribe/<str:token>/', views_tracking.unsubscribe_recipient, name='unsubscribe'),
    
    # Form view tracking
    path('form/view/<uuid:form_id>/', views_tracking.track_form_view, name='track_form_view'),
    
    # Form field interaction tracking
    path('form/interaction/<uuid:form_id>/', views_tracking.track_form_interaction, name='track_form_interaction'),
]
