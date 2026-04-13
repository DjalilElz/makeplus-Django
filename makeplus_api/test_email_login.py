#!/usr/bin/env python
"""
Test script to verify email-based login
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'makeplus_api.settings')
django.setup()

from django.contrib.auth.models import User

# Check if user exists
email = 'controller1@wemakeplus.com'
try:
    user = User.objects.get(email=email)
    print(f"✓ User found:")
    print(f"  - Username: {user.username}")
    print(f"  - Email: {user.email}")
    print(f"  - Active: {user.is_active}")
    print(f"  - Staff: {user.is_staff}")
    print(f"  - First Name: {user.first_name}")
    print(f"  - Last Name: {user.last_name}")
    
    # Check password
    if user.check_password('test123'):
        print(f"  - Password 'test123': ✓ CORRECT")
    else:
        print(f"  - Password 'test123': ✗ INCORRECT")
        print(f"  - Setting password to 'test123'...")
        user.set_password('test123')
        user.save()
        print(f"  - Password updated!")
        
except User.DoesNotExist:
    print(f"✗ User with email '{email}' NOT FOUND")
    print(f"\nCreating user...")
    user = User.objects.create_user(
        username=email,
        email=email,
        password='test123',
        first_name='Controller',
        last_name='One',
        is_active=True
    )
    print(f"✓ User created successfully!")
