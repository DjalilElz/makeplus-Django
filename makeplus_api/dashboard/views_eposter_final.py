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
    Display and handle final eposter submission form
    No login required - uses eposter code for verification
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
            poster_number = request.POST.get('poster_number', '').strip()
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
            if not all([poster_number, nom, email, telephone, specialite, domaine_communication, titre, auteurs, abstract_file]):
                return JsonResponse({
                    'success': False,
                    'error': 'Tous les champs obligatoires doivent être remplis'
                }, status=400)
            
            # Verify eposter code exists and is accepted
            try:
                original_submission = EPosterSubmission.objects.get(
                    contribution_code=poster_number,
                    event=event,
                    status='accepted'
                )
            except EPosterSubmission.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': 'Code ePoster invalide ou non validé pour cet événement'
                }, status=400)
            
            # Check if final submission already exists
            if hasattr(original_submission, 'final_submission'):
                return JsonResponse({
                    'success': False,
                    'error': 'Une soumission finale a déjà été effectuée avec ce code'
                }, status=400)
            
            # Validate file type (PDF only)
            if not abstract_file.name.lower().endswith('.pdf'):
                return JsonResponse({
                    'success': False,
                    'error': 'Le fichier doit être au format PDF'
                }, status=400)
            
            # Create final submission
            final_submission = EPosterFinalSubmission.objects.create(
                original_submission=original_submission,
                event=event,
                nom=nom,
                email=email,
                telephone=telephone,
                specialite=specialite,
                domaine_communication=domaine_communication,
                contribution_number=poster_number,
                titre=titre,
                auteurs=auteurs,
                co_auteurs=co_auteurs,
                abstract_file=abstract_file,
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Soumission finale enregistrée avec succès',
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
