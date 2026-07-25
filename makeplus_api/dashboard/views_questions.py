"""
Session Q&A moderation — anonymous by design.

Participants ask questions from the mobile app during a session (live stream
or session detail). This is the gestionnaire-facing screen: one list per
session, question text only, no asker identity — the API never sends it
(SessionQuestionSerializer.participant is write_only) and this view doesn't
either, so there is nothing here that could deanonymize a participant even by
accident.

Access is scoped by get_assigned_room_ids (not a raw RoomAssignment query):
a gestionnaire only sees/answers questions for sessions in rooms they're
actually assigned to, not every room in the event. Staff/superusers can
access anything.
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from events.models import Session, SessionQuestion
from events.utils import get_assigned_room_ids


def _can_manage_session_questions(user, session):
    """Staff/superusers can access any session; gestionnaires only their assigned room(s)."""
    if user.is_staff or user.is_superuser:
        return True
    return str(session.room_id) in get_assigned_room_ids(user)


@login_required
def my_room_sessions(request):
    """
    A gestionnaire's own sessions (across every room they're assigned to),
    each linking to that session's Q&A page. Staff/superusers land here too
    if they follow the link, seeing only rooms they're personally assigned
    to (use the full event/room admin screens for anything broader).
    """
    room_ids = get_assigned_room_ids(request.user)

    sessions = (
        Session.objects
        .filter(room_id__in=room_ids)
        .select_related('room', 'event')
        .order_by('start_time')
    )

    for session in sessions:
        session.unanswered_count = session.questions.filter(is_answered=False).count()

    context = {'sessions': sessions}
    return render(request, 'dashboard/my_room_sessions.html', context)


@login_required
def session_questions(request, session_id):
    """List + answer questions for one session, oldest first."""
    session = get_object_or_404(Session.objects.select_related('event', 'room'), id=session_id)

    if not _can_manage_session_questions(request.user, session):
        raise PermissionDenied("You do not have access to this session's questions.")

    questions = (
        SessionQuestion.objects
        .filter(session=session)
        .select_related('answered_by')
        .order_by('asked_at')
    )

    context = {
        'session': session,
        'event': session.event,
        'questions': questions,
        'unanswered_count': questions.filter(is_answered=False).count(),
    }
    return render(request, 'dashboard/session_questions.html', context)


@login_required
@require_POST
def session_question_answer(request, question_id):
    """Answer a question, or clear its answer (leaves it visible as unanswered again)."""
    question = get_object_or_404(SessionQuestion.objects.select_related('session', 'session__room'), id=question_id)

    if not _can_manage_session_questions(request.user, question.session):
        raise PermissionDenied("You do not have access to this session's questions.")

    answer_text = request.POST.get('answer_text', '').strip()

    if answer_text:
        question.answer_text = answer_text
        question.is_answered = True
        question.answered_by = request.user
        question.answered_at = timezone.now()
        messages.success(request, 'Réponse enregistrée.')
    else:
        question.answer_text = ''
        question.is_answered = False
        question.answered_by = None
        question.answered_at = None
        messages.info(request, 'Réponse retirée — question marquée comme non répondue.')

    question.save()
    return redirect('dashboard:session_questions', session_id=question.session_id)
