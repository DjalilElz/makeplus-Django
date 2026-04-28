# Mobile App API Specification

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

### 4.1 Badge Scanning API (Controller - No Room Selection Needed)

**Endpoint:** `POST /api/participants/scan/`

**⚠️ IMPORTANT: Correct URL Path**
- ✅ Correct: `https://makeplus-platform.onrender.com/api/participants/scan/`
- ❌ Wrong: `https://makeplus-platform.onrender.com/api/events/participants/scan/`

**🎯 NEW SIMPLIFIED APPROACH:**
- ✅ Controllers can work in ANY room (no room assignment needed)
- ✅ No need to select room before scanning
- ✅ Returns ALL paid items for the participant
- ✅ Shows sessions from all rooms + access + dinner + other items

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

## 6. Controller Statistics

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
