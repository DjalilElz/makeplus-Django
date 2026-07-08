"""
Registration Blocs & Paid Registration models.

Adds a configurable, per-event paid-registration flow to the form-builder
form (FormConfiguration). Four "blocs" (categories) of payable items:

  - Bloc 1: Status         (custom items, admin-defined)
  - Bloc 2: Restauration   (custom items, admin-defined)
  - Bloc 3: Workshops      (reuses existing paid Sessions, no BlocItem rows)
  - Bloc 4: Social Event   (custom items, admin-defined)

Registration-time payment (offline bank transfer with an uploaded receipt)
is recorded here; on-site caisse payment/fulfillment is recorded in
caisse.PayableItem / CaisseTransaction. A RegistrationOrder's items get
mirrored into PayableItem (see caisse.management.commands.sync_paid_bloc_items)
so an approved order's reservations can be looked up and confirmed at the
caisse counter via RegistrationOrder.participant.
"""
import uuid
from decimal import Decimal

from django.contrib.auth.models import User
from django.db import models

from events.models import Event


# The three custom (item-based) blocs. Workshops (bloc 3) is not here because
# it reuses Sessions and never has BlocItem rows.
CUSTOM_BLOC_CHOICES = [
    ('status', 'Status'),
    ('restauration', 'Restauration'),
    ('social_event', 'Social Event'),
]

SELECT_MODE_CHOICES = [
    ('single', 'Single choice (radio)'),
    ('multiple', 'Multiple choice (checkbox)'),
]


class EventBlocConfig(models.Model):
    """Per-event configuration of blocs, visibility, and reductions."""
    event = models.OneToOneField(Event, on_delete=models.CASCADE, related_name='bloc_config')

    # Bloc visibility on the public form
    show_status = models.BooleanField(default=False)
    show_restauration = models.BooleanField(default=False)
    show_workshops = models.BooleanField(default=False)
    show_social_event = models.BooleanField(default=False)

    # Per-custom-bloc selection mode
    status_select_mode = models.CharField(max_length=10, choices=SELECT_MODE_CHOICES, default='single')
    restauration_select_mode = models.CharField(max_length=10, choices=SELECT_MODE_CHOICES, default='multiple')
    social_event_select_mode = models.CharField(max_length=10, choices=SELECT_MODE_CHOICES, default='multiple')

    # Reduction by period (date ranges -> % off whole cart)
    reduction_by_period_enabled = models.BooleanField(default=False)

    # Reduction by number of distinct blocs selected
    reduction_by_blocs_enabled = models.BooleanField(default=False)
    reduction_2_blocs = models.DecimalField(max_digits=5, decimal_places=2, default=0,
                                            help_text="% off when items from 2 distinct blocs are selected")
    reduction_3_blocs = models.DecimalField(max_digits=5, decimal_places=2, default=0,
                                            help_text="% off when items from 3 distinct blocs are selected")
    reduction_4_blocs = models.DecimalField(max_digits=5, decimal_places=2, default=0,
                                            help_text="% off when items from 4 distinct blocs are selected")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Event Bloc Configuration'
        verbose_name_plural = 'Event Bloc Configurations'

    def __str__(self):
        return f"Bloc config - {self.event.name}"

    def any_bloc_visible(self):
        return any([self.show_status, self.show_restauration, self.show_workshops, self.show_social_event])

    def select_mode_for(self, bloc):
        return {
            'status': self.status_select_mode,
            'restauration': self.restauration_select_mode,
            'social_event': self.social_event_select_mode,
        }.get(bloc, 'multiple')

    def blocs_reduction_percent(self, distinct_bloc_count):
        """% reduction for the number of distinct blocs selected."""
        if not self.reduction_by_blocs_enabled:
            return Decimal('0')
        return {
            2: self.reduction_2_blocs,
            3: self.reduction_3_blocs,
            4: self.reduction_4_blocs,
        }.get(distinct_bloc_count, Decimal('0'))


class BlocItem(models.Model):
    """A custom payable item inside Status / Restauration / Social Event."""
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='bloc_items')
    bloc = models.CharField(max_length=20, choices=CUSTOM_BLOC_CHOICES)
    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Bloc Item'
        verbose_name_plural = 'Bloc Items'
        ordering = ['bloc', 'order', 'name']
        indexes = [
            models.Index(fields=['event', 'bloc', 'is_active']),
        ]

    def __str__(self):
        return f"{self.get_bloc_display()} - {self.name} ({self.price})"


class ReductionPeriod(models.Model):
    """A date range mapped to a single % discount on the whole cart."""
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='reduction_periods')
    name = models.CharField(max_length=100, blank=True, help_text="Optional label, e.g. 'Early bird'")
    start_date = models.DateField()
    end_date = models.DateField()
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Reduction Period'
        verbose_name_plural = 'Reduction Periods'
        ordering = ['start_date']

    def __str__(self):
        return f"{self.name or 'Period'} {self.start_date} - {self.end_date} ({self.discount_percent}%)"

    def contains(self, a_date):
        return self.start_date <= a_date <= self.end_date


class RegistrationOrder(models.Model):
    """A paid registration submitted from the public form (pending approval)."""
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='registration_orders')
    form_submission = models.ForeignKey(
        'FormSubmission', on_delete=models.SET_NULL, null=True, blank=True, related_name='registration_orders'
    )
    # Set once an admin approves the order (see registration_order_update) --
    # lets the caisse counter look up "what did this participant reserve".
    participant = models.ForeignKey(
        'events.Participant', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='registration_orders'
    )

    # Contact snapshot (for admin listing / search without joining the submission)
    full_name = models.CharField(max_length=255, blank=True)
    email = models.EmailField(blank=True)

    # Snapshot of what was selected: list of
    # {bloc, type: 'item'|'session', id, name, price}
    items_snapshot = models.JSONField(default=list, blank=True)
    # {bloc: subtotal} as strings
    subtotals = models.JSONField(default=dict, blank=True)
    distinct_blocs_count = models.IntegerField(default=0)

    # Money (DZD, 2 decimals)
    total_before_reduction = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    period_discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    blocs_discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    total_discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    total_after_reduction = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Bank transfer proof
    receipt_file = models.FileField(upload_to='registrations/receipts/')

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    admin_notes = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='reviewed_registration_orders')
    reviewed_at = models.DateTimeField(null=True, blank=True)

    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Registration Order'
        verbose_name_plural = 'Registration Orders'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['event', 'status', '-created_at']),
            models.Index(fields=['email']),
        ]

    def __str__(self):
        return f"{self.full_name or self.email} - {self.total_after_reduction} DZD ({self.status})"
