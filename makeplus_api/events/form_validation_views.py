"""
Form Registration Validation API Views
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.renderers import JSONRenderer
from .form_validation_service import verify_form_registration, resend_form_validation_code


class FormValidationVerifyView(APIView):
    """
    Verify form registration code
    POST /api/forms/validate/
    """
    permission_classes = []
    renderer_classes = [JSONRenderer]
    
    def post(self, request):
        email = request.data.get('email', '').strip().lower()
        form_slug = request.data.get('form_slug', '').strip()
        code = request.data.get('code', '').strip()
        
        if not all([email, form_slug, code]):
            return Response({
                'success': False,
                'message': 'Email, form_slug, and code are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get client info
        ip_address = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0] if request.META.get('HTTP_X_FORWARDED_FOR') else request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Verify code and complete registration
        success, participant, message = verify_form_registration(
            email=email,
            form_slug=form_slug,
            code=code,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        if not success:
            return Response({
                'success': False,
                'message': message
            }, status=status.HTTP_400_BAD_REQUEST)
        
        response_data = {
            'success': True,
            'message': message
        }
        
        if participant:
            response_data['participant'] = {
                'id': str(participant.id),
                'badge_id': participant.badge_id,
                'event': {
                    'id': str(participant.event.id),
                    'name': participant.event.name
                }
            }
        
        return Response(response_data, status=status.HTTP_200_OK)


class FormValidationResendView(APIView):
    """
    Resend form registration validation code
    POST /api/forms/validate/resend/
    """
    permission_classes = []
    renderer_classes = [JSONRenderer]
    
    def post(self, request):
        email = request.data.get('email', '').strip().lower()
        form_slug = request.data.get('form_slug', '').strip()
        form_data = request.data.get('form_data', {})
        
        if not all([email, form_slug, form_data]):
            return Response({
                'success': False,
                'message': 'Email, form_slug, and form_data are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get client info
        ip_address = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0] if request.META.get('HTTP_X_FORWARDED_FOR') else request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Resend validation code
        success, message, wait_seconds = resend_form_validation_code(
            email=email,
            form_slug=form_slug,
            form_data=form_data,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        if success:
            return Response({
                'success': True,
                'message': message
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'message': message,
                'wait_seconds': wait_seconds
            }, status=status.HTTP_400_BAD_REQUEST)
