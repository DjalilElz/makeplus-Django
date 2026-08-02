"""
URL Configuration for Dashboard
"""

from django.urls import path
from . import views
from . import views_email
from . import views_stats
from . import views_eposter_dashboard
from . import views_eposter_management
from . import views_eposter_final
from . import views_final_communications
from . import views_blocs
from . import views_event_owner
from . import views_questions

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
    
    # Event Registrations
    path('events/<uuid:event_id>/registrations/', views.event_registrations, name='event_registrations'),
    path('registrations/<uuid:registration_id>/approve/', views.approve_registration, name='approve_registration'),
    path('registrations/<uuid:registration_id>/delete/', views.delete_registration, name='delete_registration'),
    
    # Caisse Management
    path('caisses/', views.caisse_list, name='caisse_list'),
    path('caisses/create/', views.caisse_create, name='caisse_create'),
    path('caisses/<int:caisse_id>/', views.caisse_detail, name='caisse_detail'),
    path('caisses/<int:caisse_id>/edit/', views.caisse_edit, name='caisse_edit'),
    path('caisses/<int:caisse_id>/delete/', views.caisse_delete, name='caisse_delete'),
    
    # Payable Items Management
    path('events/<uuid:event_id>/payable-items/', views.payable_items_list, name='payable_items_list'),
    path('events/<uuid:event_id>/payable-items/create/', views.payable_item_create, name='payable_item_create'),
    path('events/<uuid:event_id>/payable-items/sync/', views.sync_paid_sessions_ajax, name='sync_paid_sessions_ajax'),
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

    # Session Q&A (anonymous — see views_questions.py)
    path('my-sessions/', views_questions.my_room_sessions, name='my_room_sessions'),
    path('my-sessions/questions/', views_questions.combined_session_questions, name='combined_session_questions'),
    path('sessions/<uuid:session_id>/questions/', views_questions.session_questions, name='session_questions'),
    path('questions/<int:question_id>/answer/', views_questions.session_question_answer, name='session_question_answer'),
    
    # Email Templates (Global) - REMOVED: Redundant with Campaigns functionality
    # path('email-templates/', views_email.email_template_list, name='email_template_list'),
    # path('email-templates/create/', views_email.email_template_create, name='email_template_create'),
    # path('email-templates/<int:template_id>/edit/', views_email.email_template_edit, name='email_template_edit'),
    # path('email-templates/<int:template_id>/delete/', views_email.email_template_delete, name='email_template_delete'),
    # path('email-templates/<int:template_id>/test/', views_email.email_template_test, name='email_template_test'),
    # path('email-templates/<int:template_id>/send/', views_email.email_template_send, name='email_template_send'),
    # path('email-templates/<int:template_id>/stats/', views_email.email_template_stats, name='email_template_stats'),
    # path('email-templates/<int:template_id>/archive/', views_email.email_template_archive, name='email_template_archive'),
    
    # Email Campaigns
    path('campaigns/create/', views_email.campaign_create, name='campaign_create'),
    path('campaigns/<uuid:campaign_id>/', views_email.campaign_detail, name='campaign_detail'),
    path('campaigns/<uuid:campaign_id>/edit/', views_email.campaign_edit, name='campaign_edit'),
    path('campaigns/<uuid:campaign_id>/delete/', views_email.campaign_delete, name='campaign_delete'),
    path('campaigns/<uuid:campaign_id>/archive/', views_email.campaign_archive, name='campaign_archive'),
    path('campaigns/<uuid:campaign_id>/unarchive/', views_email.campaign_unarchive, name='campaign_unarchive'),
    path('campaigns/<uuid:campaign_id>/test/', views_email.campaign_send_test, name='campaign_send_test'),
    path('campaigns/<uuid:campaign_id>/send/', views_email.campaign_send, name='campaign_send'),
    path('campaigns/<uuid:campaign_id>/sync-stats/', views_email.campaign_sync_stats, name='campaign_sync_stats'),
    path('campaigns/<uuid:campaign_id>/add-recipient/', views_email.campaign_add_recipient, name='campaign_add_recipient'),
    path('campaigns/<uuid:campaign_id>/bulk-add-recipients/', views_email.campaign_bulk_add_recipients, name='campaign_bulk_add_recipients'),
    path('campaigns/<uuid:campaign_id>/import-form-submissions/', views_email.campaign_import_form_submissions, name='campaign_import_form_submissions'),
    path('campaigns/<uuid:campaign_id>/recipients/<uuid:recipient_id>/delete/', views_email.campaign_delete_recipient, name='campaign_delete_recipient'),

    
    # Email Campaign Stats
    path('campaigns/', views_stats.campaign_list_with_stats, name='campaign_list_with_stats'),
    path('campaigns/<uuid:campaign_id>/stats/', views_stats.campaign_stats_detail, name='campaign_stats_detail'),
    path('campaigns/<uuid:campaign_id>/recipients/<uuid:recipient_id>/', views_stats.campaign_recipient_detail, name='campaign_recipient_detail'),

    
    # Registration Form Builder
    path('registration-form-builder/', views_email.registration_form_builder, name='registration_form_builder'),
    path('registration-form-builder/create/', views_email.registration_form_create, name='registration_form_create'),
    path('registration-form-builder/<uuid:form_id>/edit/', views_email.registration_form_edit, name='registration_form_edit'),
    path('registration-form-builder/<uuid:form_id>/delete/', views_email.registration_form_delete, name='registration_form_delete'),
    path('registration-form-builder/<uuid:form_id>/toggle/', views_email.registration_form_toggle, name='registration_form_toggle'),
    path('registration-form-builder/<uuid:form_id>/submissions/', views_email.registration_form_submissions, name='registration_form_submissions'),
    
    # Form Analytics Stats
    path('forms/', views_stats.form_list_with_stats, name='form_list_with_stats'),
    path('forms/<uuid:form_id>/stats/', views_stats.form_stats_detail, name='form_stats_detail'),
    
    # API Endpoints
    path('api/events/', views.api_events_list, name='api_events_list'),
    path('api/events/<uuid:event_id>/rooms/', views.api_event_rooms, name='api_event_rooms'),
    path('events/<uuid:event_id>/registration-fields/', views_email.event_registration_fields_api, name='event_registration_fields_api'),
    
    # Event Email Templates -- three fixed, purpose-built kinds (Confirmation,
    # Préinscription, Registration Confirmation), each with its own coherent
    # variable list. The old free-form create/edit routes stay defined
    # (harmless, some other page may still reference an old row by id) but
    # are no longer linked from the dashboard UI.
    path('events/<uuid:event_id>/email-templates/', views_email.event_email_templates, name='event_email_templates'),
    path('events/<uuid:event_id>/email-templates/kind/<str:template_type>/', views_email.event_email_template_set, name='event_email_template_set'),
    path('events/<uuid:event_id>/email-templates/create/', views_email.event_email_template_create, name='event_email_template_create'),
    path('events/<uuid:event_id>/email-templates/<int:template_id>/edit/', views_email.event_email_template_edit, name='event_email_template_edit'),
    path('events/<uuid:event_id>/email-templates/<int:template_id>/delete/', views_email.event_email_template_delete, name='event_email_template_delete'),
    
    # Send Emails
    path('events/<uuid:event_id>/email-templates/<int:template_id>/send/', views_email.send_event_email, name='send_event_email'),
    path('events/<uuid:event_id>/email-templates/<int:template_id>/send-to-registrants/', views_email.send_email_to_registrants, name='send_email_to_registrants'),
    path('events/<uuid:event_id>/email-logs/', views_email.event_email_logs, name='event_email_logs'),
    
    # API: Get event registration fields for campaign variables
    path('api/events/<uuid:event_id>/registration-fields/', views_email.get_event_registration_fields, name='api_event_registration_fields'),
    
    # Committee landing page after login -- straight to their one event,
    # or a themed picker if assigned to more than one. Never the admin
    # sidebar management home below (staff/admin only, in practice).
    path('my-committee/', views_eposter_dashboard.eposter_committee_home, name='eposter_committee_home'),

    # Scientific Contributions Management - Central Hub
    path('contributions/', views_eposter_management.eposter_management_home, name='contributions_management_home'),
    path('contributions/create/<uuid:event_id>/', views_eposter_management.create_form_for_event, name='contributions_create_form_for_event'),
    path('contributions/<uuid:event_id>/enable/', views_eposter_management.eposter_enable_for_event, name='contributions_enable_for_event'),
    path('contributions/<uuid:event_id>/toggle/', views_eposter_management.eposter_form_toggle, name='contributions_form_toggle'),
    path('contributions/<uuid:event_id>/settings/', views_eposter_management.eposter_form_settings, name='contributions_form_settings'),
    path('contributions/copy/<uuid:source_event_id>/<uuid:target_event_id>/', views_eposter_management.eposter_copy_settings, name='contributions_copy_settings'),
    
    # Scientific Contributions Management - Event Specific
    path('events/<uuid:event_id>/contributions/', views_eposter_dashboard.eposter_dashboard, name='contributions_dashboard'),
    path('events/<uuid:event_id>/contributions/submissions/', views_eposter_dashboard.eposter_submissions_list, name='contributions_submissions_list'),
    path('events/<uuid:event_id>/contributions/submissions/<uuid:submission_id>/', views_eposter_dashboard.eposter_submission_detail, name='contributions_submission_detail'),
    path('events/<uuid:event_id>/contributions/submissions/<uuid:submission_id>/validate/', views_eposter_dashboard.eposter_validate_submission, name='contributions_validate_submission'),
    path('events/<uuid:event_id>/contributions/submissions/<uuid:submission_id>/set-status/', views_eposter_dashboard.eposter_set_status, name='contributions_set_status'),
    path('events/<uuid:event_id>/contributions/submissions/<uuid:submission_id>/realtime/', views_eposter_dashboard.eposter_realtime_status, name='contributions_realtime_status'),
    path('events/<uuid:event_id>/contributions/email-templates/', views_eposter_dashboard.eposter_email_templates, name='contributions_email_templates'),
    path('events/<uuid:event_id>/contributions/email-templates/create/', views_eposter_dashboard.eposter_email_template_create, name='contributions_email_template_create'),
    path('events/<uuid:event_id>/contributions/email-templates/<uuid:template_id>/edit/', views_eposter_dashboard.eposter_email_template_edit, name='contributions_email_template_edit'),
    path('events/<uuid:event_id>/contributions/email-templates/<uuid:template_id>/delete/', views_eposter_dashboard.eposter_email_template_delete, name='contributions_email_template_delete'),
    path('events/<uuid:event_id>/contributions/export/', views_eposter_dashboard.eposter_export_excel, name='contributions_export_excel'),

    # Scientific Committee management (member/supervisor roles) -- was
    # built (views_eposter_dashboard.eposter_committee_*, committee_list.html)
    # but never wired into urls.py, so the page was unreachable and every
    # committee account defaulted to 'member' with no way to promote anyone.
    path('events/<uuid:event_id>/contributions/committee/', views_eposter_dashboard.eposter_committee_list, name='contributions_committee_list'),
    path('events/<uuid:event_id>/contributions/committee/add/', views_eposter_dashboard.eposter_committee_add, name='eposter_committee_add'),
    path('events/<uuid:event_id>/contributions/committee/create/', views_eposter_dashboard.eposter_committee_create_member, name='eposter_committee_create_member'),
    path('events/<uuid:event_id>/contributions/committee/<uuid:member_id>/remove/', views_eposter_dashboard.eposter_committee_remove, name='eposter_committee_remove'),
    path('events/<uuid:event_id>/contributions/committee/<uuid:member_id>/role/', views_eposter_dashboard.eposter_committee_update_role, name='eposter_committee_update_role'),

    # Legacy URLs for backward compatibility
    path('eposter/', views_eposter_management.eposter_management_home, name='eposter_management_home'),
    path('events/<uuid:event_id>/eposter/', views_eposter_dashboard.eposter_dashboard, name='eposter_dashboard'),

    # Final Communication Orale submissions (staff + room managers)
    path('my-final-communications/', views_final_communications.my_final_communications_home, name='my_final_communications_home'),
    path('events/<uuid:event_id>/final-communications/', views_final_communications.final_communications, name='final_communications'),
    path('final-communications/<uuid:submission_id>/download/', views_final_communications.download_final_communication, name='download_final_communication'),

    # Registration submissions (staff + event owners, read-only)
    path('my-submissions/', views_event_owner.event_owner_submissions_home, name='event_owner_submissions_home'),
    path('events/<uuid:event_id>/my-submissions/', views_event_owner.event_owner_submissions, name='event_owner_submissions'),
    path('events/<uuid:event_id>/my-submissions/export/', views_event_owner.event_owner_export_excel, name='event_owner_export_excel'),
    path('my-submissions/<uuid:order_id>/status/', views_event_owner.registration_status_save, name='registration_status_save'),
    path('my-submissions/<uuid:order_id>/notes/', views_event_owner.registration_notes_save, name='registration_notes_save'),
    path('my-submissions/<uuid:order_id>/send-payment-link/', views_event_owner.send_payment_link_email, name='send_payment_link_email'),
    path('my-submissions/<uuid:order_id>/delete/', views_event_owner.registration_delete, name='registration_delete'),

    # Registration Blocs / Paid Registration (admin config + orders)
    path('events/<uuid:event_id>/blocs/', views_blocs.blocs_config, name='blocs_config'),
    path('events/<uuid:event_id>/blocs/save/', views_blocs.blocs_config_save, name='blocs_config_save'),
    path('events/<uuid:event_id>/blocs/items/save/', views_blocs.bloc_item_save, name='bloc_item_save'),
    path('blocs/items/<int:item_id>/delete/', views_blocs.bloc_item_delete, name='bloc_item_delete'),
    path('events/<uuid:event_id>/blocs/status-rules/save/', views_blocs.bloc_status_rules_save, name='bloc_status_rules_save'),
    path('events/<uuid:event_id>/blocs/periods/save/', views_blocs.reduction_period_save, name='reduction_period_save'),
    path('blocs/periods/<int:period_id>/delete/', views_blocs.reduction_period_delete, name='reduction_period_delete'),
    path('events/<uuid:event_id>/blocs/workshops/order/save/', views_blocs.workshop_order_save, name='workshop_order_save'),
    path('events/<uuid:event_id>/blocs/orders/', views_blocs.registration_orders, name='registration_orders'),
]
