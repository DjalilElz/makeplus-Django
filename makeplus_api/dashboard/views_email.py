"""Email template management views"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.db import models
from django.db.models import Count, Q
from django.utils import timezone
from events.models import Event, Participant
from .models_email import EmailTemplate, EventEmailTemplate, EmailLog
from smtplib import SMTPException
import socket
import re


def replace_template_variables(text, context):
    """Replace template variables like {{event_name}} with actual values"""
    for key, value in context.items():
        text = text.replace(f"{{{{{key}}}}}", str(value))
    return text


@login_required
def email_template_list(request):
    """Unified campaign list - shows all campaigns (templates are now campaigns)"""
    from .models_email import EmailCampaign
    
    # Get filter parameters
    filter_status = request.GET.get('status', 'all')
    filter_event = request.GET.get('event', 'all')
    
    # Base queryset
    campaigns = EmailCampaign.objects.select_related('event', 'created_by')
    
    # Apply filters
    if filter_status == 'draft':
        campaigns = campaigns.filter(status='draft')
    elif filter_status == 'archived':
        campaigns = campaigns.filter(status='archived')
    elif filter_status == 'sent':
        campaigns = campaigns.filter(status='sent')
    elif filter_status == 'active':
        campaigns = campaigns.exclude(status='archived')
    
    if filter_event != 'all' and filter_event:
        campaigns = campaigns.filter(event_id=filter_event)
    
    campaigns = campaigns.order_by('-created_at')
    
    # Get statistics for each campaign
    from .models_email import EmailRecipient
    campaign_stats = []
    for campaign in campaigns:
        recipients = EmailRecipient.objects.filter(campaign=campaign)
        campaign_stats.append({
            'campaign': campaign,
            'total_recipients': recipients.count(),
            'sent_count': recipients.filter(status='sent').count(),
            'opened_count': recipients.filter(open_count__gt=0).count(),
            'clicked_count': recipients.filter(click_count__gt=0).count(),
        })
    
    # Get events for filter dropdown
    events = Event.objects.all().order_by('-created_at')
    
    context = {
        'campaign_stats': campaign_stats,
        'campaigns': campaigns,
        'campaign_count': campaigns.count(),
        'events': events,
        'filter_status': filter_status,
        'filter_event': filter_event,
    }
    return render(request, 'dashboard/campaign_list_with_stats.html', context)


@login_required
def email_template_create(request):
    """Create a new global email template"""
    if request.method == 'POST':
        name = request.POST.get('name')
        subject = request.POST.get('subject')
        from_email = request.POST.get('from_email', '').strip()
        description = request.POST.get('description', '')
        body_html = request.POST.get('body_html', '')
        builder_config = request.POST.get('builder_config', '{}')
        template_type = request.POST.get('template_type', 'custom')
        is_active = request.POST.get('is_active', 'true') == 'true'
        
        if not all([name, subject, body_html]):
            messages.error(request, 'Please fill in all required fields and design your email.')
            return redirect('dashboard:email_template_create')
        
        template = EmailTemplate.objects.create(
            name=name,
            subject=subject,
            from_email=from_email,
            body=body_html,  # Store HTML in body field for backward compatibility
            body_html=body_html,
            builder_config=builder_config,
            description=description,
            template_type=template_type,
            is_active=is_active,
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
        'default_from_email': settings.DEFAULT_FROM_EMAIL,
    }
    return render(request, 'dashboard/email_template_form.html', context)


@login_required
def email_template_edit(request, template_id):
    """Edit an existing global email template"""
    template = get_object_or_404(EmailTemplate, id=template_id)
    
    if request.method == 'POST':
        template.name = request.POST.get('name')
        template.subject = request.POST.get('subject')
        template.from_email = request.POST.get('from_email', '').strip()
        template.description = request.POST.get('description', '')
        body_html = request.POST.get('body_html', '')
        builder_config = request.POST.get('builder_config', '{}')
        template_type = request.POST.get('template_type', 'custom')
        is_active = request.POST.get('is_active', 'true') == 'true'
        
        template.body = body_html  # Update body for backward compatibility
        template.body_html = body_html
        template.builder_config = builder_config
        template.template_type = template_type
        template.is_active = is_active
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
        'default_from_email': settings.DEFAULT_FROM_EMAIL,
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
        body_html = request.POST.get('body_html', '')
        builder_config = request.POST.get('builder_config', '{}')
        template_type = request.POST.get('template_type', 'custom')
        is_active = request.POST.get('is_active', 'true') == 'true'
        
        if not all([name, subject, body_html]):
            messages.error(request, 'Please fill in all required fields and design your email.')
            return redirect('dashboard:event_email_template_create', event_id=event.id)
        
        base_template = None
        if base_template_id:
            base_template = get_object_or_404(EmailTemplate, id=base_template_id)
        
        event_template = EventEmailTemplate.objects.create(
            event=event,
            base_template=base_template,
            name=name,
            subject=subject,
            body=body_html,  # Store HTML in body for backward compatibility
            body_html=body_html,
            builder_config=builder_config,
            template_type=template_type,
            is_active=is_active,
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
        body_html = request.POST.get('body_html', '')
        builder_config = request.POST.get('builder_config', '{}')
        template_type = request.POST.get('template_type', 'custom')
        is_active = request.POST.get('is_active', 'true') == 'true'
        
        event_template.body = body_html  # Update body for backward compatibility
        event_template.body_html = body_html
        event_template.builder_config = builder_config
        event_template.template_type = template_type
        event_template.is_active = is_active
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


@login_required
def email_template_test(request, template_id):
    """Send a test email from a template"""
    template = get_object_or_404(EmailTemplate, id=template_id)
    
    if request.method == 'POST':
        test_email = request.POST.get('test_email')
        
        if not test_email:
            messages.error(request, 'Please provide a test email address.')
            return redirect('dashboard:email_template_list')
        
        # Create sample context data for testing
        context = {
            'event_name': 'Sample Event Name',
            'event_location': 'Sample Location',
            'event_start_date': 'Jan 1, 2026',
            'event_end_date': 'Jan 3, 2026',
            'participant_name': 'John Doe',
            'first_name': 'John',
            'last_name': 'Doe',
            'email': test_email,
            'telephone': '+1234567890',
            'etablissement': 'Sample Organization',
            'badge_id': 'BADGE-12345',
            'qr_code_url': 'https://example.com/qr-code.png',
        }
        
        # Replace template variables
        subject = replace_template_variables(template.subject, context)
        body_html = replace_template_variables(template.body_html or template.body, context)
        
        try:
            # Use custom from_email if provided, otherwise use default
            from_address = template.from_email if template.from_email else settings.DEFAULT_FROM_EMAIL
            
            send_mail(
                subject=subject,
                message='',  # Plain text version (empty for now)
                from_email=from_address,
                recipient_list=[test_email],
                html_message=body_html,
                fail_silently=False,
            )
            
            # Log the test email
            EmailLog.objects.create(
                template_name=template.name,
                recipient_email=test_email,
                subject=subject,
                body=body_html,
                status='sent',
                sent_by=request.user
            )
            
            messages.success(request, f'Test email sent successfully to {test_email}!')
        except Exception as e:
            messages.error(request, f'Failed to send test email: {str(e)}')
            EmailLog.objects.create(
                template_name=template.name,
                recipient_email=test_email,
                subject=subject,
                body=body_html,
                status='failed',
                error_message=str(e),
                sent_by=request.user
            )
    
    return redirect('dashboard:email_template_list')


@login_required
def email_template_send(request, template_id):
    """Send email to all registered users for a specific event"""
    template = get_object_or_404(EmailTemplate, id=template_id)
    
    if request.method == 'POST':
        event_id = request.POST.get('event_id')
        
        if not event_id:
            messages.error(request, 'Please select an event.')
            return redirect('dashboard:email_template_list')
        
        event = get_object_or_404(Event, id=event_id)
        
        # Get all approved registrations for this event
        from events.models import EventRegistration
        registrations = EventRegistration.objects.filter(
            event=event,
            status='approved'
        )
        
        if not registrations.exists():
            messages.warning(request, f'No approved registrations found for {event.name}.')
            return redirect('dashboard:email_template_list')
        
        sent_count = 0
        failed_count = 0
        
        for registration in registrations:
            # Create context with registration data
            context = {
                'event_name': event.name,
                'event_location': event.location or 'TBD',
                'event_start_date': event.start_date.strftime('%B %d, %Y') if event.start_date else 'TBD',
                'event_end_date': event.end_date.strftime('%B %d, %Y') if event.end_date else 'TBD',
                'participant_name': f"{registration.first_name} {registration.last_name}",
                'first_name': registration.first_name,
                'last_name': registration.last_name,
                'email': registration.email,
                'telephone': registration.telephone or 'N/A',
                'etablissement': registration.etablissement or 'N/A',
                'badge_id': registration.badge_id or 'N/A',
                'qr_code_url': request.build_absolute_uri(f'/media/qr_codes/{registration.badge_id}.png') if registration.badge_id else '',
            }
            
            # Replace template variables
            subject = replace_template_variables(template.subject, context)
            body_html = replace_template_variables(template.body_html or template.body, context)
            
            # Use custom from_email if provided, otherwise use default
            from_address = template.from_email if template.from_email else settings.DEFAULT_FROM_EMAIL
            
            try:
                send_mail(
                    subject=subject,
                    message='',
                    from_email=from_address,
                    recipient_list=[registration.email],
                    html_message=body_html,
                    fail_silently=False,
                )
                
                EmailLog.objects.create(
                    template_name=template.name,
                    event=event,
                    recipient_email=registration.email,
                    subject=subject,
                    body=body_html,
                    status='sent',
                    sent_by=request.user
                )
                sent_count += 1
            except Exception as e:
                EmailLog.objects.create(
                    template_name=template.name,
                    event=event,
                    recipient_email=registration.email,
                    subject=subject,
                    body=body_html,
                    status='failed',
                    error_message=str(e),
                    sent_by=request.user
                )
                failed_count += 1
        
        if sent_count > 0:
            messages.success(request, f'Successfully sent {sent_count} emails to {event.name} registrations!')
        if failed_count > 0:
            messages.warning(request, f'{failed_count} emails failed to send.')
    
    return redirect('dashboard:email_template_list')


@login_required
def email_template_stats(request, template_id):
    """Show statistics for an email template"""
    template = get_object_or_404(EmailTemplate, id=template_id)
    
    # Get email logs for this template - EmailLog uses template_name field
    logs = EmailLog.objects.filter(template_name=template.name).order_by('-sent_at')
    
    # Calculate statistics
    total_sent = logs.filter(status='sent').count()
    total_failed = logs.filter(status='failed').count()
    total_attempts = logs.count()
    
    # Get unique recipients
    unique_recipients = logs.values('recipient_email').distinct().count()
    
    # Get recent logs (last 50)
    recent_logs = logs[:50]
    
    # Get sending trends (group by date)
    from django.db.models.functions import TruncDate
    daily_stats = logs.annotate(
        date=TruncDate('sent_at')
    ).values('date').annotate(
        sent=Count('id', filter=Q(status='sent')),
        failed=Count('id', filter=Q(status='failed'))
    ).order_by('-date')[:30]
    
    context = {
        'template': template,
        'total_sent': total_sent,
        'total_failed': total_failed,
        'total_attempts': total_attempts,
        'unique_recipients': unique_recipients,
        'success_rate': round((total_sent / total_attempts * 100) if total_attempts > 0 else 0, 1),
        'recent_logs': recent_logs,
        'daily_stats': daily_stats,
    }
    
    return render(request, 'dashboard/email_template_stats.html', context)


@login_required
def email_template_archive(request, template_id):
    """Archive an email template"""
    if request.method == 'POST':
        template = get_object_or_404(EmailTemplate, id=template_id)
        template.is_active = False
        template.save()
        messages.success(request, f'Email template "{template.name}" has been archived.')
    
    return redirect('dashboard:email_template_list')


@login_required
def registration_form_builder(request):
    """List all custom registration forms"""
    from .models_form import FormConfiguration
    
    forms = FormConfiguration.objects.select_related('event', 'created_by').all()
    
    context = {
        'forms': forms,
    }
    
    return render(request, 'dashboard/registration_form_list.html', context)


@login_required
def registration_form_create(request):
    """Create a new custom registration form"""
    from .models_form import FormConfiguration
    from django.utils.text import slugify
    
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        event_id = request.POST.get('event_id')
        slug = request.POST.get('slug') or slugify(name)
        fields_config = request.POST.get('fields_config', '[]')
        success_message = request.POST.get('success_message', 'Thank you for your registration!')
        
        # Validate
        if not name:
            messages.error(request, 'Form name is required.')
            return redirect('dashboard:registration_form_create')
        
        # Check slug uniqueness
        if FormConfiguration.objects.filter(slug=slug).exists():
            messages.error(request, f'A form with slug "{slug}" already exists.')
            return redirect('dashboard:registration_form_create')
        
        import json
        try:
            fields_config = json.loads(fields_config)
        except:
            messages.error(request, 'Invalid field configuration.')
            return redirect('dashboard:registration_form_create')
        
        # Create form
        form = FormConfiguration.objects.create(
            name=name,
            description=description,
            slug=slug,
            event_id=event_id if event_id else None,
            fields_config=fields_config,
            success_message=success_message,
            send_confirmation_email=request.POST.get('send_confirmation_email') == 'on',
            is_active=True,
            created_by=request.user
        )
        
        # Handle banner image if uploaded
        if 'banner_image' in request.FILES:
            form.banner_image = request.FILES['banner_image']
            form.save()
        
        messages.success(request, f'Form "{form.name}" created successfully!')
        messages.info(request, f'Public URL: {request.build_absolute_uri(form.get_public_url())}')
        return redirect('dashboard:registration_form_edit', form_id=form.id)
    
    # GET request
    from .models_email import EmailTemplate
    events = Event.objects.all().order_by('-created_at')
    email_templates = EmailTemplate.objects.filter(is_active=True)
    
    context = {
        'events': events,
        'email_templates': email_templates,
    }
    
    return render(request, 'dashboard/registration_form_builder.html', context)


@login_required
def registration_form_edit(request, form_id):
    """Edit an existing custom registration form"""
    from .models_form import FormConfiguration
    from django.utils.text import slugify
    
    form = get_object_or_404(FormConfiguration, id=form_id)
    
    if request.method == 'POST':
        form.name = request.POST.get('name')
        form.description = request.POST.get('description', '')
        event_id = request.POST.get('event_id')
        form.event_id = event_id if event_id else None
        
        # Update slug if changed
        new_slug = request.POST.get('slug') or slugify(form.name)
        if new_slug != form.slug:
            if FormConfiguration.objects.filter(slug=new_slug).exclude(id=form.id).exists():
                messages.error(request, f'A form with slug "{new_slug}" already exists.')
                return redirect('dashboard:registration_form_edit', form_id=form.id)
            form.slug = new_slug
        
        fields_config = request.POST.get('fields_config', '[]')
        import json
        try:
            form.fields_config = json.loads(fields_config)
        except:
            messages.error(request, 'Invalid field configuration.')
            return redirect('dashboard:registration_form_edit', form_id=form.id)
        
        form.success_message = request.POST.get('success_message', 'Thank you for your registration!')
        form.send_confirmation_email = request.POST.get('send_confirmation_email') == 'on'
        form.is_active = request.POST.get('is_active') == 'on'
        
        # Handle banner image
        if request.POST.get('clear_banner') == 'on':
            form.banner_image = None
        elif 'banner_image' in request.FILES:
            form.banner_image = request.FILES['banner_image']
        
        form.save()
        
        messages.success(request, f'Form "{form.name}" updated successfully!')
        return redirect('dashboard:registration_form_builder')
    
    # GET request
    from .models_email import EmailTemplate
    events = Event.objects.all().order_by('-created_at')
    email_templates = EmailTemplate.objects.filter(is_active=True)
    
    context = {
        'form': form,
        'events': events,
        'email_templates': email_templates,
        'is_edit': True,
    }
    
    return render(request, 'dashboard/registration_form_builder.html', context)


@login_required
def registration_form_delete(request, form_id):
    """Delete a custom registration form"""
    from .models_form import FormConfiguration
    
    if request.method == 'POST':
        form = get_object_or_404(FormConfiguration, id=form_id)
        name = form.name
        form.delete()
        messages.success(request, f'Form "{name}" deleted successfully!')
    
    return redirect('dashboard:registration_form_builder')


@login_required
def registration_form_submissions(request, form_id):
    """View submissions for a form"""
    from .models_form import FormConfiguration, FormSubmission
    import json
    
    form = get_object_or_404(FormConfiguration, id=form_id)
    submissions = FormSubmission.objects.filter(form=form).order_by('-submitted_at')
    
    # Count by status
    pending_count = submissions.filter(status='pending').count()
    approved_count = submissions.filter(status='approved').count()
    rejected_count = submissions.filter(status='rejected').count()
    
    # Prepare submissions as JSON for JavaScript
    submissions_list = []
    for sub in submissions:
        submissions_list.append({
            'id': str(sub.id),
            'data': sub.data,
            'email': sub.email,
            'ip_address': sub.ip_address,
            'status': sub.status,
            'admin_notes': sub.admin_notes,
            'submitted_at': sub.submitted_at.isoformat(),
        })
    
    context = {
        'form': form,
        'submissions': submissions,
        'submissions_json': json.dumps(submissions_list),
        'form_fields': form.fields_config,
        'pending_count': pending_count,
        'approved_count': approved_count,
        'rejected_count': rejected_count,
    }
    
    return render(request, 'dashboard/registration_form_submissions.html', context)


@login_required
def campaign_create(request):
    """Create a new email campaign"""
    from .forms import EmailCampaignForm
    from .models_email import EmailCampaign
    from django.conf import settings
    
    if request.method == 'POST':
        form = EmailCampaignForm(request.POST)
        
        # Get additional fields
        body_html = request.POST.get('body_html', '')
        builder_config = request.POST.get('builder_config', '{}')
        body_text = request.POST.get('body_text', '')
        
        if not body_html:
            messages.error(request, 'Please design your email content using the editor.')
            return redirect('dashboard:campaign_create')
        
        if form.is_valid():
            campaign = form.save(commit=False)
            campaign.body_html = body_html
            campaign.body_text = body_text
            campaign.created_by = request.user
            campaign.status = 'draft'
            campaign.save()
            
            messages.success(request, f'Campaign "{campaign.name}" created successfully!')
            messages.info(request, 'Next step: Add recipients to your campaign.')
            return redirect('dashboard:campaign_detail', campaign_id=campaign.id)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = EmailCampaignForm()
    
    # Get events for dropdown
    events = Event.objects.all().order_by('-created_at')
    
    # Available template variables
    template_variables = [
        '{{name}}', '{{email}}', '{{event_name}}', '{{event_location}}',
        '{{event_start_date}}', '{{event_end_date}}', '{{unsubscribe_url}}'
    ]
    
    context = {
        'form': form,
        'events': events,
        'template_variables': template_variables,
        'default_from_email': getattr(settings, 'DEFAULT_FROM_EMAIL', ''),
    }
    
    return render(request, 'dashboard/campaign_form.html', context)


@login_required
def campaign_edit(request, campaign_id):
    """Edit an existing email campaign"""
    from .forms import EmailCampaignForm
    from .models_email import EmailCampaign
    from django.conf import settings
    
    campaign = get_object_or_404(EmailCampaign, id=campaign_id)
    
    # Don't allow editing if campaign is sent
    if campaign.status in ['sent', 'sending']:
        messages.warning(request, 'Cannot edit a campaign that has been sent or is being sent.')
        return redirect('dashboard:campaign_detail', campaign_id=campaign.id)
    
    if request.method == 'POST':
        form = EmailCampaignForm(request.POST, instance=campaign)
        
        # Get additional fields
        body_html = request.POST.get('body_html', '')
        builder_config = request.POST.get('builder_config', '{}')
        body_text = request.POST.get('body_text', '')
        
        if not body_html:
            messages.error(request, 'Please design your email content using the editor.')
            return redirect('dashboard:campaign_edit', campaign_id=campaign.id)
        
        if form.is_valid():
            campaign = form.save(commit=False)
            campaign.body_html = body_html
            campaign.body_text = body_text
            campaign.save()
            
            messages.success(request, f'Campaign "{campaign.name}" updated successfully!')
            return redirect('dashboard:campaign_detail', campaign_id=campaign.id)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = EmailCampaignForm(instance=campaign)
    
    # Get events for dropdown
    events = Event.objects.all().order_by('-created_at')
    
    # Available template variables
    template_variables = [
        '{{name}}', '{{email}}', '{{event_name}}', '{{event_location}}',
        '{{event_start_date}}', '{{event_end_date}}', '{{unsubscribe_url}}'
    ]
    
    context = {
        'form': form,
        'campaign': campaign,
        'events': events,
        'template_variables': template_variables,
        'default_from_email': getattr(settings, 'DEFAULT_FROM_EMAIL', ''),
        'is_edit': True,
    }
    
    return render(request, 'dashboard/campaign_form.html', context)


@login_required
def campaign_detail(request, campaign_id):
    """View campaign details and manage recipients"""
    from .models_email import EmailCampaign, EmailRecipient
    
    campaign = get_object_or_404(EmailCampaign, id=campaign_id)
    recipients = campaign.recipients.all().order_by('-created_at')
    
    # Calculate statistics
    pending_count = recipients.filter(status='pending').count()
    sent_count = recipients.filter(status='sent').count()
    delivered_count = recipients.filter(status='delivered').count()
    failed_count = recipients.filter(status='failed').count()
    
    context = {
        'campaign': campaign,
        'recipients': recipients,
        'recipient_count': recipients.count(),
        'pending_count': pending_count,
        'sent_count': sent_count,
        'delivered_count': delivered_count,
        'failed_count': failed_count,
    }
    
    return render(request, 'dashboard/campaign_detail.html', context)


@login_required
def campaign_delete(request, campaign_id):
    """Delete a campaign"""
    from .models_email import EmailCampaign
    
    if request.method == 'POST':
        campaign = get_object_or_404(EmailCampaign, id=campaign_id)
        campaign_name = campaign.name
        campaign.delete()
        messages.success(request, f'Campaign "{campaign_name}" has been deleted.')
    
    return redirect('dashboard:email_template_list')


@login_required
def campaign_archive(request, campaign_id):
    """Archive a campaign"""
    from .models_email import EmailCampaign
    
    if request.method == 'POST':
        campaign = get_object_or_404(EmailCampaign, id=campaign_id)
        campaign.status = 'archived'
        campaign.save()
        messages.success(request, f'Campaign "{campaign.name}" has been archived.')
    
    return redirect('dashboard:campaign_detail', campaign_id=campaign_id)


@login_required
def campaign_unarchive(request, campaign_id):
    """Unarchive a campaign"""
    from .models_email import EmailCampaign
    
    if request.method == 'POST':
        campaign = get_object_or_404(EmailCampaign, id=campaign_id)
        campaign.status = 'draft'
        campaign.save()
        messages.success(request, f'Campaign "{campaign.name}" has been unarchived.')
    
    return redirect('dashboard:campaign_detail', campaign_id=campaign_id)


@login_required
def campaign_add_recipient(request, campaign_id):
    """Add a single recipient to a campaign"""
    from .models_email import EmailCampaign, EmailRecipient
    import secrets
    
    campaign = get_object_or_404(EmailCampaign, id=campaign_id)
    
    if request.method == 'POST':
        email = request.POST.get('email')
        name = request.POST.get('name', '')
        
        if not email:
            messages.error(request, 'Email is required.')
            return redirect('dashboard:campaign_detail', campaign_id=campaign.id)
        
        # Check if recipient already exists
        if EmailRecipient.objects.filter(campaign=campaign, email=email).exists():
            messages.warning(request, f'Recipient {email} already exists in this campaign.')
            return redirect('dashboard:campaign_detail', campaign_id=campaign.id)
        
        # Create recipient with tracking token
        tracking_token = secrets.token_urlsafe(32)
        recipient = EmailRecipient.objects.create(
            campaign=campaign,
            email=email,
            name=name,
            tracking_token=tracking_token
        )
        
        # Update campaign recipient count
        campaign.recipient_count = campaign.recipients.count()
        campaign.save()
        
        messages.success(request, f'Recipient {email} added successfully!')
    
    return redirect('dashboard:campaign_detail', campaign_id=campaign.id)


@login_required
def campaign_bulk_add_recipients(request, campaign_id):
    """Bulk add recipients to a campaign via CSV or text"""
    from .models_email import EmailCampaign, EmailRecipient
    import secrets
    import csv
    from io import StringIO
    
    campaign = get_object_or_404(EmailCampaign, id=campaign_id)
    
    if request.method == 'POST':
        added_count = 0
        skipped_count = 0
        
        # Handle CSV file upload
        if 'csv_file' in request.FILES:
            csv_file = request.FILES['csv_file']
            file_data = csv_file.read().decode('utf-8')
            csv_reader = csv.reader(StringIO(file_data))
            
            for row in csv_reader:
                if len(row) >= 1:
                    email = row[0].strip()
                    name = row[1].strip() if len(row) > 1 else ''
                    
                    if email and not EmailRecipient.objects.filter(campaign=campaign, email=email).exists():
                        tracking_token = secrets.token_urlsafe(32)
                        EmailRecipient.objects.create(
                            campaign=campaign,
                            email=email,
                            name=name,
                            tracking_token=tracking_token
                        )
                        added_count += 1
                    else:
                        skipped_count += 1
        
        # Handle text input
        elif 'email_list' in request.POST:
            email_list = request.POST.get('email_list', '')
            lines = email_list.strip().split('\n')
            
            for line in lines:
                parts = line.strip().split(',')
                if len(parts) >= 1:
                    email = parts[0].strip()
                    name = parts[1].strip() if len(parts) > 1 else ''
                    
                    if email and not EmailRecipient.objects.filter(campaign=campaign, email=email).exists():
                        tracking_token = secrets.token_urlsafe(32)
                        EmailRecipient.objects.create(
                            campaign=campaign,
                            email=email,
                            name=name,
                            tracking_token=tracking_token
                        )
                        added_count += 1
                    else:
                        skipped_count += 1
        
        # Update campaign recipient count
        campaign.recipient_count = campaign.recipients.count()
        campaign.save()
        
        if added_count > 0:
            messages.success(request, f'Added {added_count} recipient(s) successfully!')
        if skipped_count > 0:
            messages.info(request, f'Skipped {skipped_count} duplicate(s).')
    
    return redirect('dashboard:campaign_detail', campaign_id=campaign.id)


@login_required
def campaign_delete_recipient(request, campaign_id, recipient_id):
    """Delete a recipient from a campaign"""
    from .models_email import EmailCampaign, EmailRecipient
    from django.http import JsonResponse
    
    campaign = get_object_or_404(EmailCampaign, id=campaign_id)
    
    if request.method == 'POST':
        try:
            recipient = get_object_or_404(EmailRecipient, id=recipient_id, campaign=campaign)
            recipient.delete()
            
            # Update campaign recipient count
            campaign.recipient_count = campaign.recipients.count()
            campaign.save()
            
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
def campaign_send_test(request, campaign_id):
    """Send a test email for a campaign"""
    from .models_email import EmailCampaign
    from django.http import JsonResponse
    import json
    
    campaign = get_object_or_404(EmailCampaign, id=campaign_id)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            test_email = data.get('email')
            
            if not test_email:
                return JsonResponse({'success': False, 'error': 'Email address is required'})
            
            # Build context with sample data
            context = {
                'name': 'Test User',
                'email': test_email,
                'event_name': campaign.event.name if campaign.event else 'Sample Event',
                'event_location': campaign.event.location if campaign.event else 'Sample Location',
                'event_start_date': campaign.event.start_date.strftime('%B %d, %Y') if campaign.event and campaign.event.start_date else 'TBD',
                'event_end_date': campaign.event.end_date.strftime('%B %d, %Y') if campaign.event and campaign.event.end_date else 'TBD',
                'unsubscribe_url': request.build_absolute_uri('/unsubscribe/'),
            }
            
            # Replace template variables
            subject = replace_template_variables(campaign.subject, context)
            body_html = replace_template_variables(campaign.body_html or campaign.body_text, context)
            
            # Use custom from_email if provided, otherwise use default
            from_address = campaign.from_email if campaign.from_email else settings.DEFAULT_FROM_EMAIL
            
            # Send test email
            send_mail(
                subject=f"[TEST] {subject}",
                message='',
                from_email=from_address,
                recipient_list=[test_email],
                html_message=body_html,
                fail_silently=False,
            )
            
            return JsonResponse({'success': True, 'message': f'Test email sent to {test_email}'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
def campaign_send(request, campaign_id):
    """Send campaign to all recipients"""
    from .models_email import EmailCampaign, EmailRecipient, EmailLink
    from bs4 import BeautifulSoup
    import secrets
    import hashlib
    
    campaign = get_object_or_404(EmailCampaign, id=campaign_id)
    
    # Allow sending from draft or sending status (for batch continuation)
    if campaign.status not in ['draft', 'sending']:
        messages.warning(request, 'This campaign has already been sent.')
        return redirect('dashboard:campaign_detail', campaign_id=campaign.id)
    
    # Check if there are recipients
    recipients = campaign.recipients.filter(status='pending')
    if not recipients.exists():
        messages.error(request, 'No recipients found for this campaign. Please add recipients first.')
        return redirect('dashboard:campaign_detail', campaign_id=campaign.id)
    
    if request.method == 'POST':
        # Limit batch size to prevent timeout (send max 10 emails per request)
        BATCH_SIZE = 10
        
        # Update campaign status
        campaign.status = 'sending'
        campaign.save()
        
        # Pre-process: Create EmailLink objects for all links in the email
        base_html = campaign.body_html or campaign.body_text
        soup = BeautifulSoup(base_html, 'html.parser')
        link_map = {}  # original_url -> EmailLink object
        
        for link in soup.find_all('a', href=True):
            original_url = link['href']
            # Skip mailto, tel, and anchor links
            if original_url.startswith(('mailto:', 'tel:', '#', 'javascript:')):
                continue
            
            # Get or create EmailLink for this URL
            if original_url not in link_map:
                email_link, created = EmailLink.objects.get_or_create(
                    campaign=campaign,
                    original_url=original_url,
                    defaults={
                        'tracking_token': hashlib.sha256(f"{campaign.id}{original_url}{timezone.now().isoformat()}".encode()).hexdigest()[:32]
                    }
                )
                link_map[original_url] = email_link
        
        sent_count = 0
        failed_count = 0
        
        # Only process BATCH_SIZE recipients to prevent timeout
        batch_recipients = recipients[:BATCH_SIZE]
        
        for recipient in batch_recipients:
            try:
                # Build context for template variables
                context = {
                    'name': recipient.name or recipient.email.split('@')[0],
                    'email': recipient.email,
                    'event_name': campaign.event.name if campaign.event else '',
                    'event_location': campaign.event.location if campaign.event else '',
                    'event_start_date': campaign.event.start_date.strftime('%B %d, %Y') if campaign.event and campaign.event.start_date else '',
                    'event_end_date': campaign.event.end_date.strftime('%B %d, %Y') if campaign.event and campaign.event.end_date else '',
                    'unsubscribe_url': request.build_absolute_uri(f'/track/email/unsubscribe/{recipient.tracking_token}/'),
                }
                
                # Replace template variables
                subject = replace_template_variables(campaign.subject, context)
                body_html = replace_template_variables(campaign.body_html or campaign.body_text, context)
                
                # Add link tracking to all links
                if campaign.track_clicks and link_map:
                    soup = BeautifulSoup(body_html, 'html.parser')
                    for link in soup.find_all('a', href=True):
                        original_url = link['href']
                        if original_url in link_map:
                            email_link = link_map[original_url]
                            tracking_url = request.build_absolute_uri(
                                f'/track/email/click/{email_link.tracking_token}/{recipient.tracking_token}/'
                            )
                            link['href'] = tracking_url
                    body_html = str(soup)
                
                # Add tracking pixel for opens
                if campaign.track_opens:
                    tracking_pixel = f'<img src="{request.build_absolute_uri(f"/track/email/open/{recipient.tracking_token}/")}" width="1" height="1" style="display:none;" />'
                    body_html = body_html + tracking_pixel
                
                # Add unsubscribe footer
                unsubscribe_footer = f'''
                <div style="text-align:center; margin-top:30px; padding:20px; font-size:12px; color:#999; border-top:1px solid #eee;">
                    <p>You received this email because you subscribed to our mailing list.</p>
                    <p><a href="{context['unsubscribe_url']}" style="color:#999;">Unsubscribe</a> from this list.</p>
                </div>
                '''
                body_html = body_html + unsubscribe_footer
                
                # Use custom from_email if provided, otherwise use default
                from_address = campaign.from_email if campaign.from_email else settings.DEFAULT_FROM_EMAIL
                
                # Send email with timeout protection
                try:
                    send_mail(
                        subject=subject,
                        message='',
                        from_email=from_address,
                        recipient_list=[recipient.email],
                        html_message=body_html,
                        fail_silently=False,
                    )
                    
                    # Update recipient status
                    recipient.status = 'sent'
                    recipient.sent_at = timezone.now()
                    recipient.save()
                    
                    sent_count += 1
                except SMTPException as e:
                    # SMTP-specific errors
                    recipient.status = 'failed'
                    recipient.error_message = f'SMTP Error: {str(e)}'
                    recipient.save()
                    failed_count += 1
                except socket.timeout:
                    # Connection timeout
                    recipient.status = 'failed'
                    recipient.error_message = 'Email server timeout'
                    recipient.save()
                    failed_count += 1
                except Exception as e:
                    # Other errors
                    recipient.status = 'failed'
                    recipient.error_message = str(e)
                    recipient.save()
                    failed_count += 1
                    
            except Exception as e:
                # Outer exception for template processing errors
                recipient.status = 'failed'
                recipient.error_message = f'Template error: {str(e)}'
                recipient.save()
                failed_count += 1
        
        # Check if there are more recipients to send
        remaining = recipients.count()
        
        # Update campaign status
        if remaining == 0:
            # All recipients processed
            campaign.status = 'sent'
        else:
            # Still have recipients pending, keep status as 'sending'
            campaign.status = 'sending'
        
        campaign.total_sent += sent_count
        campaign.total_delivered += sent_count
        campaign.save()
        
        if sent_count > 0:
            messages.success(request, f'Sent {sent_count} email(s) successfully!')
        if failed_count > 0:
            messages.warning(request, f'Failed to send {failed_count} email(s).')
        
        if remaining > 0:
            messages.info(request, f'{remaining} recipient(s) remaining. Click "Send" again to continue.')
            return redirect('dashboard:campaign_send', campaign_id=campaign.id)
        else:
            messages.success(request, 'Campaign sent to all recipients!')
            return redirect('dashboard:campaign_detail', campaign_id=campaign.id)
    
    # GET request - show confirmation page
    context = {
        'campaign': campaign,
        'recipient_count': recipients.count(),
    }
    return render(request, 'dashboard/campaign_send_confirm.html', context)
