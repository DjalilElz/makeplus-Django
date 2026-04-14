# Message to Mobile App Developer

## Summary

Here's the complete and accurate API specification for the mobile app. Please note the important changes and clarifications below.

---

## ⚠️ CRITICAL CHANGES

### 1. Login Endpoint Updated
- **Endpoint:** `POST /api/auth/token/`
- **Change:** Now uses `email` field instead of `username`
- **Request:**
```json
{
  "email": "controller1@wemakeplus.com",
  "password": "test123"
}
```

### 2. User Object Updated
- **Removed:** `username` field
- **Now returns:** `id`, `email`, `first_name`, `last_name` only

**Response:**
```json
{
  "access": "jwt_token...",
  "refresh": "jwt_token...",
  "user": {
    "id": 1,
    "email": "controller1@wemakeplus.com",
    "first_name": "Controller",
    "last_name": "One"
  },
  "role": "controller",
  "event": {...}
}
```

---

## ❌ WHAT'S NOT AVAILABLE

### 1. NO Registration/Signup
- There is NO `/api/auth/register/` endpoint for mobile app
- Users are created by administrators only
- Users receive credentials via email from admins
- **Action:** Remove any signup/registration screens from mobile app

### 2. NO Password Reset
- There is NO forgot password endpoint
- Password reset must be done through admin dashboard
- **Action:** Remove "Forgot Password" feature from mobile app

### 3. NO Profile Update
- User profile is read-only
- Users cannot update their name, email, etc. through mobile app
- **Action:** Make profile screen read-only (view only)

### 4. NO Change Password
- There is NO change password endpoint for mobile app
- **Action:** Remove "Change Password" feature from mobile app

---

## ✅ WHAT'S AVAILABLE

### Authentication
1. ✅ Login (JWT) - `POST /api/auth/token/`
2. ✅ Refresh Token - `POST /api/auth/token/refresh/`
3. ✅ Verify Token - `POST /api/auth/token/verify/`

### Core Features
1. ✅ Events - List, view events
2. ✅ Rooms - List, view rooms
3. ✅ Sessions - List, view, start/end sessions
4. ✅ QR Code - Verify and generate QR codes
5. ✅ Room Access - Check-in participants
6. ✅ Participants - List, view participants
7. ✅ Exposant Scans - Record booth visits

---

## 📱 MOBILE APP CHANGES NEEDED

### 1. Update Login Screen
```dart
// OLD - Remove this
final response = await http.post(
  Uri.parse('$baseUrl/api/auth/token/'),
  body: jsonEncode({
    'username': email,  // ❌ Remove
    'password': password,
  }),
);

// NEW - Use this
final response = await http.post(
  Uri.parse('$baseUrl/api/auth/token/'),
  body: jsonEncode({
    'email': email,  // ✅ Correct
    'password': password,
  }),
);
```

### 2. Update User Model
```dart
class User {
  final int id;
  final String email;
  final String firstName;
  final String lastName;
  // Remove: final String username;  // ❌ This field no longer exists
}
```

### 3. Remove These Screens/Features
- ❌ Registration/Signup screen
- ❌ Forgot Password screen
- ❌ Change Password screen
- ❌ Profile Edit screen (make it view-only)

### 4. Update Display Names
```dart
// OLD
Text(user.username)  // ❌ Remove

// NEW - Use one of these
Text(user.email)  // ✅ Option 1
Text('${user.firstName} ${user.lastName}')  // ✅ Option 2
```

---

## 📄 COMPLETE API DOCUMENTATION

Please refer to `MOBILE_APP_API_SPECIFICATION.md` for:
- Complete list of all available endpoints
- Request/response examples for each endpoint
- Authentication flow
- Error handling
- Role-based access control
- Testing credentials

---

## 🧪 TESTING

### Test Credentials
```
Email: controller1@wemakeplus.com
Password: test123
Role: controller
```

### Test Server
```
https://makeplus-django-5.onrender.com
```

### API Documentation (Swagger)
```
https://makeplus-django-5.onrender.com/swagger/
```

You can test all endpoints interactively in Swagger.

---

## 🔑 AUTHENTICATION FLOW

1. **Login:**
   ```
   POST /api/auth/token/
   Body: { "email": "user@example.com", "password": "password" }
   ```

2. **Store Tokens:**
   ```dart
   SharedPreferences prefs = await SharedPreferences.getInstance();
   await prefs.setString('access_token', response['access']);
   await prefs.setString('refresh_token', response['refresh']);
   ```

3. **Use Token in Requests:**
   ```dart
   headers: {
     'Authorization': 'Bearer $accessToken',
     'Content-Type': 'application/json',
   }
   ```

4. **Refresh When Expired:**
   ```
   POST /api/auth/token/refresh/
   Body: { "refresh": "stored_refresh_token" }
   ```

---

## 📋 CHECKLIST FOR MOBILE DEVELOPER

- [ ] Update login request to use `email` field
- [ ] Remove `username` from User model
- [ ] Remove registration/signup screen
- [ ] Remove forgot password feature
- [ ] Remove change password feature
- [ ] Make profile screen read-only
- [ ] Update all user display names to use email or full name
- [ ] Test login with test credentials
- [ ] Test token refresh flow
- [ ] Test all role-based features (controller, exposant, etc.)

---

## 🆘 SUPPORT

If you have questions or need clarification:
1. Check `MOBILE_APP_API_SPECIFICATION.md` for detailed documentation
2. Test endpoints in Swagger: https://makeplus-django-5.onrender.com/swagger/
3. Use test credentials provided above

---

## 🎯 SUMMARY

**What changed:**
- Login now uses `email` instead of `username`
- User object no longer includes `username`

**What to remove:**
- Registration/signup
- Forgot password
- Change password
- Profile editing

**What stays the same:**
- All other endpoints work as before
- Token authentication flow
- Role-based access control
