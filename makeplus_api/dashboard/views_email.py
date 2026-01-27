"""Email template management views"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.db import models
from django.utils import timezone
from events.models import Event, Participant
from .models_email import EmailTemplate, EventEmailTemplate, EmailLog
import re


def replace_template_variables(text, context):
    """Replace template variables like {{event_name}} with actual values"""
    for key, value in context.items():
        text = text.replace(f"{{{{{key}}}}}", str(value))
    return text


@login_required
def email_template_list(request):
    """List all global email templates"""
    templates = EmailTemplate.objects.all().select_related('created_by').order_by('-created_at')
    
    # Debug info for troubleshooting
    if request.GET.get('debug'):
        messages.info(request, f'Found {templates.count()} email templates')
    
    context = {
        'templates': templates,
        'template_count': templates.count(),
    }
    return render(request, 'dashboard/email_template_list.html', context)


@login_required
def email_template_create(request):
    """Create a new global email template"""
    if request.method == 'POST':
        name = request.POST.get('name')
        subject = request.POST.get('subject')
        body = request.POST.get('body')
        description = request.POST.get('description', '')
        
        if not all([name, subject, body]):
            messages.error(request, 'Please fill in all required fields.')
            return redirect('dashboard:email_template_create')
        
        template = EmailTemplate.objects.create(
            name=name,
            subject=subject,
            body=body,
            description=description,
            created_by=request.user
        )
        
        messages.success(request, f'Email template "{template.name}" created successfully!')
        return redirect('dashboard:email_template_list')
    
    # Available template variables
    template_variables = [
        '{{event_name}}', '{{event_location}}', '{{event_start_date}}', '{{event_end_date}}',
        '{{participant_name}}', '{{participant_email}}', '{{participant_phone}}',
        '{{badge_id}}', '{{qr_code_url}}'
    ]
    
    context = {
        'template_variables': template_variables,
    }
    return render(request, 'dashboard/email_template_form.html', context)


@login_required
def email_template_edit(request, template_id):
    """Edit an existing global email template"""
    template = get_object_or_404(EmailTemplate, id=template_id)
    
    if request.method == 'POST':
        template.name = request.POST.get('name')
        template.subject = request.POST.get('subject')
        template.body = request.POST.get('body')
        template.description = request.POST.get('description', '')
        template.save()
        
        messages.success(request, f'Email template "{template.name}" updated successfully!')
        return redirect('dashboard:email_template_list')
    
    # Available template variables
    template_variables = [
        '{{event_name}}', '{{event_location}}', '{{event_start_date}}', '{{event_end_date}}',
        '{{participant_name}}', '{{participant_email}}', '{{participant_phone}}',
        '{{badge_id}}', '{{qr_code_url}}'
    ]
    
    context = {
        'template': template,
        'template_variables': template_variables,
        'is_edit': True,
    }
    return render(request, 'dashboard/email_template_form.html', context)


@login_required
def email_template_delete(request, template_id):
    """Delete an email template"""
    if request.method == 'POST':
        template = get_object_or_404(EmailTemplate, id=template_id)
        name = template.name
        template.delete()
        messages.success(request, f'Email template "{name}" deleted successfully!')
    
    return redirect('dashboard:email_template_list')


@login_required
def event_email_templates(request, event_id):
    """List email templates for a specific event"""
    event = get_object_or_404(Event, id=event_id)
    event_templates = EventEmailTemplate.objects.filter(event=event).select_related('base_template', 'created_by')
    global_templates = EmailTemplate.objects.all()
    
    context = {
        'event': event,
        'event_templates': event_templates,
        'global_templates': global_templates,
    }
    return render(request, 'dashboard/event_email_templates.html', context)


@login_required
def event_email_template_create(request, event_id):
    """Create or customize email template for event"""
    event = get_object_or_404(Event, id=event_id)
    
    if request.method == 'POST':
        base_template_id = request.POST.get('base_template_id')
        name = request.POST.get('name')
        subject = request.POST.get('subject')
        body = request.POST.get('body')
        
        if not all([name, subject, body]):
            messages.error(request, 'Please fill in all required fields.')
            return redirect('dashboard:event_email_template_create', event_id=event.id)
        
        base_template = None
        if base_template_id:
            base_template = get_object_or_404(EmailTemplate, id=base_template_id)
        
        event_template = EventEmailTemplate.objects.create(
            event=event,
            base_template=base_template,
            name=name,
            subject=subject,
            body=body,
            created_by=request.user
        )
        
        messages.success(request, f'Event email template "{event_template.name}" created successfully!')
        return redirect('dashboard:event_email_templates', event_id=event.id)
    
    # If base_template_id is provided, pre-fill from global template
    base_template = None
    base_template_id = request.GET.get('base_template_id')
    if base_template_id:
        base_template = get_object_or_404(EmailTemplate, id=base_template_id)
    
    # Available template variables
    template_variables = [
        '{{event_name}}', '{{event_location}}', '{{event_start_date}}', '{{event_end_date}}',
        '{{participant_name}}', '{{participant_email}}', '{{participant_phone}}',
        '{{badge_id}}', '{{qr_code_url}}'
    ]
    
    context = {
        'event': event,
        'base_template': base_template,
        'template_variables': template_variables,
    }
    return render(request, 'dashboard/event_email_template_form.html', context)


@login_required
def event_email_template_edit(request, event_id, template_id):
    """Edit event email template"""
    event = get_object_or_404(Event, id=event_id)
    event_template = get_object_or_404(EventEmailTemplate, id=template_id, event=event)
    
    if request.method == 'POST':
        event_template.name = request.POST.get('name')
        event_template.subject = request.POST.get('subject')
        event_template.body = request.POST.get('body')
        event_template.save()
        
        messages.success(request, f'Event email template "{event_template.name}" updated successfully!')
        return redirect('dashboard:event_email_templates', event_id=event.id)
    
    # Available template variables
    template_variables = [
        '{{event_name}}', '{{event_location}}', '{{event_start_date}}', '{{event_end_date}}',
        '{{participant_name}}', '{{participant_email}}', '{{participant_phone}}',
        '{{badge_id}}', '{{qr_code_url}}'
    ]
    
    context = {
        'event': event,
        'template': event_template,
        'template_variables': template_variables,
        'is_edit': True,
    }
    return render(request, 'dashboard/event_email_template_form.html', context)


@login_required
def event_email_template_delete(request, event_id, template_id):
    """Delete event email template"""
    if request.method == 'POST':
        event = get_object_or_404(Event, id=event_id)
        template = get_object_or_404(EventEmailTemplate, id=template_id, event=event)
        name = template.name
        template.delete()
        messages.success(request, f'Event email template "{name}" deleted successfully!')
    
    return redirect('dashboard:event_email_templates', event_id=event_id)


@login_required
def send_event_email(request, event_id, template_id):
    """Send email to participants"""
    event = get_object_or_404(Event, id=event_id)
    template = get_object_or_404(EventEmailTemplate, id=template_id, event=event)
    
    if request.method == 'POST':
        target_type = request.POST.get('target_type')
        
        # Get participants based on target type
        participants = Participant.objects.filter(event=event).select_related('user')
        
        if target_type == 'attended':
            participants = participants.filter(check_in_time__isnull=False)
        elif target_type == 'not_attended':
            participants = participants.filter(check_in_time__isnull=True)
        elif target_type == 'paid':
            # Participants who have transactions
            from caisse.models import CaisseTransaction
            paid_participant_ids = CaisseTransaction.objects.filter(
                participant__event=event,
                status='completed'
            ).values_list('participant_id', flat=True).distinct()
            participants = participants.filter(id__in=paid_participant_ids)
        elif target_type == 'not_paid':
            # Participants without transactions
            from caisse.models import CaisseTransaction
            paid_participant_ids = CaisseTransaction.objects.filter(
                participant__event=event,
                status='completed'
            ).values_list('participant_id', flat=True).distinct()
            participants = participants.exclude(id__in=paid_participant_ids)
        # else: all_participants (default, no filter)
        
        if not participants.exists():
            messages.warning(request, 'No participants match the selected criteria.')
            return redirect('dashboard:send_event_email', event_id=event.id, template_id=template.id)
        
        # Create email log
        email_log = EmailLog.objects.create(
            event=event,
            template=template,
            subject=template.subject,
            body=template.body,
            target_type=target_type,
            recipient_count=participants.count(),
            sent_by=request.user,
            status='sending'
        )
        email_log.recipients.set(participants)
        
        # Send emails
        sent_count = 0
        failed_count = 0
        errors = []
        
        for participant in participants:
            try:
                # Build context for template variables
                context = {
                    'event_name': event.name,
                    'event_location': event.location,
                    'event_start_date': event.start_date.strftime('%B %d, %Y'),
                    'event_end_date': event.end_date.strftime('%B %d, %Y'),
                    'participant_name': participant.user.get_full_name() or participant.user.username,
                    'participant_email': participant.user.email,
                    'participant_phone': participant.user.profile.phone if hasattr(participant.user, 'profile') else '',
                    'badge_id': participant.badge_id,
                    'qr_code_url': request.build_absolute_uri(f'/media/qr_codes/{participant.qr_code}') if participant.qr_code else '',
                }
                
                # Replace variables in subject and body
                personalized_subject = replace_template_variables(template.subject, context)
                personalized_body = replace_template_variables(template.body, context)
                
                # Send email
                send_mail(
                    subject=personalized_subject,
                    message=personalized_body,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[participant.user.email],
                    html_message=personalized_body,
                    fail_silently=False,
                )
                sent_count += 1
            except Exception as e:
                failed_count += 1
                errors.append(f"{participant.user.email}: {str(e)}")
        
        # Update email log
        email_log.sent_count = sent_count
        email_log.failed_count = failed_count
        email_log.status = 'sent' if failed_count == 0 else 'failed'
        email_log.sent_at = timezone.now()
        if errors:
            email_log.error_message = '\n'.join(errors[:10])  # Store first 10 errors
        email_log.save()
        
        if sent_count > 0:
            messages.success(request, f'Email sent to {sent_count} participant(s) successfully!')
        if failed_count > 0:
            messages.warning(request, f'Failed to send to {failed_count} participant(s).')
        
        return redirect('dashboard:event_email_logs', event_id=event.id)
    
    # GET request - show send form
    # Count participants for each target type
    from caisse.models import CaisseTransaction
    
    all_count = Participant.objects.filter(event=event).count()
    attended_count = Participant.objects.filter(event=event, check_in_time__isnull=False).count()
    not_attended_count = Participant.objects.filter(event=event, check_in_time__isnull=True).count()
    
    paid_participant_ids = CaisseTransaction.objects.filter(
        participant__event=event,
        status='completed'
    ).values_list('participant_id', flat=True).distinct()
    paid_count = Participant.objects.filter(id__in=paid_participant_ids).count()
    not_paid_count = all_count - paid_count
    
    context = {
        'event': event,
        'template': template,
        'all_count': all_count,
        'attended_count': attended_count,
        'not_attended_count': not_attended_count,
        'paid_count': paid_count,
        'not_paid_count': not_paid_count,
    }
    return render(request, 'dashboard/send_event_email.html', context)


@login_required
def event_email_logs(request, event_id):
    """View email sending history for an event"""
    event = get_object_or_404(Event, id=event_id)
    logs = EmailLog.objects.filter(event=event).select_related('template', 'sent_by').prefetch_related('recipients')
    
    context = {
        'event': event,
        'logs': logs,
    }
    return render(request, 'dashboard/event_email_logs.html', context)


@login_required
def send_email_to_registrants(request, event_id, template_id):
    """Send email to event registrants (not yet participants)"""
    from events.models import EventRegistration
    
    event = get_object_or_404(Event, id=event_id)
    template = get_object_or_404(EventEmailTemplate, id=template_id, event=event)
    
    if request.method == 'POST':
        target_type = request.POST.get('target_type', 'all_registrants')
        
        # Get registrations based on target type
        registrations = EventRegistration.objects.filter(event=event, is_spam=False)
        
        if target_type == 'confirmed':
            registrations = registrations.filter(is_confirmed=True)
        elif target_type == 'not_confirmed':
            registrations = registrations.filter(is_confirmed=False)
        elif target_type == 'no_user_account':
            registrations = registrations.filter(user__isnull=True)
        # else: all_registrants (default, no filter)
        
        if not registrations.exists():
            messages.warning(request, 'No registrants match the selected criteria.')
            return redirect('dashboard:send_email_to_registrants', event_id=event.id, template_id=template.id)
        
        # Send emails
        sent_count = 0
        failed_count = 0
        errors = []
        
        for registration in registrations:
            try:
                # Build context for template variables
                context = {
                    'event_name': event.name,
                    'event_location': event.location,
                    'event_start_date': event.start_date.strftime('%d/%m/%Y'),
                    'event_end_date': event.end_date.strftime('%d/%m/%Y'),
                    'first_name': registration.prenom,
                    'last_name': registration.nom,
                    'participant_name': registration.get_full_name(),
                    'email': registration.email,
                    'telephone': registration.telephone,
                    'etablissement': registration.etablissement,
                }
                
                # Replace variables in subject and body
                personalized_subject = replace_template_variables(template.subject, context)
                personalized_body = replace_template_variables(template.body_html or template.body, context)
                
                # Send email
                send_mail(
                    subject=personalized_subject,
                    message=personalized_body,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[registration.email],
                    html_message=personalized_body,
                    fail_silently=False,
                )
                sent_count += 1
            except Exception as e:
                failed_count += 1
                errors.append(f"{registration.email}: {str(e)}")
        
        if sent_count > 0:
            messages.success(request, f'Email sent to {sent_count} registrant(s) successfully!')
        if failed_count > 0:
            messages.warning(request, f'Failed to send to {failed_count} registrant(s). Errors: {"; ".join(errors[:3])}')
        
        return redirect('dashboard:event_email_templates', event_id=event.id)
    
    # GET request - show send form
    from events.models import EventRegistration
    
    all_count = EventRegistration.objects.filter(event=event, is_spam=False).count()
    confirmed_count = EventRegistration.objects.filter(event=event, is_confirmed=True, is_spam=False).count()
    not_confirmed_count = EventRegistration.objects.filter(event=event, is_confirmed=False, is_spam=False).count()
    no_account_count = EventRegistration.objects.filter(event=event, user__isnull=True, is_spam=False).count()
    
    context = {
        'event': event,
        'template': template,
        'all_count': all_count,
        'confirmed_count': confirmed_count,
        'not_confirmed_count': not_confirmed_count,
        'no_account_count': no_account_count,
    }
    return render(request, 'dashboard/send_email_to_registrants.html', context)
