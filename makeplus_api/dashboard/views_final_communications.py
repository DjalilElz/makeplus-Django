"""
Final Communication Orale submissions.

Accessible by staff/superusers (any event) and by room managers
(gestionnaire des salles) scoped to the event(s) they are assigned to.
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import FileResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import never_cache

from events.models import Event, UserEventAssignment
from .models_eposter import ScientificContributionFinalSubmission


def _can_access_event_communications(user, event):
    """Staff/superusers can access any event; room managers only their own."""
    if user.is_staff or user.is_superuser:
        return True
    return UserEventAssignment.objects.filter(
        user=user, event=event, role='gestionnaire_des_salles', is_active=True
    ).exists()


@never_cache
@login_required
def my_final_communications_home(request):
    """
    Landing page for room managers after login.
    Redirects straight to their event if they manage only one,
    otherwise shows a picker.
    """
    assignments = UserEventAssignment.objects.filter(
        user=request.user, role='gestionnaire_des_salles', is_active=True
    ).select_related('event').order_by('-assigned_at')

    if not assignments.exists():
        if request.user.is_staff or request.user.is_superuser:
            return redirect('dashboard:home')
        messages.error(request, "Vous n'avez accès à aucun événement en tant que gestionnaire de salle.")
        return redirect('dashboard:login')

    if assignments.count() == 1:
        return redirect('dashboard:final_communications', event_id=assignments.first().event_id)

    events = [a.event for a in assignments]
    return render(request, 'dashboard/final_communications/event_picker.html', {'events': events})


@never_cache
@login_required
def final_communications(request, event_id):
    """
    List final Communication Orale submissions for an event, searchable
    by title or author name.
    """
    event = get_object_or_404(Event, id=event_id)

    if not _can_access_event_communications(request.user, event):
        raise PermissionDenied("You do not have access to this event's communications.")

    query = request.GET.get('q', '').strip()

    submissions = ScientificContributionFinalSubmission.objects.filter(
        event=event,
        original_submission__type_participation='communication_orale'
    ).select_related('original_submission').order_by('-submitted_at')

    if query:
        submissions = submissions.filter(
            Q(titre__icontains=query) |
            Q(auteurs__icontains=query) |
            Q(nom__icontains=query)
        )

    paginator = Paginator(submissions, 25)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'event': event,
        'page_obj': page_obj,
        'submissions': page_obj.object_list,
        'query': query,
        'is_staff_viewer': request.user.is_staff or request.user.is_superuser,
    }
    return render(request, 'dashboard/final_communications/list.html', context)


@never_cache
@login_required
def download_final_communication(request, submission_id):
    """Force-download the final submission PDF, regardless of storage backend."""
    submission = get_object_or_404(
        ScientificContributionFinalSubmission.objects.select_related('event', 'original_submission'),
        id=submission_id,
        original_submission__type_participation='communication_orale'
    )

    if not _can_access_event_communications(request.user, submission.event):
        raise PermissionDenied("You do not have access to this file.")

    filename = f"{submission.contribution_number or submission.id}.pdf"
    return FileResponse(
        submission.abstract_file.open('rb'),
        as_attachment=True,
        filename=filename,
        content_type='application/pdf'
    )
