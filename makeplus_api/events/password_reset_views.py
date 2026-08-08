"""
Password Reset API Views for Mobile App
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.renderers import JSONRenderer
from .password_reset_service import (
    request_password_reset,
    verify_password_reset,
    resend_password_reset_code,
)


def _client_info(request):
    ip_address = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0] if request.META.get('HTTP_X_FORWARDED_FOR') else request.META.get('REMOTE_ADDR')
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    return ip_address, user_agent


class PasswordResetRequestView(APIView):
    """
    Request a password reset verification code
    POST /api/auth/password-reset/request/
    Body: email, new_password
    """
    # Public/anonymous by design (a user who forgot their password can't
    # authenticate). See signup_views.py for why authentication_classes
    # must be disabled too, not just permission_classes -- a stale Bearer
    # token from a previous session would otherwise 401 this endpoint
    # before it's ever reached.
    authentication_classes = []
    permission_classes = []
    renderer_classes = [JSONRenderer]

    def post(self, request):
        email = request.data.get('email', '').strip().lower()
        new_password = request.data.get('new_password', '').strip()

        if not email or not new_password:
            return Response({
                'success': False,
                'message': 'Email et nouveau mot de passe requis'
            }, status=status.HTTP_400_BAD_REQUEST)

        ip_address, user_agent = _client_info(request)

        success, message, wait_seconds = request_password_reset(
            email=email,
            new_password=new_password,
            ip_address=ip_address,
            user_agent=user_agent
        )

        if success:
            return Response({'success': True, 'message': message}, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'message': message,
                'wait_seconds': wait_seconds
            }, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetVerifyView(APIView):
    """
    Verify reset code and apply the new password
    POST /api/auth/password-reset/verify/
    Body: email, code
    """
    authentication_classes = []
    permission_classes = []
    renderer_classes = [JSONRenderer]

    def post(self, request):
        email = request.data.get('email', '').strip().lower()
        code = request.data.get('code', '').strip()

        if not email or not code:
            return Response({
                'success': False,
                'message': 'Email et code requis'
            }, status=status.HTTP_400_BAD_REQUEST)

        ip_address, user_agent = _client_info(request)

        success, message = verify_password_reset(
            email=email,
            code=code,
            ip_address=ip_address,
            user_agent=user_agent
        )

        if success:
            return Response({'success': True, 'message': message}, status=status.HTTP_200_OK)
        else:
            return Response({'success': False, 'message': message}, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetResendView(APIView):
    """
    Resend password reset verification code
    POST /api/auth/password-reset/resend/
    Body: email, new_password
    """
    authentication_classes = []
    permission_classes = []
    renderer_classes = [JSONRenderer]

    def post(self, request):
        email = request.data.get('email', '').strip().lower()
        new_password = request.data.get('new_password', '').strip()

        if not email or not new_password:
            return Response({
                'success': False,
                'message': 'Email et nouveau mot de passe requis'
            }, status=status.HTTP_400_BAD_REQUEST)

        ip_address, user_agent = _client_info(request)

        success, message, wait_seconds = resend_password_reset_code(
            email=email,
            new_password=new_password,
            ip_address=ip_address,
            user_agent=user_agent
        )

        if success:
            return Response({'success': True, 'message': message}, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'message': message,
                'wait_seconds': wait_seconds
            }, status=status.HTTP_400_BAD_REQUEST)
