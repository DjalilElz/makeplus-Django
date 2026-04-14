#!/usr/bin/env python
"""
Script to create a user in production database
Run this on your production server or with production database connection
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'makeplus_api.settings')
django.setup()

from django.contrib.auth.models import User

# User details - CHANGE THESE AS NEEDED
email = input("Enter email: ").strip()
password = input("Enter password: ").strip()
first_name = input("Enter first name: ").strip()
last_name = input("Enter last name: ").strip()

# Check if user exists
try:
    user = User.objects.get(email=email)
    print(f"\n✓ User already exists:")
    print(f"  - Username: {user.username}")
    print(f"  - Email: {user.email}")
    print(f"  - Active: {user.is_active}")
    print(f"  - First Name: {user.first_name}")
    print(f"  - Last Name: {user.last_name}")
    
    # Update password if needed
    update = input("\nUpdate password? (y/n): ").strip().lower()
    if update == 'y':
        user.set_password(password)
        user.save()
        print("✓ Password updated!")
        
except User.DoesNotExist:
    print(f"\nCreating user with email '{email}'...")
    user = User.objects.create_user(
        username=email,  # Use email as username
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
        is_active=True
    )
    print(f"✓ User created successfully!")
    print(f"  - Username: {user.username}")
    print(f"  - Email: {user.email}")
    print(f"  - Active: {user.is_active}")

print("\n✓ Done! You can now login with:")
print(f"  Email: {email}")
print(f"  Password: {password}")
