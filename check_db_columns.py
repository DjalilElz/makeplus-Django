"""
Quick script to check database columns for final submission table
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'makeplus_api.settings')
django.setup()

from django.db import connection

with connection.cursor() as cursor:
    cursor.execute("""
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns
        WHERE table_name = 'dashboard_eposterfinalsubmission'
        ORDER BY ordinal_position;
    """)
    
    print("\nColumns in dashboard_eposterfinalsubmission table:")
    print("-" * 80)
    for row in cursor.fetchall():
        print(f"{row[0]:30} | {row[1]:20} | NULL: {row[2]:3} | Default: {row[3]}")
