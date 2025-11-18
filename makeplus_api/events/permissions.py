# events/permissions.py - Custom Permissions

from rest_framework import permissions
from .models import UserEventAssignment

class IsOrganizer(permissions.BasePermission):
    """
    Permission: User must be an organizer for the event
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Get event from object
        event = getattr(obj, 'event', None)
        if not event:
            return False
        
        # Check if user is organizer for this event
        return UserEventAssignment.objects.filter(
            user=request.user,
            event=event,
            role='organisateur',
            is_active=True
        ).exists() or request.user.is_staff


class IsOrganizerOrReadOnly(permissions.BasePermission):
    """
    Permission: Read-only for all, write for organizers only
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        
        # For write operations, check organizer status
        # This will be validated at object level
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Read permissions for authenticated users
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions only for organizers
        event = getattr(obj, 'event', None)
        if not event:
            return False
        
        return UserEventAssignment.objects.filter(
            user=request.user,
            event=event,
            role='organisateur',
            is_active=True
        ).exists() or request.user.is_staff


class IsController(permissions.BasePermission):
    """
    Permission: User must be a controller for the event
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        event = getattr(obj, 'event', None)
        if not event:
            return False
        
        # Check if user is controller for this event
        return UserEventAssignment.objects.filter(
            user=request.user,
            event=event,
            role__in=['controlleur_des_badges', 'organisateur'],  # Organizers can also control
            is_active=True
        ).exists() or request.user.is_staff


class IsParticipant(permissions.BasePermission):
    """
    Permission: User must be a participant for the event
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        event = getattr(obj, 'event', None)
        if not event:
            return False
        
        return UserEventAssignment.objects.filter(
            user=request.user,
            event=event,
            role='participant',
            is_active=True
        ).exists()


class IsEventMember(permissions.BasePermission):
    """
    Permission: User must be assigned to the event (any role)
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        event = getattr(obj, 'event', None)
        if not event:
            return False
        
        return UserEventAssignment.objects.filter(
            user=request.user,
            event=event,
            is_active=True
        ).exists() or request.user.is_staff