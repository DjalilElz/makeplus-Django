"""
Verification Models for Sign Up and Form Registration
"""

from django.db import models
from django.utils import timezone
from datetime import timedelta
import hashlib
import secrets


class SignUpVerification(models.Model):
    """
    Email verification codes for user sign up
    Expires after 3 minutes
    """
    email = models.EmailField(db_index=True)
    code_hash = models.CharField(max_length=64, db_index=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    expires_at = models.DateTimeField(db_index=True)
    
    # Status
    is_used = models.BooleanField(default=False, db_index=True)
    used_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Sign Up Verification'
        verbose_name_plural = 'Sign Up Verifications'
        indexes = [
            models.Index(fields=['email', 'is_used', '-created_at']),
            models.Index(fields=['code_hash', 'is_used']),
            models.Index(fields=['expires_at', 'is_used']),
        ]
    
    def __str__(self):
        return f"{self.email} - {'Used' if self.is_used else 'Active'}"
    
    @staticmethod
    def hash_code(code):
        """Hash a 6-digit code for secure storage"""
        return hashlib.sha256(code.encode()).hexdigest()
    
    @staticmethod
    def generate_code():
        """Generate a random 6-digit code"""
        return ''.join([str(secrets.randbelow(10)) for _ in range(6)])
    
    def is_expired(self):
        """Check if code has expired"""
        return timezone.now() > self.expires_at
    
    def verify_code(self, code):
        """Verify if provided code matches and is valid"""
        if self.is_used:
            return False, "Code already used"
        if self.is_expired():
            return False, "Code expired"
        if self.code_hash != self.hash_code(code):
            return False, "Invalid code"
        return True, "Code verified"
    
    def mark_as_used(self, ip_address=None, user_agent=''):
        """Mark code as used"""
        self.is_used = True
        self.used_at = timezone.now()
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.save(update_fields=['is_used', 'used_at', 'ip_address', 'user_agent'])
    
    @classmethod
    def create_verification(cls, email, ip_address=None, user_agent=''):
        """Create a new verification code"""
        code = cls.generate_code()
        expires_at = timezone.now() + timedelta(minutes=3)
        
        verification = cls.objects.create(
            email=email,
            code_hash=cls.hash_code(code),
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return code, verification
    
    @classmethod
    def can_resend(cls, email):
        """Check if user can request a new code (3 minutes since last request)"""
        last_code = cls.objects.filter(email=email).order_by('-created_at').first()
        if not last_code:
            return True, None
        
        time_since_last = timezone.now() - last_code.created_at
        if time_since_last < timedelta(minutes=3):
            wait_seconds = int((timedelta(minutes=3) - time_since_last).total_seconds())
            return False, wait_seconds
        
        return True, None


class FormRegistrationVerification(models.Model):
    """
    Verification codes for event registration form validation
    Expires after 3 minutes
    """
    email = models.EmailField(db_index=True)
    form = models.ForeignKey('dashboard.FormConfiguration', on_delete=models.CASCADE, related_name='verifications')
    code_hash = models.CharField(max_length=64, db_index=True)
    
    # Form submission data (stored temporarily until verified)
    form_data = models.JSONField(default=dict)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    expires_at = models.DateTimeField(db_index=True)
    
    # Status
    is_used = models.BooleanField(default=False, db_index=True)
    used_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Form Registration Verification'
        verbose_name_plural = 'Form Registration Verifications'
        indexes = [
            models.Index(fields=['email', 'form', 'is_used', '-created_at']),
            models.Index(fields=['code_hash', 'is_used']),
            models.Index(fields=['expires_at', 'is_used']),
        ]
    
    def __str__(self):
        return f"{self.email} - {self.form.name} - {'Used' if self.is_used else 'Active'}"
    
    @staticmethod
    def hash_code(code):
        """Hash a 6-digit code for secure storage"""
        return hashlib.sha256(code.encode()).hexdigest()
    
    @staticmethod
    def generate_code():
        """Generate a random 6-digit code"""
        return ''.join([str(secrets.randbelow(10)) for _ in range(6)])
    
    def is_expired(self):
        """Check if code has expired"""
        return timezone.now() > self.expires_at
    
    def verify_code(self, code):
        """Verify if provided code matches and is valid"""
        if self.is_used:
            return False, "Code already used"
        if self.is_expired():
            return False, "Code expired"
        if self.code_hash != self.hash_code(code):
            return False, "Invalid code"
        return True, "Code verified"
    
    def mark_as_used(self, ip_address=None, user_agent=''):
        """Mark code as used"""
        self.is_used = True
        self.used_at = timezone.now()
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.save(update_fields=['is_used', 'used_at', 'ip_address', 'user_agent'])
    
    @classmethod
    def create_verification(cls, email, form, form_data, ip_address=None, user_agent=''):
        """Create a new verification code"""
        code = cls.generate_code()
        expires_at = timezone.now() + timedelta(minutes=3)
        
        verification = cls.objects.create(
            email=email,
            form=form,
            code_hash=cls.hash_code(code),
            form_data=form_data,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return code, verification
    
    @classmethod
    def can_resend(cls, email, form):
        """Check if user can request a new code (3 minutes since last request)"""
        last_code = cls.objects.filter(
            email=email,
            form=form
        ).order_by('-created_at').first()
        
        if not last_code:
            return True, None
        
        time_since_last = timezone.now() - last_code.created_at
        if time_since_last < timedelta(minutes=3):
            wait_seconds = int((timedelta(minutes=3) - time_since_last).total_seconds())
            return False, wait_seconds
        
        return True, None
