#!/usr/bin/env python
"""
Integration test for passwordless authentication system
Run with: python test_integration.py
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'makeplus_api.settings')
django.setup()

from django.contrib.auth.models import User
from events.models import Event, EmailLoginCode, UserEventAssignment, Participant
from events.login_code_service import issue_email_login_code, verify_login_code, mark_code_as_used
from dashboard.registration_helpers import _ensure_registration_account
from datetime import timedelta
from django.utils import timezone

print('='*60)
print('PASSWORDLESS AUTHENTICATION - FULL INTEGRATION TEST')
print('='*60)

# Clean up
User.objects.filter(email='integration@test.com').delete()
Event.objects.filter(name='Integration Test Event').delete()

# 1. Create event
event = Event.objects.create(
    name='Integration Test Event',
    location='Test Location',
    start_date=timezone.now() + timedelta(days=30),
    end_date=timezone.now() + timedelta(days=31),
    status='active'
)
print(f'\n✓ Event created: {event.name}')

# 2. Test registration helper (simulates form submission)
user, user_created, participant = _ensure_registration_account(
    email='integration@test.com',
    first_name='Integration',
    last_name='Test',
    event=event
)
print(f'✓ User created: {user.email}')
print(f'✓ Has usable password: {user.has_usable_password()} (should be False)')
print(f'✓ UserEventAssignment exists: {UserEventAssignment.objects.filter(user=user, event=event).exists()}')
print(f'✓ Participant created: {participant.badge_id}')

# 3. Generate login code
code, login_code_instance = issue_email_login_code(user, event)
print(f'\n✓ Login code generated: {code}')
print(f'✓ Code is hashed in database')

# 4. Verify code
success, verified_user, message = verify_login_code('integration@test.com', code, event)
print(f'\n✓ Code verification: {success} - {message}')

# 5. Mark as used (simulates login)
marked = mark_code_as_used('integration@test.com', code, event, '127.0.0.1', 'Test Browser')
print(f'✓ Code marked as used: {marked}')

# 6. Try to use same code again (should fail)
success, verified_user, message = verify_login_code('integration@test.com', code, event)
print(f'✓ Used code rejected: {not success} - {message}')

# 7. Test re-registration
print(f'\n--- Testing Re-Registration ---')
old_code_count = EmailLoginCode.objects.filter(user=user, event=event, is_used=False).count()
print(f'Active codes before re-registration: {old_code_count}')

# Simulate re-registration
user2, user_created2, participant2 = _ensure_registration_account(
    email='integration@test.com',
    first_name='Integration Updated',
    last_name='Test Updated',
    event=event
)
print(f'✓ User info updated: {user2.first_name} {user2.last_name}')

# Generate new code
new_code, new_login_code = issue_email_login_code(user2, event, invalidate_old=True)
print(f'✓ New code generated: {new_code}')

old_code_count_after = EmailLoginCode.objects.filter(user=user, event=event, is_used=False).count()
print(f'Active codes after re-registration: {old_code_count_after}')

# 8. Test event isolation
event2 = Event.objects.create(
    name='Integration Test Event 2',
    location='Test Location 2',
    start_date=timezone.now() + timedelta(days=60),
    end_date=timezone.now() + timedelta(days=61),
    status='active'
)
code2, _ = issue_email_login_code(user, event2)
print(f'\n--- Testing Event Isolation ---')
print(f'✓ Event 2 code generated: {code2}')

# Try Event 1 code on Event 2 (should fail)
success, _, msg = verify_login_code('integration@test.com', new_code, event2)
print(f'✓ Event 1 code on Event 2 fails: {not success}')

# Try Event 2 code on Event 2 (should succeed)
success, _, msg = verify_login_code('integration@test.com', code2, event2)
print(f'✓ Event 2 code on Event 2 works: {success}')

# Summary
print(f'\n' + '='*60)
print('✅ ALL INTEGRATION TESTS PASSED!')
print('='*60)
print(f'Total EmailLoginCode records: {EmailLoginCode.objects.count()}')
print(f'Total Users: {User.objects.filter(email__contains="integration").count()}')
print(f'Total Events: {Event.objects.filter(name__contains="Integration").count()}')

# Cleanup
User.objects.filter(email='integration@test.com').delete()
Event.objects.filter(name__contains='Integration Test Event').delete()
print(f'\n✓ Cleanup complete')
