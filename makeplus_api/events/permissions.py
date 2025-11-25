# events/permissions.py - Custom Permissions

from rest_framework import permissions
from .models import UserEventAssignment

class IsGestionnaire(permissions.BasePermission):
    """
    Permission: User must be a gestionnaire des salles for the event
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Get event from object
        event = getattr(obj, 'event', None)
        if not event:
            return False
        
        # Check if user is gestionnaire for this event
        return UserEventAssignment.objects.filter(
            user=request.user,
            event=event,
            role='gestionnaire_des_salles',
            is_active=True
        ).exists() or request.user.is_staff


class IsGestionnaireOrReadOnly(permissions.BasePermission):
    """
    Permission: Read-only for all, write for gestionnaires only
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        
        # For write operations, check gestionnaire status
        # This will be validated at object level
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Read permissions for authenticated users
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions only for gestionnaires
        event = getattr(obj, 'event', None)
        if not event:
            return False
        
        return UserEventAssignment.objects.filter(
            user=request.user,
            event=event,
            role='gestionnaire_des_salles',
            is_active=True
        ).exists() or request.user.is_staff


class IsController(permissions.BasePermission):
    """
    Permission: User must be a controller (controlleur_des_badges) for the event
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
            role='controlleur_des_badges',
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

class IsExposant(permissions.BasePermission):
    """
    Permission: User must be an exposant for the event
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
            role='exposant',
            is_active=True
        ).exists() or request.user.is_staff


class IsAnnonceOwner(permissions.BasePermission):
    """
    Permission: User must be the creator of the annonce
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # For annonce objects
        return obj.created_by == request.user or request.user.is_staff


# Backward compatibility aliases
IsOrganizer = IsGestionnaire
IsOrganizerOrReadOnly = IsGestionnaireOrReadOnly


class IsExposant(permissions.BasePermission):
    """Permission: User must be an exposant for the event"""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        event = getattr(obj, 'event', None)
        if not event:
            return False
        return UserEventAssignment.objects.filter(user=request.user, event=event, role='exposant', is_active=True).exists() or request.user.is_staff


class IsAnnonceOwner(permissions.BasePermission):
    """Permission: User must be the creator of the annonce"""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        return obj.created_by == request.user or request.user.is_staff


# Backward compatibility aliases
IsOrganizer = IsGestionnaire
IsOrganizerOrReadOnly = IsGestionnaireOrReadOnly
