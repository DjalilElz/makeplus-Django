"""
Keeps the caisse's PayableItems in step with the registration bloc items
(status/restauration/social_event) they mirror. This used to happen only
when someone clicked the payable-items sync button or ran
sync_paid_bloc_items -- an event whose blocs were set up without that
step had no Status item at its caisse at all, so every participant who
owed their registration fee was shown as "Gratuit" (SARM 2026).
"""
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

from dashboard.models_blocs import BlocItem
from .models import PayableItem


@receiver(post_save, sender=BlocItem)
def mirror_bloc_item_to_caisse(sender, instance, **kwargs):
    # Same name/price/type as sync_paid_bloc_items, so the two never disagree.
    name = f"{instance.get_bloc_display()} - {instance.name}"
    payable = PayableItem.objects.filter(event_id=instance.event_id, bloc_item=instance).first()
    if payable is None:
        if instance.is_active:
            PayableItem.objects.create(
                event_id=instance.event_id, bloc_item=instance, name=name,
                price=instance.price, item_type='bloc', is_active=True,
            )
        return
    if (payable.name, payable.price, payable.is_active) != (name, instance.price, instance.is_active):
        payable.name, payable.price, payable.is_active = name, instance.price, instance.is_active
        payable.save(update_fields=['name', 'price', 'is_active'])


@receiver(pre_delete, sender=BlocItem)
def deactivate_mirrored_payable(sender, instance, **kwargs):
    # bloc_item is SET_NULL, which would leave an orphaned item still
    # offered at the caisse; past transactions keep pointing at it.
    PayableItem.objects.filter(bloc_item=instance).update(is_active=False)
