"""
Sign Up API Views for Mobile App
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.renderers import JSONRenderer
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .signup_service import send_signup_verification_code, verify_signup_code, resend_signup_code


class SignUpRequestView(APIView):
    """
    Request sign up verification code
    POST /api/auth/signup/request/
    """
    permission_classes = []
    renderer_classes = [JSONRenderer]
    
    def post(self, request):
        email = request.data.get('email', '').strip().lower()
        first_name = request.data.get('first_name', '').strip()
        
        if not email or not first_name:
            return Response({
                'success': False,
                'message': 'Email and first name are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get client info
        ip_address = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0] if request.META.get('HTTP_X_FORWARDED_FOR') else request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Send verification code
        success, message, wait_seconds = send_signup_verification_code(
            email=email,
            first_name=first_name,
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


class SignUpVerifyView(APIView):
    """
    Verify sign up code and create account
    POST /api/auth/signup/verify/
    """
    permission_classes = []
    renderer_classes = [JSONRenderer]
    
    def post(self, request):
        email = request.data.get('email', '').strip().lower()
        code = request.data.get('code', '').strip()
        password = request.data.get('password', '').strip()
        first_name = request.data.get('first_name', '').strip()
        last_name = request.data.get('last_name', '').strip()
        
        if not all([email, code, password, first_name, last_name]):
            return Response({
                'success': False,
                'message': 'All fields are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate password
        try:
            validate_password(password)
        except ValidationError as e:
            return Response({
                'success': False,
                'message': ', '.join(e.messages)
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get client info
        ip_address = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0] if request.META.get('HTTP_X_FORWARDED_FOR') else request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Verify code and create account
        success, user, message = verify_signup_code(
            email=email,
            code=code,
            password=password,
            first_name=first_name,
            last_name=last_name,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        if not success:
            return Response({
                'success': False,
                'message': message
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'success': True,
            'message': 'Account created successfully',
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
            }
        }, status=status.HTTP_201_CREATED)


class SignUpResendView(APIView):
    """
    Resend sign up verification code
    POST /api/auth/signup/resend/
    """
    permission_classes = []
    renderer_classes = [JSONRenderer]
    
    def post(self, request):
        email = request.data.get('email', '').strip().lower()
        first_name = request.data.get('first_name', '').strip()
        
        if not email or not first_name:
            return Response({
                'success': False,
                'message': 'Email and first name are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get client info
        ip_address = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0] if request.META.get('HTTP_X_FORWARDED_FOR') else request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Resend verification code
        success, message, wait_seconds = resend_signup_code(
            email=email,
            first_name=first_name,
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
