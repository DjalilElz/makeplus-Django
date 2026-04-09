"""
Custom middleware for MakePlus API
"""
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from .models import Event


class EventContextMiddleware:
    """
    Middleware to extract event context from JWT token and attach it to request
    """
    def __init__(self, get_response):
        self.get_response = get_response
        self.jwt_auth = JWTAuthentication()

    def __call__(self, request):
        # Initialize event_context to None
        request.event_context = None
        
        # Try to extract event_id from JWT token in Authorization header
        try:
            # Get the raw token from the Authorization header
            auth_header = request.META.get('HTTP_AUTHORIZATION', '')
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
                
                # Decode the token to get claims
                from rest_framework_simplejwt.tokens import AccessToken
                access_token = AccessToken(token)
                
                # Extract event_id from token claims
                event_id = access_token.get('event_id')
                
                if event_id:
                    try:
                        # Fetch the event object
                        event = Event.objects.get(id=event_id)
                        request.event_context = event
                    except Event.DoesNotExist:
                        pass
        except (InvalidToken, TokenError, Exception):
            # Silently fail - event_context remains None
            pass

        response = self.get_response(request)
        return response
