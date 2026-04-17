# Mobile App API Specification - MakePlus

## Base URL
```
Production: https://makeplus-django-5.onrender.com
Local: http://localhost:8000
```

---

## 🚨 MAJOR UPDATE: New Authentication System

**Breaking Changes:** The authentication system has been completely redesigned. Please read the authentication section carefully.

---

## Authentication & Sign Up

### 1. Sign Up - Request Verification Code
**Endpoint:** `POST /api/auth/signup/request/`

**Description:** Request a verification code to create a new account

**Authentication:** None (public endpoint)

**Request Body:**
```json
{
  "email": "user@example.com",
  "first_name": "John"
}
```

**Success Response:** `200 OK`
```json
{
  "success": true,
  "message": "Verification code sent to your email"
}
```

**Error Response:** `400 Bad Request`
```json
{
  "success": false,
  "message": "Email already registered",
  "wait_seconds": null
}
```

**Rate Limiting:**
- Can only request a new code every 3 minutes
- If too soon, returns `wait_seconds` indicating how long to wait

**Notes:**
- Code expires in 3 minutes
- Code is 6 digits
- Sent via email

---

### 2. Sign Up - Verify Code and Create Account
**Endpoint:** `POST /api/auth/signup/verify/`

**Description:** Verify the code and create user account

**Authentication:** None (public endpoint)

**Request Body:**
```json
{
  "email": "user@example.com",
  "code": "123456",
  "password": "SecurePassword123!",
  "first_name": "John",
  "last_name": "Doe"
}
```

**Success Response:** `201 Created`
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

**Error Responses:**

`400 Bad Request` - Invalid code:
```json
{
  "success": false,
  "message": "Invalid or expired code"
}
```

`400 Bad Request` - Weak password:
```json
{
  "success": false,
  "message": "This password is too common., This password is entirely numeric."
}
```

**Password Requirements:**
- At least 8 characters
- Cannot be too common
- Cannot be entirely numeric
- Cannot be too similar to email

---

### 3. Sign Up - Resend Verification Code
**Endpoint:** `POST /api/auth/signup/resend/`

**Description:** Resend verification code if expired or not received

**Authentication:** None (public endpoint)

**Request Body:**
```json
{
  "email": "user@example.com",
  "first_name": "John"
}
```

**Success Response:** `200 OK`
```json
{
  "success": true,
  "message": "Verification code sent to your email"
}
```

**Error Response:** `400 Bad Request` (Too soon)
```json
{
  "success": false,
  "message": "Please wait 120 seconds before requesting a new code",
  "wait_seconds": 120
}
```

**Notes:**
- Can only resend after 3 minutes from last request
- Use `wait_seconds` to show countdown timer

---

### 4. Login (Get JWT Token)
**Endpoint:** `POST /api/auth/token/`

**Description:** Login with email and password to get JWT tokens

**Authentication:** None (public endpoint)

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
```

**Success Response:** `200 OK`
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
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Tech Conference 2026",
    "start_date": "2026-06-15T09:00:00Z",
    "end_date": "2026-06-17T18:00:00Z",
    "location": "Convention Center",
    "status": "active"
  }
}
```

**Error Response:** `401 Unauthorized`
```json
{
  "detail": "No active account found with the given credentials"
}
```

**Possible Roles:**
- `participant` - Regular attendee (signed up via mobile app)
- `exposant` - Exhibitor
- `gestionnaire_des_salles` - Room manager
- `controlleur_des_badges` - Access controller
- `committee` - Committee member

**Notes:**
- If user hasn't registered for any event, `event` will be `null`
- If user registered for multiple events, returns the most recent active event

---

### 5. Refresh Token
**Endpoint:** `POST /api/auth/token/refresh/`

**Description:** Get a new access token using refresh token

**Authentication:** None (uses refresh token)

**Request Body:**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Success Response:** `200 OK`
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Error Response:** `401 Unauthorized`
```json
{
  "detail": "Token is invalid or expired",
  "code": "token_not_valid"
}
```

---

### 6. Verify Token
**Endpoint:** `POST /api/auth/token/verify/`

**Description:** Check if an access token is valid

**Authentication:** None

**Request Body:**
```json
{
  "token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Success Response:** `200 OK`
```json
{}
```

**Error Response:** `401 Unauthorized`
```json
{
  "detail": "Token is invalid or expired",
  "code": "token_not_valid"
}
```

---

### 7. Get User Profile
**Endpoint:** `GET /api/auth/me/`

**Description:** Get current user profile information

**Authentication:** Required (Bearer token)

**Headers:**
```
Authorization: Bearer <access_token>
```

**Success Response:** `200 OK`
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
    "name": "Tech Conference 2026",
    "status": "active"
  }
}
```

**Error Response:** `401 Unauthorized`
```json
{
  "detail": "Authentication credentials were not provided."
}
```

---

## Events

### 8. List Events
**Endpoint:** `GET /api/events/`

**Description:** Get list of events user has access to

**Authentication:** Required (Bearer token)

**Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `status` (optional): Filter by status (upcoming, active, completed, cancelled)
- `search` (optional): Search by name
- `page` (optional): Page number
- `page_size` (optional): Items per page (default: 20)

**Success Response:** `200 OK`
```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Tech Conference 2026",
      "description": "Annual technology conference",
      "start_date": "2026-06-15T09:00:00Z",
      "end_date": "2026-06-17T18:00:00Z",
      "location": "Convention Center",
      "location_url": "https://maps.google.com/?q=Convention+Center",
      "logo": "https://domain.com/media/events/logos/logo.png",
      "banner": "https://domain.com/media/events/banners/banner.png",
      "status": "active",
      "dynamic_status": "ongoing",
      "total_participants": 250,
      "total_rooms": 5,
      "created_at": "2026-01-15T10:00:00Z"
    }
  ]
}
```

---

### 9. Get Event Details
**Endpoint:** `GET /api/events/{event_id}/`

**Description:** Get detailed information about a specific event

**Authentication:** Required

**Success Response:** `200 OK`
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Tech Conference 2026",
  "description": "Annual technology conference",
  "start_date": "2026-06-15T09:00:00Z",
  "end_date": "2026-06-17T18:00:00Z",
  "location": "Convention Center",
  "location_url": "https://maps.google.com/?q=Convention+Center",
  "location_details": "Main Hall, Floor 3",
  "logo": "https://domain.com/media/events/logos/logo.png",
  "banner": "https://domain.com/media/events/banners/banner.png",
  "status": "active",
  "dynamic_status": "ongoing",
  "total_participants": 250,
  "total_exhibitors": 30,
  "total_rooms": 5,
  "organizer_contact": "organizer@example.com",
  "programme_file": "https://domain.com/media/events/programmes/programme.pdf",
  "guide_file": "https://domain.com/media/events/guides/guide.pdf",
  "created_at": "2026-01-15T10:00:00Z",
  "updated_at": "2026-04-01T14:30:00Z"
}
```

---

## Rooms

### 10. List Rooms
**Endpoint:** `GET /api/rooms/`

**Description:** Get list of rooms

**Authentication:** Required

**Query Parameters:**
- `event` (optional): Filter by event ID
- `is_active` (optional): Filter by active status (true/false)

**Success Response:** `200 OK`
```json
{
  "count": 5,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "room-uuid",
      "event": "event-uuid",
      "event_name": "Tech Conference 2026",
      "name": "Main Hall A",
      "capacity": 200,
      "location": "Floor 3, West Wing",
      "current_participants": 45,
      "is_active": true,
      "session_count": 8,
      "next_session": {
        "id": "session-uuid",
        "title": "AI in Healthcare",
        "start_time": "2026-06-15T14:00:00Z",
        "speaker_name": "Dr. Jane Smith"
      },
      "created_at": "2026-01-15T10:00:00Z"
    }
  ]
}
```

---

## Sessions

### 11. List Sessions
**Endpoint:** `GET /api/sessions/`

**Description:** Get list of sessions

**Authentication:** Required

**Query Parameters:**
- `event` (optional): Filter by event ID
- `room` (optional): Filter by room ID
- `status` (optional): Filter by status (scheduled, live, completed, cancelled)
- `session_type` (optional): Filter by type (conference, atelier, workshop, panel, keynote)

**Success Response:** `200 OK`
```json
{
  "count": 45,
  "next": "http://api/sessions/?page=2",
  "previous": null,
  "results": [
    {
      "id": "session-uuid",
      "event": "event-uuid",
      "room": "room-uuid",
      "room_name": "Main Hall A",
      "title": "AI in Healthcare",
      "description": "Exploring AI applications in modern healthcare",
      "start_time": "2026-06-15T14:00:00Z",
      "end_time": "2026-06-15T15:30:00Z",
      "speaker_name": "Dr. Jane Smith",
      "speaker_title": "Chief AI Officer",
      "speaker_bio": "Leading expert in healthcare AI",
      "speaker_photo_url": "https://domain.com/media/speakers/jane.jpg",
      "theme": "Healthcare Technology",
      "session_type": "conference",
      "status": "scheduled",
      "is_paid": false,
      "price": null,
      "max_participants": null,
      "youtube_live_url": "https://youtube.com/live/xyz",
      "cover_image_url": "https://domain.com/media/sessions/cover.jpg",
      "is_live": false,
      "duration_minutes": 90,
      "created_at": "2026-01-15T10:00:00Z"
    }
  ]
}
```

---

## QR Code Operations

### 12. Generate QR Code
**Endpoint:** `GET /api/qr/generate/`

**Description:** Generate QR code for current user with complete participant information including ALL paid items

**Authentication:** Required

**Success Response:** `200 OK`
```json
{
  "success": true,
  "qr_data": {
    "user_id": 1,
    "badge_id": "USER-1-ABC12345",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "full_name": "John Doe",
    "role": "participant",
    "event": {
      "id": "event-uuid",
      "name": "Tech Conference 2026",
      "start_date": "2026-06-15T09:00:00Z",
      "end_date": "2026-06-17T18:00:00Z"
    },
    "participant_id": "participant-uuid",
    "is_checked_in": true,
    "checked_in_at": "2026-06-15T09:30:00Z",
    "paid_items": [
      {
        "type": "session",
        "id": "session-uuid-1",
        "title": "Advanced Workshop",
        "is_paid": true,
        "payment_status": "paid",
        "amount_paid": 50.0,
        "has_access": true
      },
      {
        "type": "session",
        "id": "session-uuid-2",
        "title": "Free Conference",
        "is_paid": false,
        "payment_status": "free",
        "amount_paid": 0.0,
        "has_access": true
      },
      {
        "type": "room",
        "id": "room-uuid-1",
        "title": "VIP Lounge",
        "is_paid": true,
        "payment_status": "paid",
        "amount_paid": 100.0,
        "has_access": true
      }
    ],
    "total_paid_items": 2,
    "access_summary": {
      "total_sessions": 2,
      "paid_sessions": 1,
      "total_rooms": 1,
      "has_any_paid_access": true
    }
  }
}
```

**Mobile App Usage:**
When controller scans this QR code, display a screen showing:
1. **Participant Info:** Name, email, badge ID
2. **Check-in Status:** ✅ Checked in or ❌ Not checked in
3. **Access Items:** List of all items where `has_access: true`
4. **Simple Display:** Show item name and whether it's paid or free

**Access Logic (Binary - Simple):**
- `has_access: true` → ✅ Show the item (ALLOW ENTRY)
- `has_access: false` → Don't show the item (NO ACCESS)

**Important:**
- If someone paid for something → `has_access: true`
- If something is free → `has_access: true`
- Binary logic: 1 = has access, 0 = no access
- Controller just verifies participant has access
- No action buttons needed - information only

---

## Statistics & Dashboard

### 13. Get My Room Statistics
**Endpoint:** `GET /api/my-room/statistics/`

**Description:** Get statistics for check-ins performed by the current controller

**Important:** Each controller sees only THEIR OWN scans/check-ins, not all check-ins in the event

**Authentication:** Required (Controller or Gestionnaire role)

**Success Response:** `200 OK`
```json
{
  "total_rooms": 3,
  "total_sessions_today": 12,
  "my_check_ins_today": 45,
  "rooms": [
    {
      "id": "room-uuid-1",
      "name": "Salle A",
      "capacity": 200,
      "sessions_today": 4,
      "my_check_ins_today": 18
    },
    {
      "id": "room-uuid-2",
      "name": "Salle B",
      "capacity": 150,
      "sessions_today": 5,
      "my_check_ins_today": 22
    }
  ],
  "role": "controlleur_des_badges",
  "event": {
    "id": "event-uuid",
    "name": "Tech Conference 2026"
  }
}
```

---

## Error Responses

### Common Error Codes:

**400 Bad Request**
```json
{
  "detail": "Invalid request data",
  "errors": {
    "field_name": ["Error message"]
  }
}
```

**401 Unauthorized**
```json
{
  "detail": "Authentication credentials were not provided."
}
```

**403 Forbidden**
```json
{
  "detail": "You do not have permission to perform this action."
}
```

**404 Not Found**
```json
{
  "detail": "Not found."
}
```

**500 Internal Server Error**
```json
{
  "detail": "Internal server error"
}
```

---

## Authentication Flow

### 1. Sign Up (New Users)
```
POST /api/auth/signup/request/
Body: { "email": "user@example.com", "first_name": "John" }
Response: { "success": true, "message": "Verification code sent" }

User receives 6-digit code via email

POST /api/auth/signup/verify/
Body: { "email": "user@example.com", "code": "123456", "password": "SecurePassword123!", "first_name": "John", "last_name": "Doe" }
Response: { "success": true, "access": "...", "refresh": "...", "user": {...} }
```

### 2. Login (Existing Users)
```
POST /api/auth/token/
Body: { "email": "user@example.com", "password": "SecurePassword123!" }
Response: { "access": "...", "refresh": "...", "user": {...}, "role": "...", "event": {...} }
```

### 3. Store Tokens
```dart
// Store both tokens securely
SharedPreferences prefs = await SharedPreferences.getInstance();
await prefs.setString('access_token', response['access']);
await prefs.setString('refresh_token', response['refresh']);
await prefs.setString('user_role', response['role']);
```

### 4. Use Access Token
```dart
// Add to all API requests
headers: {
  'Authorization': 'Bearer $accessToken',
  'Content-Type': 'application/json',
}
```

### 5. Handle Token Expiration
```dart
// If you get 401 error, refresh the token
POST /api/auth/token/refresh/
Body: { "refresh": "stored_refresh_token" }
Response: { "access": "new_access_token" }
```

### 6. Logout
```dart
// Simply delete stored tokens
await prefs.remove('access_token');
await prefs.remove('refresh_token');
```

---

## Important Notes

1. **Sign Up Required**: Users must create an account in the mobile app before registering for events

2. **Password-Based Auth**: All authentication is now password-based (no more code login)

3. **Token Lifetime**: 
   - Access token: 1 hour
   - Refresh token: 7 days

4. **Verification Codes**:
   - Sign up code: 6 digits, expires in 3 minutes
   - Can resend after 3 minutes

5. **Multiple Events**: One user can register for multiple events with the same account

6. **Pagination**: Most list endpoints return paginated results (20 items per page by default)

7. **Date Format**: All dates are in ISO 8601 format with UTC timezone

8. **UUIDs**: Most IDs are UUIDs, not integers

9. **File URLs**: All file URLs (images, PDFs) are absolute URLs

10. **Role Required**: Some endpoints require specific roles

---

## Testing

### Test Credentials (Staff/Controllers)
```
Email: controller1@wemakeplus.com
Password: test123
Role: controlleur_des_badges
```

### Test Sign Up (Participants)
Use any email to create a new account through the sign up flow.

### Test Server
```
https://makeplus-django-5.onrender.com
```

---

**Last Updated:** April 17, 2026  
**API Version:** 2.0  
**Status:** ✅ Production Ready
