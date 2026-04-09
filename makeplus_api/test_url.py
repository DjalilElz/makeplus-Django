"""
Test if the my-room/statistics URL is accessible
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'makeplus_api.settings')
django.setup()

from django.urls import resolve, reverse
from django.conf import settings

print("🔍 Testing URL Configuration...")
print(f"DEBUG mode: {settings.DEBUG}")

try:
    # Try to reverse the URL
    url = reverse('events:my-room-statistics')
    print(f"✅ URL reverse successful: {url}")
    
    # Try to resolve the URL
    resolved = resolve(url)
    print(f"✅ URL resolves to: {resolved.func.__name__}")
    print(f"   View class: {resolved.func.view_class}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

# Test the full URL path
try:
    resolved = resolve('/api/my-room/statistics/')
    print(f"\n✅ Direct path resolution successful")
    print(f"   View: {resolved.func.view_class}")
    print(f"   URL name: {resolved.url_name}")
except Exception as e:
    print(f"\n❌ Direct path resolution failed: {e}")
    import traceback
    traceback.print_exc()
