# Mobile App API Specification - MakePlus

## Base URL
```
Production: https://makeplus-django-5.onrender.com
Local: http://localhost:8000
```

---

## ⚠️ IMPORTANT NOTES FOR MOBILE DEVELOPER

### What's Available:
1. ✅ **Login** - JWT token authentication with email/password
2. ✅ **Token Refresh** - Refresh expired access tokens
3. ✅ **Token Verify** - Verify if token is valid
4. ✅ **Event Management** - List, view events
5. ✅ **Room Management** - List, view rooms
6. ✅ **Session Management** - List, view, manage sessions
7. ✅ **QR Code** - Verify and generate QR codes
8. ✅ **Room Access** - Check-in participants

### What's NOT Available:
1. ❌ **NO Registration/Signup** - Users are created by admins only
2. ❌ **NO Password Reset** - Must be done through admin
3. ❌ **NO Profile Update** - Read-only profile
4. ❌ **NO Change Password** - Not available in mobile app

### User Creation:
- Users are created by event administrators through the dashboard
- Users receive login credentials via email
- Mobile app only handles login, not registration

---

## Authentication

### ⚠️ IMPORTANT: Use JWT Token Endpoint, NOT Login Page

**For Mobile App:** Use `POST /api/auth/token/` (JWT endpoint)  
**NOT:** `/api/auth/login/` (this is a web page for browsers, not an API)

### 1. Login (Get JWT Token)
**Endpoint:** `POST /api/auth/token/`

**Description:** Login with email and password to get JWT tokens

**Authentication:** None (public endpoint)

**Request Body:**
```json
{
  "email": "controller1@wemakeplus.com",
  "password": "test123"
}
```

**Success Response:** `200 OK`
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "email": "controller1@wemakeplus.com",
    "first_name": "Controller",
    "last_name": "One"
  },
  "role": "controller",
  "event": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Tech Conference 2026"
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
- `participant` - Regular attendee
- `exposant` - Exhibitor
- `gestionnaire` - Room manager
- `controller` - Access controller
- `admin` - Administrator

---

### 2. Refresh Token
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

### 3. Verify Token
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

## Events

### 4. List Events
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

### 5. Get Event Details
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

### 6. List Rooms
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

### 7. Get Room Details
**Endpoint:** `GET /api/rooms/{room_id}/`

**Description:** Get detailed information about a specific room

**Authentication:** Required

**Success Response:** `200 OK` (same structure as list item)

---

### 8. Verify Room Access (QR Scan)
**Endpoint:** `POST /api/rooms/{room_id}/verify_access/`

**Description:** Verify if a participant can access a room by scanning QR code

**Authentication:** Required (Controller role)

**Request Body:**
```json
{
  "qr_data": "USER-123-ABC12345",
  "session_id": "session-uuid"
}
```

**Success Response:** `200 OK`
```json
{
  "access_granted": true,
  "participant": {
    "id": "participant-uuid",
    "name": "John Doe",
    "badge_id": "BADGE-001"
  },
  "message": "Access granted"
}
```

**Error Response:** `403 Forbidden`
```json
{
  "access_granted": false,
  "message": "Participant not allowed in this room"
}
```

---

## Sessions

### 9. List Sessions
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

### 10. Get Session Details
**Endpoint:** `GET /api/sessions/{session_id}/`

**Description:** Get detailed information about a specific session

**Authentication:** Required

**Success Response:** `200 OK` (same structure as list item)

---

### 11. Start Session (Mark as Live)
**Endpoint:** `POST /api/sessions/{session_id}/start/`

**Description:** Mark session as live/in-progress

**Authentication:** Required (Gestionnaire or Admin role)

**Request Body:** None

**Success Response:** `200 OK`
```json
{
  "message": "Session marked as live",
  "session": {
    "id": "session-uuid",
    "status": "live",
    "is_live": true
  }
}
```

---

### 12. End Session (Mark as Completed)
**Endpoint:** `POST /api/sessions/{session_id}/end/`

**Description:** Mark session as completed

**Authentication:** Required (Gestionnaire or Admin role)

**Request Body:** None

**Success Response:** `200 OK`
```json
{
  "message": "Session marked as completed",
  "session": {
    "id": "session-uuid",
    "status": "completed",
    "is_live": false
  }
}
```

---

## QR Code Operations

### 13. Verify QR Code
**Endpoint:** `POST /api/qr/verify/`

**Description:** Verify a participant's QR code for room access

**Authentication:** Required (Controller role)

**Request Body:**
```json
{
  "qr_data": "USER-123-ABC12345",
  "room_id": "room-uuid",
  "session_id": "session-uuid"
}
```

**Success Response:** `200 OK`
```json
{
  "valid": true,
  "participant": {
    "id": "participant-uuid",
    "name": "John Doe",
    "badge_id": "BADGE-001",
    "has_access": true
  },
  "message": "Access granted"
}
```

**Error Response:** `400 Bad Request`
```json
{
  "valid": false,
  "message": "Invalid QR code or participant not found"
}
```

---

### 14. Generate QR Code
**Endpoint:** `GET /api/qr/generate/`

**Description:** Generate QR code for current user

**Authentication:** Required

**Success Response:** `200 OK`
```json
{
  "success": true,
  "qr_data": {
    "user_id": 1,
    "badge_id": "USER-1-ABC12345"
  }
}
```

---

## Room Access & Check-ins

### 15. List Room Access Logs
**Endpoint:** `GET /api/room-access/`

**Description:** Get room access/check-in history

**Authentication:** Required

**Query Parameters:**
- `room` (optional): Filter by room ID
- `participant` (optional): Filter by participant ID
- `status` (optional): Filter by status (granted, denied)

**Success Response:** `200 OK`
```json
{
  "count": 150,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "access-uuid",
      "participant": "participant-uuid",
      "participant_name": "John Doe",
      "room": "room-uuid",
      "room_name": "Main Hall A",
      "session": "session-uuid",
      "session_title": "AI in Healthcare",
      "accessed_at": "2026-06-15T14:05:00Z",
      "verified_by": 2,
      "verified_by_name": "Jane Controller",
      "status": "granted",
      "denial_reason": null
    }
  ]
}
```

---

### 16. Create Room Access Log
**Endpoint:** `POST /api/room-access/`

**Description:** Log a room access attempt (check-in)

**Authentication:** Required (Controller role)

**Request Body:**
```json
{
  "participant": "participant-uuid",
  "room": "room-uuid",
  "session": "session-uuid",
  "status": "granted"
}
```

**Success Response:** `201 Created`
```json
{
  "id": "access-uuid",
  "participant": "participant-uuid",
  "room": "room-uuid",
  "session": "session-uuid",
  "status": "granted",
  "accessed_at": "2026-06-15T14:05:00Z",
  "verified_by": 2
}
```

---

## Session Access (Paid Sessions)

### 20. List My Session Access
**Endpoint:** `GET /api/session-access/`

**Description:** Get list of sessions the current user has access to (including paid sessions)

**Authentication:** Required

**Query Parameters:**
- `participant` (optional): Filter by participant ID
- `session` (optional): Filter by session ID
- `payment_status` (optional): Filter by payment status (pending, paid, free)
- `has_access` (optional): Filter by access status (true/false)

**Success Response:** `200 OK`
```json
{
  "count": 10,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "access-uuid",
      "participant": "participant-uuid",
      "participant_name": "John Doe",
      "session": "session-uuid",
      "session_title": "Advanced Workshop",
      "session_type": "atelier",
      "has_access": true,
      "payment_status": "paid",
      "paid_at": "2026-06-10T10:00:00Z",
      "amount_paid": 50.00,
      "created_at": "2026-06-10T10:00:00Z"
    },
    {
      "id": "access-uuid-2",
      "participant": "participant-uuid",
      "participant_name": "John Doe",
      "session": "session-uuid-2",
      "session_title": "Free Conference",
      "session_type": "conference",
      "has_access": true,
      "payment_status": "free",
      "paid_at": null,
      "amount_paid": 0.00,
      "created_at": "2026-06-10T10:00:00Z"
    }
  ]
}
```

**Payment Status Values:**
- `pending` - Payment not yet completed
- `paid` - Payment completed, access granted
- `free` - Free session, no payment required

---

### 21. Get Session Access Details
**Endpoint:** `GET /api/session-access/{access_id}/`

**Description:** Get detailed information about a specific session access

**Authentication:** Required

**Success Response:** `200 OK` (same structure as list item)

---

### 22. Check Session Access
**Endpoint:** `GET /api/session-access/?participant={participant_id}&session={session_id}`

**Description:** Check if a participant has access to a specific session

**Authentication:** Required

**Success Response:** `200 OK`
```json
{
  "count": 1,
  "results": [
    {
      "id": "access-uuid",
      "participant": "participant-uuid",
      "session": "session-uuid",
      "has_access": true,
      "payment_status": "paid",
      "amount_paid": 50.00
    }
  ]
}
```

**No Access Response:** `200 OK`
```json
{
  "count": 0,
  "results": []
}
```

---

## Participants

### 17. List Participants
**Endpoint:** `GET /api/participants/`

**Description:** Get list of participants

**Authentication:** Required

**Query Parameters:**
- `event` (optional): Filter by event ID
- `is_checked_in` (optional): Filter by check-in status (true/false)

**Success Response:** `200 OK`
```json
{
  "count": 250,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "participant-uuid",
      "user": {
        "id": 1,
        "email": "john@example.com",
        "first_name": "John",
        "last_name": "Doe"
      },
      "event": "event-uuid",
      "badge_id": "BADGE-001",
      "qr_code_data": {
        "user_id": 1,
        "badge_id": "USER-1-ABC12345"
      },
      "is_checked_in": true,
      "checked_in_at": "2026-06-15T09:30:00Z",
      "created_at": "2026-01-15T10:00:00Z"
    }
  ]
}
```

**Note:** To get participant's session access (paid sessions), use `/api/session-access/?participant={participant_id}`

---

### 18. Get Participant Details
**Endpoint:** `GET /api/participants/{participant_id}/`

**Description:** Get detailed information about a specific participant

**Authentication:** Required

**Success Response:** `200 OK` (same structure as list item)

---

## Statistics & Dashboard

### 25. Get Dashboard Statistics
**Endpoint:** `GET /api/dashboard/stats/`

**Description:** Get dashboard statistics for current user based on their role

**Authentication:** Required

**Success Response:** `200 OK`
```json
{
  "role": "controller",
  "event": {
    "id": "event-uuid",
    "name": "Tech Conference 2026",
    "status": "active"
  },
  "check_ins_today": 45,
  "total_participants": 250,
  "total_rooms": 5
}
```

**Role-Specific Fields:**
- **Controller:** `check_ins_today`
- **Gestionnaire:** `assigned_rooms`
- **Exposant:** `total_scans`

---

### 26. Get My Room Statistics
**Endpoint:** `GET /api/my-room/statistics/`

**Description:** Get statistics for rooms assigned to current user (controller/gestionnaire only)

**Authentication:** Required (Controller or Gestionnaire role)

**Success Response:** `200 OK`
```json
{
  "assigned_rooms": 2,
  "total_sessions_today": 6,
  "current_participants": 78,
  "total_check_ins_today": 145,
  "rooms": [
    {
      "id": "room-uuid",
      "name": "Main Hall A",
      "capacity": 200,
      "sessions_today": 3,
      "check_ins_today": 75
    },
    {
      "id": "room-uuid-2",
      "name": "Workshop Room B",
      "capacity": 50,
      "sessions_today": 3,
      "check_ins_today": 70
    }
  ],
  "role": "controller",
  "event": {
    "id": "event-uuid",
    "name": "Tech Conference 2026"
  }
}
```

**Error Response:** `404 Not Found`
```json
{
  "error": "No active event assignment found"
}
```

---

### 27. Get My Events
**Endpoint:** `GET /api/my-events/`

**Description:** Get list of events assigned to current user

**Authentication:** Required

**Success Response:** `200 OK`
```json
{
  "count": 2,
  "results": [
    {
      "assignment_id": "assignment-uuid",
      "role": "controller",
      "event": {
        "id": "event-uuid",
        "name": "Tech Conference 2026",
        "start_date": "2026-06-15T09:00:00Z",
        "end_date": "2026-06-17T18:00:00Z",
        "status": "active"
      },
      "assigned_at": "2026-01-15T10:00:00Z"
    }
  ]
}
```

---

### 28. Get My Ateliers
**Endpoint:** `GET /api/my-ateliers/`

**Description:** Get list of workshops/ateliers user has access to

**Authentication:** Required

**Success Response:** `200 OK`
```json
{
  "count": 3,
  "results": [
    {
      "id": "session-uuid",
      "title": "Advanced Workshop",
      "session_type": "atelier",
      "is_paid": true,
      "price": 50.00,
      "payment_status": "paid",
      "amount_paid": 50.00,
      "start_time": "2026-06-15T14:00:00Z",
      "end_time": "2026-06-15T16:00:00Z"
    }
  ]
}
```

---

## Exposant Scans (Booth Visits)

### 29. List Exposant Scans
**Endpoint:** `GET /api/exposant-scans/`

**Description:** Get list of participant scans by exposants

**Authentication:** Required (Exposant role)

**Query Parameters:**
- `event` (optional): Filter by event ID

**Success Response:** `200 OK`
```json
{
  "count": 50,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "scan-uuid",
      "exposant": "participant-uuid",
      "exposant_name": "Acme Corp Booth",
      "scanned_participant": "participant-uuid-2",
      "scanned_participant_name": "John Doe",
      "scanned_participant_email": "john@example.com",
      "event": "event-uuid",
      "event_name": "Tech Conference 2026",
      "scanned_at": "2026-06-15T11:30:00Z",
      "notes": "Interested in product demo"
    }
  ]
}
```

---

### 30. Create Exposant Scan
**Endpoint:** `POST /api/exposant-scans/`

**Description:** Record a participant scan at exposant booth

**Authentication:** Required (Exposant role)

**Request Body:**
```json
{
  "scanned_participant": "participant-uuid",
  "event": "event-uuid",
  "notes": "Interested in product demo"
}
```

**Success Response:** `201 Created`
```json
{
  "id": "scan-uuid",
  "scanned_participant": "participant-uuid",
  "event": "event-uuid",
  "notes": "Interested in product demo",
  "scanned_at": "2026-06-15T11:30:00Z"
}
```

---

## Paid Sessions - How It Works

### Overview
Some sessions (ateliers/workshops) require payment. The mobile app needs to:
1. Show which sessions are paid (`is_paid: true`)
2. Display the price
3. Check if user has access before allowing entry
4. Show payment status

### Session Fields for Paid Sessions
```json
{
  "id": "session-uuid",
  "title": "Advanced Workshop",
  "session_type": "atelier",
  "is_paid": true,
  "price": 50.00,
  "max_participants": 30,
  "status": "scheduled"
}
```

### Checking User Access to Paid Session

**Step 1: Get user's participant ID**
```
GET /api/participants/?event={event_id}&user={user_id}
```

**Step 2: Check session access**
```
GET /api/session-access/?participant={participant_id}&session={session_id}
```

**Step 3: Verify access**
```json
// Has access
{
  "count": 1,
  "results": [{
    "has_access": true,
    "payment_status": "paid"
  }]
}

// No access
{
  "count": 0,
  "results": []
}
```

### Display Logic in Mobile App

```dart
// Example Flutter code
bool canAccessSession(Session session, List<SessionAccess> userAccess) {
  // Free sessions - everyone can access
  if (!session.isPaid) {
    return true;
  }
  
  // Paid sessions - check if user has paid
  final access = userAccess.firstWhere(
    (a) => a.sessionId == session.id,
    orElse: () => null,
  );
  
  return access != null && access.hasAccess && access.paymentStatus == 'paid';
}

// Display session with payment indicator
Widget buildSessionCard(Session session) {
  return Card(
    child: Column(
      children: [
        Text(session.title),
        if (session.isPaid) ...[
          Chip(
            label: Text('Paid - ${session.price}€'),
            backgroundColor: Colors.orange,
          ),
          if (!userHasAccess(session)) 
            Text('Payment required', style: TextStyle(color: Colors.red)),
        ],
      ],
    ),
  );
}
```

### Payment Status Values

- **`pending`**: User registered but hasn't paid yet
- **`paid`**: User has paid and has access
- **`free`**: Free session, no payment required

### Important Notes

1. **Payment Processing**: Payment is handled outside the mobile app (admin dashboard or external payment system)
2. **Access Control**: Controllers should verify `has_access` before allowing entry
3. **Max Participants**: Some paid sessions have limited capacity (`max_participants`)
4. **Session Types**: Usually `atelier` or `workshop` sessions are paid, `conference` sessions are free

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

### 1. Login
```
POST /api/auth/token/
Body: { "email": "user@example.com", "password": "password" }
Response: { "access": "...", "refresh": "...", "user": {...}, "role": "...", "event": {...} }
```

### 2. Store Tokens
```dart
// Store both tokens securely
SharedPreferences prefs = await SharedPreferences.getInstance();
await prefs.setString('access_token', response['access']);
await prefs.setString('refresh_token', response['refresh']);
await prefs.setString('user_role', response['role']);
```

### 3. Use Access Token
```dart
// Add to all API requests
headers: {
  'Authorization': 'Bearer $accessToken',
  'Content-Type': 'application/json',
}
```

### 4. Handle Token Expiration
```dart
// If you get 401 error, refresh the token
POST /api/auth/token/refresh/
Body: { "refresh": "stored_refresh_token" }
Response: { "access": "new_access_token" }
```

### 5. Logout
```dart
// Simply delete stored tokens
await prefs.remove('access_token');
await prefs.remove('refresh_token');
```

---

## Role-Based Access

### Participant
- View events, rooms, sessions
- Generate own QR code
- View own profile

### Exposant (Exhibitor)
- All Participant permissions
- Scan participant QR codes
- View scan history
- Export scans

### Controller
- All Participant permissions
- Verify participant QR codes
- Log room access
- View access logs

### Gestionnaire (Room Manager)
- All Controller permissions
- Start/end sessions
- View room statistics
- Manage room assignments

### Admin
- All permissions
- Manage events, rooms, sessions
- Manage users and assignments

---

## Important Notes

1. **No Registration**: Users cannot register through the mobile app. They must be created by administrators.

2. **Token Lifetime**: 
   - Access token: 1 hour
   - Refresh token: 7 days

3. **Pagination**: Most list endpoints return paginated results (20 items per page by default)

4. **Date Format**: All dates are in ISO 8601 format with UTC timezone

5. **UUIDs**: Most IDs are UUIDs, not integers

6. **File URLs**: All file URLs (images, PDFs) are absolute URLs

7. **Role Required**: Some endpoints require specific roles. Check the authentication section.

---

## Testing

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

### Swagger Documentation
```
https://makeplus-django-5.onrender.com/swagger/
```
