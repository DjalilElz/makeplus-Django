"""
Public ePoster Form View
Allows anyone to submit an ePoster without authentication
"""
from django.shortcuts import render, get_object_or_404
from django.http import Http404
from events.models import Event


def public_eposter_form_view(request, event_id):
    """
    Render the public ePoster submission form
    """
    event = get_object_or_404(Event, id=event_id)
    
    # Check if submissions are open
    if not event.settings.get('eposter_submissions_open', True):
        return render(request, 'dashboard/eposter/submissions_closed.html', {
            'event': event
        })
    
    context = {
        'event': event
    }
    
    return render(request, 'dashboard/eposter/public_form.html', context)
