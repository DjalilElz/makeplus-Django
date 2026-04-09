"""
Signals for automatic syncing of paid sessions to payable items
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from events.models import Session
from caisse.models import PayableItem


@receiver(post_save, sender=Session)
def sync_session_to_payable_item(sender, instance, created, **kwargs):
    """
    Automatically create/update PayableItem when a paid session is saved
    """
    session = instance
    
    # Only process if session is paid
    if session.is_paid and session.price > 0:
        # Create or update payable item
        payable_item, item_created = PayableItem.objects.get_or_create(
            event=session.event,
            session=session,
            defaults={
                'name': f"{session.get_session_type_display()} - {session.title}",
                'description': session.description or f"{session.speaker_name} - {session.start_time.strftime('%d/%m/%Y %H:%M')}",
                'price': session.price,
                'item_type': 'session',
                'is_active': True
            }
        )
        
        # Update if already exists
        if not item_created:
            updated = False
            new_name = f"{session.get_session_type_display()} - {session.title}"
            
            if payable_item.name != new_name:
                payable_item.name = new_name
                updated = True
            
            if payable_item.price != session.price:
                payable_item.price = session.price
                updated = True
            
            if payable_item.description != (session.description or f"{session.speaker_name} - {session.start_time.strftime('%d/%m/%Y %H:%M')}"):
                payable_item.description = session.description or f"{session.speaker_name} - {session.start_time.strftime('%d/%m/%Y %H:%M')}"
                updated = True
            
            if not payable_item.is_active:
                payable_item.is_active = True
                updated = True
            
            if updated:
                payable_item.save()
    
    else:
        # If session is no longer paid, deactivate the payable item
        try:
            payable_item = PayableItem.objects.get(
                event=session.event,
                session=session
            )
            if payable_item.is_active:
                payable_item.is_active = False
                payable_item.save()
        except PayableItem.DoesNotExist:
            pass


@receiver(post_delete, sender=Session)
def deactivate_payable_item_on_session_delete(sender, instance, **kwargs):
    """
    Deactivate PayableItem when session is deleted
    """
    session = instance
    
    try:
        payable_item = PayableItem.objects.get(
            event=session.event,
            session=session
        )
        payable_item.is_active = False
        payable_item.save()
    except PayableItem.DoesNotExist:
        pass
