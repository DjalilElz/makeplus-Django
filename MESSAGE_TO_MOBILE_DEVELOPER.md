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

### ⚠️ CRITICAL: QR Code Architecture

**The QR code contains ONLY identification data, NOT payment data!**

#### QR Code Structure (Minimal):
```json
{
  "user_id": 58,
  "badge_id": "USER-58-37F80526",
  "email": "abdeldjalil.elazizi@ensia.edu.dz",
  "first_name": "djalil",
  "last_name": "azizi"
}
```

**Why?**
- ✅ QR code never changes (same badge forever)
- ✅ Payment data is always fresh from database
- ✅ No need to regenerate QR code after payments
- ✅ No stale data issues

#### How Badge Scanning Works:

1. **Controller scans QR code** → Gets `user_id` and `badge_id`
2. **Mobile app calls API** → `POST /api/events/participants/scan/`
3. **Backend queries database** → Fetches ALL paid items from `CaisseTransaction` table
4. **Backend returns fresh data** → Controller sees current payment status
5. **Controller displays** → Shows all paid items (sessions, access, dinner, other)

**🔄 Real-Time Data Flow:**
```
Participant pays at caisse (10:30 AM)
    ↓
CaisseTransaction created in database
    ↓
Controller scans badge (10:45 AM)
    ↓
Backend queries CaisseTransaction table (FRESH DATA)
    ↓
Backend returns ALL paid items
    ↓
Controller sees payment immediately ✅
```

**Key Point:** The QR code is just an ID card. The actual payment data comes from the database via API call.

### How Paid Sessions Work

When a participant pays for a session/workshop at the caisse (cash register):

1. **Payment Processing:**
   - Caisse operator selects participant and paid items (sessions/workshops/access)
   - System creates `CaisseTransaction` with status='completed'
   - Items are linked to transaction in database
   - **QR code does NOT change** - same badge_id forever

2. **Badge Scanning (Controller):**
   - Controller scans participant's QR code/badge
   - **QR code contains ONLY:** `user_id`, `badge_id`, `email`, `name`
   - Mobile app calls `POST /api/events/participants/scan/`
   - **Backend fetches FRESH data from database** (queries `CaisseTransaction` table)
   - Backend returns ALL paid items (sessions, access, dinner, other)
   - Controller sees complete list of what participant has access to
   - **No verification needed** - if paid, participant enters directly

**Important:** The QR code is just an identifier. Payment data always comes from the database via API call, ensuring it's always up-to-date.

**🔄 Real-Time Data Fetching:**
- **QR Code Purpose:** Identification only (contains `user_id` and `badge_id`)
- **Data Source:** Database (`CaisseTransaction` table) - always fresh and up-to-date
- **Controller Benefit:** Sees latest payments immediately, even if participant hasn't refreshed their app
- **Example:** Participant pays at 10:30 AM, controller scans at 10:45 AM → Controller sees the payment ✅

### 🚨 IMPORTANT: Remove Room Assignment Check

**Your mobile app is checking for a room assignment that NO LONGER EXISTS!**

**DELETE this code:**
```dart
// ❌ REMOVE THIS - Controllers don't need room assignments anymore
final metadata = userAssignment['metadata'];
final roomId = metadata?['room_id'];

if (roomId == null) {
  showError("No room assignment found");  // This error is wrong!
  return;
}
```

**Why?** Controllers can now work in ANY room without assignment. The new endpoint returns ALL paid items from ALL rooms.

**See `MOBILE_APP_CONTROLLER_FIX.md` for complete migration guide.**

---

### Badge Scanning API (Primary Method)

**Endpoint:** `POST /api/events/participants/scan/`

**🎯 SIMPLIFIED - No Room Selection Needed:**
- ✅ Controllers work in ANY room (no specific assignment)
- ✅ No need to select room before scanning
- ✅ Just scan badge and see ALL paid items
- ✅ Returns sessions from all rooms + access + dinner + other

**🔄 Real-Time Data Fetching:** 
- **QR Code Purpose:** Identification only (contains `user_id` and `badge_id`)
- **Data Source:** Database (`CaisseTransaction` table) - always fresh
- **Controller Benefit:** Sees latest payments immediately
- **Example:** Participant pays at 10:30 AM, controller scans at 10:45 AM → Controller sees the payment ✅

**Headers:**
```
Authorization: Bearer <controller_token>
Content-Type: application/json
```

**Request:**
```json
{
  "qr_data": "{\"user_id\": 58, \"badge_id\": \"USER-58-37F80526\", \"email\": \"user@example.com\", \"first_name\": \"djalil\", \"last_name\": \"azizi\"}"
}
```

**🔑 Key Points:** 
- `qr_data` is the JSON string from the participant's QR code
- QR code contains ONLY identification data: `user_id`, `badge_id`, `email`, `first_name`, `last_name`
- QR code does NOT contain payment data (`paid_items`)
- Backend uses `user_id` to identify the participant
- Backend queries `CaisseTransaction` table for **REAL-TIME** paid items
- This ensures controller always sees latest payments

**How It Works:**
1. Controller scans QR code → Gets `user_id`, `badge_id`, `email`, `name`
2. Backend extracts `user_id` from QR code
3. Backend gets controller's active event
4. Backend queries `CaisseTransaction` table (**FRESH DATA**)
5. Backend returns ALL paid items: sessions (all rooms), access, dinner, other
6. Controller displays complete payment history

**Response (Success):**
```json
{
  "status": "success",
  "participant": {
    "id": "participant-uuid",
    "name": "djalil azizi",
    "email": "abdeldjalil.elazizi@ensia.edu.dz",
    "badge_id": "USER-58-37F80526"
  },
  "event": {
    "id": "event-uuid",
    "name": "TechSummit Algeria 2026"
  },
  "paid_items": [
    {
      "type": "session",
      "id": "session-uuid-1",
      "title": "Intro to AI",
      "is_paid": true,
      "payment_status": "paid",
      "amount_paid": 6000.0,
      "has_access": true,
      "transaction_date": "2026-04-27T10:30:00Z",
      "session_details": {
        "start_time": "2026-06-15T14:00:00Z",
        "end_time": "2026-06-15T16:00:00Z",
        "room": "Conference Hall A",
        "room_id": "room-uuid-1"
      }
    },
    {
      "type": "access",
      "id": "access-uuid",
      "title": "VIP Lounge Access",
      "is_paid": true,
      "payment_status": "paid",
      "amount_paid": 2000.0,
      "has_access": true,
      "transaction_date": "2026-04-24T10:30:00Z"
    },
    {
      "type": "dinner",
      "id": "dinner-uuid",
      "title": "Gala Dinner",
      "is_paid": true,
      "payment_status": "paid",
      "amount_paid": 75.00,
      "has_access": true,
      "transaction_date": "2026-04-24T11:00:00Z"
    },
    {
      "type": "other",
      "id": "other-uuid",
      "title": "Event T-Shirt",
      "is_paid": true,
      "payment_status": "paid",
      "amount_paid": 25.00,
      "has_access": true,
      "transaction_date": "2026-04-24T11:00:00Z"
    }
  ],
  "free_items": [
    {
      "type": "session",
      "id": "session-uuid-2",
      "title": "Opening Keynote",
      "is_paid": false,
      "payment_status": "free",
      "amount_paid": 0,
      "has_access": true
    }
  ],
  "total_paid_items": 4,
  "total_free_items": 1,
  "has_access": true
}
```

**📦 Payable Item Types:**

There are TWO types of payable items:

### 1. Session-Linked Items (`item_type='session'`)
- **Automatically synced** from sessions marked as paid (`is_paid=True`)
- Linked to a specific `Session` object via `session` field
- Example: "Advanced Python Workshop - 50 DA"
- Created when admin marks a session as paid

### 2. Custom Items (Created by Admin)
Admins can create custom payable items from the dashboard with these types:

- **`access`** - VIP access, backstage passes, special areas
  - Example: "VIP Lounge Access - 100 DA"
  
- **`dinner`** - Event meals, lunch, dinner, coffee breaks
  - Example: "Gala Dinner - 75 DA"
  
- **`other`** - Merchandise, materials, certificates, etc.
  - Example: "Event T-Shirt - 25 DA"

**✅ What Controller Sees:**
- ALL paid items (session-linked + custom items)
- ALL free sessions in the current room
- Real-time data from database (always fresh)
- Transaction dates for each payment

**Response (Not Registered for Event):**
```json
{
  "status": "error",
  "message": "Participant not registered for this event",
  "participant": {
    "id": "participant-uuid",
    "name": "John Doe",
    "email": "user@example.com",
    "badge_id": "USER-1-ABC12345"
  }
}
```

**Response (Invalid QR Code):**
```json
{
  "status": "invalid",
  "message": "Invalid QR code format"
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

// 2. Parse QR data to display immediately (optional - for offline mode)
final qrData = jsonDecode(qrCode);
final badgeId = qrData['badge_id'];
final userName = qrData['full_name'] ?? '${qrData['first_name']} ${qrData['last_name']}';

// 3. Call backend to get FRESH data from database
// ✅ NO ROOM SELECTION NEEDED - Works for any room
final response = await http.post(
  Uri.parse('$baseUrl/api/events/participants/scan/'),
  headers: {
    'Authorization': 'Bearer $controllerToken',
    'Content-Type': 'application/json',
  },
  body: jsonEncode({
    'qr_data': qrCode,
  }),
);

final result = jsonDecode(response.body);

// 4. Display results
if (result['status'] == 'success') {
  // Show participant info
  final participant = result['participant'];
  showParticipantInfo(participant['name'], participant['email']);
  
  // Show ALL paid items (sessions, access, dinner, other)
  final paidItems = result['paid_items'] ?? [];
  final freeItems = result['free_items'] ?? [];
  
  // Display paid items by type
  if (paidItems.isNotEmpty) {
    // Group by type for better display
    final sessions = paidItems.where((i) => i['type'] == 'session').toList();
    final access = paidItems.where((i) => i['type'] == 'access').toList();
    final dinners = paidItems.where((i) => i['type'] == 'dinner').toList();
    final others = paidItems.where((i) => i['type'] == 'other').toList();
    
    // Display each category
    if (sessions.isNotEmpty) {
      showSection('Paid Workshops', sessions);
      // Example: "✅ Advanced Python Workshop (50 DA)"
    }
    if (access.isNotEmpty) {
      showSection('Access Passes', access);
      // Example: "✅ VIP Lounge Access (100 DA)"
    }
    if (dinners.isNotEmpty) {
      showSection('Meals', dinners);
      // Example: "✅ Gala Dinner (75 DA)"
    }
    if (others.isNotEmpty) {
      showSection('Other Items', others);
      // Example: "✅ Event T-Shirt (25 DA)"
    }
  }
  
  // Display free items
  if (freeItems.isNotEmpty) {
    showFreeItemsList(freeItems);
    // Example: "🆓 Opening Keynote (Free)"
  }
  
  // Show summary
  final totalPaid = paidItems.fold(0.0, (sum, item) => sum + item['amount_paid']);
  showSuccess(
    'Access Granted\n'
    '${paidItems.length} paid items (${totalPaid} DA)\n'
    '${freeItems.length} free items'
  );
  
} else if (result['status'] == 'error') {
  showError('Error: ${result['message']}');
} else {
  showError('Invalid QR Code');
}
```

**🔄 Real-Time Data Benefits:**
- ✅ Controller sees payments made seconds ago
- ✅ No need for participant to refresh their app
- ✅ No stale data issues
- ✅ Single source of truth: database

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
2. **QR Code Format**: Contains complete JSON with `user_id`, `badge_id`, and `paid_items` array
3. **No Session Selection**: Controller doesn't select a session - they just scan and see ALL items
4. **Payment Status**: All paid items have `payment_status='paid'` and `has_access=True`
5. **Free Items**: Free sessions/items shown to everyone with `is_paid=false`
6. **Item Types**: 
   - `session`: Paid workshops/ateliers
   - `access`: Special access (VIP lounge, backstage, etc.)
   - `room`: Room-specific access
   - `other`: Any other paid items
7. **Currency**: All prices are in DA (Algerian Dinar)
8. **Direct Access**: If participant paid, they enter directly - no grant/deny logic

### Testing Flow:

1. ✅ Participant signs up → Participant profile created
2. ✅ Participant registers for Event A → UserEventAssignment + ParticipantEventRegistration created
3. ✅ Participant pays for Workshop 1 at caisse → CaisseTransaction + SessionAccess created → QR code regenerated
4. ✅ Controller scans participant's badge → Backend returns ALL paid items + free items → Controller displays list
5. ✅ Participant enters directly (no verification needed)

### Alternative: Verify Access Endpoint (Legacy)

**Note:** This endpoint is still available but NOT recommended for the new flow. Use `scan_participant` instead.

**Endpoint:** `POST /api/events/rooms/{room_id}/verify_access/`

This endpoint requires a `session` parameter and performs backend verification. It's designed for session-specific access control, but the new flow uses `scan_participant` which simply displays what's in the QR code.

---

**Last Updated:** April 25, 2026  
**Status:** ✅ Paid Sessions Feature Implemented

---

## 🎯 SUMMARY: How the System Works

### For Participants:
1. **Sign up** in mobile app → Get permanent QR code with `badge_id`
2. **Register for event** on website → Link to event
3. **Pay at caisse** → Items added to database, QR code data updated (same `badge_id`)
4. **Show badge** to controller → Controller sees ALL paid items (fresh from database)

### For Controllers:
1. **Scan participant's QR code** → Extract `user_id` and `badge_id`
2. **Backend queries database** → Fetch ALL paid items from `CaisseTransaction` table
3. **Display results** → Show ALL item types (session, access, dinner, other) + free items
4. **Grant access** → Participant enters directly

### Key Points:
- ✅ **One Badge Forever:** Participant gets ONE permanent QR code with fixed `badge_id`
- ✅ **Real-Time Data:** Controller always sees fresh data from database, not from QR code
- ✅ **All Item Types:** Sessions, access, dinner, other - everything shows when scanning
- ✅ **No Refresh Needed:** Participant doesn't need to refresh app after payment
- ✅ **Single Source of Truth:** `CaisseTransaction` table in database

### Data Flow:
```
Participant pays at caisse (10:30 AM)
    ↓
CaisseTransaction created in database
    ↓
SessionAccess records created
    ↓
Participant's QR code data updated (badge_id stays same)
    ↓
Controller scans badge (10:45 AM)
    ↓
Backend queries CaisseTransaction table (FRESH DATA)
    ↓
Controller sees payment immediately ✅
```

---

## 🏪 Caisse (Cash Register) System

### Caisse Login

**URL:** `https://makeplus-platform.onrender.com/caisse/`

**Credentials:** Created by event administrators in the dashboard

**Features:**
- Process payments for sessions, workshops, and other items
- Search participants by name, email, or QR code
- View transaction history
- Print participant badges
- Real-time capacity tracking for paid sessions

### Payable Items Management

**Two Types of Payable Items:**

1. **Session-Linked Items** (Automatic)
   - Created automatically when admin marks a session as `is_paid=True`
   - Linked to Session object via `session` field
   - Price comes from session's `price` field
   - Example: "Advanced Python Workshop - 50 DA"

2. **Custom Items** (Manual)
   - Created by admin in dashboard: `/dashboard/events/{event_id}/payable-items/create/`
   - Admin fills form:
     - Item Name (e.g., "Dinner", "Access Badge", "Event T-Shirt")
     - Price in DZD (Algerian Dinars)
     - Item Type: access, dinner, or other
   - NOT linked to any session (`session` field is NULL)
   - Example: "VIP Lounge Access - 100 DA"

### How It Works:

1. **Caisse operator logs in** at `/caisse/`
2. **Search for participant** by name, email, or scan QR code
3. **Select items to purchase** (session-linked + custom items)
4. **Process payment** → Creates transaction + SessionAccess records
5. **QR code automatically regenerated** with new paid items (same `badge_id`)
6. **Print badge** (optional) with updated QR code

### Payment Processing:

When a payment is processed:
- `CaisseTransaction` created with status='completed'
- `SessionAccess` records created for each paid session
- Participant's QR code regenerated with updated `paid_items` array
- Badge can be reprinted with new QR code

### Caisse Dashboard Features:

- View all participants registered for the event
- See which items each participant has already paid for
- Check session capacity (max participants vs. registered)
- View recent transactions
- Transaction statistics (total amount, participant count, etc.)

---
