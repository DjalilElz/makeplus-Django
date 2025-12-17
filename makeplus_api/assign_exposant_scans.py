"""
Assign scanned participants to exposant: yacine.belkacem@innovtech.dz
"""
import os
import django
import sys

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'makeplus_api.settings')
django.setup()

from django.contrib.auth.models import User
from events.models import (
    Event, Participant, ExposantScan, UserEventAssignment
)
from datetime import datetime, timedelta
from django.utils import timezone
import random

def assign_exposant_scans():
    """Assign scanned participants to exposant for testing"""
    
    print("=" * 80)
    print("Assigning Scanned Participants to Exposant")
    print("=" * 80)
    
    # Get the exposant user
    exposant_email = "yacine.belkacem@innovtech.dz"
    try:
        exposant_user = User.objects.get(email=exposant_email)
        print(f"\n✓ Found exposant user: {exposant_user.get_full_name()} ({exposant_email})")
    except User.DoesNotExist:
        print(f"\n❌ Exposant user not found: {exposant_email}")
        return
    
    # Get the exposant's participant profiles
    exposant_participants = Participant.objects.filter(user=exposant_user).select_related('event')
    
    if not exposant_participants.exists():
        print("\n❌ No participant profiles found for this exposant")
        return
    
    print(f"\n✓ Found {exposant_participants.count()} event(s) for exposant")
    
    total_scans_created = 0
    
    # For each event the exposant is assigned to
    for exposant_participant in exposant_participants:
        event = exposant_participant.event
        print(f"\n" + "=" * 80)
        print(f"Processing Event: {event.name}")
        print("=" * 80)
        
        # Get all participants from the same event (excluding the exposant themselves)
        event_participants = Participant.objects.filter(
            event=event
        ).exclude(
            id=exposant_participant.id
        ).select_related('user')
        
        if not event_participants.exists():
            print(f"  ⚠️  No other participants found in this event")
            continue
        
        print(f"\n  ✓ Found {event_participants.count()} participants in event")
        
        # Delete existing scans for this exposant (for clean testing)
        existing_scans = ExposantScan.objects.filter(exposant=exposant_participant)
        if existing_scans.exists():
            count = existing_scans.count()
            existing_scans.delete()
            print(f"\n  🗑️  Deleted {count} existing scans for fresh testing")
        
        # Select random participants to scan (between 5 and min(15, total participants))
        num_scans = min(random.randint(5, 15), event_participants.count())
        participants_to_scan = random.sample(list(event_participants), num_scans)
        
        print(f"\n  📱 Creating {num_scans} booth visit scans...")
        
        # Sample notes for variety
        sample_notes = [
            "Intéressé par nos produits",
            "Demande de suivi commercial",
            "A pris une brochure",
            "Veut une démo du produit",
            "Discuté des partenariats",
            "Potentiel client B2B",
            "Demande de devis",
            "Intéressé par l'innovation",
            "A laissé ses coordonnées",
            "Rendez-vous à planifier",
            "",  # Some without notes
            "",
            ""
        ]
        
        # Create scans with realistic timestamps (spread over last 3 days)
        base_time = timezone.now() - timedelta(days=3)
        
        scans_created = []
        for i, participant in enumerate(participants_to_scan):
            # Random time within the last 3 days
            random_offset = random.randint(0, 3 * 24 * 60)  # Random minutes in 3 days
            scan_time = base_time + timedelta(minutes=random_offset)
            
            # Create the scan
            scan = ExposantScan.objects.create(
                exposant=exposant_participant,
                scanned_participant=participant,
                event=event,
                notes=random.choice(sample_notes)
            )
            
            # Manually set the created time for more realistic data
            scan.scanned_at = scan_time
            scan.save(update_fields=['scanned_at'])
            
            scans_created.append(scan)
            total_scans_created += 1
            
            print(f"    ✓ Scan #{i+1}: {participant.user.get_full_name() or participant.user.username}")
            print(f"      Email: {participant.user.email}")
            print(f"      Badge: {participant.badge_id}")
            print(f"      Time: {scan_time.strftime('%Y-%m-%d %H:%M')}")
            if scan.notes:
                print(f"      Note: {scan.notes}")
        
        # Show statistics
        today = timezone.now().date()
        today_scans = [s for s in scans_created if s.scanned_at.date() == today]
        
        print(f"\n  📊 Statistics for {event.name}:")
        print(f"    Total Scans: {len(scans_created)}")
        print(f"    Today's Scans: {len(today_scans)}")
        print(f"    First Scan: {min(s.scanned_at for s in scans_created).strftime('%Y-%m-%d %H:%M')}")
        print(f"    Last Scan: {max(s.scanned_at for s in scans_created).strftime('%Y-%m-%d %H:%M')}")
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"\n👤 Exposant: {exposant_user.get_full_name()} ({exposant_email})")
    print(f"📊 Total Scans Created: {total_scans_created}")
    print(f"🎯 Events Processed: {exposant_participants.count()}")
    
    print("\n" + "=" * 80)
    print("✅ Exposant Scans Assigned Successfully!")
    print("=" * 80)
    
    print("\n📝 Next Steps:")
    print("  1. Login with: yacine.belkacem@innovtech.dz / makeplus2025")
    print("  2. Navigate to exposant dashboard")
    print("  3. View booth visit statistics")
    print("  4. Test 'Export to Excel' button")
    print("  5. Check GET /api/exposant-scans/my_scans/?event_id={event_id}")
    print("  6. Test GET /api/exposant-scans/export_excel/")
    print("\n")

if __name__ == '__main__':
    assign_exposant_scans()
