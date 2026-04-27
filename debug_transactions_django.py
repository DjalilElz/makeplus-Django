#!/usr/bin/env python
"""Debug transactions using Django ORM connected to Supabase"""

import os
import sys
import django

# Setup Django with Supabase settings
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'makeplus_api'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'makeplus_api.settings')

# Override database settings to use Supabase
os.environ['DB_ENGINE'] = 'django.db.backends.postgresql'
os.environ['DB_NAME'] = 'postgres'
os.environ['DB_USER'] = 'postgres'
os.environ['DB_PASSWORD'] = 'Djalilsalima23'
os.environ['DB_HOST'] = 'db.zrxlxmaagygvqsokbwyf.supabase.co'
os.environ['DB_PORT'] = '5432'

django.setup()

from caisse.models import CaisseTransaction, PayableItem
from events.models import Participant
from django.contrib.auth.models import User
from django.db import connection

print("=== Connecting to Supabase Database ===\n")

try:
    # Test connection
    with connection.cursor() as cursor:
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"✅ Connected to PostgreSQL: {version[0][:50]}...\n")
except Exception as e:
    print(f"❌ Connection failed: {e}\n")
    sys.exit(1)

print("=== Recent Transactions ===\n")

# Get recent transactions
transactions = CaisseTransaction.objects.filter(
    status='completed'
).select_related('participant__user').prefetch_related('items').order_by('-created_at')[:10]

if not transactions:
    print("❌ No completed transactions found")
else:
    print(f"✅ Found {transactions.count()} completed transactions\n")
    
    for tx in transactions:
        print(f"Transaction ID: {tx.id}")
        print(f"Participant: {tx.participant.user.get_full_name()} ({tx.participant.user.email})")
        print(f"Status: {tx.status}")
        print(f"Amount: {tx.total_amount} DA")
        print(f"Created: {tx.created_at}")
        
        items = tx.items.all()
        print(f"Items count: {items.count()}")
        
        if items:
            print("Items:")
            for item in items:
                session_info = f" (Session: {item.session.title})" if item.session else ""
                print(f"  - {item.name} ({item.item_type}) - {item.price} DA{session_info}")
        else:
            print("  ⚠️ NO ITEMS LINKED TO THIS TRANSACTION!")
        
        print("-" * 70)

# Check for orphaned transactions
print("\n=== Checking for Orphaned Transactions ===\n")

orphaned = CaisseTransaction.objects.filter(
    status='completed',
    items__isnull=True
).select_related('participant__user').order_by('-created_at')[:5]

if orphaned.exists():
    print(f"⚠️ Found {orphaned.count()} transactions with NO items:")
    for tx in orphaned:
        print(f"  - Transaction {tx.id}: {tx.participant.user.email} - {tx.total_amount} DA (Created: {tx.created_at})")
else:
    print("✅ No orphaned transactions found")

# Test a specific participant if provided
print("\n=== Test Specific Participant ===\n")
print("Enter participant email to debug (or press Enter to skip):")
email = input().strip()

if email:
    try:
        user = User.objects.get(email=email)
        participant = Participant.objects.get(user=user)
        
        print(f"\nParticipant: {user.get_full_name()} ({user.email})")
        print(f"Participant ID: {participant.id}")
        
        # Get all transactions
        all_txs = CaisseTransaction.objects.filter(
            participant=participant
        ).prefetch_related('items').order_by('-created_at')
        
        print(f"Total transactions: {all_txs.count()}")
        print(f"Completed transactions: {all_txs.filter(status='completed').count()}")
        
        print("\nAll transactions:")
        for tx in all_txs:
            items_count = tx.items.count()
            print(f"  - TX {tx.id}: {tx.status}, {tx.total_amount} DA, {items_count} items, {tx.created_at}")
            
            if items_count > 0:
                for item in tx.items.all():
                    print(f"      • {item.name} ({item.item_type}) - {item.price} DA")
        
    except User.DoesNotExist:
        print(f"❌ User with email '{email}' not found")
    except Participant.DoesNotExist:
        print(f"❌ Participant profile not found for user '{email}'")
    except Exception as e:
        print(f"❌ Error: {e}")

print("\n✅ Debug complete")
