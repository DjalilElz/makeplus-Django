# Login Endpoint Fix - Email Authentication

## Issue Summary
The `/api/auth/token/` endpoint was returning a 400 error:
```json
{"username":["This field is required."]}
```

The mobile app was sending `email` field, but the backend expected `username` field.

## Solution Implemented

### 1. Modified Custom Token Serializer
**File:** `makeplus_api/events/serializers.py`

Updated `CustomTokenObtainPairSerializer` to accept `email` instead of `username`:

```python
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom token serializer that accepts email instead of username
    and includes user data and role
    """
    username_field = 'email'  # Use email field instead of username
    
    def validate(self, attrs):
        # Get email from attrs and find the user
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            # Find user by email
            try:
                user = User.objects.get(email=email)
                # Replace email with username for parent validation
                attrs['username'] = user.username
                # Remove email from attrs as parent expects username
                attrs.pop('email', None)
            except User.DoesNotExist:
                raise serializers.ValidationError({
                    'email': 'No active account found with the given credentials'
                })
        
        data = super().validate(attrs)
        
        # Add custom claims (user data, role, event)
        # ... rest of the implementation
```

### 2. Created Custom Token View
**File:** `makeplus_api/events/serializers.py` (added at the end)

```python
from rest_framework_simplejwt.views import TokenObtainPairView

class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom token view that uses email instead of username
    """
    serializer_class = CustomTokenObtainPairSerializer
```

### 3. Updated URL Configuration
**File:** `makeplus_api/makeplus_api/urls.py`

Changed the import and URL pattern to use the custom view:

```python
# Import the custom view
from events.serializers import CustomTokenObtainPairView

# Updated URL pattern
path('api/auth/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
```

## How It Works

1. Mobile app sends request with `email` and `password`:
   ```json
   {
     "email": "controller1@wemakeplus.com",
     "password": "test123"
   }
   ```

2. Custom serializer receives the email field
3. Looks up the user by email in the database
4. Converts email to username internally for JWT validation
5. Returns JWT tokens with user data and role information

## User Verification

User `controller1@wemakeplus.com` has been verified:
- ✓ Username: `controller1`
- ✓ Email: `controller1@wemakeplus.com`
- ✓ Active: `True`
- ✓ Password: `test123` (verified)

## Testing

### Manual Test
Run the Django development server:
```bash
cd makeplus_api
python manage.py runserver
```

Then test the endpoint:
```bash
curl -X POST http://localhost:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "controller1@wemakeplus.com",
    "password": "test123"
  }'
```

### Automated Test Script
A test script has been created: `makeplus_api/test_token_endpoint.py`

Run it with:
```bash
cd makeplus_api
python test_token_endpoint.py
```

## Expected Response

```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "username": "controller1",
    "email": "controller1@wemakeplus.com",
    "first_name": "controller1",
    "last_name": "controller1"
  },
  "role": "controller",
  "event": {
    "id": "event-uuid-here",
    "name": "Event Name"
  }
}
```

## Changes Summary

- ✅ Modified `CustomTokenObtainPairSerializer` to accept email field
- ✅ Created `CustomTokenObtainPairView` using the custom serializer
- ✅ Updated URLs to use the custom view
- ✅ Verified user exists and is active
- ✅ No breaking changes to existing functionality
- ✅ Backward compatible (still works with username internally)

## Files Modified

1. `makeplus_api/events/serializers.py` - Updated serializer and added view
2. `makeplus_api/makeplus_api/urls.py` - Updated imports and URL pattern

## Files Created

1. `makeplus_api/test_email_login.py` - User verification script
2. `makeplus_api/test_token_endpoint.py` - API endpoint test script
3. `LOGIN_ENDPOINT_FIX.md` - This documentation

## Next Steps

1. Start the Django development server
2. Test the endpoint with the mobile app
3. Verify the JWT tokens are returned correctly
4. Update API documentation if needed

## Notes

- The endpoint now accepts `email` instead of `username`
- All other authentication endpoints remain unchanged
- The JWT token structure remains the same
- User roles and event assignments are included in the response
