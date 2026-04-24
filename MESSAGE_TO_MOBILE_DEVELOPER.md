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
   - User account created
   - Participant profile created automatically
   - Badge ID and QR code generated
2. **User registers for events** on website (with validation code)
   - Links participant to specific events
3. **User logs in** with email + password
   - Returns user data, role, event info, and QR code

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
  },
  "qr_code": {
    "user_id": 1,
    "badge_id": "USER-1-ABC12345",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "full_name": "John Doe",
    "role": "participant",
    "event": null,
    "paid_items": [],
    "access_summary": {...}
  }
}
```

**Note:** QR code is automatically generated when account is created. The participant profile is also created automatically with a unique badge_id.

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
  },
  "qr_code": {
    "user_id": 1,
    "badge_id": "USER-1-ABC12345",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "full_name": "John Doe",
    "role": "participant",
    "event": {...},
    "paid_items": [...],
    "access_summary": {...}
  }
}
```

**Note:** 
- If user hasn't registered for any event yet, `event` will be `null`.
- QR code is automatically generated and included in the response

---

### Get User Profile (with QR Code)

**Endpoint:** `GET /api/auth/me/`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "id": 1,
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "full_name": "John Doe",
  "role": "participant",
  "event": {
    "id": "event-uuid",
    "name": "TechSummit Algeria 2026",
    "status": "active"
  },
  "participant": {
    "id": "participant-uuid",
    "badge_id": "USER-1-ABC12345",
    "role": "participant",
    "qr_code_data": {
      "user_id": 1,
      "badge_id": "USER-1-ABC12345",
      "email": "user@example.com",
      "first_name": "John",
      "last_name": "Doe",
      "full_name": "John Doe",
      "role": "participant",
      "event": {...},
      "paid_items": [...],
      "access_summary": {...}
    },
    "registered_events": [
      {
        "id": "event-uuid-1",
        "name": "TechSummit Algeria 2026",
        "status": "active",
        "start_date": "2026-06-15T09:00:00Z",
        "end_date": "2026-06-17T18:00:00Z"
      },
      {
        "id": "event-uuid-2",
        "name": "Innovation Forum 2026",
        "status": "upcoming",
        "start_date": "2026-09-20T09:00:00Z",
        "end_date": "2026-09-22T18:00:00Z"
      }
    ]
  },
  "qr_code": {
    "user_id": 1,
    "badge_id": "USER-1-ABC12345",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "full_name": "John Doe",
    "role": "participant",
    "event": {...},
    "participant_id": "participant-uuid",
    "is_checked_in": false,
    "checked_in_at": null,
    "paid_items": [...],
    "total_paid_items": 2,
    "access_summary": {
      "total_sessions": 5,
      "paid_sessions": 2,
      "total_rooms": 3,
      "has_any_paid_access": true
    }
  }
}
```

**Note:**
- This endpoint returns complete user profile including:
  - User basic info
  - Current role and event assignment
  - Participant profile with badge_id and QR code data
  - List of ALL registered events
  - Complete QR code data with payment and access information
- Use this endpoint to refresh user data after event registration or payments

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

### 1. Automatic Participant Profile
- Users who sign up get a Participant profile created automatically
- One user = One participant profile (permanent)
- Badge ID and QR code generated on signup
- Role is always "participant" for mobile app users

### 2. Sign Up Creates Participant
- User signs up → User account + Participant profile created
- Participant has unique badge_id and QR code
- User can then register for multiple events

### 3. Event Registration
- User registers for Event A → Links participant to Event A
- User registers for Event B → Links participant to Event B
- Same participant, multiple event registrations

### 4. Password-Based Authentication
- ❌ NO MORE login with email + code
- ✅ Login with email + password only
- Use standard JWT token authentication
- Tokens expire: Access (1 hour), Refresh (7 days)

### 5. QR Code Auto-Generated
- ✅ QR code automatically included in login response
- ✅ QR code automatically included in signup response
- ❌ No need to call `/api/qr/generate/` separately
- Reduces API calls and improves performance
- Store QR code data locally for offline access

### 6. Verification Codes
- Sign up code: 6 digits, expires in 3 minutes
- Can resend after 3 minutes
- Codes are hashed and stored securely

### 7. Multiple Events
- One participant can register for multiple events
- Each event registration tracked separately
- User's `event` in login response shows their most recent active event

### 8. User Roles
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
9. Store tokens AND QR code data from response
10. Show success → Navigate to home (user is logged in)
```

### Update Login Screen
```dart
// Remove code input
// Keep only:
- Email input
- Password input
- Login button
- "Don't have an account? Sign up" link

// After successful login:
- Store access token, refresh token, AND qr_code data
- QR code is already in the response!
```

### Add Resend Functionality
```dart
// On sign up screen
- Show countdown timer (3 minutes)
- Enable "Resend Code" button after timer expires
- Handle wait_seconds from API response
```

### Store QR Code Data
```dart
// After login or signup
final response = await loginOrSignup();

// Store tokens
await prefs.setString('access_token', response['access']);
await prefs.setString('refresh_token', response['refresh']);

// Store QR code data (already included in response!)
await prefs.setString('qr_code_data', jsonEncode(response['qr_code']));

// No need to call /api/qr/generate/ separately
```

### Display QR Code
```dart
// Retrieve stored QR code data
final qrCodeJson = prefs.getString('qr_code_data');
final qrData = jsonDecode(qrCodeJson);

// Generate QR code image from badge_id or full qr_data
final qrImage = QrImage(
  data: jsonEncode(qrData), // Or use qrData['badge_id']
  version: QrVersions.auto,
  size: 200.0,
);

// Optional: Refresh QR code if user registers for new events
final refreshedQR = await api.get('/api/qr/generate/');
await prefs.setString('qr_code_data', jsonEncode(refreshedQR['qr_data']));
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

### User Profile & QR Code
- `GET /api/auth/me/` - Get current user profile (includes QR code, participant data, and registered events)
- `GET /api/qr/generate/` - Refresh QR code data (optional - QR code already provided on login/signup)

### Other Endpoints
- All other endpoints remain the same (events, rooms, sessions, etc.)

---

## ⚠️ IMPORTANT: QR Code is Auto-Generated

**QR code is automatically included in login and signup responses!**

You don't need to call `/api/qr/generate/` separately - the QR code data is already provided when users:
- Login: `POST /api/auth/token/` → Returns `qr_code` field
- Sign up: `POST /api/auth/signup/verify/` → Returns `qr_code` field

**Optional Refresh:** Use `GET /api/qr/generate/` only if you need to refresh QR code data after user registers for new events or makes payments.

**DO NOT USE:** `/api/my-ateliers/` for QR codes (that's for listing workshops only)

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


---

## 💳 Paid Sessions & Badge Scanning

### How Paid Sessions Work

When a participant pays for a session/workshop at the caisse (cash register):

1. **Payment Processing:**
   - Caisse operator selects participant and paid items (sessions/workshops)
   - System creates `CaisseTransaction` with status='completed'
   - System creates `SessionAccess` records for each paid session:
     - `has_access=True`
     - `payment_status='paid'`
     - `amount_paid=<session_price>`

2. **Badge Scanning (Controller):**
   - Controller scans participant's QR code/badge
   - Mobile app calls `POST /api/events/rooms/{room_id}/verify_access/`
   - Backend checks if `SessionAccess` exists for that participant and session
   - If exists with `has_access=True` → Access granted ✅
   - If not exists or `has_access=False` → Access denied ❌

### Badge Verification API

**Endpoint:** `POST /api/events/rooms/{room_id}/verify_access/`

**Headers:**
```
Authorization: Bearer <controller_token>
Content-Type: application/json
```

**Request:**
```json
{
  "qr_data": "{\"user_id\": 1, \"badge_id\": \"USER-1-ABC12345\"}",
  "session": "session-uuid-here"
}
```

**Note:** 
- `qr_data` is the JSON string from the participant's QR code
- `session` is REQUIRED when checking access for a paid workshop/atelier
- `session` is OPTIONAL for general room access

**Response (Access Granted):**
```json
{
  "status": "granted",
  "message": "Access granted successfully",
  "participant": {
    "id": "participant-uuid",
    "name": "John Doe",
    "email": "user@example.com",
    "badge_id": "USER-1-ABC12345"
  },
  "access": {
    "id": "access-uuid",
    "accessed_at": "2026-04-24T20:00:00Z"
  }
}
```

**Response (Payment Required):**
```json
{
  "status": "denied",
  "message": "Payment required for this atelier",
  "participant": {
    "id": "participant-uuid",
    "name": "John Doe",
    "badge_id": "USER-1-ABC12345"
  },
  "session": {
    "title": "Advanced Python Workshop",
    "price": "50.00"
  }
}
```

**Response (Not Registered for Event):**
```json
{
  "status": "denied",
  "message": "User does not have access to this event",
  "user": {
    "name": "John Doe",
    "email": "user@example.com"
  }
}
```

### Get Participant's Paid Sessions

**Endpoint:** `GET /api/events/my-ateliers/`

**Headers:**
```
Authorization: Bearer <participant_token>
```

**Response:**
```json
{
  "count": 2,
  "results": [
    {
      "id": "session-uuid-1",
      "title": "Advanced Python Workshop",
      "description": "Learn advanced Python concepts",
      "start_time": "2026-06-15T14:00:00Z",
      "end_time": "2026-06-15T16:00:00Z",
      "room": {
        "id": "room-uuid",
        "name": "Room A"
      },
      "payment_status": "paid",
      "amount_paid": 50.00,
      "is_paid": true,
      "price": 50.00
    },
    {
      "id": "session-uuid-2",
      "title": "Web Development Bootcamp",
      "description": "Full-stack web development",
      "start_time": "2026-06-16T10:00:00Z",
      "end_time": "2026-06-16T12:00:00Z",
      "room": {
        "id": "room-uuid-2",
        "name": "Room B"
      },
      "payment_status": "paid",
      "amount_paid": 75.00,
      "is_paid": true,
      "price": 75.00
    }
  ]
}
```

### Mobile App Implementation

#### For Controllers (Badge Scanning):

```dart
// 1. Scan QR code
final qrCode = await scanQRCode();

// 2. Parse QR data
final qrData = jsonDecode(qrCode);

// 3. Get current session (if scanning for specific workshop)
final sessionId = getCurrentSessionId(); // From your session selection

// 4. Verify access
final response = await http.post(
  Uri.parse('$baseUrl/api/events/rooms/$roomId/verify_access/'),
  headers: {
    'Authorization': 'Bearer $controllerToken',
    'Content-Type': 'application/json',
  },
  body: jsonEncode({
    'qr_data': qrCode,
    'session': sessionId, // Include if checking for paid session
  }),
);

final result = jsonDecode(response.body);

// 5. Show result
if (result['status'] == 'granted') {
  showSuccess('Access Granted: ${result['participant']['name']}');
} else {
  showError('Access Denied: ${result['message']}');
  if (result['session'] != null) {
    showPaymentRequired(result['session']['title'], result['session']['price']);
  }
}
```

#### For Participants (View Paid Sessions):

```dart
// Fetch paid sessions
final response = await http.get(
  Uri.parse('$baseUrl/api/events/my-ateliers/'),
  headers: {
    'Authorization': 'Bearer $participantToken',
  },
);

final data = jsonDecode(response.body);
final paidSessions = data['results'];

// Display in UI
ListView.builder(
  itemCount: paidSessions.length,
  itemBuilder: (context, index) {
    final session = paidSessions[index];
    return ListTile(
      title: Text(session['title']),
      subtitle: Text('Paid: ${session['amount_paid']} DA'),
      trailing: Icon(Icons.check_circle, color: Colors.green),
    );
  },
);
```

### Important Notes:

1. **SessionAccess Records**: Automatically created when payment is processed at caisse
2. **QR Code Format**: Contains JSON with `user_id` and `badge_id`
3. **Session Parameter**: MUST be included when verifying access for paid workshops
4. **Payment Status**: Check `payment_status='paid'` and `has_access=True` in SessionAccess
5. **Currency**: All prices are in DA (Algerian Dinar)

### Testing Flow:

1. ✅ Participant signs up → Participant profile created
2. ✅ Participant registers for Event A → UserEventAssignment + ParticipantEventRegistration created
3. ✅ Participant pays for Workshop 1 at caisse → CaisseTransaction + SessionAccess created
4. ✅ Controller scans participant's badge → Backend checks SessionAccess → Access granted/denied

---

**Last Updated:** April 24, 2026  
**Status:** ✅ Paid Sessions Feature Implemented
