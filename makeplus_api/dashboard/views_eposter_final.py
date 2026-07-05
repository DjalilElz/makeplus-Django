"""
Views for ePoster Final Submission
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, FileResponse, Http404
from django.views.decorators.http import require_http_methods, require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from django.conf import settings
from .models_eposter import EPosterSubmission, EPosterFinalSubmission
from events.models import Event
import os


@require_http_methods(["GET", "POST"])
@csrf_exempt
def eposter_final_submission_form(request, event_id):
    """
    Display and handle final contribution submission form
    No login required - uses contribution code for verification
    
    Two cases:
    1. User with original submission + email match → Update/link to original
    2. User without original submission → Create standalone final submission
    """
    event = get_object_or_404(Event, id=event_id)
    
    if request.method == 'GET':
        # Display the form
        context = {
            'event': event,
            'specialite_choices': EPosterFinalSubmission.SPECIALITE_CHOICES,
            'domaine_choices': EPosterFinalSubmission.DOMAINE_COMMUNICATION_CHOICES,
        }
        return render(request, 'dashboard/eposter/final_submission_form.html', context)
    
    elif request.method == 'POST':
        # Handle form submission
        try:
            # Get form data
            contribution_number = request.POST.get('contribution_number', '').strip()
            nom = request.POST.get('nom', '').strip()
            email = request.POST.get('email', '').strip()
            telephone = request.POST.get('telephone', '').strip()
            specialite = request.POST.get('specialite', '')
            domaine_communication = request.POST.get('domaine_communication', '')
            titre = request.POST.get('titre', '').strip()
            auteurs = request.POST.get('auteurs', '').strip()
            co_auteurs = request.POST.get('co_auteurs', '').strip()
            abstract_file = request.FILES.get('abstract_file')
            
            # Validate required fields
            if not all([contribution_number, nom, email, telephone, specialite, domaine_communication, titre, auteurs, abstract_file]):
                return JsonResponse({
                    'success': False,
                    'error': 'Tous les champs obligatoires doivent être remplis'
                }, status=400)
            
            # Validate file type (PDF only)
            if not abstract_file.name.lower().endswith('.pdf'):
                return JsonResponse({
                    'success': False,
                    'error': 'Le fichier doit être au format PDF'
                }, status=400)
            
            # Check if contribution code exists in original submissions
            original_submission = EPosterSubmission.objects.filter(
                contribution_code=contribution_number,
                event=event
            ).first()
            
            if original_submission:
                # Case 1: Original submission exists
                # Validate email matches
                if original_submission.email != email:
                    return JsonResponse({
                        'success': False,
                        'error': 'L\'email ne correspond pas à la soumission originale. Veuillez utiliser l\'email avec lequel vous avez soumis initialement.'
                    }, status=400)
                
                # Email matches - proceed with update/create
                # Check if final submission already exists for this original submission
                final_submission = EPosterFinalSubmission.objects.filter(
                    original_submission=original_submission
                ).first()
                
                if final_submission:
                    # Update existing final submission - override changed fields
                    final_submission.nom = nom
                    final_submission.email = email
                    final_submission.telephone = telephone
                    final_submission.specialite = specialite
                    final_submission.domaine_communication = domaine_communication
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
                    final_submission = EPosterFinalSubmission.objects.create(
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
                # Case 2: No original submission - create standalone final submission
                # Check if contribution code format is valid
                if not (contribution_number.startswith('EPOSTER-') or contribution_number.startswith('COMORAL-')):
                    return JsonResponse({
                        'success': False,
                        'error': 'Format du numéro de contribution invalide. Il doit commencer par EPOSTER- ou COMORAL-'
                    }, status=400)
                
                # Check if this contribution number is already used in final submissions
                existing_final = EPosterFinalSubmission.objects.filter(
                    contribution_number=contribution_number,
                    event=event
                ).first()
                
                if existing_final:
                    return JsonResponse({
                        'success': False,
                        'error': 'Ce numéro de contribution a déjà été utilisé pour une soumission finale'
                    }, status=400)
                
                # Create standalone final submission
                final_submission = EPosterFinalSubmission.objects.create(
                    original_submission=None,  # No link to original
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


@require_GET
def eposter_gallery(request, event_id):
    """
    Display gallery of all final eposter submissions for an event
    """
    event = get_object_or_404(Event, id=event_id)
    
    # Get all final submissions for this event
    final_submissions = EPosterFinalSubmission.objects.filter(
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
    final_submission = get_object_or_404(EPosterFinalSubmission, id=submission_id)
    
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
