#!/usr/bin/env python
"""Check which database is connected and list users"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'makeplus_api.settings')
django.setup()

from django.db import connection
from django.contrib.auth.models import User

print("=" * 60)
print("DATABASE CONNECTION INFO")
print("=" * 60)
print(f"Host: {connection.settings_dict['HOST']}")
print(f"User: {connection.settings_dict['USER']}")
print(f"Database: {connection.settings_dict['NAME']}")
print(f"Port: {connection.settings_dict['PORT']}")
print()

print("=" * 60)
print("USERS IN THIS DATABASE")
print("=" * 60)
users = User.objects.all()
print(f"Total users: {users.count()}")
print()

for u in users:
    print(f"  Username: {u.username}")
    print(f"  Email: {u.email}")
    print(f"  Staff: {u.is_staff} | Superuser: {u.is_superuser}")
    print(f"  Date joined: {u.date_joined}")
    print("-" * 40)
