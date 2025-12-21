"""
URL Configuration for Dashboard
"""

from django.urls import path
from . import views
from . import views_email

app_name = 'dashboard'

urlpatterns = [
    # Authentication
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Dashboard Home
    path('', views.dashboard_home, name='home'),
    
    # Event Management
    path('events/<uuid:event_id>/', views.event_detail, name='event_detail'),
    path('events/<uuid:event_id>/edit/', views.event_edit, name='event_edit'),
    path('events/<uuid:event_id>/delete/', views.event_delete, name='event_delete'),
    
    # Multi-Step Event Creation
    path('events/create/step1/', views.event_create_step1, name='event_create_step1'),
    path('events/create/step2/', views.event_create_step2, name='event_create_step2'),
    path('events/create/step3/', views.event_create_step3, name='event_create_step3'),
    path('events/create/step4/', views.event_create_step4, name='event_create_step4'),
    
    # User Management
    path('users/', views.user_list, name='user_list'),
    path('users/create/', views.user_create, name='user_create'),
    path('users/<int:user_id>/', views.user_detail, name='user_detail'),
    path('users/<int:user_id>/delete/', views.user_delete, name='user_delete'),
    path('users/<int:user_id>/qr-code/download/', views.download_qr_code, name='download_qr_code'),
    path('assignments/<int:assignment_id>/change-role/', views.user_change_role, name='user_change_role'),
    
    # Event-specific User Management
    path('events/<uuid:event_id>/users/', views.event_users, name='event_users'),
    path('events/<uuid:event_id>/users/<int:user_id>/delete/', views.event_user_delete, name='event_user_delete'),
    
    # Caisse Management
    path('caisses/', views.caisse_list, name='caisse_list'),
    path('caisses/create/', views.caisse_create, name='caisse_create'),
    path('caisses/<int:caisse_id>/', views.caisse_detail, name='caisse_detail'),
    path('caisses/<int:caisse_id>/edit/', views.caisse_edit, name='caisse_edit'),
    path('caisses/<int:caisse_id>/delete/', views.caisse_delete, name='caisse_delete'),
    
    # Payable Items Management
    path('events/<uuid:event_id>/payable-items/', views.payable_items_list, name='payable_items_list'),
    path('events/<uuid:event_id>/payable-items/create/', views.payable_item_create, name='payable_item_create'),
    path('payable-items/<int:item_id>/edit/', views.payable_item_edit, name='payable_item_edit'),
    path('payable-items/<int:item_id>/delete/', views.payable_item_delete, name='payable_item_delete'),
    
    # Room Management
    path('events/<uuid:event_id>/rooms/create/', views.room_create, name='room_create'),
    path('rooms/<uuid:room_id>/edit/', views.room_edit, name='room_edit'),
    path('rooms/<uuid:room_id>/delete/', views.room_delete, name='room_delete'),
    
    # Session Management
    path('events/<uuid:event_id>/sessions/create/', views.session_create, name='session_create'),
    path('sessions/<uuid:session_id>/edit/', views.session_edit, name='session_edit'),
    path('sessions/<uuid:session_id>/delete/', views.session_delete, name='session_delete'),
    
    # Email Templates (Global)
    path('email-templates/', views_email.email_template_list, name='email_template_list'),
    path('email-templates/create/', views_email.email_template_create, name='email_template_create'),
    path('email-templates/<int:template_id>/edit/', views_email.email_template_edit, name='email_template_edit'),
    path('email-templates/<int:template_id>/delete/', views_email.email_template_delete, name='email_template_delete'),
    
    # Event Email Templates
    path('events/<uuid:event_id>/email-templates/', views_email.event_email_templates, name='event_email_templates'),
    path('events/<uuid:event_id>/email-templates/create/', views_email.event_email_template_create, name='event_email_template_create'),
    path('events/<uuid:event_id>/email-templates/<int:template_id>/edit/', views_email.event_email_template_edit, name='event_email_template_edit'),
    path('events/<uuid:event_id>/email-templates/<int:template_id>/delete/', views_email.event_email_template_delete, name='event_email_template_delete'),
    
    # Send Emails
    path('events/<uuid:event_id>/email-templates/<int:template_id>/send/', views_email.send_event_email, name='send_event_email'),
    path('events/<uuid:event_id>/email-logs/', views_email.event_email_logs, name='event_email_logs'),
]
