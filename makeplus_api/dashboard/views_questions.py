"""
Session Q&A moderation — anonymous by design.

Participants ask questions from the mobile app during a session (live stream
or session detail). This is the gestionnaire-facing screen: one list per
session, question text only, no asker identity — the API never sends it
(SessionQuestionSerializer.participant is write_only) and this view doesn't
either, so there is nothing here that could deanonymize a participant even by
accident.
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from events.models import Session, SessionQuestion
from .views import is_staff_user


@login_required
@user_passes_test(is_staff_user)
def session_questions(request, session_id):
    """List + answer questions for one session, oldest first."""
    session = get_object_or_404(Session.objects.select_related('event', 'room'), id=session_id)

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
@user_passes_test(is_staff_user)
@require_POST
def session_question_answer(request, question_id):
    """Answer a question, or clear its answer (leaves it visible as unanswered again)."""
    question = get_object_or_404(SessionQuestion.objects.select_related('session'), id=question_id)
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
