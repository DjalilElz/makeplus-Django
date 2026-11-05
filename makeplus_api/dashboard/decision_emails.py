"""
Decision e-mails (acceptance / rejection) for scientific contributions:
building one message, and sending many quickly.

Speed: messages are sent through Postmark's batch API (BATCH_SIZE per call)
with every template and decider comment loaded up front, and the results
written back with one UPDATE per batch -- instead of one Postmark call and
several queries per author. Progress is visible live because every attempt
stamps decision_email_attempt_at (read by the status endpoint).
"""
import logging

from django.conf import settings
from django.template import Context, Template
from django.utils import timezone

from .models_eposter import (
    ScientificContributionEmailTemplate as EmailTemplate,
    ScientificContributionSubmission as Submission,
    ScientificContributionValidation as Validation,
)

logger = logging.getLogger(__name__)

# Postmark accepts up to 500 messages per batch call; smaller batches keep the
# live progress moving (results are recorded after each batch).
BATCH_SIZE = 25

RESULT_FIELDS = [
    'acceptance_email_sent', 'rejection_email_sent', 'decision_email_sent_at',
    'decision_email_error', 'decision_email_send_count', 'decision_email_attempt_at',
]


def default_base_url():
    return getattr(settings, 'SITE_URL', 'https://makeplus-events.onrender.com')


def template_type_for(submission):
    decision = 'accepted' if submission.status == 'accepted' else 'rejected'
    return f'{submission.type_participation}_{decision}'


def record(submission, sent, error='', save=True, now=None):
    """Keeps track of the decision e-mail: sent (when, how many times) or not (why)."""
    now = now or timezone.now()
    field = 'acceptance_email_sent' if submission.status == 'accepted' else 'rejection_email_sent'
    setattr(submission, field, bool(sent))
    submission.decision_email_attempt_at = now
    if sent:
        submission.decision_email_sent_at = now
        submission.decision_email_error = ''
        submission.decision_email_send_count = (submission.decision_email_send_count or 0) + 1
    else:
        submission.decision_email_error = (error or 'Non envoyé')[:255]
    if save:
        submission.save(update_fields=RESULT_FIELDS)


def build(submission, base_url=None, templates=None, remarques=None):
    """
    (template_type, subject, html) for this submission's decision; subject and
    html are None when the event has no active template for it. templates /
    remarques are optional preloaded maps (see send_many) -- looked up one by
    one otherwise.
    """
    template_type = template_type_for(submission)
    if templates is not None:
        template = templates.get((submission.event_id, template_type))
    else:
        template = EmailTemplate.objects.filter(
            event_id=submission.event_id, template_type=template_type, is_active=True,
        ).order_by('id').first()
    if template is None:
        return template_type, None, None

    final_submission_url = ''
    show_final_submission = submission.status == 'accepted' and submission.requires_final_submission()
    if show_final_submission:
        base = (base_url or default_base_url()).rstrip('/')
        if submission.type_participation == 'e_poster':
            final_submission_url = f'{base}/contributions/final-submission/eposter/{submission.event_id}/'
        elif submission.type_participation == 'communication_orale':
            final_submission_url = f'{base}/contributions/final-submission/communication/{submission.event_id}/'

    # The decider's own comment (the rejection reason, typically).
    if remarques is not None:
        remarque = remarques.get((submission.id, submission.final_decision_by_id), '')
    elif submission.final_decision_by_id:
        validation = Validation.objects.filter(
            submission=submission, committee_member_id=submission.final_decision_by_id,
        ).first()
        remarque = validation.comments if validation and validation.comments else ''
    else:
        remarque = ''

    event = submission.event
    context = Context({
        'nom': submission.nom,
        'prenom': submission.prenom,
        'titre': submission.titre_travail,
        'event_name': event.name,
        'event_location': event.location or '',
        'event_start_date': event.start_date.strftime('%d/%m/%Y') if event.start_date else '',
        'event_end_date': event.end_date.strftime('%d/%m/%Y') if event.end_date else '',
        'contribution_number': submission.contribution_code or '',
        'remarque': remarque,
        'final_submission_url': final_submission_url,
        'type_participation': submission.get_type_participation_display(),
        'show_final_submission': show_final_submission,
    })
    return template_type, Template(template.subject).render(context), Template(template.body_html).render(context)


def postmark_batch(messages):
    """One Postmark batch call; returns Postmark's per-message results (same order)."""
    from .postmark_client import get_postmark_client
    return get_postmark_client().send_batch(messages)


def _send_one(submission, subject, html):
    from .email_sender import send_email
    success, error, _ = send_email(
        to_email=submission.email, subject=subject, html_content=html,
        from_email=settings.DEFAULT_FROM_EMAIL, to_name=f'{submission.prenom} {submission.nom}', use_api=True,
    )
    return success, error


def send_many(submission_ids, base_url=None):
    """
    Sends the decision e-mail of every decided submission in submission_ids
    (acceptance or rejection template per its own status). Returns
    (sent, not_sent). Results are recorded on each submission.
    """
    submissions = list(Submission.objects.filter(
        id__in=list(submission_ids), status__in=['accepted', 'rejected'],
    ).select_related('event').order_by('nom', 'prenom'))
    if not submissions:
        return 0, 0

    event_ids = {s.event_id for s in submissions}
    templates = {}
    for t in EmailTemplate.objects.filter(event_id__in=event_ids, is_active=True).order_by('id'):
        templates.setdefault((t.event_id, t.template_type), t)
    remarques = {
        (v['submission_id'], v['committee_member_id']): v['comments'] or ''
        for v in Validation.objects.filter(submission__in=submissions).values(
            'submission_id', 'committee_member_id', 'comments')
    }
    sender = f'MakePlus <{settings.DEFAULT_FROM_EMAIL}>'
    stream = getattr(settings, 'POSTMARK_MESSAGE_STREAM', 'outbound')

    sent = not_sent = 0
    for start in range(0, len(submissions), BATCH_SIZE):
        chunk = submissions[start:start + BATCH_SIZE]
        now = timezone.now()
        to_send = []  # (submission, subject, html)
        for submission in chunk:
            try:
                template_type, subject, html = build(submission, base_url, templates, remarques)
            except Exception as exc:  # a broken template must not stop the others
                record(submission, False, f'Erreur dans le modèle : {exc}', save=False, now=now)
                not_sent += 1
                continue
            if subject is None:
                record(submission, False, f"Aucun modèle d'e-mail actif « {template_type} »", save=False, now=now)
                not_sent += 1
                continue
            to_send.append((submission, subject, html))

        if to_send:
            messages = [{
                'From': sender,
                'To': f'{s.prenom} {s.nom} <{s.email}>',
                'Subject': subject,
                'HtmlBody': html,
                'TrackOpens': True,
                'TrackLinks': 'HtmlAndText',
                'MessageStream': stream,
            } for s, subject, html in to_send]
            try:
                results = postmark_batch(messages)
                if len(results) != len(to_send):
                    raise ValueError('unexpected Postmark batch response')
                for (submission, _, _), result in zip(to_send, results):
                    ok = result.get('ErrorCode', 1) == 0
                    record(submission, ok, '' if ok else f"Échec d'envoi : {result.get('Message', 'erreur')}",
                           save=False, now=now)
                    sent += ok
                    not_sent += not ok
            except Exception as exc:
                # Batch API unavailable: same e-mails one by one (with the SMTP fallback).
                logger.warning('Postmark batch failed (%s), sending one by one', exc)
                for submission, subject, html in to_send:
                    try:
                        ok, error = _send_one(submission, subject, html)
                    except Exception as one_exc:
                        ok, error = False, str(one_exc)
                    record(submission, ok, '' if ok else f"Échec d'envoi : {error}", save=False, now=timezone.now())
                    sent += ok
                    not_sent += not ok
        Submission.objects.bulk_update(chunk, RESULT_FIELDS)
    return sent, not_sent
