"""
Views for ePoster and Communication Orale Final Submissions
Separate views for each submission type
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, FileResponse, Http404
from django.views.decorators.http import require_http_methods, require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from django.conf import settings
from .models_eposter import ScientificContributionSubmission, ScientificContributionFinalSubmission
from events.models import Event
import os


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
        }
        return render(request, 'dashboard/eposter/final_submission_form.html', context)
    
    elif request.method == 'POST':
        return handle_final_submission(request, event, 'communication_orale')


def handle_final_submission(request, event, expected_type):
    """
    Handle final submission POST request for both E-Poster and Communication Orale
    
    Two cases:
    1. User with original submission + email match → Update/link to original
    2. User without original submission → Create standalone final submission
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
        service = request.POST.get('service', '').strip()
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
        
        # Ensure contribution_number is not empty
        if not contribution_number:
            return JsonResponse({
                'success': False,
                'error': 'Le numéro de contribution est requis'
            }, status=400)
        
        # Validate required fields
        if not all([contribution_number, nom, prenom, email, telephone, grade, service, etablissement, wilaya, titre, abstract_file]):
            return JsonResponse({
                'success': False,
                'error': 'All required fields must be filled'
            }, status=400)
        
        # Validate file type (PDF only)
        if not abstract_file.name.lower().endswith('.pdf'):
            return JsonResponse({
                'success': False,
                'error': 'File must be in PDF format'
            }, status=400)
        
        # Check if contribution code exists in original submissions
        original_submission = ScientificContributionSubmission.objects.filter(
            contribution_code=contribution_number,
            event=event
        ).first()
        
        if original_submission:
            # Case 1: Original submission exists
            
            # Validate submission type matches
            if original_submission.type_participation != expected_type:
                type_names = {
                    'e_poster': 'E-Poster',
                    'communication_orale': 'Communication Orale'
                }
                return JsonResponse({
                    'success': False,
                    'error': f'Ce numéro de contribution est pour {type_names.get(original_submission.type_participation)}. Veuillez utiliser le bon formulaire de soumission finale.'
                }, status=400)
            
            # Validate email matches
            if original_submission.email.lower() != email.lower():
                return JsonResponse({
                    'success': False,
                    'error': 'L\'email ne correspond pas à la soumission originale. Veuillez utiliser l\'email avec lequel vous avez soumis initialement.'
                }, status=400)
            
            # Email and type match - proceed with update/create
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
            
        else:
            # Case 2: No original submission found
            return JsonResponse({
                'success': False,
                'error': 'Ce numéro de contribution n\'existe pas dans notre système. Veuillez vérifier le numéro ou contacter l\'organisateur.'
            }, status=400)
        
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


@require_GET
def eposter_gallery(request, event_id):
    """
    Display gallery of all final eposter submissions for an event
    """
    event = get_object_or_404(Event, id=event_id)
    
    # Get all final submissions for this event
    final_submissions = ScientificContributionFinalSubmission.objects.filter(
        event=event
    ).select_related('original_submission').order_by('-submitted_at')
    
    context = {
        'event': event,
        'submissions': final_submissions,
    }
    
    return render(request, 'dashboard/eposter/gallery.html', context)


@require_GET
def eposter_view_pdf(request, submission_id):
    """
    View or download the PDF file of a final submission
    """
    final_submission = get_object_or_404(ScientificContributionFinalSubmission, id=submission_id)
    
    # Get the file path
    file_path = final_submission.abstract_file.path
    
    if not os.path.exists(file_path):
        raise Http404("Fichier PDF introuvable")
    
    # Return the PDF file
    response = FileResponse(
        open(file_path, 'rb'),
        content_type='application/pdf'
    )
    
    # Set filename for download
    filename = f"contribution_{final_submission.contribution_number}.pdf"
    response['Content-Disposition'] = f'inline; filename="{filename}"'
    
    return response
