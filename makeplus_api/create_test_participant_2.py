#!/usr/bin/env python
"""
Create Second Test Participant with Ateliers and Sessions
For testing the new user-level QR code system
"""

import os
import sys
import django
from datetime import datetime, timedelta

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'makeplus_api.settings')
django.setup()

from django.contrib.auth.models import User
from events.models import (
    Event, Participant, Session, Room, 
    UserEventAssignment, SessionAccess, RoomAccess,
    UserProfile
)
from decimal import Decimal

def create_test_participant():
    print("=" * 70)
    print("Creating Second Test Participant with Ateliers")
    print("=" * 70)
    
    # Get the event
    try:
        event = Event.objects.get(name__icontains="StartupWeek Oran")
        print(f"\n✅ Found Event: {event.name}")
        print(f"   Event ID: {event.id}")
    except Event.DoesNotExist:
        print("\n❌ Event 'StartupWeek Oran 2025' not found!")
        return
    
    # Create user
    email = "participant2.test@startupweek.dz"
    password = "makeplus2025"
    
    # Delete if exists
    User.objects.filter(email=email).delete()
    
    user = User.objects.create_user(
        username=email.split('@')[0],
        email=email,
        password=password,
        first_name="Leila",
        last_name="Mansouri"
    )
    print(f"\n✅ Created User:")
    print(f"   Email: {email}")
    print(f"   Password: {password}")
    print(f"   Name: {user.get_full_name()}")
    print(f"   User ID: {user.id}")
    
    # Generate user-level QR code
    qr_data = UserProfile.get_qr_for_user(user)
    print(f"\n✅ Generated User-Level QR Code:")
    print(f"   Badge ID: {qr_data.get('badge_id')}")
    print(f"   QR Data: {qr_data}")
    
    # Assign to event as participant
    assignment = UserEventAssignment.objects.create(
        user=user,
        event=event,
        role='participant',
        is_active=True
    )
    print(f"\n✅ Created Event Assignment:")
    print(f"   Role: {assignment.role}")
    print(f"   Event: {event.name}")
    
    # Create participant profile
    participant = Participant.objects.create(
        user=user,
        event=event,
        badge_id=qr_data.get('badge_id'),  # Use user-level badge ID
        qr_code_data=qr_data,  # Store user-level QR data
        is_checked_in=False
    )
    print(f"\n✅ Created Participant Profile:")
    print(f"   Badge ID: {participant.badge_id}")
    print(f"   Checked In: {participant.is_checked_in}")
    
    # Get some rooms
    rooms = list(Room.objects.filter(event=event)[:3])
    if rooms:
        print(f"\n✅ Available Rooms: {len(rooms)}")
        for room in rooms:
            print(f"   - {room.name}")
    
    # Get sessions (conferences and ateliers)
    print("\n" + "-" * 70)
    print("Assigning Sessions and Ateliers")
    print("-" * 70)
    
    # Assign 3 free conference sessions
    free_sessions = Session.objects.filter(
        event=event,
        is_paid=False,
        session_type='conference'
    )[:3]
    
    print(f"\n📅 Assigned {free_sessions.count()} Free Conference Sessions:")
    for session in free_sessions:
        # Create session access (free sessions automatically have access)
        SessionAccess.objects.create(
            participant=participant,
            session=session,
            has_access=True,
            payment_status='free'
        )
        print(f"   ✅ {session.title}")
        print(f"      Time: {session.start_time.strftime('%H:%M')} - {session.end_time.strftime('%H:%M')}")
        print(f"      Room: {session.room.name}")
    
    # Assign 5 paid ateliers with different payment statuses
    paid_sessions = Session.objects.filter(
        event=event,
        is_paid=True,
        session_type='atelier'
    )[:5]
    
    if paid_sessions.count() >= 5:
        paid_count = 0
        pending_count = 0
        total_paid = Decimal('0.00')
        total_pending = Decimal('0.00')
        
        print(f"\n💰 Assigned {paid_sessions.count()} Paid Ateliers:")
        
        for idx, session in enumerate(paid_sessions):
            # First 3 are paid, last 2 are pending
            if idx < 3:
                status = 'paid'
                has_access = True
                amount = session.price
                paid_count += 1
                total_paid += session.price
                icon = "✅"
            else:
                status = 'pending'
                has_access = False
                amount = Decimal('0.00')
                pending_count += 1
                total_pending += session.price
                icon = "⏳"
            
            SessionAccess.objects.create(
                participant=participant,
                session=session,
                has_access=has_access,
                payment_status=status,
                amount_paid=amount
            )
            
            print(f"   {icon} {session.title}")
            print(f"      Price: {session.price} DZD")
            print(f"      Status: {status.upper()}")
            print(f"      Access: {'Granted' if has_access else 'Denied (Payment Required)'}")
            print(f"      Time: {session.start_time.strftime('%H:%M')} - {session.end_time.strftime('%H:%M')}")
        
        print(f"\n💵 Payment Summary:")
        print(f"   Paid Ateliers: {paid_count}")
        print(f"   Pending Ateliers: {pending_count}")
        print(f"   Total Paid: {total_paid} DZD")
        print(f"   Total Pending: {total_pending} DZD")
        print(f"   Grand Total: {total_paid + total_pending} DZD")
    
    else:
        print(f"\n⚠️  Only {paid_sessions.count()} paid ateliers available (need 5)")
    
    # Create some room access history
    print("\n" + "-" * 70)
    print("Creating Room Access History")
    print("-" * 70)
    
    # Find a controller
    controller_assignment = UserEventAssignment.objects.filter(
        event=event,
        role='controlleur_des_badges',
        is_active=True
    ).first()
    
    controller = controller_assignment.user if controller_assignment else None
    
    if rooms and controller:
        print(f"\n🚪 Creating {min(4, len(rooms))} Room Access Records:")
        for i, room in enumerate(rooms[:4]):
            access = RoomAccess.objects.create(
                participant=participant,
                room=room,
                verified_by=controller,
                status='granted'
            )
            print(f"   ✅ {room.name}")
            print(f"      Verified by: {controller.get_full_name()}")
            print(f"      Time: {access.accessed_at.strftime('%Y-%m-%d %H:%M:%S')}")
    elif not rooms:
        print("\n⚠️  No rooms available for access history")
    elif not controller:
        print("\n⚠️  No controller found for access history")
    
    # Summary
    print("\n" + "=" * 70)
    print("✅ TEST PARTICIPANT CREATED SUCCESSFULLY")
    print("=" * 70)
    print(f"\n📧 Login Credentials:")
    print(f"   Email: {email}")
    print(f"   Password: {password}")
    print(f"\n🎫 Badge Information:")
    print(f"   Badge ID: {participant.badge_id}")
    print(f"   User ID: {user.id}")
    print(f"   QR Code Data: {qr_data}")
    print(f"\n📊 Profile Summary:")
    print(f"   Free Conferences: {free_sessions.count()}")
    print(f"   Paid Ateliers (Paid): {paid_count if paid_sessions.count() >= 5 else 0}")
    print(f"   Paid Ateliers (Pending): {pending_count if paid_sessions.count() >= 5 else 0}")
    print(f"   Room Access Records: {min(4, len(rooms)) if rooms and controller else 0}")
    print(f"\n🧪 API Testing Endpoints:")
    print(f"   POST /api/auth/login/")
    print(f"   GET  /api/auth/me/")
    print(f"   GET  /api/my-ateliers/")
    print(f"\n🔗 Event Context:")
    print(f"   Event: {event.name}")
    print(f"   Event ID: {event.id}")
    print(f"   Location: {event.location}")
    print(f"   Dates: {event.start_date.date()} to {event.end_date.date()}")
    print("\n" + "=" * 70)

if __name__ == '__main__':
    create_test_participant()
