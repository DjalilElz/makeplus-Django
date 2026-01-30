"""
ePoster Management Views - Central hub for Call for Communicants forms
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from events.models import Event
from .models_eposter import EPosterSubmission, EPosterCommitteeMember, EventFormConfiguration


@login_required
def eposter_management_home(request):
    """
    Central Call for Communicants Management page - shows ALL events
    Forms are automatically available for all events (no manual creation needed)
    """
    # Get all events with ePoster statistics
    events = Event.objects.annotate(
        total_submissions=Count('eposter_submissions'),
        pending_submissions=Count('eposter_submissions', filter=Q(eposter_submissions__status='pending')),
        accepted_submissions=Count('eposter_submissions', filter=Q(eposter_submissions__status='accepted')),
        rejected_submissions=Count('eposter_submissions', filter=Q(eposter_submissions__status='rejected')),
        committee_members_count=Count('eposter_committee_members', filter=Q(eposter_committee_members__is_active=True))
    ).order_by('-start_date')
    
    # Check if user is committee member for any events
    user_committee_events = EPosterCommitteeMember.objects.filter(
        user=request.user,
        is_active=True
    ).values_list('event_id', flat=True)
    
    context = {
        'events': events,
        'user_committee_events': list(user_committee_events),
        'is_admin': request.user.is_staff or request.user.is_superuser,
    }
    
    return render(request, 'dashboard/eposter/management_home.html', context)


@login_required
def create_form_for_event(request, event_id):
    """
    Create a form for an event - choose form type
    """
    event = get_object_or_404(Event, id=event_id)
    
    if request.method == 'POST':
        form_type = request.POST.get('form_type', 'communicant')
        title = request.POST.get('title', '')
        description = request.POST.get('description', '')
        
        # Create or update the form configuration
        config, created = EventFormConfiguration.objects.update_or_create(
            event=event,
            form_type=form_type,
            defaults={
                'is_active': True,
                'title': title,
                'description': description,
                'created_by': request.user,
            }
        )
        
        if form_type == 'communicant':
            messages.success(
                request, 
                f'Call for Communicants form created for "{event.name}". '
                f'Public URL: /eposter/{event.id}/'
            )
            return redirect('dashboard:eposter_dashboard', event_id=event.id)
        else:
            messages.success(
                request, 
                f'Participant registration form created for "{event.name}".'
            )
            return redirect('dashboard:event_detail', event_id=event.id)
    
    # GET request - show form type selection
    context = {
        'event': event,
        'existing_configs': EventFormConfiguration.objects.filter(event=event),
    }
    return render(request, 'dashboard/eposter/create_form.html', context)


@login_required
def eposter_enable_for_event(request, event_id):
    """
    Enable Call for Communicants for an event (quick action)
    """
    event = get_object_or_404(Event, id=event_id)
    
    if request.method == 'POST':
        # Create communicant form configuration
        config, created = EventFormConfiguration.objects.get_or_create(
            event=event,
            form_type='communicant',
            defaults={
                'is_active': True,
                'created_by': request.user,
            }
        )
        
        if not created:
            config.is_active = True
            config.save()
        
        messages.success(
            request, 
            f'Call for Communicants enabled for "{event.name}". '
            f'Public URL: /eposter/{event.id}/'
        )
        return redirect('dashboard:eposter_dashboard', event_id=event.id)
    
    return redirect('dashboard:eposter_management_home')


@login_required
def eposter_copy_settings(request, source_event_id, target_event_id):
    """
    Copy ePoster settings from one event to another
    """
    source_event = get_object_or_404(Event, id=source_event_id)
    target_event = get_object_or_404(Event, id=target_event_id)
    
    if request.method == 'POST':
        # Copy committee members
        source_members = EPosterCommitteeMember.objects.filter(event=source_event, is_active=True)
        for member in source_members:
            EPosterCommitteeMember.objects.get_or_create(
                event=target_event,
                user=member.user,
                defaults={
                    'role': member.role,
                    'is_active': True
                }
            )
        
        # Copy email templates
        from .models_eposter import EPosterEmailTemplate
        source_templates = EPosterEmailTemplate.objects.filter(event=source_event)
        for template in source_templates:
            EPosterEmailTemplate.objects.get_or_create(
                event=target_event,
                type=template.type,
                defaults={
                    'subject': template.subject,
                    'body': template.body
                }
            )
        
        messages.success(
            request,
            f'Paramètres copiés de "{source_event.name}" vers "{target_event.name}"'
        )
        return redirect('dashboard:eposter_dashboard', event_id=target_event.id)
    
    return redirect('dashboard:eposter_management_home')
