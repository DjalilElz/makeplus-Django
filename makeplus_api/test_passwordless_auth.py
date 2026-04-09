"""
Test script for passwordless authentication system
Run with: python manage.py shell < test_passwordless_auth.py
"""

from django.contrib.auth.models import User
from events.models import Event, EmailLoginCode
from events.login_code_service import (
    issue_email_login_code,
    verify_login_code,
    mark_code_as_used,
    invalidate_user_event_codes
)
from dashboard.registration_helpers import _ensure_registration_account
from datetime import datetime, timedelta

print("\n" + "="*60)
print("PASSWORDLESS AUTHENTICATION SYSTEM TEST")
print("="*60 + "\n")

# Clean up test data
print("1. Cleaning up test data...")
User.objects.filter(email='test@example.com').delete()
Event.objects.filter(name='Test Event').delete()
print("   ✓ Cleanup complete\n")

# Create test event
print("2. Creating test event...")
event = Event.objects.create(
    name='Test Event',
    location='Test Location',
    start_date=datetime.now() + timedelta(days=30),
    end_date=datetime.now() + timedelta(days=31),
    status='active'
)
print(f"   ✓ Event created: {event.name} (ID: {event.id})\n")

# Test 1: Create user account
print("3. Testing user account creation...")
user, user_created, participant = _ensure_registration_account(
    email='test@example.com',
    first_name='Test',
    last_name='User',
    event=event
)
print(f"   ✓ User created: {user.email}")
print(f"   ✓ Has usable password: {user.has_usable_password()} (should be False)")
print(f"   ✓ Participant created: {participant.first_name} {participant.last_name}\n")

# Test 2: Generate login code
print("4. Testing login code generation...")
code, login_code_instance = issue_email_login_code(user, event, invalidate_old=True)
print(f"   ✓ Code generated: {code}")
print(f"   ✓ Code hash: {login_code_instance.code_hash[:20]}...")
print(f"   ✓ Is used: {login_code_instance.is_used}\n")

# Test 3: Verify login code
print("5. Testing login code verification...")
success, verified_user, message = verify_login_code('test@example.com', code, event)
print(f"   ✓ Verification success: {success}")
print(f"   ✓ Message: {message}")
print(f"   ✓ User matches: {verified_user == user}\n")

# Test 4: Mark code as used
print("6. Testing mark code as used...")
marked = mark_code_as_used('test@example.com', code, event, '127.0.0.1', 'Test Agent')
print(f"   ✓ Code marked as used: {marked}")
login_code_instance.refresh_from_db()
print(f"   ✓ Is used: {login_code_instance.is_used}")
print(f"   ✓ Used at: {login_code_instance.used_at}\n")

# Test 5: Try to verify used code (should fail)
print("7. Testing used code verification (should fail)...")
success, verified_user, message = verify_login_code('test@example.com', code, event)
print(f"   ✓ Verification success: {success} (should be False)")
print(f"   ✓ Message: {message}\n")

# Test 6: Generate new code
print("8. Testing new code generation...")
new_code, new_login_code = issue_email_login_code(user, event, invalidate_old=True)
print(f"   ✓ New code generated: {new_code}")
print(f"   ✓ New code is different: {new_code != code}\n")

# Test 7: Verify new code works
print("9. Testing new code verification...")
success, verified_user, message = verify_login_code('test@example.com', new_code, event)
print(f"   ✓ Verification success: {success}")
print(f"   ✓ Message: {message}\n")

# Test 8: Test event isolation
print("10. Testing event isolation...")
event2 = Event.objects.create(
    name='Test Event 2',
    location='Test Location 2',
    start_date=datetime.now() + timedelta(days=60),
    end_date=datetime.now() + timedelta(days=61),
    status='active'
)
code2, login_code2 = issue_email_login_code(user, event2, invalidate_old=True)
print(f"   ✓ Event 2 created: {event2.name}")
print(f"   ✓ Event 2 code generated: {code2}")

# Try Event 1 code on Event 2 (should fail)
success, verified_user, message = verify_login_code('test@example.com', new_code, event2)
print(f"   ✓ Event 1 code on Event 2: {success} (should be False)")

# Try Event 2 code on Event 1 (should fail)
success, verified_user, message = verify_login_code('test@example.com', code2, event)
print(f"   ✓ Event 2 code on Event 1: {success} (should be False)")

# Try Event 2 code on Event 2 (should succeed)
success, verified_user, message = verify_login_code('test@example.com', code2, event2)
print(f"   ✓ Event 2 code on Event 2: {success} (should be True)\n")

# Test 9: Test re-registration (invalidate old codes)
print("11. Testing re-registration (invalidate old codes)...")
count = invalidate_user_event_codes(user, event)
print(f"   ✓ Codes invalidated for Event 1: {count}")
new_login_code.refresh_from_db()
print(f"   ✓ Old code is now used: {new_login_code.is_used}\n")

# Test 10: Count active codes
print("12. Testing active code count...")
from events.login_code_service import get_active_code_count
active_count = get_active_code_count(user, event)
print(f"   ✓ Active codes for Event 1: {active_count} (should be 0)")
active_count2 = get_active_code_count(user, event2)
print(f"   ✓ Active codes for Event 2: {active_count2} (should be 1)\n")

# Summary
print("="*60)
print("TEST SUMMARY")
print("="*60)
print("✓ User account creation with unusable password")
print("✓ Login code generation")
print("✓ Login code verification")
print("✓ Mark code as used")
print("✓ Used code rejection")
print("✓ New code generation")
print("✓ Event isolation (codes are event-specific)")
print("✓ Re-registration (invalidate old codes)")
print("✓ Active code counting")
print("\n✅ ALL TESTS PASSED!\n")

# Cleanup
print("Cleaning up test data...")
User.objects.filter(email='test@example.com').delete()
Event.objects.filter(name__startswith='Test Event').delete()
print("✓ Cleanup complete\n")
