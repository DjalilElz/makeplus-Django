#!/usr/bin/env python
"""Check and update event data in database"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'makeplus_api.settings')
django.setup()

from events.models import Event
from django.utils import timezone
from datetime import datetime

print("=== CURRENT EVENT DATA ===\n")
events = Event.objects.all()
print(f"Total Events: {events.count()}\n")

for event in events:
    print(f"Event ID: {event.id}")
    print(f"  Name: {event.name}")
    print(f"  Start Date: {event.start_date}")
    print(f"  End Date: {event.end_date}")
    print(f"  Location: {event.location}")
    print(f"  Start Date ISO: {event.start_date.isoformat() if event.start_date else 'None'}")
    print(f"  End Date ISO: {event.end_date.isoformat() if event.end_date else 'None'}")
    print()

print("\n=== UPDATE EVENT DATA ===")
update = input("Do you want to update the event data? (yes/no): ").strip().lower()

if update == 'yes':
    event = Event.objects.first()
    if event:
        print(f"\nUpdating event: {event.name}")

        # Get new values
        new_name = input(f"New name (current: {event.name}, press Enter to keep): ").strip()
        new_start = input(f"New start date YYYY-MM-DD (current: {event.start_date.date()}, press Enter to keep): ").strip()
        new_end = input(f"New end date YYYY-MM-DD (current: {event.end_date.date()}, press Enter to keep): ").strip()
        new_location = input(f"New location (current: {event.location}, press Enter to keep): ").strip()

        # Update fields
        if new_name:
            event.name = new_name
        if new_start:
            event.start_date = timezone.make_aware(datetime.strptime(new_start, '%Y-%m-%d'))
        if new_end:
            event.end_date = timezone.make_aware(datetime.strptime(new_end, '%Y-%m-%d'))
        if new_location:
            event.location = new_location

        event.save()
        print("\n✓ Event updated successfully!")
        print(f"\nNew values:")
        print(f"  Name: {event.name}")
        print(f"  Start: {event.start_date}")
        print(f"  End: {event.end_date}")
        print(f"  Location: {event.location}")
    else:
        print("No events found!")
else:
    print("Skipping update.")
