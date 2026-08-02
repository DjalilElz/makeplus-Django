"""
ePoster Dashboard Views
Admin dashboard views for managing ePoster submissions
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse, HttpResponseForbidden
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.utils import timezone
from django.core.mail import send_mail
from django.template import Template, Context
from django.conf import settings
from django.contrib.auth.models import User
import json
import csv

from events.models import (
    Event, UserEventAssignment, Participant, UserProfile, ParticipantEventRegistration
)
from .models_eposter import (
    EPosterSubmission,
    EPosterValidation,
    EPosterCommitteeMember,
    EPosterEmailTemplate
)


def check_event_access(user, event):
    """
    Check if user has access to the event's ePoster submissions (view + decide).
    Returns True if user is staff/superuser OR is an active committee member
    (member or supervisor) for this event.
    """
    if user.is_staff or user.is_superuser:
        return True

    return EPosterCommitteeMember.objects.filter(
        user=user,
        event=event,
        is_active=True
    ).exists()


def get_supervisor_membership(user, event):
    """
    Returns the user's active EPosterCommitteeMember row for this event if
    they are a supervisor (or legacy president), otherwise None.
    """
    if not user.is_authenticated:
        return None
    membership = EPosterCommitteeMember.objects.filter(
        user=user,
        event=event,
        is_active=True
    ).first()
    if membership and membership.is_supervisor():
        return membership
    return None


def check_supervisor_access(user, event):
    """
    Committee stats dashboard and member-management are supervisor/staff
    only -- plain committee members can view + decide on submissions but
    get none of that visibility (see check_event_access for their access).
    """
    if user.is_staff or user.is_superuser:
        return True
    return get_supervisor_membership(user, event) is not None


@login_required
def eposter_dashboard(request, event_id):
    """
    Main ePoster dashboard for an event
    Shows statistics and overview
    """
    event = get_object_or_404(Event, id=event_id)

    # The stats dashboard (who-decided-what, counts per type) is
    # supervisor/staff only -- plain members only get the submissions list.
    if not check_supervisor_access(request.user, event):
        messages.error(request, "Seul le superviseur du comité ou un administrateur peut voir ce tableau de bord.")
        return redirect('dashboard:contributions_submissions_list', event_id=event.id)

    # Get statistics
    submissions = EPosterSubmission.objects.filter(event=event)
    stats = {
        'total': submissions.count(),
        'pending': submissions.filter(status='pending').count(),
        'accepted': submissions.filter(status='accepted').count(),
        'rejected': submissions.filter(status='rejected').count(),
        'revision': submissions.filter(status='revision_requested').count(),
    }
    
    # Recent submissions
    recent_submissions = submissions.order_by('-submitted_at')[:10]
    
    # Committee members
    committee = EPosterCommitteeMember.objects.filter(
        event=event, 
        is_active=True
    ).select_related('user')
    
    # By type stats -- resolved to a plain list of dicts (not a lazy
    # QuerySet) with a human-readable label, both for the template's
    # {{ by_type|json_script }} (json.dumps can't serialize a QuerySet)
    # and so the chart doesn't have to show raw type_participation codes.
    type_labels = dict(EPosterSubmission.TYPE_PARTICIPATION_CHOICES)
    by_type = [
        {
            'type_participation': row['type_participation'],
            'label': type_labels.get(row['type_participation'], row['type_participation']),
            'count': row['count'],
        }
        for row in submissions.values('type_participation').annotate(count=Count('id')).order_by('-count')
    ]

    # Who decided what -- the supervisor's "see who validated/rejected each
    # submission" view. Each submission has a single, final decider now
    # (see eposter_validate_submission), so this is just the decided
    # submissions with their decider, most recent first.
    recent_decisions = submissions.filter(
        status__in=['accepted', 'rejected'],
        final_decision_by__isnull=False,
    ).select_related('final_decision_by').order_by('-final_decision_date')[:20]

    context = {
        'event': event,
        'stats': stats,
        'recent_submissions': recent_submissions,
        'committee': committee,
        'by_type': by_type,
        'recent_decisions': recent_decisions,
    }

    return render(request, 'dashboard/eposter/dashboard.html', context)


@login_required
def eposter_submissions_list(request, event_id):
    """
    List all ePoster submissions for an event
    With filtering and search
    """
    from django.core.cache import cache
    from django.views.decorators.cache import never_cache
    
    event = get_object_or_404(Event, id=event_id)
    
    # Check access permission
    if not check_event_access(request.user, event):
        messages.error(request, "Vous n'avez pas accès à cet événement.")
        return redirect('dashboard:contributions_management_home')
    
    # Clear cache to ensure fresh data
    cache.clear()
    
    submissions = EPosterSubmission.objects.filter(event=event)
    
    # Filters
    status_filter = request.GET.get('status', '')
    type_filter = request.GET.get('type', '')
    search = request.GET.get('search', '')
    
    if status_filter:
        submissions = submissions.filter(status=status_filter)
    
    if type_filter:
        submissions = submissions.filter(type_participation=type_filter)
    
    if search:
        submissions = submissions.filter(
            Q(nom__icontains=search) |
            Q(prenom__icontains=search) |
            Q(titre_travail__icontains=search) |
            Q(email__icontains=search) |
            Q(etablissement__icontains=search)
        )
    
    # Annotate with validation counts
    submissions = submissions.annotate(
        validations_count=Count('validations', filter=Q(validations__is_approved=True)),
        rejections_count=Count('validations', filter=Q(validations__is_approved=False))
    ).order_by('-submitted_at')
    
    # Pagination
    paginator = Paginator(submissions, 20)
    page = request.GET.get('page', 1)
    submissions_page = paginator.get_page(page)
    
    context = {
        'event': event,
        'submissions': submissions_page,
        'status_filter': status_filter,
        'type_filter': type_filter,
        'search': search,
        'status_choices': EPosterSubmission.STATUS_CHOICES,
        'type_choices': EPosterSubmission.TYPE_PARTICIPATION_CHOICES,
    }
    
    # Add no-cache headers
    response = render(request, 'dashboard/eposter/submissions_list.html', context)
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    
    return response


@login_required
def eposter_submission_detail(request, event_id, submission_id):
    """
    View detailed submission with validation interface
    """
    event = get_object_or_404(Event, id=event_id)
    
    # Check access permission
    if not check_event_access(request.user, event):
        messages.error(request, "Vous n'avez pas accès à cet événement.")
        return redirect('dashboard:contributions_management_home')
    
    submission = get_object_or_404(
        EPosterSubmission.objects.prefetch_related('validations__committee_member'),
        id=submission_id,
        event=event
    )
    
    # Check if current user is a committee member
    user_membership = EPosterCommitteeMember.objects.filter(
        event=event,
        user=request.user,
        is_active=True
    ).first()
    
    # Get user's existing validation if any
    user_validation = None
    if user_membership:
        user_validation = EPosterValidation.objects.filter(
            submission=submission,
            committee_member=request.user
        ).first()
    
    # Get all committee members and their validation status
    committee = EPosterCommitteeMember.objects.filter(
        event=event,
        is_active=True
    ).select_related('user')
    
    committee_status = []
    for member in committee:
        validation = submission.validations.filter(
            committee_member=member.user
        ).first()
        committee_status.append({
            'member': member,
            'validation': validation
        })
    
    context = {
        'event': event,
        'submission': submission,
        'user_membership': user_membership,
        'user_validation': user_validation,
        'committee_status': committee_status,
        'can_validate': user_membership is not None and submission.status == 'pending',
        # Only supervisors/staff see who made the final decision -- plain
        # members just see the resulting status (pending/accepted/rejected).
        'is_supervisor': check_supervisor_access(request.user, event),
    }

    return render(request, 'dashboard/eposter/submission_detail.html', context)


@login_required
def eposter_validate_submission(request, event_id, submission_id):
    """
    Handle committee member validation
    One committee member's decision is final - no voting system
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    event = get_object_or_404(Event, id=event_id)
    submission = get_object_or_404(EPosterSubmission, id=submission_id, event=event)
    
    # Check if user is committee member
    membership = EPosterCommitteeMember.objects.filter(
        event=event,
        user=request.user,
        is_active=True
    ).first()
    
    if not membership:
        return JsonResponse({'error': 'Vous n\'êtes pas membre du comité'}, status=403)
    
    if submission.status != 'pending':
        return JsonResponse({'error': 'Cette soumission n\'est plus en attente'}, status=400)
    
    # Get validation data
    is_approved = request.POST.get('is_approved') == 'true'
    comments = request.POST.get('comments', '')
    
    # Create or update validation (no rating needed)
    validation, created = EPosterValidation.objects.update_or_create(
        submission=submission,
        committee_member=request.user,
        defaults={
            'is_approved': is_approved,
            'comments': comments,
            'rating': None,  # No rating system
        }
    )
    
    # Immediately update submission status based on this single decision
    if is_approved:
        submission.status = 'accepted'
    else:
        submission.status = 'rejected'
    
    submission.final_decision_date = timezone.now()
    submission.final_decision_by = request.user
    submission.save()
    
    print(f"Submission {submission.id} status updated to: {submission.status}")
    
    # Send decision email
    email_sent = False
    try:
        email_sent = send_decision_email(submission, request=request)
        if email_sent:
            print(f"Decision email sent successfully for submission {submission.id}")
        else:
            print(f"Failed to send decision email for submission {submission.id}")
    except Exception as e:
        print(f"Exception while sending decision email: {e}")
        import traceback
        traceback.print_exc()
    
    return JsonResponse({
        'success': True,
        'email_sent': email_sent,
        'validation': {
            'id': str(validation.id),
            'is_approved': validation.is_approved,
            'comments': validation.comments,
        },
        'submission_status': submission.status,
        'status_changed': True,
    })


@login_required
def eposter_set_status(request, event_id, submission_id):
    """
    Manually set submission status (admin/president only)
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    event = get_object_or_404(Event, id=event_id)
    
    # Check access permission
    if not check_event_access(request.user, event):
        return JsonResponse({'error': "You don't have access to this event."}, status=403)
    
    submission = get_object_or_404(EPosterSubmission, id=submission_id, event=event)
    
    # Check if user is president or admin
    is_president = EPosterCommitteeMember.objects.filter(
        event=event,
        user=request.user,
        role='president',
        is_active=True
    ).exists()
    
    if not is_president and not request.user.is_staff:
        return JsonResponse(
            {'error': 'Seul le président du comité ou un admin peut modifier le statut'},
            status=403
        )
    
    new_status = request.POST.get('status')
    if new_status not in ['pending', 'accepted', 'rejected', 'revision_requested']:
        return JsonResponse({'error': 'Statut invalide'}, status=400)
    
    submission.status = new_status
    submission.final_decision_by = request.user
    submission.final_decision_date = timezone.now()
    
    if new_status == 'rejected':
        submission.rejection_reason = request.POST.get('rejection_reason', '')
    
    submission.save()
    
    # Send email
    if new_status in ['accepted', 'rejected']:
        send_decision_email(submission, request=request)
    
    messages.success(request, f'Statut mis à jour: {submission.get_status_display()}')
    
    return redirect('dashboard:contributions_submission_detail', event_id=event_id, submission_id=submission_id)


def send_decision_email(submission, request=None):
    """Helper to send acceptance/rejection email using Brevo API"""
    from .email_sender import send_email

    try:
        # Determine template type based on submission type and decision
        decision = 'accepted' if submission.status == 'accepted' else 'rejected'
        template_type = f"{submission.type_participation}_{decision}"
        
        template = EPosterEmailTemplate.objects.filter(
            event=submission.event,
            template_type=template_type,
            is_active=True
        ).first()
        
        if not template:
            print(f"No email template found for type '{template_type}' and event '{submission.event.name}'")
            return False
        
        # Generate contribution code if accepted and not already generated
        # Only for e_poster and communication_orale types
        if submission.status == 'accepted' and not submission.contribution_code:
            if submission.requires_final_submission():
                submission.generate_contribution_code()
                submission.save(update_fields=['contribution_code'])
        
        # Build final submission URL (only for types that require final submission).
        # Derived from the actual incoming request whenever one is available,
        # not the SITE_URL setting -- that env var has drifted to a retired
        # domain before (makeplus-platform.onrender.com) and silently sent
        # dead links in acceptance emails until the env var itself is fixed.
        final_submission_url = ''
        show_final_submission = False
        if submission.status == 'accepted' and submission.requires_final_submission():
            show_final_submission = True
            if request is not None:
                base_url = request.build_absolute_uri('/').rstrip('/')
            else:
                base_url = getattr(settings, 'SITE_URL', 'https://makeplus-events.onrender.com')

            # Generate URL based on submission type
            if submission.type_participation == 'e_poster':
                final_submission_url = f"{base_url}/contributions/final-submission/eposter/{submission.event.id}/"
            elif submission.type_participation == 'communication_orale':
                final_submission_url = f"{base_url}/contributions/final-submission/communication/{submission.event.id}/"
            else:
                final_submission_url = ''
        
        # Get committee member's remarks/comments from the validation
        remarque = ''
        if submission.final_decision_by:
            validation = EPosterValidation.objects.filter(
                submission=submission,
                committee_member=submission.final_decision_by
            ).first()
            if validation and validation.comments:
                remarque = validation.comments
        
        # Get contribution number (for e-poster and communication orale only)
        contribution_number = submission.contribution_code if submission.contribution_code else ''
        
        context = {
            'nom': submission.nom,
            'prenom': submission.prenom,
            'titre': submission.titre_travail,
            'event_name': submission.event.name,
            'event_location': submission.event.location or '',
            'event_start_date': submission.event.start_date.strftime('%d/%m/%Y') if submission.event.start_date else '',
            'event_end_date': submission.event.end_date.strftime('%d/%m/%Y') if submission.event.end_date else '',
            'contribution_number': contribution_number,
            'remarque': remarque,
            'final_submission_url': final_submission_url if show_final_submission else '',
            'type_participation': submission.get_type_participation_display(),
            'show_final_submission': show_final_submission,
        }
        
        subject = Template(template.subject).render(Context(context))
        body = Template(template.body_html).render(Context(context))
        
        print(f"Sending {template_type} email to {submission.email} via Brevo API")
        print(f"Subject: {subject}")
        if submission.status == 'accepted':
            print(f"Contribution Code: {submission.contribution_code}")
            print(f"Final Submission URL: {final_submission_url}")
        
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
            print(f"Email sent successfully via Brevo API to {submission.email}, message_id: {message_id}")
            
            if submission.status == 'accepted':
                submission.acceptance_email_sent = True
            else:
                submission.rejection_email_sent = True
            submission.save(update_fields=['acceptance_email_sent', 'rejection_email_sent'])
            
            return True
        else:
            print(f"Failed to send email via Brevo API: {error}")
            return False
            
    except Exception as e:
        print(f"Error sending decision email: {e}")
        import traceback
        traceback.print_exc()
        return False


@login_required
def eposter_committee_list(request, event_id):
    """
    List and manage committee members.
    Staff/admin can manage any event's committee; a committee supervisor
    can manage their own event's committee too (member accounts only).
    """
    event = get_object_or_404(Event, id=event_id)

    is_admin = request.user.is_staff or request.user.is_superuser
    is_supervisor = get_supervisor_membership(request.user, event) is not None
    if not is_admin and not is_supervisor:
        messages.error(request, "Seul un administrateur ou le superviseur du comité peut gérer les membres du comité.")
        return redirect('dashboard:contributions_management_home')

    committee = EPosterCommitteeMember.objects.filter(
        event=event
    ).select_related('user', 'assigned_by').annotate(
        validations_count=Count('user__eposter_validations', filter=Q(user__eposter_validations__submission__event=event))
    ).order_by('-assigned_at')

    # Get available users - only users with 'committee' role assigned to this event
    existing_member_ids = committee.values_list('user_id', flat=True)
    from events.models import UserEventAssignment
    committee_user_ids = UserEventAssignment.objects.filter(
        event=event,
        role='committee',
        is_active=True
    ).values_list('user_id', flat=True)

    available_users = User.objects.filter(
        id__in=committee_user_ids
    ).exclude(
        id__in=existing_member_ids
    ).order_by('first_name', 'last_name')

    # A supervisor may only create plain members; only staff/admin can hand
    # out the supervisor role itself.
    role_choices = EPosterCommitteeMember.ROLE_CHOICES if is_admin else [('member', 'Membre')]

    context = {
        'event': event,
        'committee': committee,
        'available_users': available_users,
        'role_choices': role_choices,
        'is_admin': is_admin,
        'is_supervisor': is_supervisor,
    }

    return render(request, 'dashboard/eposter/committee_list.html', context)


@login_required
def eposter_committee_add(request, event_id):
    """
    Add a committee member.
    Staff/admin can add any role; a committee supervisor can only add
    plain members (their own role, or another supervisor, can't be
    self-granted this way).
    """
    event = get_object_or_404(Event, id=event_id)

    is_admin = request.user.is_staff or request.user.is_superuser
    is_supervisor = get_supervisor_membership(request.user, event) is not None
    if not is_admin and not is_supervisor:
        messages.error(request, "Seul un administrateur ou le superviseur du comité peut gérer les membres du comité.")
        return redirect('dashboard:contributions_management_home')

    if request.method != 'POST':
        return redirect('dashboard:contributions_committee_list', event_id=event_id)

    user_id = request.POST.get('user_id')
    role = request.POST.get('role', 'member')
    specialty = request.POST.get('specialty', '')

    # Supervisors can only create plain members, regardless of what the
    # submitted form said.
    if not is_admin:
        role = 'member'

    user = get_object_or_404(User, id=user_id)

    # Check if already exists
    existing = EPosterCommitteeMember.objects.filter(event=event, user=user).first()
    if existing:
        messages.warning(request, f'{user.get_full_name() or user.username} est déjà membre du comité')
        return redirect('dashboard:contributions_committee_list', event_id=event_id)
    
    EPosterCommitteeMember.objects.create(
        event=event,
        user=user,
        role=role,
        specialty=specialty,
        assigned_by=request.user
    )
    
    messages.success(request, f'{user.get_full_name() or user.username} ajouté au comité')
    return redirect('dashboard:contributions_committee_list', event_id=event_id)


@login_required
def eposter_committee_remove(request, event_id, member_id):
    """
    Remove a committee member.
    Staff/admin can remove anyone; a supervisor can only remove plain
    members -- not another supervisor.
    """
    event = get_object_or_404(Event, id=event_id)
    member = get_object_or_404(EPosterCommitteeMember, id=member_id, event=event)

    is_admin = request.user.is_staff or request.user.is_superuser
    is_supervisor = get_supervisor_membership(request.user, event) is not None

    if not is_admin:
        if not is_supervisor:
            messages.error(request, "Seul un administrateur ou le superviseur du comité peut gérer les membres du comité.")
            return redirect('dashboard:contributions_management_home')
        if member.is_supervisor():
            messages.error(request, "Un superviseur ne peut pas retirer un autre superviseur du comité.")
            return redirect('dashboard:contributions_committee_list', event_id=event_id)

    member_name = member.user.get_full_name() or member.user.username
    member.delete()

    messages.success(request, f'{member_name} retiré du comité')
    return redirect('dashboard:contributions_committee_list', event_id=event_id)


@login_required
def eposter_committee_update_role(request, event_id, member_id):
    """
    Promote/demote a committee member between 'member' and 'supervisor'.
    Staff/admin only -- a supervisor can add plain members but can't grant
    the supervisor role themselves (see eposter_committee_add).
    """
    if request.method != 'POST':
        return redirect('dashboard:contributions_committee_list', event_id=event_id)

    event = get_object_or_404(Event, id=event_id)

    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, "Seuls les administrateurs peuvent changer le rôle d'un membre du comité.")
        return redirect('dashboard:contributions_committee_list', event_id=event_id)

    member = get_object_or_404(EPosterCommitteeMember, id=member_id, event=event)

    new_role = request.POST.get('role')
    if new_role not in ('member', 'supervisor'):
        messages.error(request, "Rôle invalide.")
        return redirect('dashboard:contributions_committee_list', event_id=event_id)

    member.role = new_role
    member.save(update_fields=['role'])

    messages.success(
        request,
        f'{member.user.get_full_name() or member.user.username} est maintenant '
        f'{"Superviseur" if new_role == "supervisor" else "Membre"} du comité.'
    )
    return redirect('dashboard:contributions_committee_list', event_id=event_id)


@login_required
def eposter_committee_create_member(request, event_id):
    """
    Create a brand-new user and add them straight to this event's
    scientific committee, without leaving this page. Unlike the general
    /dashboard/users/create/ flow (which any committee member can reach
    and which can create any role for any event), this is scoped to
    committee-only creation for THIS event, and works for a supervisor,
    not just staff/admin.
    """
    event = get_object_or_404(Event, id=event_id)

    is_admin = request.user.is_staff or request.user.is_superuser
    is_supervisor = get_supervisor_membership(request.user, event) is not None
    if not is_admin and not is_supervisor:
        messages.error(request, "Seul un administrateur ou le superviseur du comité peut gérer les membres du comité.")
        return redirect('dashboard:contributions_management_home')

    if request.method != 'POST':
        return redirect('dashboard:contributions_committee_list', event_id=event_id)

    email = request.POST.get('email', '').strip().lower()
    first_name = request.POST.get('first_name', '').strip()
    last_name = request.POST.get('last_name', '').strip()
    password = request.POST.get('password', '')
    specialty = request.POST.get('specialty', '').strip()

    # A supervisor can only ever create plain members, regardless of what
    # the submitted form said (mirrors eposter_committee_add).
    committee_role = request.POST.get('committee_role', 'member')
    if not is_admin or committee_role not in ('member', 'supervisor'):
        committee_role = 'member'

    if not email or not first_name or not last_name or not password:
        messages.error(request, "Tous les champs sont obligatoires.")
        return redirect('dashboard:contributions_committee_list', event_id=event_id)

    if len(password) < 8:
        messages.error(request, "Le mot de passe doit contenir au moins 8 caractères.")
        return redirect('dashboard:contributions_committee_list', event_id=event_id)

    if User.objects.filter(email__iexact=email).exists():
        messages.error(request, f"Un utilisateur avec l'e-mail « {email} » existe déjà.")
        return redirect('dashboard:contributions_committee_list', event_id=event_id)

    base_username = email.split('@')[0]
    username = base_username
    counter = 1
    while User.objects.filter(username=username).exists():
        username = f"{base_username}{counter}"
        counter += 1

    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
    )

    qr_data = UserProfile.get_qr_for_user(user)

    UserEventAssignment.objects.create(
        user=user, event=event, role='committee', is_active=True, assigned_by=request.user,
    )
    EPosterCommitteeMember.objects.create(
        event=event, user=user, role=committee_role, specialty=specialty,
        is_active=True, assigned_by=request.user,
    )

    participant, _ = Participant.objects.get_or_create(
        user=user,
        defaults={'badge_id': qr_data['badge_id'], 'qr_code_data': qr_data},
    )
    ParticipantEventRegistration.objects.get_or_create(participant=participant, event=event)

    messages.success(
        request,
        f'{user.get_full_name()} ajouté au comité en tant que '
        f'{"Superviseur" if committee_role == "supervisor" else "Membre"}.'
    )
    return redirect('dashboard:contributions_committee_list', event_id=event_id)


@login_required
def eposter_email_templates(request, event_id):
    """
    Manage ePoster email templates
    Only staff/admin can access this view
    """
    # Admin only
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, "Seuls les administrateurs peuvent gérer les modèles d'e-mail.")
        return redirect('dashboard:contributions_management_home')
    
    event = get_object_or_404(Event, id=event_id)
    
    # Clear cache to ensure fresh data
    from django.core.cache import cache
    cache.clear()
    
    templates = EPosterEmailTemplate.objects.filter(event=event).order_by('template_type')
    
    # Debug logging
    print(f"Templates for event {event.id}: {templates.count()}")
    for t in templates:
        print(f"  - {t.template_type}: {t.subject[:50]}")
    
    # Check which templates exist
    existing_types = set(t.template_type for t in templates)
    missing_types = [
        (t[0], t[1]) for t in EPosterEmailTemplate.TYPE_CHOICES 
        if t[0] not in existing_types
    ]
    
    context = {
        'event': event,
        'templates': templates,
        'missing_types': missing_types,
        'type_choices': EPosterEmailTemplate.TYPE_CHOICES,
    }
    
    response = render(request, 'dashboard/eposter/email_templates.html', context)
    # Add no-cache headers
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    
    return response


@login_required
def eposter_email_template_create(request, event_id):
    """
    Create new email template
    Only staff/admin can access this view
    """
    # Admin only
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, "Seuls les administrateurs peuvent gérer les modèles d'e-mail.")
        return redirect('dashboard:contributions_management_home')
    
    event = get_object_or_404(Event, id=event_id)
    
    if request.method == 'POST':
        template_type = request.POST.get('template_type')
        subject = request.POST.get('subject')
        body_html = request.POST.get('body_html')
        body_text = request.POST.get('body_text', '')
        design_json = request.POST.get('design_json', '{}')
        
        # Debug logging
        print(f"Creating template - Type: {template_type}, Subject: {subject[:50] if subject else 'None'}")
        print(f"Body HTML length: {len(body_html) if body_html else 0}")
        print(f"Design JSON length: {len(design_json) if design_json else 0}")
        
        # Validate required fields
        if not template_type or not subject or not body_html:
            messages.error(request, 'Tous les champs obligatoires doivent être remplis')
            return redirect('dashboard:contributions_email_template_create', event_id=event_id) + f'?type={template_type}'
        
        # Check if already exists
        if EPosterEmailTemplate.objects.filter(event=event, template_type=template_type).exists():
            messages.error(request, 'Un modèle de ce type existe déjà')
            return redirect('dashboard:contributions_email_templates', event_id=event_id)
        
        # Create template
        try:
            template = EPosterEmailTemplate.objects.create(
                event=event,
                template_type=template_type,
                subject=subject,
                body_html=body_html,
                body_text=body_text,
                design_json=design_json,
                created_by=request.user
            )
            print(f"Template created successfully: {template.id}")
            
            # Clear cache
            from django.core.cache import cache
            cache.clear()
            
            messages.success(request, 'Modèle créé avec succès')
            return redirect('dashboard:contributions_email_templates', event_id=event_id)
        except Exception as e:
            print(f"Error creating template: {e}")
            messages.error(request, f'Erreur lors de la création du modèle : {str(e)}')
            return redirect('dashboard:contributions_email_template_create', event_id=event_id) + f'?type={template_type}'
    
    # GET - show create form
    template_type = request.GET.get('type', '')
    
    # Default templates (only accepted and rejected)
    defaults = {
        'accepted': {
            'subject': 'Félicitations ! Votre soumission a été acceptée - {{event_name}}',
            'body_html': '''
<p>Bonjour {{prenom}} {{nom}},</p>
<p><strong>Félicitations !</strong> Nous avons le plaisir de vous informer que votre soumission intitulée "<strong>{{titre}}</strong>" a été acceptée pour l'événement {{event_name}}.</p>
<p>Nous vous contacterons prochainement avec les détails concernant la présentation de votre travail.</p>
<p>Cordialement,<br>L'équipe organisatrice</p>
'''
        },
        'rejected': {
            'subject': 'Résultat de votre soumission - {{event_name}}',
            'body_html': '''
<p>Bonjour {{prenom}} {{nom}},</p>
<p>Nous vous remercions pour votre soumission intitulée "<strong>{{titre}}</strong>" pour l'événement {{event_name}}.</p>
<p>Après examen par notre comité scientifique, nous regrettons de vous informer que votre soumission n'a pas été retenue.</p>
<p>Nous vous encourageons à soumettre de nouveau lors de nos prochains événements.</p>
<p>Cordialement,<br>L'équipe organisatrice</p>
'''
        }
    }
    
    # Determine which variables to show based on template type
    show_contribution_number = template_type in ['e_poster_accepted', 'communication_orale_accepted']
    show_final_submission = template_type in ['e_poster_accepted', 'communication_orale_accepted']
    
    context = {
        'event': event,
        'template_type': template_type,
        'type_choices': EPosterEmailTemplate.TYPE_CHOICES,
        'defaults': defaults.get(template_type, {'subject': '', 'body_html': ''}),
        'show_contribution_number': show_contribution_number,
        'show_final_submission': show_final_submission,
    }
    
    return render(request, 'dashboard/eposter/email_template_form_unlayer.html', context)


@login_required
def eposter_email_template_edit(request, event_id, template_id):
    """
    Edit email template
    Only staff/admin can access this view
    """
    # Admin only
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, "Seuls les administrateurs peuvent gérer les modèles d'e-mail.")
        return redirect('dashboard:contributions_management_home')
    
    event = get_object_or_404(Event, id=event_id)
    template = get_object_or_404(EPosterEmailTemplate, id=template_id, event=event)
    
    if request.method == 'POST':
        template.subject = request.POST.get('subject')
        template.body_html = request.POST.get('body_html')
        template.body_text = request.POST.get('body_text', '')
        template.design_json = request.POST.get('design_json', '{}')
        template.is_active = request.POST.get('is_active') == 'on'
        template.save()
        
        messages.success(request, 'Modèle mis à jour')
        return redirect('dashboard:contributions_email_templates', event_id=event_id)
    
    # Determine which variables to show based on template type
    show_contribution_number = template.template_type in ['e_poster_accepted', 'communication_orale_accepted']
    show_final_submission = template.template_type in ['e_poster_accepted', 'communication_orale_accepted']
    
    context = {
        'event': event,
        'template': template,
        'template_type': template.template_type,
        'type_choices': EPosterEmailTemplate.TYPE_CHOICES,
        'defaults': {'subject': '', 'body_html': ''},  # Empty defaults for edit mode
        'show_contribution_number': show_contribution_number,
        'show_final_submission': show_final_submission,
    }

    return render(request, 'dashboard/eposter/email_template_form_unlayer.html', context)


@login_required
def eposter_email_template_delete(request, event_id, template_id):
    """
    Delete email template
    Only staff/admin can access this view
    """
    # Admin only
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, "Seuls les administrateurs peuvent gérer les modèles d'e-mail.")
        return redirect('dashboard:contributions_management_home')
    
    event = get_object_or_404(Event, id=event_id)
    template = get_object_or_404(EPosterEmailTemplate, id=template_id, event=event)
    
    template.delete()
    messages.success(request, 'Modèle supprimé')
    
    return redirect('dashboard:contributions_email_templates', event_id=event_id)


@login_required
def eposter_export_csv(request, event_id):
    """
    Export submissions to CSV
    """
    event = get_object_or_404(Event, id=event_id)
    
    # Check access permission
    if not check_event_access(request.user, event):
        messages.error(request, "Vous n'avez pas accès à cet événement.")
        return redirect('dashboard:contributions_management_home')
    
    submissions = EPosterSubmission.objects.filter(event=event).order_by('-submitted_at')
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="eposters_{event.name}_{timezone.now().date()}.csv"'
    response.write('\ufeff')  # UTF-8 BOM for Excel
    
    writer = csv.writer(response, delimiter=';')
    writer.writerow([
        'ID', 'Date soumission', 'Statut',
        'Nom', 'Prénom', 'Email', 'Téléphone', 'Genre',
        'Grade', 'Secteur', 'Établissement', 'Wilaya',
        'Type', 'Thème', 'Titre',
        'Validations', 'Rejets'
    ])
    
    for s in submissions:
        writer.writerow([
            str(s.id), s.submitted_at.strftime('%Y-%m-%d %H:%M'), s.get_status_display(),
            s.nom, s.prenom, s.email, s.telephone, s.get_genre_display(),
            s.get_grade_display(), s.get_secteur_display(), s.etablissement, s.wilaya,
            s.get_type_participation_display(), s.theme, s.titre_travail,
            s.get_validations_count(), s.get_rejections_count()
        ])
    
    return response


@login_required  
def eposter_realtime_status(request, event_id, submission_id):
    """
    Get real-time status for a submission (AJAX endpoint for polling)
    """
    event = get_object_or_404(Event, id=event_id)
    
    # Check access permission
    if not check_event_access(request.user, event):
        return JsonResponse({'error': "You don't have access to this event."}, status=403)
    
    submission = get_object_or_404(
        EPosterSubmission,
        id=submission_id,
        event_id=event_id
    )
    
    validations = EPosterValidation.objects.filter(
        submission=submission
    ).select_related('committee_member')
    
    committee = EPosterCommitteeMember.objects.filter(
        event_id=event_id,
        is_active=True
    ).select_related('user')
    
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
                'validated_at': validation.validated_at.isoformat()
            } if validation else None
        })
    
    return JsonResponse({
        'status': submission.status,
        'status_display': submission.get_status_display(),
        'validations_count': submission.get_validations_count(),
        'rejections_count': submission.get_rejections_count(),
        'validations_required': submission.validations_required,
        'committee_status': committee_status,
    })
