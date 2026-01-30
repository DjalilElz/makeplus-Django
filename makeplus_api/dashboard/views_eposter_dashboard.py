"""
ePoster Dashboard Views
Admin dashboard views for managing ePoster submissions
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.utils import timezone
from django.core.mail import send_mail
from django.template import Template, Context
from django.conf import settings
from django.contrib.auth.models import User
import json
import csv

from events.models import Event
from .models_eposter import (
    EPosterSubmission,
    EPosterValidation,
    EPosterCommitteeMember,
    EPosterEmailTemplate
)


@login_required
def eposter_dashboard(request, event_id):
    """
    Main ePoster dashboard for an event
    Shows statistics and overview
    """
    event = get_object_or_404(Event, id=event_id)
    
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
    
    # By type stats
    by_type = submissions.values('type_participation').annotate(
        count=Count('id')
    ).order_by('-count')
    
    context = {
        'event': event,
        'stats': stats,
        'recent_submissions': recent_submissions,
        'committee': committee,
        'by_type': by_type,
    }
    
    return render(request, 'dashboard/eposter/dashboard.html', context)


@login_required
def eposter_submissions_list(request, event_id):
    """
    List all ePoster submissions for an event
    With filtering and search
    """
    event = get_object_or_404(Event, id=event_id)
    
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
    
    return render(request, 'dashboard/eposter/submissions_list.html', context)


@login_required
def eposter_submission_detail(request, event_id, submission_id):
    """
    View detailed submission with validation interface
    """
    event = get_object_or_404(Event, id=event_id)
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
    }
    
    return render(request, 'dashboard/eposter/submission_detail.html', context)


@login_required
def eposter_validate_submission(request, event_id, submission_id):
    """
    Handle committee member validation
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
    rating = request.POST.get('rating')
    
    # Create or update validation
    validation, created = EPosterValidation.objects.update_or_create(
        submission=submission,
        committee_member=request.user,
        defaults={
            'is_approved': is_approved,
            'comments': comments,
            'rating': int(rating) if rating else None,
        }
    )
    
    # Check if status should change
    status_changed = submission.check_and_update_status()
    
    # Send email if status changed
    if status_changed:
        send_decision_email(submission)
    
    return JsonResponse({
        'success': True,
        'validation': {
            'id': str(validation.id),
            'is_approved': validation.is_approved,
            'comments': validation.comments,
            'rating': validation.rating,
        },
        'submission_status': submission.status,
        'status_changed': status_changed,
        'validations_count': submission.get_validations_count(),
        'rejections_count': submission.get_rejections_count(),
    })


@login_required
def eposter_set_status(request, event_id, submission_id):
    """
    Manually set submission status (admin/president only)
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    event = get_object_or_404(Event, id=event_id)
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
        send_decision_email(submission)
    
    messages.success(request, f'Statut mis à jour: {submission.get_status_display()}')
    
    return redirect('dashboard:eposter_submission_detail', event_id=event_id, submission_id=submission_id)


def send_decision_email(submission):
    """Helper to send acceptance/rejection email"""
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
                'rejection_reason': submission.rejection_reason,
            }
            
            subject = Template(template.subject).render(Context(context))
            body = Template(template.body_html).render(Context(context))
            
            send_mail(
                subject=subject,
                message=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[submission.email],
                html_message=body,
                fail_silently=True
            )
            
            if submission.status == 'accepted':
                submission.acceptance_email_sent = True
            else:
                submission.rejection_email_sent = True
            submission.save(update_fields=['acceptance_email_sent', 'rejection_email_sent'])
    except Exception as e:
        print(f"Error sending email: {e}")


@login_required
def eposter_committee_list(request, event_id):
    """
    List and manage committee members
    """
    event = get_object_or_404(Event, id=event_id)
    
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
    
    context = {
        'event': event,
        'committee': committee,
        'available_users': available_users,
        'role_choices': EPosterCommitteeMember.ROLE_CHOICES,
    }
    
    return render(request, 'dashboard/eposter/committee_list.html', context)


@login_required
def eposter_committee_add(request, event_id):
    """
    Add a committee member
    """
    if request.method != 'POST':
        return redirect('dashboard:eposter_committee_list', event_id=event_id)
    
    event = get_object_or_404(Event, id=event_id)
    
    user_id = request.POST.get('user_id')
    role = request.POST.get('role', 'member')
    specialty = request.POST.get('specialty', '')
    
    user = get_object_or_404(User, id=user_id)
    
    # Check if already exists
    existing = EPosterCommitteeMember.objects.filter(event=event, user=user).first()
    if existing:
        messages.warning(request, f'{user.get_full_name() or user.username} est déjà membre du comité')
        return redirect('dashboard:eposter_committee_list', event_id=event_id)
    
    EPosterCommitteeMember.objects.create(
        event=event,
        user=user,
        role=role,
        specialty=specialty,
        assigned_by=request.user
    )
    
    messages.success(request, f'{user.get_full_name() or user.username} ajouté au comité')
    return redirect('dashboard:eposter_committee_list', event_id=event_id)


@login_required
def eposter_committee_remove(request, event_id, member_id):
    """
    Remove a committee member
    """
    event = get_object_or_404(Event, id=event_id)
    member = get_object_or_404(EPosterCommitteeMember, id=member_id, event=event)
    
    member_name = member.user.get_full_name() or member.user.username
    member.delete()
    
    messages.success(request, f'{member_name} retiré du comité')
    return redirect('dashboard:eposter_committee_list', event_id=event_id)


@login_required
def eposter_email_templates(request, event_id):
    """
    Manage ePoster email templates
    """
    event = get_object_or_404(Event, id=event_id)
    
    templates = EPosterEmailTemplate.objects.filter(event=event)
    
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
    
    return render(request, 'dashboard/eposter/email_templates.html', context)


@login_required
def eposter_email_template_create(request, event_id):
    """
    Create new email template
    """
    event = get_object_or_404(Event, id=event_id)
    
    if request.method == 'POST':
        template_type = request.POST.get('template_type')
        subject = request.POST.get('subject')
        body_html = request.POST.get('body_html')
        body_text = request.POST.get('body_text', '')
        
        # Check if already exists
        if EPosterEmailTemplate.objects.filter(event=event, template_type=template_type).exists():
            messages.error(request, 'Un template de ce type existe déjà')
            return redirect('dashboard:eposter_email_templates', event_id=event_id)
        
        EPosterEmailTemplate.objects.create(
            event=event,
            template_type=template_type,
            subject=subject,
            body_html=body_html,
            body_text=body_text,
            created_by=request.user
        )
        
        messages.success(request, 'Template créé avec succès')
        return redirect('dashboard:eposter_email_templates', event_id=event_id)
    
    # GET - show create form
    template_type = request.GET.get('type', '')
    
    # Default templates
    defaults = {
        'submission_received': {
            'subject': 'Confirmation de soumission - {{event_name}}',
            'body_html': '''
<p>Bonjour {{prenom}} {{nom}},</p>
<p>Nous avons bien reçu votre soumission intitulée "<strong>{{titre}}</strong>" pour l'événement {{event_name}}.</p>
<p>Votre soumission est en cours d'évaluation par notre comité scientifique. Vous recevrez une notification dès que la décision sera prise.</p>
<p>Cordialement,<br>L'équipe organisatrice</p>
'''
        },
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
{% if rejection_reason %}<p><strong>Motif:</strong> {{rejection_reason}}</p>{% endif %}
<p>Nous vous encourageons à soumettre de nouveau lors de nos prochains événements.</p>
<p>Cordialement,<br>L'équipe organisatrice</p>
'''
        },
        'revision_requested': {
            'subject': 'Révision demandée pour votre soumission - {{event_name}}',
            'body_html': '''
<p>Bonjour {{prenom}} {{nom}},</p>
<p>Concernant votre soumission intitulée "<strong>{{titre}}</strong>" pour l'événement {{event_name}}, notre comité scientifique souhaite que vous apportiez quelques modifications.</p>
<p>Veuillez nous contacter pour plus de détails.</p>
<p>Cordialement,<br>L'équipe organisatrice</p>
'''
        }
    }
    
    context = {
        'event': event,
        'template_type': template_type,
        'type_choices': EPosterEmailTemplate.TYPE_CHOICES,
        'defaults': defaults.get(template_type, {'subject': '', 'body_html': ''}),
    }
    
    return render(request, 'dashboard/eposter/email_template_form.html', context)


@login_required
def eposter_email_template_edit(request, event_id, template_id):
    """
    Edit email template
    """
    event = get_object_or_404(Event, id=event_id)
    template = get_object_or_404(EPosterEmailTemplate, id=template_id, event=event)
    
    if request.method == 'POST':
        template.subject = request.POST.get('subject')
        template.body_html = request.POST.get('body_html')
        template.body_text = request.POST.get('body_text', '')
        template.is_active = request.POST.get('is_active') == 'on'
        template.save()
        
        messages.success(request, 'Template mis à jour')
        return redirect('dashboard:eposter_email_templates', event_id=event_id)
    
    context = {
        'event': event,
        'template': template,
        'type_choices': EPosterEmailTemplate.TYPE_CHOICES,
    }
    
    return render(request, 'dashboard/eposter/email_template_form.html', context)


@login_required
def eposter_email_template_delete(request, event_id, template_id):
    """
    Delete email template
    """
    event = get_object_or_404(Event, id=event_id)
    template = get_object_or_404(EPosterEmailTemplate, id=template_id, event=event)
    
    template.delete()
    messages.success(request, 'Template supprimé')
    
    return redirect('dashboard:eposter_email_templates', event_id=event_id)


@login_required
def eposter_export_csv(request, event_id):
    """
    Export submissions to CSV
    """
    event = get_object_or_404(Event, id=event_id)
    submissions = EPosterSubmission.objects.filter(event=event).order_by('-submitted_at')
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="eposters_{event.name}_{timezone.now().date()}.csv"'
    response.write('\ufeff')  # UTF-8 BOM for Excel
    
    writer = csv.writer(response, delimiter=';')
    writer.writerow([
        'ID', 'Date soumission', 'Statut',
        'Nom', 'Prénom', 'Email', 'Téléphone', 'Genre',
        'Grade', 'Service', 'Établissement', 'Wilaya',
        'Type', 'Thème', 'Titre',
        'Validations', 'Rejets'
    ])
    
    for s in submissions:
        writer.writerow([
            str(s.id), s.submitted_at.strftime('%Y-%m-%d %H:%M'), s.get_status_display(),
            s.nom, s.prenom, s.email, s.telephone, s.get_genre_display(),
            s.get_grade_display(), s.service, s.etablissement, s.wilaya,
            s.get_type_participation_display(), s.theme, s.titre_travail,
            s.get_validations_count(), s.get_rejections_count()
        ])
    
    return response


@login_required  
def eposter_realtime_status(request, event_id, submission_id):
    """
    Get real-time status for a submission (AJAX endpoint for polling)
    """
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
