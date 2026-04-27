#!/usr/bin/env python
"""Connect to Supabase and debug transaction issues"""

import psycopg2
from psycopg2.extras import RealDictCursor

# Supabase connection details
DB_CONFIG = {
    'dbname': 'postgres',
    'user': 'postgres',
    'password': 'Djalilsalima23',
    'host': 'db.zrxlxmaagygvqsokbwyf.supabase.co',
    'port': 5432
}

def connect_db():
    """Connect to Supabase PostgreSQL"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print("✅ Connected to Supabase database")
        return conn
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return None

def check_transactions():
    """Check recent transactions and their items"""
    conn = connect_db()
    if not conn:
        return
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get recent transactions
        print("\n=== Recent Transactions ===\n")
        cursor.execute("""
            SELECT 
                ct.id,
                ct.status,
                ct.total_amount,
                ct.created_at,
                u.email as participant_email,
                u.first_name,
                u.last_name
            FROM caisse_caissetransaction ct
            JOIN events_participant p ON ct.participant_id = p.id
            JOIN auth_user u ON p.user_id = u.id
            ORDER BY ct.created_at DESC
            LIMIT 10
        """)
        
        transactions = cursor.fetchall()
        
        if not transactions:
            print("❌ No transactions found")
            return
        
        print(f"✅ Found {len(transactions)} recent transactions\n")
        
        for tx in transactions:
            print(f"Transaction ID: {tx['id']}")
            print(f"Participant: {tx['first_name']} {tx['last_name']} ({tx['participant_email']})")
            print(f"Status: {tx['status']}")
            print(f"Amount: {tx['total_amount']} DA")
            print(f"Created: {tx['created_at']}")
            
            # Get items for this transaction
            cursor.execute("""
                SELECT 
                    pi.id,
                    pi.name,
                    pi.item_type,
                    pi.price,
                    s.title as session_title
                FROM caisse_caissetransaction_items cti
                JOIN caisse_payableitem pi ON cti.payableitem_id = pi.id
                LEFT JOIN events_session s ON pi.session_id = s.id
                WHERE cti.caissetransaction_id = %s
            """, (tx['id'],))
            
            items = cursor.fetchall()
            
            if items:
                print(f"Items ({len(items)}):")
                for item in items:
                    session_info = f" (Session: {item['session_title']})" if item['session_title'] else ""
                    print(f"  - {item['name']} ({item['item_type']}) - {item['price']} DA{session_info}")
            else:
                print("  ⚠️ NO ITEMS LINKED TO THIS TRANSACTION!")
            
            print("-" * 70)
        
        # Check for orphaned transactions (transactions with no items)
        print("\n=== Checking for Orphaned Transactions ===\n")
        cursor.execute("""
            SELECT 
                ct.id,
                ct.status,
                ct.total_amount,
                ct.created_at,
                u.email
            FROM caisse_caissetransaction ct
            JOIN events_participant p ON ct.participant_id = p.id
            JOIN auth_user u ON p.user_id = u.id
            LEFT JOIN caisse_caissetransaction_items cti ON ct.id = cti.caissetransaction_id
            WHERE cti.id IS NULL
            AND ct.status = 'completed'
            ORDER BY ct.created_at DESC
            LIMIT 5
        """)
        
        orphaned = cursor.fetchall()
        
        if orphaned:
            print(f"⚠️ Found {len(orphaned)} transactions with NO items:")
            for tx in orphaned:
                print(f"  - Transaction {tx['id']}: {tx['email']} - {tx['total_amount']} DA (Created: {tx['created_at']})")
        else:
            print("✅ No orphaned transactions found")
        
        cursor.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        conn.close()
        print("\n✅ Connection closed")

if __name__ == "__main__":
    check_transactions()
