#!/usr/bin/env python
"""Reset admin password"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'makeplus_api.settings')
django.setup()

from django.contrib.auth.models import User

# Get or create admin user
try:
    admin = User.objects.get(username='admin')
    print(f"Found existing admin user: {admin.username}")
except User.DoesNotExist:
    admin = User.objects.create_superuser(
        username='admin',
        email='admin@makeplus.com',
        password='admin123'
    )
    print("Created new admin user")

# Set password (using set_password for proper hashing)
admin.set_password('admin123')
admin.is_staff = True
admin.is_superuser = True
admin.save()

print("=" * 60)
print("✓ Admin user updated successfully!")
print("=" * 60)
print(f"Username: admin")
print(f"Password: admin123")
print(f"Email: {admin.email}")
print(f"Is Staff: {admin.is_staff}")
print(f"Is Superuser: {admin.is_superuser}")
print("=" * 60)

# Test authentication
from django.contrib.auth import authenticate
user = authenticate(username='admin', password='admin123')
if user:
    print("✓ Password authentication SUCCESSFUL!")
else:
    print("✗ Password authentication FAILED!")
