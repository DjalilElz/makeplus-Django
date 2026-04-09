"""
Public ePoster Form View
Allows anyone to submit an ePoster without authentication
"""
from django.shortcuts import render, get_object_or_404
from django.http import Http404
from django.views.decorators.cache import never_cache
from events.models import Event
from .models_eposter import EventFormConfiguration


@never_cache
def public_eposter_form_view(request, event_id):
    """
    Render the public ePoster submission form
    """
    event = get_object_or_404(Event, id=event_id)
    
    # Get or create the form configuration (forms always exist, just toggle active status)
    config, created = EventFormConfiguration.objects.get_or_create(
        event=event,
        form_type='communicant',
        defaults={
            'is_active': True,  # Active by default
        }
    )
    
    # Check if the form is active
    if not config.is_active:
        return render(request, 'dashboard/eposter/form_closed.html', {
            'event': event
        })
    
    context = {
        'event': event
    }
    
    return render(request, 'dashboard/eposter/public_form.html', context)
