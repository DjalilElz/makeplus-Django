#!/usr/bin/env python
"""Debug script to check transaction and item relationships"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'makeplus_api'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'makeplus_api.settings')
django.setup()

from caisse.models import CaisseTransaction, PayableItem
from events.models import Participant

print("=== Testing Transaction Query ===\n")

# Get recent transactions
transactions = CaisseTransaction.objects.filter(status='completed').order_by('-created_at')[:5]

if not transactions:
    print("❌ No completed transactions found in database")
else:
    print(f"✅ Found {transactions.count()} completed transactions\n")
    
    for tx in transactions:
        print(f"Transaction ID: {tx.id}")
        print(f"Participant: {tx.participant.user.email}")
        print(f"Total Amount: {tx.total_amount}")
        print(f"Created: {tx.created_at}")
        print(f"Items count: {tx.items.count()}")
        
        items = tx.items.all()
        if items:
            print("Items:")
            for item in items:
                print(f"  - {item.name} ({item.item_type}) - {item.price} DA")
        else:
            print("  ⚠️ No items linked to this transaction!")
        
        print("-" * 50)

# Test the scan_participant logic
print("\n=== Testing Scan Logic ===\n")

participant = Participant.objects.first()
if participant:
    print(f"Testing with participant: {participant.user.email}")
    
    completed_txs = CaisseTransaction.objects.filter(
        participant=participant,
        status='completed'
    ).prefetch_related('items__session')
    
    print(f"Completed transactions for this participant: {completed_txs.count()}")
    
    paid_items_list = []
    for transaction in completed_txs:
        print(f"\nTransaction {transaction.id}:")
        print(f"  Items in transaction: {transaction.items.count()}")
        
        for item in transaction.items.all():
            print(f"    - {item.name} ({item.item_type})")
            paid_items_list.append({
                'type': item.item_type,
                'title': item.name,
                'amount_paid': float(item.price),
            })
    
    print(f"\n✅ Total paid items found: {len(paid_items_list)}")
    for item in paid_items_list:
        print(f"  - {item['title']} ({item['type']}) - {item['amount_paid']} DA")
else:
    print("❌ No participants found")
