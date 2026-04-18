# Message to Mobile App Developer

## 🚨 MAJOR UPDATE: New Sign Up & Authentication Flow

**Date:** April 17, 2026

### ⚠️ BREAKING CHANGES - Action Required

The authentication system has been completely redesigned. Please read carefully and update your mobile app accordingly.

---

## 🎯 What Changed

### OLD FLOW (Deprecated ❌)
1. User fills registration form on website
2. System creates account automatically
3. User receives login code via email
4. User logs in with email + code

### NEW FLOW (Current ✅)
1. **User signs up in mobile app** (email + password + verification)
2. **User registers for events** on website (with validation code)
3. **User logs in** with email + password

---

## 📱 New Mobile App Flow

### Step 1: Sign Up (New Users)

Users must create an account in the mobile app BEFORE registering for any events.

**Endpoint:** `POST /api/auth/signup/request/`

**Request:**
```json
{
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "password": "mypass123"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Verification code sent to your email"
}
```

**User receives 6-digit code via email (expires in 3 minutes)**

**Password is validated in this step:**
- Must be at least 8 characters
- Must contain at least one number

---

**Endpoint:** `POST /api/auth/signup/verify/`

**Request:**
```json
{
  "email": "user@example.com",
  "code": "123456"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Account created successfully",
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe"
  }
}
```

**Resend Code:** `POST /api/auth/signup/resend/`
- Requires: email, first_name, last_name, password (same as request)
- Can only resend after 3 minutes
- Returns `wait_seconds` if too soon

---

### Step 2: Login (Existing Users)

**Endpoint:** `POST /api/auth/token/`

**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
```

**Response:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe"
  },
  "role": "participant",
  "event": {
    "id": "event-uuid",
    "name": "TechSummit Algeria 2026",
    "start_date": "2026-06-15T09:00:00Z",
    "end_date": "2026-06-17T18:00:00Z",
    "location": "Convention Center",
    "status": "active"
  }
}
```

**Note:** If user hasn't registered for any event yet, `event` will be `null`.

---

### Step 3: Event Registration (Website)

Users register for events on the website using the same email they used to sign up.

**Flow:**
1. User fills registration form on website
2. System checks if user exists
3. If user exists → Sends validation code via email
4. If user doesn't exist → Shows error "Please create account first"
5. User enters validation code on website
6. System links user to event as participant

**This happens on the website, not in the mobile app.**

---

## 🔑 Key Points for Mobile Developer

### 1. Sign Up is Required
- Users MUST sign up in the mobile app first
- Cannot register for events without an account
- Sign up creates account with role "participant"
- Account is NOT linked to any event yet

### 2. Password-Based Authentication
- ❌ NO MORE login with email + code
- ✅ Login with email + password only
- Use standard JWT token authentication
- Tokens expire: Access (1 hour), Refresh (7 days)

### 3. Verification Codes
- Sign up code: 6 digits, expires in 3 minutes
- Can resend after 3 minutes
- Codes are hashed and stored securely

### 4. Multiple Events
- One user account can register for multiple events
- Same account, different participant records per event
- User's `event` in login response shows their active event

### 5. User Roles
- **Participants:** Sign up via mobile app (email + password)
- **Controllers/Staff:** Created by admins (email + password)
- All users login with email + password

---

## 📋 Mobile App Changes Needed

### Add Sign Up Screen
```dart
// Sign Up Flow - Step 1: Collect Info
1. Email input
2. First name input
3. Last name input
4. Password input (validate: 8+ chars, has number)
5. Request verification code button

// Sign Up Flow - Step 2: Verify
6. Show "Code sent to email" message
7. Code input (6 digits)
8. Verify button
9. Show success → Navigate to login (or auto-login with returned tokens)
```

### Update Login Screen
```dart
// Remove code input
// Keep only:
- Email input
- Password input
- Login button
- "Don't have an account? Sign up" link
```

### Add Resend Functionality
```dart
// On sign up screen
- Show countdown timer (3 minutes)
- Enable "Resend Code" button after timer expires
- Handle wait_seconds from API response
```

---

## 🚀 API Endpoints Summary

### Sign Up (New)
- `POST /api/auth/signup/request/` - Request verification code
- `POST /api/auth/signup/verify/` - Verify code and create account
- `POST /api/auth/signup/resend/` - Resend verification code

### Authentication
- `POST /api/auth/token/` - Login with email + password
- `POST /api/auth/token/refresh/` - Refresh access token
- `POST /api/auth/token/verify/` - Verify token validity

### User Profile
- `GET /api/auth/me/` - Get current user profile

### Other Endpoints
- All other endpoints remain the same (events, rooms, sessions, etc.)

---

## ⚠️ Removed Endpoints

These endpoints NO LONGER EXIST:
- ❌ `POST /api/auth/token/code/` (login with code)
- ❌ Any code-based login functionality

---

## 🧪 Test Credentials

### For Testing Login (Staff/Controllers)
```
Email: controller1@wemakeplus.com
Password: test123
Role: controller
```

### For Testing Sign Up (Participants)
Use any email and create a new account through the sign up flow.

---

## 📞 Questions?

Check `MOBILE_APP_API_SPECIFICATION.md` for complete API documentation with all request/response examples.

---

## ✅ Migration Notes

### Existing Users
- All existing participant accounts have been deleted (development phase)
- Controllers and staff accounts remain unchanged
- All users must use password-based login now

### Database
- New tables: `events_signupverification`, `events_formregistrationverification`
- Optimized indexes for performance
- 3-minute expiry on all verification codes

---

**Last Updated:** April 17, 2026  
**Status:** ✅ Ready for Implementation
