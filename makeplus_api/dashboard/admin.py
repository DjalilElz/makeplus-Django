from django.contrib import admin
from .models_email import (
    EmailTemplate, EventEmailTemplate, EmailLog,
    EmailCampaign, EmailRecipient, EmailLink, EmailClick, EmailOpen
)
from .models_form import (
    FormConfiguration, FormSubmission,
    FormAnalytics, FormView, FormFieldInteraction
)
from .models_eposter import (
    EPosterSubmission, EPosterValidation, 
    EPosterCommitteeMember, EPosterEmailTemplate,
    EventFormConfiguration
)


@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'subject', 'created_by', 'created_at', 'updated_at']
    list_filter = ['created_at', 'created_by']
    search_fields = ['name', 'subject', 'body', 'description']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(EventEmailTemplate)
class EventEmailTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'event', 'base_template', 'created_by', 'created_at']
    list_filter = ['event', 'created_at', 'created_by']
    search_fields = ['name', 'subject', 'body']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    list_display = ['event', 'subject', 'target_type', 'recipient_count', 'sent_count', 'status', 'sent_by', 'created_at']
    list_filter = ['status', 'target_type', 'event', 'created_at']
    search_fields = ['subject', 'body']
    readonly_fields = ['created_at', 'sent_at', 'sent_count', 'failed_count']


@admin.register(FormConfiguration)
class FormConfigurationAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'event', 'is_active', 'submission_count', 'created_by', 'created_at']
    list_filter = ['is_active', 'event', 'created_at']
    search_fields = ['name', 'description', 'slug']
    readonly_fields = ['created_at', 'updated_at', 'submission_count']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(FormSubmission)
class FormSubmissionAdmin(admin.ModelAdmin):
    list_display = ['form', 'email', 'status', 'submitted_at', 'reviewed_by']
    list_filter = ['status', 'form', 'submitted_at']
    search_fields = ['email', 'data', 'admin_notes']
    readonly_fields = ['submitted_at', 'ip_address', 'user_agent']


@admin.register(EmailCampaign)
class EmailCampaignAdmin(admin.ModelAdmin):
    list_display = ['name', 'event', 'status', 'total_sent', 'unique_opens', 'unique_clicks', 'get_open_rate', 'get_click_rate', 'created_at']
    list_filter = ['status', 'event', 'created_at', 'track_opens', 'track_clicks']
    search_fields = ['name', 'subject', 'from_email']
    readonly_fields = ['created_at', 'updated_at', 'total_sent', 'total_delivered', 'total_failed', 
                       'total_opened', 'total_clicked', 'unique_opens', 'unique_clicks', 'sent_at', 'completed_at']
    
    def get_open_rate(self, obj):
        return f"{obj.get_open_rate()}%"
    get_open_rate.short_description = 'Open Rate'
    
    def get_click_rate(self, obj):
        return f"{obj.get_click_rate()}%"
    get_click_rate.short_description = 'Click Rate'


@admin.register(EmailRecipient)
class EmailRecipientAdmin(admin.ModelAdmin):
    list_display = ['email', 'campaign', 'status', 'open_count', 'click_count', 'sent_at', 'first_opened_at']
    list_filter = ['status', 'campaign', 'sent_at']
    search_fields = ['email', 'name', 'tracking_token']
    readonly_fields = ['tracking_token', 'sent_at', 'delivered_at', 'first_opened_at', 
                       'last_opened_at', 'open_count', 'click_count', 'created_at']


@admin.register(EmailLink)
class EmailLinkAdmin(admin.ModelAdmin):
    list_display = ['original_url', 'campaign', 'total_clicks', 'unique_clicks', 'get_click_rate']
    list_filter = ['campaign', 'created_at']
    search_fields = ['original_url', 'tracking_token']
    readonly_fields = ['tracking_token', 'total_clicks', 'unique_clicks', 'created_at']
    
    def get_click_rate(self, obj):
        return f"{obj.get_click_rate()}%"
    get_click_rate.short_description = 'Click Rate'


@admin.register(EmailClick)
class EmailClickAdmin(admin.ModelAdmin):
    list_display = ['recipient', 'link', 'clicked_at', 'ip_address']
    list_filter = ['clicked_at', 'link__campaign']
    search_fields = ['recipient__email', 'link__original_url', 'ip_address']
    readonly_fields = ['clicked_at']


@admin.register(EmailOpen)
class EmailOpenAdmin(admin.ModelAdmin):
    list_display = ['recipient', 'opened_at', 'ip_address']
    list_filter = ['opened_at', 'recipient__campaign']
    search_fields = ['recipient__email', 'ip_address']
    readonly_fields = ['opened_at']


@admin.register(FormAnalytics)
class FormAnalyticsAdmin(admin.ModelAdmin):
    list_display = ['form', 'total_views', 'total_submissions', 'conversion_rate', 'last_updated']
    list_filter = ['form', 'last_updated']
    search_fields = ['form__name']
    readonly_fields = ['last_updated']


@admin.register(FormView)
class FormViewAdmin(admin.ModelAdmin):
    list_display = ['form', 'session_id', 'device_type', 'browser', 'completed', 'viewed_at']
    list_filter = ['completed', 'device_type', 'browser', 'form', 'viewed_at']
    search_fields = ['session_id', 'ip_address', 'referer']
    readonly_fields = ['viewed_at']


@admin.register(FormFieldInteraction)
class FormFieldInteractionAdmin(admin.ModelAdmin):
    list_display = ['form_view', 'field_name', 'time_spent', 'changes_count', 'completed', 'created_at']
    list_filter = ['completed', 'field_name', 'created_at']
    search_fields = ['field_name', 'form_view__form__name']
    readonly_fields = ['created_at']


# ePoster Admin
@admin.register(EPosterSubmission)
class EPosterSubmissionAdmin(admin.ModelAdmin):
    list_display = ['titre_travail', 'nom', 'prenom', 'email', 'type_participation', 'status', 'event', 'submitted_at']
    list_filter = ['status', 'type_participation', 'event', 'submitted_at']
    search_fields = ['titre_travail', 'nom', 'prenom', 'email', 'theme', 'etablissement']
    readonly_fields = ['submitted_at', 'updated_at', 'ip_address', 'user_agent']
    fieldsets = (
        ('Personal Information', {
            'fields': ('nom', 'prenom', 'email', 'telephone', 'genre')
        }),
        ('Professional Information', {
            'fields': ('grade', 'grade_autre', 'service', 'etablissement', 'wilaya')
        }),
        ('Submission Details', {
            'fields': ('event', 'type_participation', 'theme', 'titre_travail', 'auteurs')
        }),
        ('Abstract', {
            'fields': ('introduction', 'materiels_methodes', 'resultats', 'conclusion')
        }),
        ('Files', {
            'fields': ('fichier_resume', 'fichier_poster')
        }),
        ('Validation', {
            'fields': ('status', 'validations_required', 'rejection_reason', 
                      'final_decision_by', 'final_decision_date')
        }),
        ('Email Status', {
            'fields': ('acceptance_email_sent', 'rejection_email_sent')
        }),
        ('Metadata', {
            'fields': ('ip_address', 'user_agent', 'submitted_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(EPosterValidation)
class EPosterValidationAdmin(admin.ModelAdmin):
    list_display = ['submission', 'committee_member', 'is_approved', 'rating', 'validated_at']
    list_filter = ['is_approved', 'rating', 'validated_at', 'submission__event']
    search_fields = ['submission__titre_travail', 'committee_member__username', 'comments']
    readonly_fields = ['validated_at', 'updated_at']


@admin.register(EPosterCommitteeMember)
class EPosterCommitteeMemberAdmin(admin.ModelAdmin):
    list_display = ['user', 'event', 'role', 'specialty', 'is_active', 'assigned_at']
    list_filter = ['role', 'is_active', 'event', 'assigned_at']
    search_fields = ['user__username', 'user__email', 'specialty']
    readonly_fields = ['assigned_at']


@admin.register(EPosterEmailTemplate)
class EPosterEmailTemplateAdmin(admin.ModelAdmin):
    list_display = ['event', 'template_type', 'subject', 'is_active', 'created_at']
    list_filter = ['template_type', 'is_active', 'event', 'created_at']
    search_fields = ['subject', 'body_html']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(EventFormConfiguration)
class EventFormConfigurationAdmin(admin.ModelAdmin):
    list_display = ['event', 'form_type', 'title', 'is_active', 'submission_deadline', 'created_at']
    list_filter = ['form_type', 'is_active', 'created_at']
    search_fields = ['event__name', 'title', 'description']
    readonly_fields = ['created_at', 'updated_at']
