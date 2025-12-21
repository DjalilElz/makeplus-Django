# events/admin.py - Django Admin Configuration

from django.contrib import admin
from django.utils.html import format_html
from .models import Event, Room, Session, Participant, RoomAccess, UserEventAssignment

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['name', 'start_date', 'end_date', 'location', 'status_badge', 'total_rooms', 'total_participants']
    list_filter = ['status', 'start_date']
    search_fields = ['name', 'location']
    readonly_fields = ['id', 'total_rooms', 'total_participants', 'total_exhibitors', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'start_date', 'end_date')
        }),
        ('Location', {
            'fields': ('location', 'location_details')
        }),
        ('Branding', {
            'fields': ('logo', 'banner')
        }),
        ('Configuration', {
            'fields': ('status', 'themes', 'settings', 'organizer_contact')
        }),
        ('Statistics', {
            'fields': ('total_rooms', 'total_participants', 'total_exhibitors'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('id', 'created_by', 'created_at', 'updated_at', 'metadata'),
            'classes': ('collapse',)
        }),
    )
    
    def status_badge(self, obj):
        colors = {
            'upcoming': '#FFA500',
            'active': '#4CAF50',
            'completed': '#9E9E9E',
            'cancelled': '#F44336'
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            colors.get(obj.status, '#000'),
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ['name', 'event', 'capacity', 'current_participants', 'occupancy_bar', 'location', 'is_active']
    list_filter = ['event', 'is_active']
    search_fields = ['name', 'location', 'event__name']
    readonly_fields = ['id', 'current_participants', 'occupancy_percentage', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('event', 'name', 'description')
        }),
        ('Capacity', {
            'fields': ('capacity', 'location', 'is_active')
        }),
        ('Current Status', {
            'fields': ('current_participants', 'occupancy_percentage'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('id', 'created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def occupancy_bar(self, obj):
        percentage = obj.occupancy_percentage
        color = '#4CAF50' if percentage < 70 else '#FFA500' if percentage < 90 else '#F44336'
        return format_html(
            '<div style="width: 100px; height: 20px; border: 1px solid #ddd;">'
            '<div style="width: {}%; height: 100%; background-color: {};"></div>'
            '</div>',
            min(percentage, 100),
            color
        )
    occupancy_bar.short_description = 'Occupancy'


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ['title', 'event', 'room', 'speaker_name', 'start_time', 'end_time', 'status_badge', 'duration']
    list_filter = ['status', 'event', 'theme']
    search_fields = ['title', 'speaker_name', 'description']
    readonly_fields = ['id', 'duration_minutes', 'is_live', 'created_at', 'updated_at']
    date_hierarchy = 'start_time'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('event', 'room', 'title', 'description', 'theme')
        }),
        ('Schedule', {
            'fields': ('start_time', 'end_time', 'status')
        }),
        ('Speaker', {
            'fields': ('speaker_name', 'speaker_title', 'speaker_bio', 'speaker_photo_url'),
            'classes': ('collapse',)
        }),
        ('Media', {
            'fields': ('cover_image_url',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('id', 'is_live', 'duration_minutes', 'created_by', 'created_at', 'updated_at', 'metadata'),
            'classes': ('collapse',)
        }),
    )
    
    def status_badge(self, obj):
        colors = {
            'scheduled': '#2196F3',
            'live': '#4CAF50',
            'completed': '#9E9E9E',
            'cancelled': '#F44336'
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            colors.get(obj.status, '#000'),
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def duration(self, obj):
        return f"{obj.duration_minutes()} min"
    duration.short_description = 'Duration'
    
    actions = ['mark_as_live', 'mark_as_completed', 'mark_as_cancelled']
    
    def mark_as_live(self, request, queryset):
        updated = queryset.update(status='live')
        self.message_user(request, f'{updated} sessions marked as live.')
    mark_as_live.short_description = 'Mark selected sessions as LIVE'
    
    def mark_as_completed(self, request, queryset):
        updated = queryset.update(status='completed')
        self.message_user(request, f'{updated} sessions marked as completed.')
    mark_as_completed.short_description = 'Mark selected sessions as COMPLETED'
    
    def mark_as_cancelled(self, request, queryset):
        updated = queryset.update(status='cancelled')
        self.message_user(request, f'{updated} sessions cancelled.')
    mark_as_cancelled.short_description = 'Cancel selected sessions'


@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
    list_display = ['user', 'event', 'badge_id', 'is_checked_in', 'checked_in_at']
    list_filter = ['event', 'is_checked_in']
    search_fields = ['user__username', 'user__email', 'badge_id']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('User & Event', {
            'fields': ('user', 'event')
        }),
        ('Badge Information', {
            'fields': ('badge_id', 'qr_code_data')
        }),
        ('Check-in Status', {
            'fields': ('is_checked_in', 'checked_in_at')
        }),
        ('Access Control', {
            'fields': ('allowed_rooms',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    filter_horizontal = ['allowed_rooms']


@admin.register(RoomAccess)
class RoomAccessAdmin(admin.ModelAdmin):
    list_display = ['participant', 'room', 'session', 'accessed_at', 'status_badge', 'verified_by']
    list_filter = ['status', 'room', 'accessed_at']
    search_fields = ['participant__user__username', 'room__name']
    readonly_fields = ['accessed_at']
    date_hierarchy = 'accessed_at'
    
    fieldsets = (
        ('Access Information', {
            'fields': ('participant', 'room', 'session')
        }),
        ('Verification', {
            'fields': ('accessed_at', 'verified_by', 'status', 'denial_reason')
        }),
    )
    
    def status_badge(self, obj):
        colors = {
            'granted': '#4CAF50',
            'denied': '#F44336'
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            colors.get(obj.status, '#000'),
            obj.get_status_display().upper()
        )
    status_badge.short_description = 'Status'


@admin.register(UserEventAssignment)
class UserEventAssignmentAdmin(admin.ModelAdmin):
    list_display = ['user', 'event', 'role_badge', 'is_active', 'assigned_at', 'assigned_by']
    list_filter = ['role', 'is_active', 'event']
    search_fields = ['user__username', 'event__name']
    readonly_fields = ['assigned_at']
    
    fieldsets = (
        ('Assignment', {
            'fields': ('user', 'event', 'role', 'is_active')
        }),
        ('Metadata', {
            'fields': ('assigned_at', 'assigned_by'),
            'classes': ('collapse',)
        }),
    )
    
    def role_badge(self, obj):
        colors = {
            'organizer': '#9C27B0',
            'controller': '#2196F3',
            'participant': '#4CAF50',
            'exhibitor': '#FF9800'
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            colors.get(obj.role, '#000'),
            obj.get_role_display().upper()
        )
    role_badge.short_description = 'Role'