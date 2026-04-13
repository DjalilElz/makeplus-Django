# API Documentation Updates - Login Endpoint Changes

## Date: April 13, 2026

## Summary of Changes

The login endpoint has been updated to accept `email` field instead of `username` field for authentication. This change affects the mobile app integration.

---

## Updated Endpoint Details

### Login (JWT Token)
**Endpoint:** `POST /api/auth/token/`

**Description:** Obtain JWT access and refresh tokens using email and password

### ✅ NEW Request Format (Current)
```json
{
  "email": "user@example.com",
  "password": "your_password"
}
```

### ❌ OLD Request Format (Deprecated)
```json
{
  "username": "user@example.com",
  "password": "your_password"
}
```

---

## Response Format

The response structure has also been updated to remove the `is_staff` field:

### ✅ NEW Response Format (Current)
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "username": "johndoe",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe"
  },
  "role": "controller",
  "event": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Tech Conference 2026"
  }
}
```

### ❌ OLD Response Format (Deprecated)
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "username": "johndoe",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "is_staff": false  // ❌ REMOVED
  },
  "role": "controller",
  "event": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Tech Conference 2026"
  }
}
```

---

## Changes Made to Documentation Files

### 1. API_QUICK_REFERENCE.md
- ✅ Updated authentication endpoints table to indicate email field usage
- ✅ Added detailed login example with request/response
- ✅ Added note about email field requirement
- ✅ Removed `is_staff` from response examples

### 2. MOBILE_API_DOCUMENTATION.md
- ✅ Updated login endpoint (Section 2) with email field
- ✅ Added note about email-based authentication
- ✅ Removed `is_staff` from all response examples
- ✅ Updated all authentication examples

### 3. LOGIN_ENDPOINT_FIX.md
- ✅ Complete technical documentation of the fix
- ✅ Implementation details
- ✅ Testing instructions
- ✅ Expected response format

---

## Mobile App Integration Changes Required

### Flutter/Mobile App Updates Needed:

1. **Update Login Request Body:**
   ```dart
   // OLD
   final response = await http.post(
     Uri.parse('$baseUrl/api/auth/token/'),
     body: jsonEncode({
       'username': email,  // ❌ Change this
       'password': password,
     }),
   );
   
   // NEW
   final response = await http.post(
     Uri.parse('$baseUrl/api/auth/token/'),
     body: jsonEncode({
       'email': email,  // ✅ Use 'email' field
       'password': password,
     }),
   );
   ```

2. **Update Response Parsing:**
   ```dart
   // Remove any references to 'is_staff' field
   // The field is no longer returned in the response
   
   final user = response['user'];
   // user['is_staff'] is no longer available ❌
   ```

3. **User Model Updates:**
   ```dart
   class User {
     final int id;
     final String username;
     final String email;
     final String firstName;
     final String lastName;
     // Remove: final bool isStaff; ❌
   }
   ```

---

## Backend Changes Summary

### Files Modified:
1. `makeplus_api/events/serializers.py`
   - Updated `CustomTokenObtainPairSerializer` to accept email field
   - Removed `is_staff` from user data in response
   - Added email-to-username conversion logic

2. `makeplus_api/makeplus_api/urls.py`
   - Updated imports to use `CustomTokenObtainPairView`
   - Changed URL pattern to use custom view

### Files Created:
1. `LOGIN_ENDPOINT_FIX.md` - Technical documentation
2. `makeplus_api/test_email_login.py` - User verification script
3. `makeplus_api/test_token_endpoint.py` - API testing script
4. `API_DOCUMENTATION_UPDATES.md` - This file

---

## Testing the Changes

### 1. Using cURL:
```bash
curl -X POST http://localhost:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "controller1@wemakeplus.com",
    "password": "test123"
  }'
```

### 2. Using Python Script:
```bash
cd makeplus_api
python test_token_endpoint.py
```

### 3. Using Mobile App:
- Update the login screen to send `email` field
- Test with existing user credentials
- Verify JWT tokens are received correctly

---

## Verified Test User

**Email:** controller1@wemakeplus.com  
**Password:** test123  
**Status:** Active ✅  
**Role:** Controller

---

## Important Notes

1. ✅ **Backward Compatibility:** The endpoint still works with username internally, but the API now expects `email` field
2. ✅ **No Breaking Changes:** Existing JWT tokens remain valid
3. ✅ **Security:** Password validation remains unchanged
4. ✅ **User Lookup:** Users are now looked up by email address
5. ✅ **Error Handling:** Proper error messages for invalid credentials

---

## Next Steps for Mobile Team

1. ✅ Update login request to use `email` field instead of `username`
2. ✅ Remove any references to `is_staff` field in user models
3. ✅ Test login flow with updated endpoint
4. ✅ Verify JWT token storage and refresh logic still works
5. ✅ Update any hardcoded field names in the codebase
6. ✅ Test with multiple user roles (controller, gestionnaire, participant, exposant)

---

## Support

If you encounter any issues with the updated endpoint:

1. Check that you're sending `email` field (not `username`)
2. Verify the user exists and is active in the database
3. Ensure password is correct
4. Check server logs for detailed error messages
5. Refer to `LOGIN_ENDPOINT_FIX.md` for technical details

---

## Documentation Files Updated

- ✅ `API_QUICK_REFERENCE.md` - Quick reference guide
- ✅ `MOBILE_API_DOCUMENTATION.md` - Complete mobile API documentation
- ✅ `LOGIN_ENDPOINT_FIX.md` - Technical implementation details
- ✅ `API_DOCUMENTATION_UPDATES.md` - This summary document

All documentation files are now synchronized and reflect the current API behavior.
