# Message to Mobile App Developer

## Summary

Here's the complete and accurate API specification for the mobile app. Please note the important changes and clarifications below.

---

## ⚠️ CRITICAL CHANGES

### 0. IMPORTANT: Correct Login Endpoint
- **Mobile App Must Use:** `POST /api/auth/token/` (JWT endpoint)
- **DO NOT Use:** `/api/auth/login/` (this is a web page, not an API)
- The mobile app should NEVER access `/api/auth/login/`

### 1. Login Endpoint Updated
- **Endpoint:** `POST /api/auth/token/`
- **Change:** Now uses `email` field instead of `username`

### 2. User Object Updated
- **Removed:** `username` field
- **Now returns:** `id`, `email`, `first_name`, `last_name` only

---

## ❌ WHAT'S NOT AVAILABLE

### 1. NO Registration/Signup
- Users are created by administrators only
- Users receive credentials via email from admins
- **Action:** Remove any signup/registration screens from mobile app

### 2. NO Password Reset
- Password reset must be done through admin dashboard
- **Action:** Remove "Forgot Password" feature from mobile app

### 3. NO Profile Update
- User profile is read-only
- **Action:** Make profile screen read-only (view only)

### 4. NO Change Password
- Not available in mobile app
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
4. ✅ **Paid Sessions** - Check access, view payment status
5. ✅ QR Code - Verify and generate QR codes
6. ✅ Room Access - Check-in participants
7. ✅ Participants - List, view participants
8. ✅ Exposant Scans - Record booth visits

---

## 📱 MOBILE APP CHANGES NEEDED

### 1. Update Login Request
- Change from `username` field to `email` field

### 2. Update User Model
- Remove `username` field
- Keep: `id`, `email`, `first_name`, `last_name`

### 3. Remove These Screens/Features
- ❌ Registration/Signup screen
- ❌ Forgot Password screen
- ❌ Change Password screen
- ❌ Profile Edit screen (make it view-only)

### 4. Update Display Names
- Use `email` or `first_name + last_name` instead of `username`

---

## 💰 PAID SESSIONS

### What You Need to Know

Some sessions (workshops/ateliers) require payment. The mobile app needs to:

1. **Display paid sessions** with price indicator
2. **Check user access** before allowing entry
3. **Show payment status** (pending, paid, free)

### Key Information:
- Sessions have `is_paid` and `price` fields
- Use `/api/session-access/` endpoint to check user access
- Payment status: `pending`, `paid`, `free`
- Payment processing is done outside the mobile app (admin dashboard)

---

## 📄 DOCUMENTATION FILES

### For API Details:
**`MOBILE_APP_API_SPECIFICATION.md`** - Complete API reference
- All 24 available endpoints
- Request/response examples
- Authentication flow
- Error handling
- Role-based access control

### For Implementation:
**`PAID_SESSIONS_INFO.md`** - Paid sessions implementation guide
- Code examples
- UI recommendations
- Complete implementation flow

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

## 📋 CHECKLIST FOR MOBILE DEVELOPER

- [ ] Update login request to use `email` field
- [ ] Remove `username` from User model
- [ ] Remove registration/signup screen
- [ ] Remove forgot password feature
- [ ] Remove change password feature
- [ ] Make profile screen read-only
- [ ] Update all user display names to use email or full name
- [ ] Implement paid sessions display and access check
- [ ] Test login with test credentials
- [ ] Test token refresh flow
- [ ] Test all role-based features (controller, exposant, etc.)

---

## 🆘 SUPPORT

If you have questions or need clarification:
1. Check `MOBILE_APP_API_SPECIFICATION.md` for detailed API documentation
2. Check `PAID_SESSIONS_INFO.md` for implementation examples
3. Test endpoints in Swagger: https://makeplus-django-5.onrender.com/swagger/
4. Use test credentials provided above

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

**What to add:**
- Paid sessions support

**What stays the same:**
- All other endpoints work as before
- Token authentication flow
- Role-based access control
