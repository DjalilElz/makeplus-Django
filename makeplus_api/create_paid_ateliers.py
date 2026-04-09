"""
Create paid ateliers and assign them to test participant
"""

import os
import django

# Force USE_SUPABASE for production database
os.environ['USE_SUPABASE'] = 'true'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'makeplus_api.settings')
django.setup()

from django.contrib.auth.models import User
from events.models import Event, Session, Participant, SessionAccess, Room
from django.utils import timezone
from datetime import timedelta

print("🔧 Connecting to PRODUCTION database (Supabase)...")

try:
    # Get the event and participant
    event = Event.objects.get(name='StartupWeek Oran 2025')
    participant_user = User.objects.get(email='participant.test@startupweek.dz')
    participant = Participant.objects.get(user=participant_user, event=event)
    
    print(f"✅ Found participant: {participant_user.get_full_name()}")
    print(f"   Event: {event.name}")
    print(f"   Badge: {participant.badge_id}")
    
    # Get a room for the ateliers
    room = Room.objects.filter(event=event).first()
    
    if not room:
        print("❌ No rooms found in this event")
        exit(1)
    
    print(f"✅ Using room: {room.name}")
    
    # Create paid ateliers
    ateliers_data = [
        {
            'title': 'Atelier: Pitch Deck & Levée de Fonds',
            'description': 'Apprenez à créer un pitch deck convaincant et à lever des fonds pour votre startup. Atelier pratique avec retours personnalisés.',
            'speaker_name': 'Sarah Meziane',
            'speaker_title': 'Venture Capitalist',
            'theme': 'Financement',
            'price': 5000.00,  # 5000 DZD
            'duration_hours': 3
        },
        {
            'title': 'Atelier: Growth Hacking & Acquisition',
            'description': 'Stratégies de croissance rapide pour startups. Techniques d\'acquisition de clients et optimisation des conversions.',
            'speaker_name': 'Karim Belkacem',
            'speaker_title': 'Growth Marketing Expert',
            'theme': 'Marketing',
            'price': 4500.00,  # 4500 DZD
            'duration_hours': 2
        },
        {
            'title': 'Atelier: Legal & Juridique pour Startups',
            'description': 'Comprendre les aspects juridiques de la création d\'entreprise en Algérie. Statuts, contrats, propriété intellectuelle.',
            'speaker_name': 'Amina Khadri',
            'speaker_title': 'Avocate d\'Affaires',
            'theme': 'Juridique',
            'price': 3500.00,  # 3500 DZD
            'duration_hours': 2
        },
        {
            'title': 'Atelier: UX/UI Design Workshop',
            'description': 'Atelier pratique de design UX/UI. Créez des interfaces utilisateur attractives et fonctionnelles pour vos applications.',
            'speaker_name': 'Mehdi Raouf',
            'speaker_title': 'UX/UI Designer',
            'theme': 'Design',
            'price': 6000.00,  # 6000 DZD
            'duration_hours': 4
        }
    ]
    
    print(f"\n🎨 Creating {len(ateliers_data)} paid ateliers...")
    
    created_ateliers = []
    base_time = timezone.now() + timedelta(days=2)
    
    for i, atelier_data in enumerate(ateliers_data):
        # Calculate start and end times
        start_time = base_time + timedelta(hours=i * 4)
        end_time = start_time + timedelta(hours=atelier_data['duration_hours'])
        
        # Create the atelier session
        atelier, created = Session.objects.get_or_create(
            event=event,
            title=atelier_data['title'],
            defaults={
                'room': room,
                'description': atelier_data['description'],
                'start_time': start_time,
                'end_time': end_time,
                'speaker_name': atelier_data['speaker_name'],
                'speaker_title': atelier_data['speaker_title'],
                'theme': atelier_data['theme'],
                'session_type': 'atelier',
                'status': 'pas_encore',
                'is_paid': True,
                'price': atelier_data['price']
            }
        )
        
        if created:
            created_ateliers.append(atelier)
            print(f"\n  ✅ Created: {atelier.title}")
            print(f"     Speaker: {atelier.speaker_name}")
            print(f"     Price: {atelier.price} DZD")
            print(f"     Duration: {atelier_data['duration_hours']}h")
            print(f"     Date: {start_time.strftime('%Y-%m-%d %H:%M')}")
        else:
            created_ateliers.append(atelier)
            print(f"\n  ℹ️  Already exists: {atelier.title}")
    
    # Assign ateliers to participant (some paid, some pending)
    print(f"\n💰 Assigning ateliers to participant...")
    
    assigned_count = 0
    for i, atelier in enumerate(created_ateliers):
        # First 2 ateliers are paid, last 2 are pending payment
        if i < 2:
            payment_status = 'paid'
            has_access = True
            paid_at = timezone.now()
            amount_paid = atelier.price
        else:
            payment_status = 'pending'
            has_access = False
            paid_at = None
            amount_paid = 0
        
        access, created = SessionAccess.objects.get_or_create(
            session=atelier,
            participant=participant,
            defaults={
                'has_access': has_access,
                'payment_status': payment_status,
                'paid_at': paid_at,
                'amount_paid': amount_paid
            }
        )
        
        if created:
            assigned_count += 1
            status_icon = "✅" if payment_status == 'paid' else "⏳"
            status_text = "PAID - Access Granted" if payment_status == 'paid' else "PENDING - Awaiting Payment"
            print(f"  {status_icon} {atelier.title}")
            print(f"     Status: {status_text}")
            print(f"     Amount: {amount_paid if payment_status == 'paid' else atelier.price} DZD")
    
    print(f"\n✨ Assigned {assigned_count} new ateliers")
    
    # Show summary
    print(f"\n" + "="*70)
    print(f"✨ PAID ATELIERS SETUP COMPLETE!")
    print(f"="*70)
    
    print(f"\n🔑 Login Credentials:")
    print(f"   Email: participant.test@startupweek.dz")
    print(f"   Password: makeplus2025")
    print(f"   Event ID: {event.id}")
    
    print(f"\n📊 Participant's Ateliers Summary:")
    all_ateliers = SessionAccess.objects.filter(
        participant=participant,
        session__session_type='atelier'
    )
    
    paid_count = all_ateliers.filter(payment_status='paid').count()
    pending_count = all_ateliers.filter(payment_status='pending').count()
    total_paid = sum(a.amount_paid for a in all_ateliers.filter(payment_status='paid'))
    total_pending = sum(a.session.price for a in all_ateliers.filter(payment_status='pending'))
    
    print(f"   Total Ateliers: {all_ateliers.count()}")
    print(f"   ✅ Paid & Accessible: {paid_count} ({total_paid} DZD)")
    print(f"   ⏳ Pending Payment: {pending_count} ({total_pending} DZD)")
    
    print(f"\n📱 Test in Flutter App:")
    print(f"   The participant should see:")
    print(f"   - {paid_count} ateliers with 'PAID' badge and full access")
    print(f"   - {pending_count} ateliers with 'PENDING PAYMENT' and payment button")
    print(f"   - Total amount paid: {total_paid} DZD")
    print(f"   - Total amount pending: {total_pending} DZD")
    
    print(f"\n📡 API Endpoints:")
    print(f"   GET /api/session-access/ - List all participant's sessions")
    print(f"   GET /api/sessions/?session_type=atelier - List all ateliers")
    
    print(f"\n🌐 Production URL:")
    print(f"   https://makeplus-django-5.onrender.com")
    
    print(f"\n" + "="*70)
    
except Event.DoesNotExist:
    print("❌ Event not found")
except User.DoesNotExist:
    print("❌ Participant user not found. Please run setup_participant_test.py first")
except Participant.DoesNotExist:
    print("❌ Participant profile not found. Please run setup_participant_test.py first")
except Exception as e:
    print(f"❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()
