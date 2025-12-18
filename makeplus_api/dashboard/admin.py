from django.contrib import admin
from .models_email import EmailTemplate, EventEmailTemplate, EmailLog


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
