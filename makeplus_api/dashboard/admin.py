from django.contrib import admin
from .models_email import EmailTemplate, EventEmailTemplate, EmailLog
from .models_form import FormConfiguration, FormSubmission


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
