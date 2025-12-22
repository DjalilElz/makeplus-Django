"""
Views for Caisse (Cash Register) Operators
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import never_cache
from django.db.models import Q
from django.utils import timezone
import json
from decimal import Decimal
import qrcode
from io import BytesIO
import base64

from caisse.models import Caisse, PayableItem, CaisseTransaction
from events.models import Participant, Event


def caisse_required(view_func):
    """Decorator to check if caisse is logged in"""
    def wrapper(request, *args, **kwargs):
        caisse_id = request.session.get('caisse_id')
        if not caisse_id:
            messages.warning(request, 'Please log in to continue.')
            return redirect('caisse:login')
        
        try:
            caisse = Caisse.objects.select_related('event').get(id=caisse_id, is_active=True)
            request.caisse = caisse
        except Caisse.DoesNotExist:
            del request.session['caisse_id']
            messages.error(request, 'Your caisse session is invalid. Please log in again.')
            return redirect('caisse:login')
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


# ==================== Authentication ====================

def caisse_login(request):
    """Login page for caisse operators"""
    if request.session.get('caisse_id'):
        return redirect('caisse:dashboard')
    
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        try:
            caisse = Caisse.objects.get(email=email, is_active=True)
            if caisse.check_password(password):
                request.session['caisse_id'] = caisse.id
                request.session['caisse_name'] = caisse.name
                messages.success(request, f'Welcome to {caisse.name}!')
                return redirect('caisse:dashboard')
            else:
                messages.error(request, 'Invalid email or password.')
        except Caisse.DoesNotExist:
            messages.error(request, 'Invalid email or password.')
    
    return render(request, 'caisse/login.html')


@caisse_required
def caisse_logout(request):
    """Logout caisse operator"""
    caisse_name = request.session.get('caisse_name', 'Caisse')
    del request.session['caisse_id']
    if 'caisse_name' in request.session:
        del request.session['caisse_name']
    messages.success(request, f'Logged out from {caisse_name}.')
    return redirect('caisse:login')


# ==================== Dashboard ====================

@never_cache
@caisse_required
def caisse_dashboard(request):
    """Main dashboard for caisse operators"""
    caisse = request.caisse
    event = caisse.event
    
    # Get payable items for this event
    payable_items = PayableItem.objects.filter(
        event=event,
        is_active=True
    ).select_related('session').order_by('item_type', 'name')
    
    # Statistics
    total_amount = caisse.get_total_amount()
    total_participants = caisse.get_total_participants()
    transaction_count = caisse.get_transaction_count()
    
    # Get only participants (users with role 'participant') for this event
    from events.models import UserEventAssignment
    participant_user_ids = UserEventAssignment.objects.filter(
        event=event,
        role='participant'
    ).values_list('user_id', flat=True)
    
    all_participants = Participant.objects.filter(
        event=event,
        user_id__in=participant_user_ids
    ).select_related('user').prefetch_related(
        'caisse_transactions__items',
        'caisse_transactions__caisse'
    ).order_by('user__first_name', 'user__last_name')
    
    # Build a dictionary of participant paid items for quick lookup
    participant_paid_items = {}
    for participant in all_participants:
        completed_transactions = participant.caisse_transactions.filter(status='completed')
        paid_item_ids = set()
        for transaction in completed_transactions:
            paid_item_ids.update(transaction.items.values_list('id', flat=True))
        participant_paid_items[str(participant.id)] = list(paid_item_ids)
    
    # Recent transactions
    recent_transactions = caisse.transactions.filter(
        status='completed'
    ).select_related('participant__user').prefetch_related('items').order_by('-created_at')[:10]
    
    context = {
        'caisse': caisse,
        'event': event,
        'payable_items': payable_items,
        'total_amount': total_amount,
        'total_participants': total_participants,
        'transaction_count': transaction_count,
        'all_participants': all_participants,
        'participant_paid_items_json': json.dumps(participant_paid_items),
        'recent_transactions': recent_transactions
    }
    
    return render(request, 'caisse/dashboard.html', context)


# ==================== Participant Search ====================

@caisse_required
@require_http_methods(["GET"])
def search_participant(request):
    """Search for participant by name, email, or QR code"""
    query = request.GET.get('q', '').strip()
    caisse = request.caisse
    event = caisse.event
    
    if not query:
        return JsonResponse({'success': False, 'message': 'Please enter a search term'})
    
    # Get only users with 'participant' role
    from events.models import UserEventAssignment
    participant_user_ids = UserEventAssignment.objects.filter(
        event=event,
        role='participant'
    ).values_list('user_id', flat=True)
    
    # Search participants with participant role only
    participants = Participant.objects.filter(
        event=event,
        user_id__in=participant_user_ids
    ).filter(
        Q(user__first_name__icontains=query) |
        Q(user__last_name__icontains=query) |
        Q(user__email__icontains=query) |
        Q(user__username__icontains=query) |
        Q(qr_code__icontains=query)
    ).select_related('user').prefetch_related('caisse_transactions')[:10]
    
    if not participants.exists():
        return JsonResponse({'success': False, 'message': 'No participants found'})
    
    results = []
    for participant in participants:
        # Check if already checked in
        has_transaction = participant.caisse_transactions.filter(
            caisse=caisse,
            status='completed'
        ).exists()
        
        # Get previous transactions
        transaction_count = participant.caisse_transactions.filter(
            status='completed'
        ).count()
        
        results.append({
            'id': participant.id,
            'name': participant.user.get_full_name() or participant.user.username,
            'email': participant.user.email,
            'qr_code': participant.qr_code,
            'checked_in': has_transaction,
            'transaction_count': transaction_count
        })
    
    return JsonResponse({'success': True, 'participants': results})


@caisse_required
@require_http_methods(["GET"])
def get_participant_paid_items(request, participant_id):
    """Get list of items already paid by a participant"""
    caisse = request.caisse
    
    try:
        participant = Participant.objects.get(id=participant_id, event=caisse.event)
    except Participant.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Participant not found'})
    
    # Get all completed transactions for this participant
    completed_transactions = CaisseTransaction.objects.filter(
        participant=participant,
        status='completed'
    ).prefetch_related('items')
    
    # Collect all paid item IDs
    paid_item_ids = set()
    for transaction in completed_transactions:
        paid_item_ids.update(transaction.items.values_list('id', flat=True))
    
    return JsonResponse({
        'success': True,
        'paid_items': list(paid_item_ids)
    })


# ==================== Transaction Processing ====================

@caisse_required
@require_http_methods(["POST"])
def process_transaction(request):
    """Process a payment transaction"""
    import json
    
    caisse = request.caisse
    
    # Parse JSON body
    try:
        data = json.loads(request.body)
        participant_id = data.get('participant_id')
        item_ids = data.get('items', [])
        notes = data.get('notes', '')
        action = data.get('action', 'process_and_print')  # Default to process_and_print
    except json.JSONDecodeError:
        # Fallback to POST data
        participant_id = request.POST.get('participant_id')
        item_ids = request.POST.getlist('items[]')
        notes = request.POST.get('notes', '')
        action = request.POST.get('action', 'process_and_print')
    
    if not participant_id:
        return JsonResponse({'success': False, 'message': 'Participant ID required'})
    
    try:
        participant = Participant.objects.get(id=participant_id, event=caisse.event)
    except Participant.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Participant not found'})
    
    # For print_badge action, we don't need items
    if action == 'print_badge':
        return JsonResponse({
            'success': True,
            'message': 'Badge print initiated',
            'action': 'print_badge'
        })
    
    # For process and process_and_print, items are required
    if not item_ids:
        return JsonResponse({'success': False, 'message': 'Please select at least one item'})
    
    # Get items and calculate total
    items = PayableItem.objects.filter(id__in=item_ids, event=caisse.event, is_active=True)
    if not items.exists():
        return JsonResponse({'success': False, 'message': 'Invalid items selected'})
    
    total_amount = sum(item.price for item in items)
    
    # Create transaction
    transaction = CaisseTransaction.objects.create(
        caisse=caisse,
        participant=participant,
        total_amount=total_amount,
        status='completed',
        notes=notes,
        marked_present=True
    )
    transaction.items.set(items)
    
    # Grant access to the selected sessions/ateliers
    # Update participant's allowed_rooms with sessions linked to the paid items
    from events.models import Session
    
    for item in items:
        if item.session:
            # Get the session
            session = item.session
            
            # Grant access by adding session's room to participant's allowed_rooms
            if session.room:
                # Get or update participant's allowed_rooms in metadata
                if not participant.metadata:
                    participant.metadata = {}
                
                allowed_rooms = participant.metadata.get('allowed_rooms', [])
                if not isinstance(allowed_rooms, list):
                    allowed_rooms = []
                
                # Add room ID if not already present
                room_id_str = str(session.room.id)
                if room_id_str not in allowed_rooms:
                    allowed_rooms.append(room_id_str)
                
                participant.metadata['allowed_rooms'] = allowed_rooms
                participant.save()
    
    return JsonResponse({
        'success': True,
        'message': 'Transaction processed successfully',
        'transaction_id': transaction.id,
        'total_amount': float(total_amount),
        'action': action
    })


# ==================== Transaction History ====================

@caisse_required
def transaction_history(request):
    """View transaction history for this caisse"""
    caisse = request.caisse
    
    status_filter = request.GET.get('status', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    transactions = caisse.transactions.select_related(
        'participant__user'
    ).prefetch_related('items').order_by('-created_at')
    
    # Apply filters
    if status_filter:
        transactions = transactions.filter(status=status_filter)
    
    if date_from:
        transactions = transactions.filter(created_at__date__gte=date_from)
    
    if date_to:
        transactions = transactions.filter(created_at__date__lte=date_to)
    
    context = {
        'caisse': caisse,
        'transactions': transactions[:100],  # Limit to 100
        'status_filter': status_filter,
        'date_from': date_from,
        'date_to': date_to
    }
    
    return render(request, 'caisse/transaction_history.html', context)


@caisse_required
@require_http_methods(["POST"])
def cancel_transaction(request, transaction_id):
    """Cancel a transaction and remove granted access"""
    import json
    from events.models import Session
    
    caisse = request.caisse
    
    try:
        transaction = CaisseTransaction.objects.get(id=transaction_id, caisse=caisse, status='completed')
    except CaisseTransaction.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Transaction not found or already cancelled'})
    
    # Parse JSON body
    try:
        data = json.loads(request.body)
        reason = data.get('reason', 'No reason provided')
    except json.JSONDecodeError:
        reason = request.POST.get('reason', 'No reason provided')
    
    # Get the participant before canceling
    participant = transaction.participant
    
    # Collect room IDs from the cancelled items that need to be removed
    rooms_to_remove = []
    for item in transaction.items.all():
        if item.session and item.session.room:
            rooms_to_remove.append(str(item.session.room.id))
    
    # Remove access to these rooms from participant's metadata
    if rooms_to_remove and participant.metadata and 'allowed_rooms' in participant.metadata:
        allowed_rooms = participant.metadata.get('allowed_rooms', [])
        if isinstance(allowed_rooms, list):
            # Check if any other completed transactions grant access to these rooms
            # Only remove if no other completed transaction provides access
            other_completed_transactions = CaisseTransaction.objects.filter(
                participant=participant,
                status='completed'
            ).exclude(id=transaction.id).prefetch_related('items__session__room')
            
            # Collect room IDs from other completed transactions
            rooms_from_other_transactions = set()
            for other_trans in other_completed_transactions:
                for item in other_trans.items.all():
                    if item.session and item.session.room:
                        rooms_from_other_transactions.add(str(item.session.room.id))
            
            # Remove only rooms not granted by other transactions
            new_allowed_rooms = [
                room_id for room_id in allowed_rooms 
                if room_id not in rooms_to_remove or room_id in rooms_from_other_transactions
            ]
            
            participant.metadata['allowed_rooms'] = new_allowed_rooms
            participant.save()
    
    # Cancel the transaction
    transaction.cancel(cancelled_by=caisse.name, reason=reason)
    
    return JsonResponse({
        'success': True,
        'message': 'Transaction cancelled successfully and access revoked'
    })


# ==================== Badge Printing ====================

@caisse_required
def print_badge(request, participant_id):
    """Generate printable badge with QR code"""
    caisse = request.caisse
    
    try:
        participant = Participant.objects.select_related('user').get(
            id=participant_id,
            event=caisse.event
        )
    except Participant.DoesNotExist:
        messages.error(request, 'Participant not found')
        return redirect('caisse:dashboard')
    
    # Generate QR code image
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(participant.badge_id)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()
    
    context = {
        'caisse': caisse,
        'participant': participant,
        'event': caisse.event,
        'name': participant.user.get_full_name() or participant.user.username,
        'email': participant.user.email,
        'badge_id': participant.badge_id,
        'qr_code_base64': qr_code_base64
    }
    
    return render(request, 'caisse/print_badge.html', context)
