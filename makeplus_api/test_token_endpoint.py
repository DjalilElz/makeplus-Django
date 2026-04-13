#!/usr/bin/env python
"""
Test the token endpoint with email-based authentication
"""
import requests
import json

# API endpoint
url = 'http://localhost:8000/api/auth/token/'

# Test data
data = {
    'email': 'controller1@wemakeplus.com',
    'password': 'test123'
}

print(f"Testing endpoint: {url}")
print(f"Request body: {json.dumps(data, indent=2)}")
print("\n" + "="*50 + "\n")

try:
    response = requests.post(url, json=data)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    print(f"\nResponse Body:")
    print(json.dumps(response.json(), indent=2))
    
    if response.status_code == 200:
        print("\n✓ SUCCESS! Login works with email field!")
    else:
        print("\n✗ FAILED! Check the error above.")
        
except requests.exceptions.ConnectionError:
    print("✗ ERROR: Could not connect to server.")
    print("Make sure the Django server is running on http://localhost:8000")
except Exception as e:
    print(f"✗ ERROR: {e}")
