import os
import sys

print("=" * 70)
print("SUPABASE CONNECTION DIAGNOSTIC TEST")
print("=" * 70)
print()

# Test 1: Check .env file
print("📁 Test 1: Checking .env file...")
try:
    from decouple import config
    
    db_host = config('SUPABASE_DB_HOST')
    db_port = config('SUPABASE_DB_PORT')
    db_user = config('SUPABASE_DB_USER')
    db_name = config('SUPABASE_DB_NAME')
    
    print(f"✅ .env file loaded successfully")
    print(f"   Host: {db_host}")
    print(f"   Port: {db_port}")
    print(f"   User: {db_user}")
    print(f"   Database: {db_name}")
    print()
except Exception as e:
    print(f"❌ Error loading .env: {e}")
    sys.exit(1)

# Test 2: Check psycopg2
print("📦 Test 2: Checking psycopg2...")
try:
    import psycopg2
    print(f"✅ psycopg2 version: {psycopg2.__version__}")
    print()
except ImportError as e:
    print(f"❌ psycopg2 not installed: {e}")
    print("   Run: pip install psycopg2-binary")
    sys.exit(1)

# Test 3: Test raw connection
print("🔌 Test 3: Testing raw database connection...")
try:
    conn = psycopg2.connect(
        dbname=db_name,
        user=db_user,
        password=config('SUPABASE_DB_PASSWORD'),
        host=db_host,
        port=db_port,
        sslmode='require',
        connect_timeout=10
    )
    
    print("✅ Raw connection successful!")
    
    cursor = conn.cursor()
    cursor.execute("SELECT version();")
    version = cursor.fetchone()[0]
    print(f"   PostgreSQL: {version[:80]}...")
    
    cursor.close()
    conn.close()
    print()
    
except Exception as e:
    print(f"❌ Raw connection failed!")
    print(f"   Error type: {type(e).__name__}")
    print(f"   Error message: {e}")
    print()
    sys.exit(1)

# Test 4: Test Django connection
print("🐍 Test 4: Testing Django connection...")
try:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'makeplus_api.settings')
    import django
    django.setup()
    
    from django.db import connection
    
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        
    print("✅ Django connection successful!")
    print()
    
except Exception as e:
    print(f"❌ Django connection failed!")
    print(f"   Error type: {type(e).__name__}")
    print(f"   Error message: {e}")
    print()
    sys.exit(1)

# All tests passed
print("=" * 70)
print("✅ ALL TESTS PASSED! Your database is properly configured.")
print("=" * 70)
print()
print("Next steps:")
print("1. python manage.py makemigrations")
print("2. python manage.py migrate")
print("3. python manage.py createsuperuser")