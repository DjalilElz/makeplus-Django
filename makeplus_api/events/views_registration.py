"""
Public Event Registration Views
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction
from django.contrib.auth.models import User
from datetime import datetime
import hashlib
import re

from .models import Event, EventRegistration, Session, Participant, UserProfile
from dashboard.models_email import EventEmailTemplate


def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def calculate_spam_score(request, email, telephone):
    """Calculate spam score based on various factors"""
    score = 0
    
    # Check for suspicious patterns
    if re.search(r'[^\w\s@.-]', email):  # Special chars in email
        score += 10
    
    if not re.match(r'^[0-9\s\+\-\(\)]+$', telephone):  # Invalid phone format
        score += 15
    
    # Check submission rate from same IP
    ip_address = get_client_ip(request)
    recent_submissions = EventRegistration.objects.filter(
        ip_address=ip_address,
        created_at__gte=timezone.now() - timezone.timedelta(minutes=5)
    ).count()
    
    if recent_submissions > 3:
        score += 50
    
    # Check for duplicate emails in short time
    duplicate_emails = EventRegistration.objects.filter(
        email=email,
        created_at__gte=timezone.now() - timezone.timedelta(hours=1)
    ).count()
    
    if duplicate_emails > 2:
        score += 40
    
    return score


@require_http_methods(["GET"])
def event_registration_page(request, event_id):
    """
    Public event registration page
    URL: /events/{event_id}/register/
    """
    event = get_object_or_404(Event, id=event_id, registration_enabled=True)
    
    # Check if event is already completed
    if event.status == 'completed':
        messages.warning(request, "This event has already ended. Registration is closed.")
        return render(request, 'events/registration_closed.html', {'event': event})
    
    # Get sessions grouped by day for workshop selection
    sessions = Session.objects.filter(event=event).order_by('start_time')
    
    # Group sessions by day
    sessions_by_day = {}
    for session in sessions:
        day_key = session.start_time.date()
        day_label = session.start_time.strftime('%d %B %Y')
        
        if day_key not in sessions_by_day:
            sessions_by_day[day_key] = {
                'date': day_key,
                'label': day_label,
                'sessions': []
            }
        
        sessions_by_day[day_key]['sessions'].append(session)
    
    # Calculate countdown timer (time until event starts)
    now = timezone.now()
    time_until_event = None
    if event.start_date > now:
        delta = event.start_date - now
        time_until_event = {
            'days': delta.days,
            'hours': (delta.seconds // 3600) % 24,
            'minutes': (delta.seconds // 60) % 60,
            'seconds': delta.seconds % 60,
            'total_seconds': delta.total_seconds()
        }
    
    context = {
        'event': event,
        'sessions_by_day': sessions_by_day.values(),
        'time_until_event': time_until_event,
        'registration_config': event.registration_fields_config or {},
    }
    
    return render(request, 'events/public_registration.html', context)


@require_http_methods(["POST"])
def event_registration_submit(request, event_id):
    """
    Handle event registration form submission
    URL: /events/{event_id}/register/submit/
    """
    event = get_object_or_404(Event, id=event_id, registration_enabled=True)
    
    # Get form data
    nom = request.POST.get('nom', '').strip()
    prenom = request.POST.get('prenom', '').strip()
    email = request.POST.get('email', '').strip().lower()
    telephone = request.POST.get('telephone', '').strip()
    pays = request.POST.get('pays', 'algerie')
    wilaya = request.POST.get('wilaya', '').strip()
    secteur = request.POST.get('secteur', '')
    etablissement = request.POST.get('etablissement', '').strip()
    specialite = request.POST.get('specialite', '').strip()
    
    # Validate required fields
    errors = []
    if not nom:
        errors.append("Le nom est requis")
    if not prenom:
        errors.append("Le prénom est requis")
    if not email or '@' not in email:
        errors.append("Un email valide est requis")
    if not telephone:
        errors.append("Le numéro de téléphone est requis")
    if not secteur:
        errors.append("Le secteur est requis")
    if not etablissement:
        errors.append("L'établissement est requis")
    
    if errors:
        messages.error(request, "Erreurs de validation: " + ", ".join(errors))
        return redirect('events:event_registration', event_id=event_id)
    
    # Get selected workshops
    ateliers_selected = {}
    for key in request.POST:
        if key.startswith('workshop_'):
            # Format: workshop_{day}_{session_id}
            parts = key.split('_')
            if len(parts) >= 3:
                day = parts[1]
                session_id = parts[2]
                
                if day not in ateliers_selected:
                    ateliers_selected[day] = []
                
                ateliers_selected[day].append(session_id)
    
    # Anti-spam check
    spam_score = calculate_spam_score(request, email, telephone)
    is_spam = spam_score > 50
    
    if is_spam:
        messages.error(request, "Votre inscription a été marquée comme suspecte. Veuillez contacter l'organisateur.")
        return redirect('events:event_registration', event_id=event_id)
    
    # Check for duplicate registration
    existing_registration = EventRegistration.objects.filter(
        event=event,
        email=email
    ).first()
    
    if existing_registration:
        messages.warning(request, "Vous êtes déjà inscrit à cet événement. Un email de confirmation vous a été envoyé.")
        return redirect('events:registration_success', registration_id=existing_registration.id)
    
    # Create registration
    try:
        with transaction.atomic():
            registration = EventRegistration.objects.create(
                event=event,
                nom=nom,
                prenom=prenom,
                email=email,
                telephone=telephone,
                pays=pays,
                wilaya=wilaya,
                secteur=secteur,
                etablissement=etablissement,
                specialite=specialite,
                ateliers_selected=ateliers_selected,
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
                spam_score=spam_score,
                is_spam=is_spam
            )
            
            # Send confirmation email
            send_registration_confirmation_email(registration)
            
            messages.success(request, "Inscription réussie! Un email de confirmation vous a été envoyé.")
            return redirect('events:registration_success', registration_id=registration.id)
            
    except Exception as e:
        messages.error(request, f"Erreur lors de l'inscription: {str(e)}")
        return redirect('events:event_registration', event_id=event_id)


def send_registration_confirmation_email(registration):
    """Send confirmation email to registered user"""
    event = registration.event
    
    # Try to find registration confirmation template
    template = EventEmailTemplate.objects.filter(
        event=event,
        template_type='registration_confirmation',
        is_active=True
    ).first()
    
    if template:
        # Use template and replace variables
        subject = template.subject
        body = template.body_html or template.body
        
        # Replace template variables
        replacements = {
            '{{first_name}}': registration.prenom,
            '{{last_name}}': registration.nom,
            '{{event_name}}': event.name,
            '{{event_date}}': event.start_date.strftime('%d/%m/%Y'),
            '{{event_location}}': event.location,
            '{{participant_name}}': registration.get_full_name(),
        }
        
        for key, value in replacements.items():
            subject = subject.replace(key, value)
            body = body.replace(key, value)
    else:
        # Default confirmation email
        subject = f"Confirmation d'inscription - {event.name}"
        body = f"""
        <html>
        <body>
            <h2>Bienvenue {registration.prenom}!</h2>
            <p>Votre inscription à l'événement <strong>{event.name}</strong> a été confirmée.</p>
            <p><strong>Détails de l'événement:</strong></p>
            <ul>
                <li>Date: {event.start_date.strftime('%d/%m/%Y %H:%M')}</li>
                <li>Lieu: {event.location}</li>
            </ul>
            <p>Vous recevrez prochainement votre badge et plus d'informations.</p>
            <p>À bientôt!</p>
        </body>
        </html>
        """
    
    # Send email
    try:
        send_mail(
            subject=subject,
            message=body,  # Plain text version
            html_message=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[registration.email],
            fail_silently=False,
        )
        
        registration.confirmation_sent_at = timezone.now()
        registration.is_confirmed = True
        registration.save()
        
    except Exception as e:
        print(f"Failed to send confirmation email: {e}")


@require_http_methods(["GET"])
def registration_success(request, registration_id):
    """
    Registration success page
    URL: /events/registration/success/{registration_id}/
    """
    registration = get_object_or_404(EventRegistration, id=registration_id)
    
    context = {
        'registration': registration,
        'event': registration.event,
    }
    
    return render(request, 'events/registration_success.html', context)


# API endpoint for AJAX form submission (optional)
@require_http_methods(["POST"])
def event_registration_api(request, event_id):
    """
    JSON API endpoint for event registration
    URL: /api/events/{event_id}/register/
    """
    import json
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    
    event = get_object_or_404(Event, id=event_id, registration_enabled=True)
    
    # Extract and validate data
    required_fields = ['nom', 'prenom', 'email', 'telephone', 'secteur', 'etablissement']
    for field in required_fields:
        if not data.get(field):
            return JsonResponse({'error': f'{field} is required'}, status=400)
    
    # Anti-spam check
    spam_score = calculate_spam_score(request, data.get('email'), data.get('telephone'))
    
    if spam_score > 50:
        return JsonResponse({'error': 'Registration flagged as spam'}, status=403)
    
    # Check for duplicate
    if EventRegistration.objects.filter(event=event, email=data.get('email')).exists():
        return JsonResponse({'error': 'Already registered'}, status=409)
    
    try:
        with transaction.atomic():
            registration = EventRegistration.objects.create(
                event=event,
                nom=data.get('nom'),
                prenom=data.get('prenom'),
                email=data.get('email').lower(),
                telephone=data.get('telephone'),
                pays=data.get('pays', 'algerie'),
                wilaya=data.get('wilaya', ''),
                secteur=data.get('secteur'),
                etablissement=data.get('etablissement'),
                specialite=data.get('specialite', ''),
                ateliers_selected=data.get('ateliers_selected', {}),
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
                spam_score=spam_score
            )
            
            # Send confirmation email
            send_registration_confirmation_email(registration)
            
            return JsonResponse({
                'success': True,
                'registration_id': str(registration.id),
                'message': 'Registration successful'
            })
            
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
