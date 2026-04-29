# Mobile App API Specification

## 🎭 User Roles (IMPORTANT)

### Role-Based Requirements

Different user roles have different requirements:

| Role | Room Assignment | Purpose | Endpoints |
|------|----------------|---------|-----------|
| `controlleur_des_badges` | ❌ Not needed | Scan badges anywhere | `/api/participants/scan/` |
| `gestionnaire_des_salles` | ✅ Required | Manage specific room | `/api/user-assignments/` (includes room_assignment) |
| `participant` | ❌ Not needed | Attend event | `/api/auth/me/`, `/api/events/my-ateliers/` |

**⚠️ CRITICAL:**
- **Badge Controllers** (`controlleur_des_badges`) do NOT need room assignment
- **Room Managers** (`gestionnaire_des_salles`) DO need room assignment
- Room assignment is automatically included in `/api/user-assignments/` response
- Check user role before implementing navigation logic

**✅ FIXED:** Room managers can now access their room assignments via API (permission issue resolved)

**See `ROLES_CLARIFICATION.md` for complete implementation guide.**

---

## ⚠️ CRITICAL: QR Code Architecture

### QR Code Contains ONLY Identification Data

The QR code is a **permanent identifier** that never changes. It contains ONLY:

```json
{
  "user_id": 58,
  "badge_id": "USER-58-37F80526",
  "email": "abdeldjalil.elazizi@ensia.edu.dz",
  "first_name": "djalil",
  "last_name": "azizi"
}
```

### QR Code Does NOT Contain:
- ❌ Payment data (`paid_items`)
- ❌ Transaction history
- ❌ Session access information
- ❌ Any dynamic data that changes

### Why This Design?

1. **QR code never changes** - Same badge forever, no reprinting needed
2. **Always fresh data** - Payment data comes from database via API
3. **No stale data** - Controller always sees current payment status
4. **Instant updates** - Payments visible immediately after transaction

### How It Works:

```
┌─────────────────┐
│  Participant    │
│  Scans Badge    │
└────────┬────────┘
         │
         │ QR Code: {"user_id": 58, "badge_id": "USER-58-..."}
         │
         ▼
┌─────────────────┐
│  Controller App │
│  Reads QR Code  │
└────────┬────────┘
         │
         │ POST /api/events/rooms/{room_id}/scan_participant/
         │ Body: {"qr_data": "..."}
         │
         ▼
┌─────────────────┐
│  Backend API    │
│  Extracts       │
│  user_id        │
└────────┬────────┘
         │
         │ SELECT * FROM CaisseTransaction
         │ WHERE participant.user_id = 58
         │ AND status = 'completed'
         │
         ▼
┌─────────────────┐
│  Database       │
│  Returns ALL    │
│  Paid Items     │
└────────┬────────┘
         │
         │ Response: {"paid_items": [...], "free_items": [...]}
         │
         ▼
┌─────────────────┐
│  Controller App │
│  Displays Items │
└─────────────────┘
```

### For Mobile Developers:

**Controller App:**
1. Scan QR code → Get `user_id` and `badge_id`
2. Call API with QR data
3. Display items from API response (NOT from QR code)

**Participant App:**
1. Display QR code with `badge_id` (for scanning)
2. To show paid items, call `GET /api/auth/me/` or `GET /api/events/my-ateliers/`
3. Never store payment data permanently (always fetch fresh)

---

## Base URL
```
Production: https://makeplus-platform.onrender.com
Development: http://localhost:8000
```

## Authentication

All authenticated endpoints require a Bearer token in the Authorization header:
```
Authorization: Bearer <access_token>
```

---

## 1. Sign Up Flow

### 1.1 Request Verification Code

**Endpoint:** `POST /api/events/auth/signup/request/`

**Request:**
```json
{
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "password": "SecurePass123"
}
```

**Response (Success):**
```json
{
  "success": true,
  "message": "Verification code sent to your email"
}
```

**Response (Error):**
```json
{
  "success": false,
  "message": "Email already exists"
}
```

### 1.2 Verify Code and Create Account

**Endpoint:** `POST /api/events/auth/signup/verify/`

**Request:**
```json
{
  "email": "user@example.com",
  "code": "123456"
}
```

**Response (Success):**
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
    "paid_items": [],
    "total_paid_items": 0
  }
}
```

### 1.3 Resend Verification Code

**Endpoint:** `POST /api/events/auth/signup/resend/`

**Request:**
```json
{
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "password": "SecurePass123"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Verification code resent"
}
```

---

## 2. Login

**Endpoint:** `POST /api/events/auth/token/`

**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123"
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
    "name": "TechSummit 2026",
    "status": "active"
  },
  "qr_code": {
    "user_id": 1,
    "badge_id": "USER-1-ABC12345",
    "email": "user@example.com",
    "full_name": "John Doe",
    "role": "participant",
    "paid_items": [
      {
        "type": "session",
        "id": "session-uuid",
        "title": "Workshop A",
        "is_paid": true,
        "payment_status": "paid",
        "amount_paid": 50.00,
        "has_access": true
      }
    ],
    "total_paid_items": 1
  }
}
```

---

## 3. User Profile

**Endpoint:** `GET /api/events/auth/me/`

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
    "name": "TechSummit 2026",
    "status": "active"
  },
  "participant": {
    "id": "participant-uuid",
    "badge_id": "USER-1-ABC12345",
    "role": "participant",
    "qr_code_data": { ... },
    "registered_events": [
      {
        "id": "event-uuid",
        "name": "TechSummit 2026",
        "status": "active",
        "start_date": "2026-06-15T09:00:00Z",
        "end_date": "2026-06-17T18:00:00Z"
      }
    ]
  },
  "qr_code": {
    "user_id": 1,
    "badge_id": "USER-1-ABC12345",
    "paid_items": [ ... ],
    "total_paid_items": 2
  }
}
```

---

## 4. Badge Scanning (Controller)

### 4.1 Badge Scanning API (Badge Controllers Only - No Room Selection Needed)

**Endpoint:** `POST /api/participants/scan/`

**⚠️ IMPORTANT: Correct URL Path**
- ✅ Correct: `https://makeplus-platform.onrender.com/api/participants/scan/`
- ❌ Wrong: `https://makeplus-platform.onrender.com/api/events/participants/scan/`

**🎯 FOR BADGE CONTROLLERS ONLY (`controlleur_des_badges`):**
- ✅ Controllers can work in ANY room (no room assignment needed)
- ✅ No need to select room before scanning
- ✅ Returns ALL paid items for the participant
- ✅ Shows sessions from all rooms + access + dinner + other items

**⚠️ NOT FOR ROOM MANAGERS (`gestionnaire_des_salles`):**
- Room managers still need room assignment
- They use different endpoints for room management
- See `ROLES_CLARIFICATION.md` for details

**🔄 QR Code Contains Only ID Data:** 
- The QR code contains ONLY: `user_id`, `badge_id`, `email`, `first_name`, `last_name`
- The QR code does NOT contain payment data (`paid_items`)
- Backend ALWAYS fetches fresh payment data from database

**Headers:**
```
Authorization: Bearer <controller_token>
Content-Type: application/json
```

**Request:**
```json
{
  "qr_data": "{\"user_id\": 58, \"badge_id\": \"USER-58-37F80526\", \"email\": \"user@example.com\", \"first_name\": \"John\", \"last_name\": \"Doe\"}"
}
```

**How It Works:**
1. Controller scans QR code (gets user_id, badge_id, email, name)
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
      "transaction_date": "2026-04-27T10:30:00Z"
    },
    {
      "type": "dinner",
      "id": "dinner-uuid",
      "title": "Gala Dinner",
      "is_paid": true,
      "payment_status": "paid",
      "amount_paid": 3000.0,
      "has_access": true,
      "transaction_date": "2026-04-27T11:00:00Z"
    },
    {
      "type": "other",
      "id": "other-uuid",
      "title": "Event T-Shirt",
      "is_paid": true,
      "payment_status": "paid",
      "amount_paid": 1000.0,
      "has_access": true,
      "transaction_date": "2026-04-27T11:00:00Z"
    }
  ],
  "total_paid_items": 4,
  "total_amount": 12000.0,
  "has_access": true
}
```

**📦 Item Types Returned:**

1. **Sessions** (`type: "session"`)
   - Workshops/Ateliers from ANY room
   - Includes room name and time details
   - Example: "Intro to AI" in "Conference Hall A"

2. **Access** (`type: "access"`)
   - VIP access, backstage passes, special areas
   - Example: "VIP Lounge Access"

3. **Dinner** (`type: "dinner"`)
   - Meals, lunch, dinner, coffee breaks
   - Example: "Gala Dinner"

4. **Other** (`type: "other"`)
   - Merchandise, materials, certificates
   - Example: "Event T-Shirt"

**Response (Not Registered):**
```json
{
  "status": "error",
  "message": "Participant not registered for this event",
  "participant": {
    "id": "participant-uuid",
    "name": "John Doe",
    "email": "user@example.com",
    "badge_id": "USER-58-37F80526"
  },
  "event": {
    "id": "event-uuid",
    "name": "TechSummit Algeria 2026"
  }
}
```

**Response (Invalid QR):**
```json
{
  "status": "invalid",
  "message": "Invalid QR code format - user_id missing"
}
```

**Response (Not Registered):**
```json
{
  "status": "error",
  "message": "Participant not registered for this event",
  "participant": {
    "id": "participant-uuid",
    "name": "John Doe",
    "email": "user@example.com",
    "badge_id": "USER-58-37F80526"
  },
  "event": {
    "id": "event-uuid",
    "name": "TechSummit Algeria 2026"
  }
}
```

**Response (Invalid QR):**
```json
{
  "status": "invalid",
  "message": "Invalid QR code format - user_id missing"
}
```

**Response (User Not Found):**
```json
{
  "status": "invalid",
  "message": "Invalid QR code - user not found"
}
```

**Key Benefits:**
- ✅ **Always Fresh:** Data comes from database, not QR code
- ✅ **Real-Time:** Controller sees payments immediately after they're made
- ✅ **No Refresh Needed:** Participant doesn't need to refresh their app
- ✅ **Accurate:** No stale data issues
- ✅ **Complete:** Shows ALL item types (session-linked + custom items)
- ✅ **No Room Selection:** Controller can scan in any room

### 4.2 Verify Access (Legacy - Session-Specific)

**Endpoint:** `POST /api/events/rooms/{room_id}/verify_access/`

**Description:** Legacy endpoint for session-specific access verification. Use `scan_participant` instead for the new flow.

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
- `session` is REQUIRED for this endpoint
- This endpoint performs backend verification and creates RoomAccess records
- Use `scan_participant` for simpler flow without session selection

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
  "session": {
    "id": "session-uuid",
    "title": "Advanced Python Workshop",
    "room": "Conference Hall A"
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
  "message": "Payment required for this session",
  "participant": {
    "id": "participant-uuid",
    "name": "John Doe",
    "badge_id": "USER-1-ABC12345"
  },
  "session": {
    "id": "session-uuid",
    "title": "Advanced Python Workshop",
    "price": "50.00",
    "start_time": "2026-06-15T14:00:00Z"
  }
}
```

---

## 5. Get Paid Sessions (Participant)

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

---

## 6. User Assignments (Get User Role and Room Assignment)

**Endpoint:** `GET /api/user-assignments/`

**Description:** Get user's event assignment including role and room assignment (for room managers). The room assignment is automatically included in the response for users with role `gestionnaire_des_salles`.

**Headers:**
```
Authorization: Bearer <token>
```

**Query Parameters:**
- `user` (required): User ID
- `event` (required): Event ID
- `is_active` (optional): Filter by active status (default: true)

**Example Request:**
```
GET /api/user-assignments/?user=41&event=d3c3de4d-a41e-4b69-9bcf-f8b365a72647&is_active=true
```

**Response (Badge Controller):**
```json
{
  "count": 1,
  "results": [
    {
      "id": 40,
      "user": {
        "id": 41,
        "email": "controller1@wemakeplus.com",
        "first_name": "Controller",
        "last_name": "One"
      },
      "event": {
        "id": "d3c3de4d-a41e-4b69-9bcf-f8b365a72647",
        "name": "TechSummit Algeria 2026",
        ...
      },
      "role": "controlleur_des_badges",
      "is_active": true,
      "assigned_at": "2026-04-10T10:00:00Z",
      "metadata": null,
      "room_assignment": null
    }
  ]
}
```

**Response (Room Manager with Room Assignment):**
```json
{
  "count": 1,
  "results": [
    {
      "id": 40,
      "user": {
        "id": 41,
        "email": "gestionaire1@wemakeplus.com",
        "first_name": "gestionaire1",
        "last_name": "gestionaire1"
      },
      "event": {
        "id": "d3c3de4d-a41e-4b69-9bcf-f8b365a72647",
        "name": "TechSummit Algeria 2026",
        ...
      },
      "role": "gestionnaire_des_salles",
      "is_active": true,
      "assigned_at": "2026-04-10T10:00:00Z",
      "metadata": null,
      "room_assignment": {
        "id": 40,
        "room_id": "room-uuid-here",
        "room_name": "salle A",
        "start_time": "2026-06-15T08:00:00Z",
        "end_time": "2026-06-17T22:00:00Z"
      }
    }
  ]
}
```

**Usage in Mobile App:**
```dart
// Single API call gets both role and room assignment
final response = await http.get(
  Uri.parse('$baseUrl/api/user-assignments/?user=$userId&event=$eventId&is_active=true'),
  headers: {
    'Authorization': 'Bearer $token',
  },
);

if (response.statusCode == 200) {
  final data = jsonDecode(response.body);
  if (data['results'] != null && data['results'].isNotEmpty) {
    final userAssignment = data['results'][0];
    final role = userAssignment['role'];
    
    if (role == 'controlleur_des_badges') {
      // No room assignment needed
      navigateToBadgeScanner();
    } else if (role == 'gestionnaire_des_salles') {
      final roomAssignment = userAssignment['room_assignment'];
      if (roomAssignment != null) {
        final roomId = roomAssignment['room_id'];
        final roomName = roomAssignment['room_name'];
        navigateToRoomManagement(roomId, roomName);
      } else {
        showError("No room assigned");
      }
    }
  }
}
```

---

## 8. Room Assignments (Alternative Endpoint - Optional)

**Endpoint:** `GET /api/room-assignments/`

**Description:** Alternative endpoint to get room assignments directly. **Note:** You don't need to use this endpoint if you're using `/api/user-assignments/` which already includes the room assignment.

**Headers:**
```
Authorization: Bearer <token>
```

**Query Parameters:**
- `user` (optional): Filter by user ID
- `event` (optional): Filter by event ID
- `is_active` (optional): Filter by active status (true/false)
- `current` (optional): Get only current assignments (start_time <= now <= end_time)

**Example Request:**
```
GET /api/room-assignments/?user=41&event=d3c3de4d-a41e-4b69-9bcf-f8b365a72647&is_active=true
```

**Response:**
```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 40,
      "user": 41,
      "user_name": "gestionaire1 gestionaire1",
      "room": "room-uuid",
      "room_name": "salle A",
      "event": "event-uuid",
      "event_name": "TechSummit Algeria 2026",
      "role": "gestionnaire_des_salles",
      "start_time": "2026-06-15T08:00:00Z",
      "end_time": "2026-06-17T22:00:00Z",
      "is_active": true,
      "assigned_at": "2026-04-10T10:00:00Z",
      "assigned_by": 1,
      "assigned_by_name": "admin"
    }
  ]
}
```

---

## 9. Controller Statistics

**Endpoint:** `GET /api/events/my-room/statistics/`

**Headers:**
```
Authorization: Bearer <controller_token>
```

**Response:**
```json
{
  "total_rooms": 3,
  "total_sessions_today": 5,
  "my_check_ins_today": 12,
  "rooms": [
    {
      "id": "room-uuid",
      "name": "Conference Hall A",
      "capacity": 100,
      "sessions_today": 2,
      "my_check_ins_today": 5
    }
  ],
  "role": "controlleur_des_badges",
  "event": {
    "id": "event-uuid",
    "name": "TechSummit 2026"
  }
}
```

---

## Key Concepts

### QR Code Structure

The QR code contains complete JSON with all participant information and paid items. **The badge_id remains constant** - only the data inside the QR code is updated when payments are made.

```json
{
  "user_id": 1,
  "badge_id": "USER-1-ABC12345",  // This NEVER changes
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "full_name": "John Doe",
  "role": "participant",
  "event": {
    "id": "event-uuid",
    "name": "TechSummit 2026",
    "start_date": "2026-06-15T09:00:00Z",
    "end_date": "2026-06-17T18:00:00Z"
  },
  "participant_id": "participant-uuid",
  "is_checked_in": false,
  "checked_in_at": null,
  "paid_items": [  // This array is updated when participant pays
    {
      "type": "session",
      "id": "session-uuid",
      "title": "Advanced Python Workshop",
      "is_paid": true,
      "payment_status": "paid",
      "amount_paid": 50.00,
      "has_access": true
    },
    {
      "type": "access",
      "id": "access-uuid",
      "title": "VIP Lounge Access",
      "is_paid": true,
      "payment_status": "paid",
      "amount_paid": 100.00,
      "has_access": true
    },
    {
      "type": "room",
      "id": "room-uuid",
      "title": "Conference Hall A",
      "is_paid": false,
      "payment_status": "free",
      "amount_paid": 0,
      "has_access": true
    }
  ],
  "total_paid_items": 2,
  "access_summary": {
    "total_sessions": 1,
    "paid_sessions": 1,
    "total_rooms": 1,
    "has_any_paid_access": true
  }
}
```

**Important:** The `badge_id` is generated once during signup and never changes. When a participant makes a payment, only the `paid_items` array is updated with new items. The participant keeps the same QR code (same badge_id), but the data inside it is refreshed.

### Payment Flow

1. **Participant pays at caisse** → `SessionAccess` records created with `has_access=True`, `payment_status='paid'`
2. **QR code data updated** → `paid_items` array updated with all paid sessions, access, rooms, etc. **The badge_id stays the same!**
3. **Controller scans badge** → Calls `scan_participant` endpoint → Backend returns ALL paid items + free items
4. **Controller displays list** → Shows participant name, paid items, free items
5. **Participant enters directly** → No verification/grant/deny logic - if paid, they have access

**Important:** The participant receives ONE QR code with a permanent `badge_id` (e.g., "USER-1-ABC12345"). When they make payments, the data inside the QR code is updated (the `paid_items` array grows), but the `badge_id` remains the same. The participant doesn't need to get a new QR code - they can keep using the same one, and it will always show their latest paid items when scanned.

### Item Types

**Payable Items** are things participants can purchase at caisses during check-in.

There are TWO types:

### 1. Session-Linked Items (`type: "session"`)
- **Automatically synced** from sessions marked as paid (`is_paid=True`)
- Linked to a specific `Session` object via `session` field
- Example: "Advanced Python Workshop - 50 DA"
- Created when admin marks a session as paid

### 2. Custom Items (Created by Admin)
Admins can manually create custom payable items from the dashboard:

- **`access`** - VIP access, backstage passes, special areas
  - Example: "VIP Lounge Access - 100 DA"
  
- **`dinner`** - Event meals, lunch, dinner, coffee breaks
  - Example: "Gala Dinner - 75 DA"
  
- **`other`** - Merchandise, materials, certificates, etc.
  - Example: "Event T-Shirt - 25 DA"

**When Controller Scans Badge:**
- ✅ Shows ALL paid items (session-linked + custom items)
- ✅ Shows ALL free sessions in the current room
- ✅ Real-time data from database (always fresh)
- ✅ Includes transaction dates for each payment

**Example Response:**
```json
{
  "paid_items": [
    {"type": "session", "title": "Python Workshop", "amount_paid": 50.00, "transaction_date": "2026-04-24T10:30:00Z"},
    {"type": "access", "title": "VIP Lounge", "amount_paid": 100.00, "transaction_date": "2026-04-24T10:30:00Z"},
    {"type": "dinner", "title": "Gala Dinner", "amount_paid": 75.00, "transaction_date": "2026-04-24T11:00:00Z"},
    {"type": "other", "title": "Event T-Shirt", "amount_paid": 25.00, "transaction_date": "2026-04-24T11:00:00Z"}
  ],
  "free_items": [
    {"type": "session", "title": "Opening Keynote", "amount_paid": 0}
  ]
}
```

**Data Source:**
- ❌ NOT from QR code (may be stale)
- ✅ FROM `CaisseTransaction` table (always fresh)
- ✅ Query: Get all completed transactions for participant
- ✅ Result: ALL items from ALL transactions (session-linked + custom)

### Free vs Paid

- **Free items**: `is_paid=false`, `payment_status='free'`, everyone has access
- **Paid items**: `is_paid=true`, `payment_status='paid'`, only those who paid have access
- **Payment status values**: `paid`, `free`, `pending`, `refunded`

### Badge Scanning Flow

**New Flow (Recommended):**
1. Controller scans QR code
2. Mobile app calls `POST /api/events/rooms/{room_id}/scan_participant/`
3. Backend parses QR code and returns:
   - Participant info
   - ALL paid items from QR code
   - ALL free items in the room
4. Controller displays complete list
5. Participant enters (no verification needed)

**Legacy Flow (Session-Specific):**
1. Controller selects session
2. Controller scans QR code
3. Mobile app calls `POST /api/events/rooms/{room_id}/verify_access/` with `session` parameter
4. Backend checks `SessionAccess` table
5. Returns granted/denied status
6. Creates `RoomAccess` record

**Use the new flow for simpler implementation!**

---

## Mobile App Implementation Guide

### Controller App - Badge Scanning Screen

```dart
class BadgeScannerScreen extends StatefulWidget {
  // ✅ NO ROOM SELECTION NEEDED - Controller can scan in any room
  
  @override
  _BadgeScannerScreenState createState() => _BadgeScannerScreenState();
}

class _BadgeScannerScreenState extends State<BadgeScannerScreen> {
  
  Future<void> scanBadge() async {
    try {
      // 1. Scan QR code
      final qrCode = await BarcodeScanner.scan();
      
      if (qrCode.isEmpty) return;
      
      // 2. Call scan_participant endpoint (fetches FRESH data from database)
      // ✅ NO ROOM ID NEEDED - Works for any room
      final response = await http.post(
        Uri.parse('$baseUrl/api/participants/scan/'),
        headers: {
          'Authorization': 'Bearer $controllerToken',
          'Content-Type': 'application/json',
        },
        body: jsonEncode({'qr_data': qrCode}),
      );
      
      final result = jsonDecode(response.body);
      
      // 3. Handle response
      if (result['status'] == 'success') {
        _showAccessGranted(result);
      } else if (result['status'] == 'error') {
        _showError(result['message']);
      } else {
        _showError('Invalid QR code');
      }
      
    } catch (e) {
      _showError('Scan failed: $e');
    }
  }
  
  void _showAccessGranted(Map<String, dynamic> result) {
    final participant = result['participant'];
    final paidItems = result['paid_items'] ?? [];
    final event = result['event'];
    final totalAmount = result['total_amount'] ?? 0.0;
    
    // Group paid items by type
    final sessions = paidItems.where((i) => i['type'] == 'session').toList();
    final access = paidItems.where((i) => i['type'] == 'access').toList();
    final dinners = paidItems.where((i) => i['type'] == 'dinner').toList();
    final others = paidItems.where((i) => i['type'] == 'other').toList();
    
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('✅ Access Granted'),
        content: SingleChildScrollView(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisSize: MainAxisSize.min,
            children: [
              // Participant info
              Text('Name: ${participant['name']}',
                style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
              Text('Email: ${participant['email']}'),
              Text('Badge: ${participant['badge_id']}'),
              Text('Event: ${event['name']}',
                style: TextStyle(color: Colors.blue)),
              
              SizedBox(height: 16),
              
              // Paid Workshops (with room info)
              if (sessions.isNotEmpty) ...[
                Text('Paid Workshops:', style: TextStyle(fontWeight: FontWeight.bold)),
                ...sessions.map((item) {
                  final sessionDetails = item['session_details'];
                  final roomName = sessionDetails?['room'] ?? 'Unknown Room';
                  return Padding(
                    padding: EdgeInsets.only(left: 8, top: 4),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text('✅ ${item['title']} (${item['amount_paid']} DA)'),
                        Text('   Room: $roomName', 
                          style: TextStyle(fontSize: 12, color: Colors.grey)),
                      ],
                    ),
                  );
                }),
                SizedBox(height: 8),
              ],
              
              // Access Passes
              if (access.isNotEmpty) ...[
                Text('Access Passes:', style: TextStyle(fontWeight: FontWeight.bold)),
                ...access.map((item) => Padding(
                  padding: EdgeInsets.only(left: 8, top: 4),
                  child: Text('✅ ${item['title']} (${item['amount_paid']} DA)'),
                )),
                SizedBox(height: 8),
              ],
              
              // Meals
              if (dinners.isNotEmpty) ...[
                Text('Meals:', style: TextStyle(fontWeight: FontWeight.bold)),
                ...dinners.map((item) => Padding(
                  padding: EdgeInsets.only(left: 8, top: 4),
                  child: Text('✅ ${item['title']} (${item['amount_paid']} DA)'),
                )),
                SizedBox(height: 8),
              ],
              
              // Other Items
              if (others.isNotEmpty) ...[
                Text('Other Items:', style: TextStyle(fontWeight: FontWeight.bold)),
                ...others.map((item) => Padding(
                  padding: EdgeInsets.only(left: 8, top: 4),
                  child: Text('✅ ${item['title']} (${item['amount_paid']} DA)'),
                )),
                SizedBox(height: 8),
              ],
              
              SizedBox(height: 12),
              
              // Summary
              Container(
                padding: EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: Colors.green.shade50,
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Summary:', style: TextStyle(fontWeight: FontWeight.bold)),
                    Text('${paidItems.length} paid items'),
                    Text('Total: $totalAmount DA',
                      style: TextStyle(fontWeight: FontWeight.bold, color: Colors.green)),
                  ],
                ),
              ),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: Text('OK'),
          ),
        ],
      ),
    );
  }
  
  void _showError(String message) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('❌ Access Denied'),
        content: Text(message),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: Text('OK'),
          ),
        ],
      ),
    );
  }
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Scan Badge - Any Room'),
      ),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.qr_code_scanner, size: 100, color: Colors.blue),
            SizedBox(height: 24),
            Text('🔄 Real-Time Data',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
            Text('Always fetches fresh data from database',
              style: TextStyle(color: Colors.grey)),
            SizedBox(height: 8),
            Text('✅ Works in Any Room',
              style: TextStyle(fontSize: 14, color: Colors.green)),
            Text('No room selection needed',
              style: TextStyle(color: Colors.grey)),
            SizedBox(height: 24),
            ElevatedButton.icon(
              onPressed: scanBadge,
              icon: Icon(Icons.camera_alt),
              label: Text('Scan QR Code'),
              style: ElevatedButton.styleFrom(
                padding: EdgeInsets.symmetric(horizontal: 32, vertical: 16),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
```

**🔄 Real-Time Data Benefits:**
- ✅ Controller sees payments made seconds ago
- ✅ No need for participant to refresh their app
- ✅ No stale data issues
- ✅ Single source of truth: database
- ✅ Shows ALL item types (session, access, dinner, other)
- ✅ Works in any room - no room selection neededr sees payments made seconds ago
- ✅ No need for participant to refresh their app
- ✅ No stale data issues
- ✅ Single source of truth: database
- ✅ Shows ALL item types (session, access, dinner, other)

### Participant App - View Paid Sessions

```dart
class MyPaidSessionsScreen extends StatefulWidget {
  @override
  _MyPaidSessionsScreenState createState() => _MyPaidSessionsScreenState();
}

class _MyPaidSessionsScreenState extends State<MyPaidSessionsScreen> {
  List<dynamic> paidSessions = [];
  bool isLoading = true;
  
  @override
  void initState() {
    super.initState();
    _loadPaidSessions();
  }
  
  Future<void> _loadPaidSessions() async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/api/events/my-ateliers/'),
        headers: {
          'Authorization': 'Bearer $participantToken',
        },
      );
      
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        setState(() {
          paidSessions = data['results'];
          isLoading = false;
        });
      }
    } catch (e) {
      setState(() => isLoading = false);
      _showError('Failed to load sessions: $e');
    }
  }
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('My Paid Sessions'),
      ),
      body: isLoading
        ? Center(child: CircularProgressIndicator())
        : paidSessions.isEmpty
          ? Center(child: Text('No paid sessions yet'))
          : ListView.builder(
              itemCount: paidSessions.length,
              itemBuilder: (context, index) {
                final session = paidSessions[index];
                return Card(
                  margin: EdgeInsets.all(8),
                  child: ListTile(
                    leading: Icon(Icons.check_circle, color: Colors.green, size: 40),
                    title: Text(session['title'],
                      style: TextStyle(fontWeight: FontWeight.bold)),
                    subtitle: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text('Room: ${session['room']['name']}'),
                        Text('Paid: ${session['amount_paid']} DA',
                          style: TextStyle(color: Colors.green)),
                        Text('Start: ${_formatDate(session['start_time'])}'),
                      ],
                    ),
                    trailing: Icon(Icons.arrow_forward_ios),
                    onTap: () => _showSessionDetails(session),
                  ),
                );
              },
            ),
    );
  }
  
  String _formatDate(String isoDate) {
    final date = DateTime.parse(isoDate);
    return '${date.day}/${date.month}/${date.year} ${date.hour}:${date.minute.toString().padLeft(2, '0')}';
  }
  
  void _showSessionDetails(Map<String, dynamic> session) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(session['title']),
        content: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(session['description'] ?? 'No description'),
            SizedBox(height: 16),
            Text('Room: ${session['room']['name']}'),
            Text('Start: ${_formatDate(session['start_time'])}'),
            Text('End: ${_formatDate(session['end_time'])}'),
            SizedBox(height: 8),
            Text('Amount Paid: ${session['amount_paid']} DA',
              style: TextStyle(fontWeight: FontWeight.bold, color: Colors.green)),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: Text('Close'),
          ),
        ],
      ),
    );
  }
  
  void _showError(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message)),
    );
  }
}
```

---

## Error Codes

- `400` - Bad Request (invalid data)
- `401` - Unauthorized (invalid/missing token)
- `403` - Forbidden (not registered for event)
- `404` - Not Found (user/participant not found)
- `500` - Internal Server Error

---

## Currency

All prices are in **DA (Algerian Dinar)**.

---

**Last Updated:** April 25, 2026  
**Version:** 2.1

---

## 🎯 SUMMARY: System Architecture

### Real-Time Data Flow

**Payment Processing:**
```
1. Participant pays at caisse
   ↓
2. CaisseTransaction created (status='completed')
   ↓
3. SessionAccess records created (has_access=True)
   ↓
4. Participant's QR code data updated (badge_id stays same)
```

**Badge Scanning:**
```
1. Controller scans QR code
   ↓
2. Backend extracts user_id (identification only)
   ↓
3. Backend queries CaisseTransaction table (FRESH DATA)
   ↓
4. Backend returns ALL paid items from database
   ↓
5. Controller displays real-time list
```

### Key Principles

1. **QR Code Purpose:** Identification only (`user_id`, `badge_id`)
2. **Data Source:** Database (`CaisseTransaction` table), NOT QR code
3. **Item Types:** session, access, dinner, other
4. **Badge ID:** Permanent, never changes
5. **Real-Time:** Controller always sees latest payments

### Why This Architecture?

**Problem:** QR code stored in participant's app can be stale after payment

**Solution:** 
- QR code used for identification only
- Backend queries database for fresh data
- Controller always sees latest payments
- No need for participant to refresh app

**Benefits:**
- ✅ Real-time accuracy
- ✅ No stale data issues
- ✅ Single source of truth
- ✅ Better user experience


---

## 7. Controller Statistics (Updated)

### 7.1 Get Controller Statistics

**Endpoint:** `GET /api/my-room/statistics/`

**🆕 NEW: Automatic Scan Logging**

The backend now automatically saves a log record every time a controller scans a badge. The statistics endpoint returns these logs without any changes needed in your mobile app!

**Headers:**
```
Authorization: Bearer <controller_token>
```

**Response:**
```json
{
  "total_rooms": 3,
  "total_sessions_today": 5,
  "my_check_ins_today": 12,
  "successful_scans_today": 10,
  "recent_scans": [
    {
      "id": 1,
      "participant": {
        "user_id": 58,
        "name": "djalil azizi",
        "email": "abdeldjalil.elazizi@ensia.edu.dz",
        "badge_id": "USER-58-37F80526"
      },
      "scanned_at": "2026-04-28T10:30:00Z",
      "status": "success",
      "error_message": null,
      "total_paid_items": 4,
      "total_amount": 12000.0
    },
    {
      "id": 2,
      "participant": {
        "user_id": 59,
        "name": "John Doe",
        "email": "john@example.com",
        "badge_id": "USER-59-ABC12345"
      },
      "scanned_at": "2026-04-28T10:25:00Z",
      "status": "not_registered",
      "error_message": "Participant not registered for this event",
      "total_paid_items": 0,
      "total_amount": 0
    },
    {
      "id": 3,
      "participant": {
        "user_id": 60,
        "name": "Jane Smith",
        "email": "jane@example.com",
        "badge_id": "USER-60-XYZ98765"
      },
      "scanned_at": "2026-04-28T10:20:00Z",
      "status": "success",
      "error_message": null,
      "total_paid_items": 2,
      "total_amount": 8000.0
    }
  ],
  "role": "controlleur_des_badges",
  "event": {
    "id": "d3c3de4d-a41e-4b69-9bcf-f8b365a72647",
    "name": "TechSummit Algeria 2026"
  }
}
```

**Response Fields:**

**Existing Fields:**
- `total_rooms`: Number of active rooms in the event
- `total_sessions_today`: Number of sessions scheduled today
- `my_check_ins_today`: Total scans performed by this controller today
- `role`: Controller's role
- `event`: Event information

**🆕 NEW Fields:**
- `successful_scans_today`: Count of successful scans today (status='success')
- `recent_scans`: Array of last 50 scans with full details

**Scan Object Structure:**
- `id`: Unique scan log ID
- `participant`: Object with participant details
  - `user_id`: Participant's user ID
  - `name`: Participant's full name
  - `email`: Participant's email
  - `badge_id`: Participant's badge ID
- `scanned_at`: ISO 8601 timestamp of when scan occurred
- `status`: Scan status
  - `"success"`: Scan successful, participant registered
  - `"not_registered"`: Participant not registered for event
  - `"error"`: Other error occurred
- `error_message`: Error details if scan failed (null if successful)
- `total_paid_items`: Number of paid items at scan time
- `total_amount`: Total amount paid at scan time (in DA)

**Status Values:**
- `success`: Participant scanned successfully
- `not_registered`: Participant not registered for this event
- `error`: Other error (invalid QR, network issue, etc.)

---

## 8. Automatic Scan Logging

### How It Works

**No Changes Needed in Mobile App!** 🎉

The backend automatically logs every scan when you call `POST /api/participants/scan/`. Your existing code will automatically benefit from this feature.

**Flow:**
```
1. Controller scans QR code
   ↓
2. Mobile app calls: POST /api/participants/scan/
   ↓
3. Backend:
   - Returns participant data (existing)
   - Saves scan log to database (NEW - automatic)
   ↓
4. Mobile app shows dialog
   ↓
5. Stats page calls: GET /api/my-room/statistics/
   ↓
6. Backend returns saved scans from database
   ↓
7. Mobile app displays scan history
```

**What Gets Logged:**

Every scan (successful or failed) is automatically logged with:
- Controller who scanned
- Event context
- Participant info (user_id, badge_id, name, email)
- Scan timestamp
- Status (success/error/not_registered)
- Error message (if failed)
- Payment info at scan time (total_paid_items, total_amount)

**Benefits:**
- ✅ Automatic - no extra API calls needed
- ✅ Real-time statistics
- ✅ Audit trail for all scans
- ✅ Error tracking
- ✅ No mobile app changes required

---

## 9. Mobile App Implementation

### Statistics Screen

```dart
class ControllerStatisticsScreen extends StatefulWidget {
  @override
  _ControllerStatisticsScreenState createState() => _ControllerStatisticsScreenState();
}

class _ControllerStatisticsScreenState extends State<ControllerStatisticsScreen> {
  Map<String, dynamic>? stats;
  bool isLoading = true;
  
  @override
  void initState() {
    super.initState();
    _loadStatistics();
  }
  
  Future<void> _loadStatistics() async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/api/my-room/statistics/'),
        headers: {
          'Authorization': 'Bearer $controllerToken',
        },
      );
      
      if (response.statusCode == 200) {
        setState(() {
          stats = jsonDecode(response.body);
          isLoading = false;
        });
      }
    } catch (e) {
      setState(() => isLoading = false);
      _showError('Failed to load statistics: $e');
    }
  }
  
  @override
  Widget build(BuildContext context) {
    if (isLoading) {
      return Scaffold(
        appBar: AppBar(title: Text('Statistics')),
        body: Center(child: CircularProgressIndicator()),
      );
    }
    
    if (stats == null) {
      return Scaffold(
        appBar: AppBar(title: Text('Statistics')),
        body: Center(child: Text('Failed to load statistics')),
      );
    }
    
    return Scaffold(
      appBar: AppBar(
        title: Text('My Statistics'),
        actions: [
          IconButton(
            icon: Icon(Icons.refresh),
            onPressed: () {
              setState(() => isLoading = true);
              _loadStatistics();
            },
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _loadStatistics,
        child: ListView(
          padding: EdgeInsets.all(16),
          children: [
            // Summary Cards
            Row(
              children: [
                Expanded(
                  child: _buildStatCard(
                    'Total Scans Today',
                    '${stats!['my_check_ins_today']}',
                    Icons.qr_code_scanner,
                    Colors.blue,
                  ),
                ),
                SizedBox(width: 16),
                Expanded(
                  child: _buildStatCard(
                    'Successful',
                    '${stats!['successful_scans_today']}',
                    Icons.check_circle,
                    Colors.green,
                  ),
                ),
              ],
            ),
            
            SizedBox(height: 24),
            
            // Recent Scans Section
            Text('Recent Scans',
              style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
            SizedBox(height: 12),
            
            // Recent Scans List
            ...((stats!['recent_scans'] ?? []) as List).map((scan) {
              return _buildScanItem(scan);
            }).toList(),
          ],
        ),
      ),
    );
  }
  
  Widget _buildStatCard(String title, String value, IconData icon, Color color) {
    return Card(
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          children: [
            Icon(icon, size: 40, color: color),
            SizedBox(height: 8),
            Text(value,
              style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold)),
            Text(title,
              style: TextStyle(fontSize: 12, color: Colors.grey),
              textAlign: TextAlign.center),
          ],
        ),
      ),
    );
  }
  
  Widget _buildScanItem(Map<String, dynamic> scan) {
    final participant = scan['participant'];
    final status = scan['status'];
    final isSuccess = status == 'success';
    
    return Card(
      margin: EdgeInsets.only(bottom: 8),
      child: ListTile(
        leading: CircleAvatar(
          backgroundColor: isSuccess ? Colors.green : Colors.red,
          child: Icon(
            isSuccess ? Icons.check : Icons.error,
            color: Colors.white,
          ),
        ),
        title: Text(participant['name'],
          style: TextStyle(fontWeight: FontWeight.bold)),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Badge: ${participant['badge_id']}'),
            if (isSuccess)
              Text('${scan['total_paid_items']} items - ${scan['total_amount']} DA',
                style: TextStyle(color: Colors.green))
            else
              Text(scan['error_message'] ?? 'Error',
                style: TextStyle(color: Colors.red)),
          ],
        ),
        trailing: Text(_formatTime(scan['scanned_at']),
          style: TextStyle(fontSize: 12, color: Colors.grey)),
        onTap: () => _showScanDetails(scan),
      ),
    );
  }
  
  String _formatTime(String isoDate) {
    final date = DateTime.parse(isoDate);
    final now = DateTime.now();
    final diff = now.difference(date);
    
    if (diff.inMinutes < 1) return 'Just now';
    if (diff.inMinutes < 60) return '${diff.inMinutes}m ago';
    if (diff.inHours < 24) return '${diff.inHours}h ago';
    return '${date.day}/${date.month} ${date.hour}:${date.minute.toString().padLeft(2, '0')}';
  }
  
  void _showScanDetails(Map<String, dynamic> scan) {
    final participant = scan['participant'];
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Scan Details'),
        content: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: [
            Text('Name: ${participant['name']}',
              style: TextStyle(fontWeight: FontWeight.bold)),
            Text('Email: ${participant['email']}'),
            Text('Badge: ${participant['badge_id']}'),
            SizedBox(height: 12),
            Text('Status: ${scan['status']}'),
            Text('Scanned: ${_formatTime(scan['scanned_at'])}'),
            if (scan['status'] == 'success') ...[
              SizedBox(height: 12),
              Text('Paid Items: ${scan['total_paid_items']}'),
              Text('Total Amount: ${scan['total_amount']} DA',
                style: TextStyle(fontWeight: FontWeight.bold, color: Colors.green)),
            ] else if (scan['error_message'] != null) ...[
              SizedBox(height: 12),
              Text('Error:', style: TextStyle(fontWeight: FontWeight.bold)),
              Text(scan['error_message'],
                style: TextStyle(color: Colors.red)),
            ],
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: Text('Close'),
          ),
        ],
      ),
    );
  }
  
  void _showError(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message)),
    );
  }
}
```

---

## Summary of Changes

### What's New (April 28, 2026)

1. **Automatic Scan Logging**
   - Every scan is automatically logged to database
   - No changes needed in mobile app
   - Works with existing code

2. **Enhanced Statistics Endpoint**
   - New field: `successful_scans_today`
   - New field: `recent_scans` (last 50 scans)
   - Each scan includes full participant and payment details

3. **Scan Status Tracking**
   - Success: Participant scanned successfully
   - Not Registered: Participant not registered for event
   - Error: Other errors

4. **Audit Trail**
   - Complete history of all scans
   - Includes failed scans for troubleshooting
   - Timestamp, participant info, payment details

### Mobile App: No Changes Required

Your existing code will automatically:
- ✅ Log scans when calling `/api/participants/scan/`
- ✅ Receive scan history from `/api/my-room/statistics/`
- ✅ Display the data (if you implement the UI)

---

**Last Updated:** April 28, 2026  
**Version:** 2.2  
**Status:** ✅ Deployed and Ready
