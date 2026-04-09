"""
ePoster API Views
RESTful endpoints for ePoster submissions and validations
"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from django.db.models import Count, Q
from django.utils import timezone
from django.core.mail import send_mail
from django.template import Template, Context
from django.conf import settings

from events.models import Event
from .models_eposter import (
    EPosterSubmission,
    EPosterValidation,
    EPosterCommitteeMember,
    EPosterEmailTemplate
)
from .serializers_eposter import (
    EPosterSubmissionSerializer,
    EPosterSubmissionCreateSerializer,
    EPosterSubmissionListSerializer,
    EPosterValidationSerializer,
    EPosterValidationCreateSerializer,
    CommitteeMemberSerializer,
    EPosterEmailTemplateSerializer,
    EPosterStatisticsSerializer
)


class IsCommitteeMember(permissions.BasePermission):
    """Permission check for committee members"""
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Get event_id from URL kwargs or query params
        event_id = view.kwargs.get('event_id') or request.query_params.get('event_id')
        if not event_id:
            return False
        
        return EPosterCommitteeMember.objects.filter(
            event_id=event_id,
            user=request.user,
            is_active=True
        ).exists()


class EPosterSubmissionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for ePoster submissions
    
    - Public: Create submission (AllowAny)
    - Committee: List, retrieve, update status
    """
    queryset = EPosterSubmission.objects.all()
    
    def get_permissions(self):
        if self.action == 'create':
            return [AllowAny()]
        return [IsAuthenticated()]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return EPosterSubmissionCreateSerializer
        if self.action == 'list':
            return EPosterSubmissionListSerializer
        return EPosterSubmissionSerializer
    
    def get_queryset(self):
        queryset = EPosterSubmission.objects.all()
        event_id = self.request.query_params.get('event_id')
        
        if event_id:
            queryset = queryset.filter(event_id=event_id)
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by type
        type_filter = self.request.query_params.get('type')
        if type_filter:
            queryset = queryset.filter(type_participation=type_filter)
        
        # Search
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(nom__icontains=search) |
                Q(prenom__icontains=search) |
                Q(titre_travail__icontains=search) |
                Q(email__icontains=search)
            )
        
        return queryset.select_related('event').prefetch_related('validations')
    
    def create(self, request, *args, **kwargs):
        """Public submission endpoint"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Add IP and user agent
        submission = serializer.save(
            ip_address=self.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500]
        )
        
        # Send confirmation email
        self.send_submission_confirmation(submission)
        
        return Response(
            EPosterSubmissionSerializer(submission).data,
            status=status.HTTP_201_CREATED
        )
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')
    
    def send_submission_confirmation(self, submission):
        """Send email confirmation after submission - DISABLED (only acceptance/rejection emails)"""
        # Submission confirmation emails are not used in this system
        # Only acceptance and rejection emails are sent
        pass
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def validate(self, request, pk=None):
        """
        Committee member validates a submission
        """
        submission = self.get_object()
        
        # Check if user is committee member
        is_member = EPosterCommitteeMember.objects.filter(
            event=submission.event,
            user=request.user,
            is_active=True
        ).exists()
        
        if not is_member:
            return Response(
                {'error': 'You are not a committee member for this event'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if already validated
        existing = EPosterValidation.objects.filter(
            submission=submission,
            committee_member=request.user
        ).first()
        
        serializer = EPosterValidationCreateSerializer(
            instance=existing,
            data={**request.data, 'submission': submission.id},
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        
        if existing:
            # Update existing validation
            existing.is_approved = serializer.validated_data['is_approved']
            existing.comments = serializer.validated_data.get('comments', '')
            existing.rating = serializer.validated_data.get('rating')
            existing.save()
            validation = existing
        else:
            # Create new validation
            validation = serializer.save()
        
        # Check if status should change
        status_changed = submission.check_and_update_status()
        
        # If status changed to accepted/rejected, send email
        if status_changed:
            self.send_decision_email(submission)
        
        return Response({
            'validation': EPosterValidationSerializer(validation).data,
            'submission': EPosterSubmissionSerializer(submission).data,
            'status_changed': status_changed
        })
    
    def send_decision_email(self, submission):
        """Send acceptance or rejection email using Brevo API"""
        from .email_sender import send_email
        
        try:
            template_type = 'accepted' if submission.status == 'accepted' else 'rejected'
            template = EPosterEmailTemplate.objects.filter(
                event=submission.event,
                template_type=template_type,
                is_active=True
            ).first()
            
            if template:
                context = {
                    'nom': submission.nom,
                    'prenom': submission.prenom,
                    'titre': submission.titre_travail,
                    'event_name': submission.event.name,
                }
                
                subject = Template(template.subject).render(Context(context))
                body = Template(template.body_html).render(Context(context))
                
                # Use Brevo API for sending
                success, error, message_id = send_email(
                    to_email=submission.email,
                    subject=subject,
                    html_content=body,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to_name=f"{submission.prenom} {submission.nom}",
                    use_api=True  # Force Brevo API usage
                )
                
                if success:
                    # Mark email as sent
                    if submission.status == 'accepted':
                        submission.acceptance_email_sent = True
                    else:
                        submission.rejection_email_sent = True
                    submission.save(update_fields=['acceptance_email_sent', 'rejection_email_sent'])
                else:
                    print(f"Failed to send email via Brevo API: {error}")
        except Exception as e:
            print(f"Error sending decision email: {e}")
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def set_status(self, request, pk=None):
        """
        Manually set submission status (for committee president or admin)
        """
        submission = self.get_object()
        
        # Check if user is committee president or admin
        is_president = EPosterCommitteeMember.objects.filter(
            event=submission.event,
            user=request.user,
            role='president',
            is_active=True
        ).exists()
        
        if not (is_president or request.user.is_staff):
            return Response(
                {'error': 'Only committee president or admin can manually set status'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        new_status = request.data.get('status')
        if new_status not in ['accepted', 'rejected', 'revision_requested', 'pending']:
            return Response(
                {'error': 'Invalid status'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        submission.status = new_status
        submission.final_decision_by = request.user
        submission.final_decision_date = timezone.now()
        
        if new_status == 'rejected':
            submission.rejection_reason = request.data.get('rejection_reason', '')
        
        submission.save()
        
        # Send email if status is final
        if new_status in ['accepted', 'rejected']:
            self.send_decision_email(submission)
        
        return Response(EPosterSubmissionSerializer(submission).data)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def my_pending(self, request):
        """
        Get submissions pending validation by current committee member
        """
        event_id = request.query_params.get('event_id')
        if not event_id:
            return Response(
                {'error': 'event_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if user is committee member
        membership = EPosterCommitteeMember.objects.filter(
            event_id=event_id,
            user=request.user,
            is_active=True
        ).first()
        
        if not membership:
            return Response(
                {'error': 'You are not a committee member for this event'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        pending_submissions = membership.get_pending_submissions()
        serializer = EPosterSubmissionListSerializer(pending_submissions, many=True)
        
        return Response({
            'pending': serializer.data,
            'count': pending_submissions.count()
        })
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def statistics(self, request):
        """
        Get ePoster statistics for an event
        """
        event_id = request.query_params.get('event_id')
        if not event_id:
            return Response(
                {'error': 'event_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        submissions = EPosterSubmission.objects.filter(event_id=event_id)
        
        # Count by status
        status_counts = submissions.values('status').annotate(count=Count('id'))
        status_dict = {s['status']: s['count'] for s in status_counts}
        
        # Count by type
        type_counts = submissions.values('type_participation').annotate(count=Count('id'))
        type_dict = {t['type_participation']: t['count'] for t in type_counts}
        
        # Count by theme
        theme_counts = submissions.values('theme').annotate(count=Count('id'))
        theme_dict = {t['theme']: t['count'] for t in theme_counts}
        
        # Committee stats
        committee_count = EPosterCommitteeMember.objects.filter(
            event_id=event_id,
            is_active=True
        ).count()
        
        total_validations = EPosterValidation.objects.filter(
            submission__event_id=event_id
        ).count()
        
        stats = {
            'total_submissions': submissions.count(),
            'pending_count': status_dict.get('pending', 0),
            'accepted_count': status_dict.get('accepted', 0),
            'rejected_count': status_dict.get('rejected', 0),
            'revision_requested_count': status_dict.get('revision_requested', 0),
            'by_type': type_dict,
            'by_theme': theme_dict,
            'committee_members_count': committee_count,
            'total_validations': total_validations,
        }
        
        return Response(stats)


class EPosterValidationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing validations
    Used for real-time committee tracking
    """
    queryset = EPosterValidation.objects.all()
    serializer_class = EPosterValidationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = EPosterValidation.objects.all()
        
        # Filter by submission
        submission_id = self.request.query_params.get('submission_id')
        if submission_id:
            queryset = queryset.filter(submission_id=submission_id)
        
        # Filter by event
        event_id = self.request.query_params.get('event_id')
        if event_id:
            queryset = queryset.filter(submission__event_id=event_id)
        
        # Filter by committee member
        member_id = self.request.query_params.get('member_id')
        if member_id:
            queryset = queryset.filter(committee_member_id=member_id)
        
        return queryset.select_related('submission', 'committee_member')


class EPosterCommitteeMemberViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing committee members
    """
    queryset = EPosterCommitteeMember.objects.all()
    serializer_class = CommitteeMemberSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = EPosterCommitteeMember.objects.all()
        
        event_id = self.request.query_params.get('event_id')
        if event_id:
            queryset = queryset.filter(event_id=event_id)
        
        return queryset.select_related('user', 'event')
    
    def perform_create(self, serializer):
        serializer.save(assigned_by=self.request.user)


class EPosterEmailTemplateViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing ePoster email templates
    """
    queryset = EPosterEmailTemplate.objects.all()
    serializer_class = EPosterEmailTemplateSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = EPosterEmailTemplate.objects.all()
        
        event_id = self.request.query_params.get('event_id')
        if event_id:
            queryset = queryset.filter(event_id=event_id)
        
        return queryset.select_related('event')
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


# Public submission endpoint (for form without authentication)
@api_view(['POST'])
@permission_classes([AllowAny])
def public_eposter_submit(request, event_id):
    """
    Public endpoint for ePoster submission
    No authentication required
    """
    from .models_eposter import EventFormConfiguration
    
    event = get_object_or_404(Event, id=event_id)
    
    # Get or create the form configuration (forms always exist)
    config, created = EventFormConfiguration.objects.get_or_create(
        event=event,
        form_type='communicant',
        defaults={
            'is_active': True,
        }
    )
    
    # Check if the form is active
    if not config.is_active:
        return Response(
            {'error': 'The Call for Communicants form is currently closed and not accepting submissions'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Build data dict manually to avoid deepcopy issues with file objects
    data = {}
    for key in request.data:
        data[key] = request.data[key]
    data['event'] = event.id
    
    # Handle auteurs JSON parsing if it's a string
    if 'auteurs' in data and isinstance(data['auteurs'], str):
        try:
            import json
            data['auteurs'] = json.loads(data['auteurs'])
        except (json.JSONDecodeError, TypeError):
            data['auteurs'] = []
    
    serializer = EPosterSubmissionCreateSerializer(data=data)
    if not serializer.is_valid():
        print(f"ePoster submission validation errors: {serializer.errors}")
        return Response({
            'success': False,
            'error': 'Validation error',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Get IP address
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    
    submission = serializer.save(
        ip_address=ip,
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:500]
    )
    
    # Submission confirmation emails are not used - only acceptance/rejection emails
    # No email sent at submission time
    
    return Response({
        'success': True,
        'message': 'Votre soumission a été reçue avec succès. Vous recevrez un email de confirmation.',
        'submission_id': str(submission.id)
    }, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def realtime_validation_status(request, submission_id):
    """
    Get real-time validation status for a submission
    Returns all validations and their status
    """
    submission = get_object_or_404(EPosterSubmission, id=submission_id)
    
    # Check if user is committee member for this event
    is_member = EPosterCommitteeMember.objects.filter(
        event=submission.event,
        user=request.user,
        is_active=True
    ).exists()
    
    if not is_member and not request.user.is_staff:
        return Response(
            {'error': 'Access denied'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    validations = EPosterValidation.objects.filter(
        submission=submission
    ).select_related('committee_member')
    
    # Get all committee members
    committee = EPosterCommitteeMember.objects.filter(
        event=submission.event,
        is_active=True
    ).select_related('user')
    
    # Build response with who has/hasn't voted
    voted_ids = set(v.committee_member_id for v in validations)
    
    committee_status = []
    for member in committee:
        validation = next(
            (v for v in validations if v.committee_member_id == member.user_id),
            None
        )
        committee_status.append({
            'member_id': member.user_id,
            'member_name': member.user.get_full_name() or member.user.username,
            'role': member.get_role_display(),
            'has_voted': member.user_id in voted_ids,
            'vote': {
                'is_approved': validation.is_approved,
                'comments': validation.comments,
                'rating': validation.rating,
                'validated_at': validation.validated_at.isoformat()
            } if validation else None
        })
    
    return Response({
        'submission': EPosterSubmissionSerializer(submission).data,
        'committee_status': committee_status,
        'validations_count': submission.get_validations_count(),
        'rejections_count': submission.get_rejections_count(),
        'validations_required': submission.validations_required,
        'can_be_approved': submission.get_validations_count() >= submission.validations_required
    })
