#!/usr/bin/env python
"""Update event dates to match desired configuration"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'makeplus_api.settings')
django.setup()

from events.models import Event
from django.utils import timezone
from datetime import datetime

print("=== UPDATING EVENT DATA ===\n")

# Get the event
event = Event.objects.first()

if event:
    print(f"Current Event Data:")
    print(f"  Name: {event.name}")
    print(f"  Start: {event.start_date}")
    print(f"  End: {event.end_date}")
    print(f"  Location: {event.location}")

    # Update to desired values
    event.name = "MakePlus 2025"
    event.start_date = timezone.make_aware(datetime(2025, 11, 12, 0, 0, 0))
    event.end_date = timezone.make_aware(datetime(2025, 11, 14, 23, 59, 59))
    event.location = "Centre des Congrès, Alger"

    event.save()

    print(f"\n[OK] Event updated successfully!\n")
    print(f"New Event Data:")
    print(f"  Name: {event.name}")
    print(f"  Start: {event.start_date} ({event.start_date.isoformat()})")
    print(f"  End: {event.end_date} ({event.end_date.isoformat()})")
    print(f"  Location: {event.location}")
else:
    print("ERROR: No events found in database!")
