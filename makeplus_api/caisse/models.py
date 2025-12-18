from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from events.models import Event, Participant, Session
from django.utils import timezone


class Caisse(models.Model):
    """Cash register/checkout station for an event"""
    name = models.CharField(max_length=100, help_text="Caisse name (e.g., 'Caisse 1', 'Main Entrance')")
    email = models.EmailField(unique=True, help_text="Login email for caisse operator")
    password = models.CharField(max_length=128, help_text="Hashed password")
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='caisses')
    is_active = models.BooleanField(default=True, help_text="Whether this caisse is currently active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Caisse"
        verbose_name_plural = "Caisses"
        ordering = ['event', 'name']
        indexes = [
            models.Index(fields=['event', 'is_active']),
            models.Index(fields=['email']),
        ]

    def __str__(self):
        return f"{self.name} - {self.event.name}"

    def set_password(self, raw_password):
        """Hash and set password"""
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        """Check if provided password matches"""
        return check_password(raw_password, self.password)

    def get_total_amount(self):
        """Get total amount collected by this caisse"""
        completed_transactions = self.transactions.filter(status='completed')
        return sum(t.total_amount for t in completed_transactions)

    def get_total_participants(self):
        """Get total number of participants processed"""
        return self.transactions.filter(status='completed').values('participant').distinct().count()

    def get_transaction_count(self):
        """Get total number of completed transactions"""
        return self.transactions.filter(status='completed').count()


class PayableItem(models.Model):
    """Items that can be paid for at a caisse"""
    ITEM_TYPES = [
        ('atelier', 'Atelier/Workshop'),
        ('dinner', 'Dinner/Meal'),
        ('other', 'Other'),
    ]

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='payable_items')
    name = models.CharField(max_length=200, help_text="Item name")
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Price in local currency")
    item_type = models.CharField(max_length=20, choices=ITEM_TYPES, default='other')
    session = models.ForeignKey(Session, on_delete=models.SET_NULL, null=True, blank=True, 
                                related_name='payable_items',
                                help_text="Link to session if this is an atelier payment")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Payable Item"
        verbose_name_plural = "Payable Items"
        ordering = ['event', 'item_type', 'name']
        indexes = [
            models.Index(fields=['event', 'is_active']),
            models.Index(fields=['item_type']),
        ]

    def __str__(self):
        return f"{self.name} - {self.price} ({self.event.name})"


class CaisseTransaction(models.Model):
    """Record of a transaction at a caisse"""
    STATUS_CHOICES = [
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    caisse = models.ForeignKey(Caisse, on_delete=models.CASCADE, related_name='transactions')
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE, related_name='caisse_transactions')
    
    # Payment details
    items = models.ManyToManyField(PayableItem, related_name='transactions')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Status and metadata
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='completed')
    notes = models.TextField(blank=True, help_text="Additional notes or reasons for cancellation")
    
    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancelled_by = models.CharField(max_length=200, blank=True, help_text="Who cancelled this transaction")
    
    # Check-in tracking
    marked_present = models.BooleanField(default=True, help_text="Whether participant was marked as present")

    class Meta:
        verbose_name = "Caisse Transaction"
        verbose_name_plural = "Caisse Transactions"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['caisse', 'status', '-created_at']),
            models.Index(fields=['participant', '-created_at']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f"{self.participant.user.get_full_name()} - {self.total_amount} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"

    def cancel(self, cancelled_by=None, reason=""):
        """Cancel this transaction"""
        self.status = 'cancelled'
        self.cancelled_at = timezone.now()
        self.cancelled_by = cancelled_by or "Unknown"
        if reason:
            self.notes = f"Cancelled: {reason}\n{self.notes}" if self.notes else f"Cancelled: {reason}"
        self.save()

    def get_items_list(self):
        """Get comma-separated list of item names"""
        return ", ".join([item.name for item in self.items.all()])
