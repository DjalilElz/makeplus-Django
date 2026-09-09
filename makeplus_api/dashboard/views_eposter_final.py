"""
Views for ePoster and Communication Orale Final Submissions
Separate views for each submission type
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods, require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import never_cache
from django.core.paginator import Paginator
from django.db.models import Q
from django.conf import settings
from .models_eposter import ScientificContributionSubmission, ScientificContributionFinalSubmission, EventFormConfiguration
from events.models import Event


def _require_contribution_number(event):
    """
    Whether the "Numéro de Contribution (Code)" field is mandatory on the
    final submission form for this event -- per-event toggle on the
    communicant EventFormConfiguration, defaulting to True (today's
    behavior) when no config row exists yet for this event.
    """
    config = EventFormConfiguration.objects.filter(event=event, form_type='communicant').first()
    return config.require_contribution_number if config else True


@require_http_methods(["GET", "POST"])
@csrf_exempt
def eposter_final_submission_form(request, event_id):
    """
    Display and handle E-Poster final submission form
    No login required - uses contribution code for verification
    """
    event = get_object_or_404(Event, id=event_id)

    if request.method == 'GET':
        # Display the form
        context = {
            'event': event,
            'submission_type': 'e_poster',
            'submission_label': 'E-Poster',
            'file_label': 'E-Poster Final (PDF)',
            'specialite_choices': ScientificContributionFinalSubmission.SPECIALITE_CHOICES,
            'domaine_choices': ScientificContributionFinalSubmission.DOMAINE_COMMUNICATION_CHOICES,
            'require_contribution_number': _require_contribution_number(event),
        }
        return render(request, 'dashboard/eposter/final_submission_form.html', context)

    elif request.method == 'POST':
        return handle_final_submission(request, event, 'e_poster')


@require_http_methods(["GET", "POST"])
@csrf_exempt
def communication_orale_final_submission_form(request, event_id):
    """
    Display and handle Communication Orale final submission form
    No login required - uses contribution code for verification
    """
    event = get_object_or_404(Event, id=event_id)

    if request.method == 'GET':
        # Display the form
        context = {
            'event': event,
            'submission_type': 'communication_orale',
            'submission_label': 'Communication Orale',
            'file_label': 'Présentation Finale (PDF)',
            'specialite_choices': ScientificContributionFinalSubmission.SPECIALITE_CHOICES,
            'domaine_choices': ScientificContributionFinalSubmission.DOMAINE_COMMUNICATION_CHOICES,
            'require_contribution_number': _require_contribution_number(event),
        }
        return render(request, 'dashboard/eposter/final_submission_form.html', context)

    elif request.method == 'POST':
        return handle_final_submission(request, event, 'communication_orale')


def handle_final_submission(request, event, expected_type):
    """
    Handle final submission POST request for both E-Poster and Communication Orale.

    Always links to an accepted original ScientificContributionSubmission --
    there is no standalone path. How it's found depends on this event's
    EventFormConfiguration.require_contribution_number, not on whether the
    field happens to be filled in:
    1. Required -> contribution_number must exactly match a
       contribution_code for this event (plus type/email cross-checks).
    2. Not required -> codes aren't used for this event at all, so the
       typed value is never compared against an existing
       contribution_code. The original submission is matched by e-mail +
       participation type among accepted submissions instead
       (ambiguous/no match -> error asking to contact the organizer).
       Whatever was typed (non-blank) then BECOMES that submission's
       official contribution_code (rejected if another submission
       already has that exact code).
    """
    try:
        # Get form data
        contribution_number = request.POST.get('contribution_number', '').strip()
        nom = request.POST.get('nom', '').strip()
        prenom = request.POST.get('prenom', '').strip()
        email = request.POST.get('email', '').strip()
        telephone = request.POST.get('telephone', '').strip()
        grade = request.POST.get('grade', '')
        grade_autre = request.POST.get('grade_autre', '').strip()
        secteur = request.POST.get('secteur', '').strip()
        etablissement = request.POST.get('etablissement', '').strip()
        wilaya = request.POST.get('wilaya', '').strip()
        theme = request.POST.get('theme', '').strip()
        titre = request.POST.get('titre', '').strip()
        auteurs_json = request.POST.get('auteurs', '[]')
        abstract_file = request.FILES.get('abstract_file')
        
        # Parse co-authors
        import json
        try:
            co_authors_list = json.loads(auteurs_json)
            # Format co-authors as text
            co_auteurs = '\n'.join([f"{a.get('prenom', '')} {a.get('nom', '')} - {a.get('affiliation', '')}".strip() 
                                   for a in co_authors_list if a.get('nom') and a.get('prenom')])
        except:
            co_auteurs = ''
        
        # Main author info
        auteurs = f"{prenom} {nom}"
        
        # For specialite and domaine, use grade and theme as substitutes
        specialite = (grade if grade != 'autre' else grade_autre) or 'non_specifie'
        domaine_communication = theme if theme else 'divers'
        
        # Whether the code field is mandatory for this event -- if not,
        # authors who don't have (or lost) their code can still submit,
        # matched instead by e-mail + participation type below.
        code_required = _require_contribution_number(event)
        if code_required and not contribution_number:
            return JsonResponse({
                'success': False,
                'error': 'Le numéro de contribution est requis'
            }, status=400)

        # Validate required fields (contribution_number is handled above,
        # independently, since whether it's required depends on the event)
        if not all([nom, prenom, email, telephone, secteur, etablissement, wilaya, titre, abstract_file]):
            return JsonResponse({
                'success': False,
                'error': 'Tous les champs obligatoires doivent être remplis'
            }, status=400)

        # Validate file type (PDF only)
        if not abstract_file.name.lower().endswith('.pdf'):
            return JsonResponse({
                'success': False,
                'error': 'File must be in PDF format'
            }, status=400)

        type_names = {
            'e_poster': 'E-Poster',
            'communication_orale': 'Communication Orale'
        }

        if code_required:
            # Codes are in use for this event -- exact match required,
            # same validation as always.
            original_submission = ScientificContributionSubmission.objects.filter(
                contribution_code=contribution_number,
                event=event
            ).first()

            if not original_submission:
                return JsonResponse({
                    'success': False,
                    'error': 'Ce numéro de contribution n\'existe pas dans notre système. Veuillez vérifier le numéro ou contacter l\'organisateur.'
                }, status=400)

            if original_submission.type_participation != expected_type:
                return JsonResponse({
                    'success': False,
                    'error': f'Ce numéro de contribution est pour {type_names.get(original_submission.type_participation)}. Veuillez utiliser le bon formulaire de soumission finale.'
                }, status=400)

            if original_submission.email.lower() != email.lower():
                return JsonResponse({
                    'success': False,
                    'error': 'L\'email ne correspond pas à la soumission originale. Veuillez utiliser l\'email avec lequel vous avez soumis initialement.'
                }, status=400)
        else:
            # Codes aren't used for this event at all -- there is no real
            # contribution_code to match against, so whatever was typed
            # (or left blank) is taken as-is and saved on the final
            # submission unchanged. Matching the original accepted
            # submission is always done by e-mail + participation type
            # here, never by comparing the typed text to a code.
            candidates = list(ScientificContributionSubmission.objects.filter(
                event=event,
                email__iexact=email,
                type_participation=expected_type,
                status='accepted',
            ))

            if not candidates:
                return JsonResponse({
                    'success': False,
                    'error': "Aucune soumission acceptée de type "
                             f"{type_names.get(expected_type)} n'a été trouvée pour cet e-mail. "
                             "Vérifiez l'adresse utilisée lors de la soumission initiale, ou contactez l'organisateur."
                }, status=400)

            if len(candidates) > 1:
                return JsonResponse({
                    'success': False,
                    'error': "Plusieurs soumissions acceptées correspondent à cet e-mail pour ce type de participation. "
                             "Merci de contacter l'organisateur."
                }, status=400)

            original_submission = candidates[0]

            # Whatever the author typed becomes that submission's official
            # contribution_code -- since codes aren't otherwise assigned
            # for this event, their own entry (e.g. "54") IS the number
            # from here on (visible on the submission's committee page,
            # in exports, etc.), not just free text kept on the final
            # submission record.
            if contribution_number and contribution_number != original_submission.contribution_code:
                taken = ScientificContributionSubmission.objects.filter(
                    contribution_code=contribution_number
                ).exclude(id=original_submission.id).exists()
                if taken:
                    return JsonResponse({
                        'success': False,
                        'error': f'Le numéro « {contribution_number} » est déjà utilisé par une autre soumission. Veuillez en choisir un autre.'
                    }, status=400)
                original_submission.contribution_code = contribution_number
                original_submission.save(update_fields=['contribution_code', 'updated_at'])

        # Check if final submission already exists for this original submission
        final_submission = ScientificContributionFinalSubmission.objects.filter(
            original_submission=original_submission
        ).first()

        if final_submission:
            # Update existing final submission - override changed fields
            final_submission.nom = nom
            final_submission.email = email
            final_submission.telephone = telephone
            final_submission.specialite = specialite
            final_submission.domaine_communication = domaine_communication
            final_submission.contribution_number = contribution_number
            final_submission.titre = titre
            final_submission.auteurs = auteurs
            final_submission.co_auteurs = co_auteurs
            final_submission.abstract_file = abstract_file
            final_submission.ip_address = request.META.get('REMOTE_ADDR')
            final_submission.user_agent = request.META.get('HTTP_USER_AGENT', '')
            final_submission.save()

            message = 'Soumission finale mise à jour avec succès'
        else:
            # Create new final submission linked to original
            final_submission = ScientificContributionFinalSubmission.objects.create(
                original_submission=original_submission,
                event=event,
                nom=nom,
                email=email,
                telephone=telephone,
                specialite=specialite,
                domaine_communication=domaine_communication,
                contribution_number=contribution_number,
                titre=titre,
                auteurs=auteurs,
                co_auteurs=co_auteurs,
                abstract_file=abstract_file,
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )

            message = 'Soumission finale enregistrée avec succès'

        return JsonResponse({
            'success': True,
            'message': message,
            'submission_id': str(final_submission.id)
        })
        
    except Exception as e:
        print(f"Error in final submission: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': f'Erreur lors de la soumission: {str(e)}'
        }, status=500)


@never_cache
@require_GET
def eposter_public_gallery(request, event_id):
    """
    Public gallery of final E-Poster submissions for an event.
    No login required. Searchable by title or author name.
    """
    event = get_object_or_404(Event, id=event_id)

    query = request.GET.get('q', '').strip()

    submissions = ScientificContributionFinalSubmission.objects.filter(
        event=event,
        original_submission__type_participation='e_poster'
    ).select_related('original_submission').order_by('-submitted_at')

    if query:
        submissions = submissions.filter(
            Q(titre__icontains=query) |
            Q(auteurs__icontains=query) |
            Q(nom__icontains=query)
        )

    paginator = Paginator(submissions, 24)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'event': event,
        'page_obj': page_obj,
        'submissions': page_obj.object_list,
        'query': query,
    }

    return render(request, 'dashboard/eposter/public_gallery.html', context)
