#!/usr/bin/env python
"""Test dashboard login authentication"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'makeplus_api.settings')
django.setup()

from django.contrib.auth import authenticate
from django.contrib.auth.models import User

print("=" * 60)
print("TESTING LOGIN AUTHENTICATION")
print("=" * 60)

# Get admin user
try:
    admin = User.objects.get(username='admin')
    print(f"✓ User found: {admin.username}")
    print(f"  Email: {admin.email}")
    print(f"  Is Staff: {admin.is_staff}")
    print(f"  Is Superuser: {admin.is_superuser}")
    print(f"  Is Active: {admin.is_active}")
    print()
    
    # Test authentication
    print("Testing authentication with username='admin', password='admin123'...")
    user = authenticate(username='admin', password='admin123')
    
    if user is not None:
        print("✓ authenticate() returned user object")
        print(f"  Authenticated user: {user.username}")
        print(f"  Is staff: {user.is_staff}")
        print(f"  Is superuser: {user.is_superuser}")
        print()
        
        # Check dashboard access requirements
        if user.is_staff or user.is_superuser:
            print("✓ User has dashboard access (is_staff or is_superuser)")
        else:
            print("✗ User DOES NOT have dashboard access!")
            print("  User must be staff or superuser")
    else:
        print("✗ authenticate() returned None - AUTHENTICATION FAILED!")
        print()
        print("Debugging info:")
        print(f"  Password set: {bool(admin.password)}")
        print(f"  Password hash: {admin.password[:50]}...")
        
except User.DoesNotExist:
    print("✗ Admin user not found!")

print("=" * 60)
