# Mobile App API Specification

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

### 4.1 Scan Participant Badge (Primary Method)

**Endpoint:** `POST /api/events/rooms/{room_id}/scan_participant/`

**Description:** Scan participant's QR code and display ALL paid items (sessions, access, rooms, etc.) + free items. **This endpoint ALWAYS fetches FRESH data from the database**, not from the QR code.

**🔄 Real-Time Data:** The QR code is used ONLY for participant identification (user_id, badge_id). The paid items are ALWAYS fetched from the database in real-time, ensuring the controller sees the latest payments even if the participant hasn't refreshed their app.

**Headers:**
```
Authorization: Bearer <controller_token>
Content-Type: application/json
```

**Request:**
```json
{
  "qr_data": "{\"user_id\": 1, \"badge_id\": \"USER-1-ABC12345\", \"paid_items\": [...]}"
}
```

**Note:** The `paid_items` in the QR code are IGNORED by the backend. The backend uses `user_id` to identify the participant, then queries the `SessionAccess` table for fresh data.

**How It Works:**
1. Controller scans QR code
2. Backend extracts `user_id` from QR code
3. Backend queries `SessionAccess` table for latest paid items
4. Backend returns FRESH data from database
5. Controller displays real-time payment information

**Response (Success):**
```json
{
  "status": "success",
  "participant": {
    "id": "participant-uuid",
    "name": "John Doe",
    "email": "user@example.com",
    "badge_id": "USER-1-ABC12345"
  },
  "room": {
    "id": "room-uuid",
    "name": "Conference Hall A"
  },
  "event": {
    "id": "event-uuid",
    "name": "TechSummit 2026"
  },
  "paid_items": [
    {
      "type": "session",
      "id": "session-uuid-1",
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
  "total_paid_items": 2,
  "total_free_items": 1,
  "has_access": true
}
```

**Key Benefits:**
- ✅ **Always Fresh:** Data comes from database, not QR code
- ✅ **Real-Time:** Controller sees payments immediately after they're made
- ✅ **No Refresh Needed:** Participant doesn't need to refresh their app
- ✅ **Accurate:** No stale data issues

**Response (Not Registered):**
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

**Response (Invalid QR):**
```json
{
  "status": "invalid",
  "message": "Invalid QR code format"
}
```

**Response (User Not Found):**
```json
{
  "status": "invalid",
  "message": "Invalid QR code - user not found"
}
```

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

- **session**: Paid workshops/ateliers (e.g., "Advanced Python Workshop - 50 DA")
- **access**: Special access (e.g., "VIP Lounge Access - 100 DA")
- **room**: Room-specific access (e.g., "Conference Hall A - Free")
- **other**: Any other paid items

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
  final String roomId;
  final String roomName;
  
  @override
  _BadgeScannerScreenState createState() => _BadgeScannerScreenState();
}

class _BadgeScannerScreenState extends State<BadgeScannerScreen> {
  
  Future<void> scanBadge() async {
    try {
      // 1. Scan QR code
      final qrCode = await BarcodeScanner.scan();
      
      if (qrCode.isEmpty) return;
      
      // 2. Call scan_participant endpoint
      final response = await http.post(
        Uri.parse('$baseUrl/api/events/rooms/${widget.roomId}/scan_participant/'),
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
    final freeItems = result['free_items'] ?? [];
    
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
              
              SizedBox(height: 16),
              
              // Paid items
              if (paidItems.isNotEmpty) ...[
                Text('Paid Items:', style: TextStyle(fontWeight: FontWeight.bold)),
                ...paidItems.map((item) => Padding(
                  padding: EdgeInsets.only(left: 8, top: 4),
                  child: Text('✅ ${item['title']} (${item['amount_paid']} DA)'),
                )),
                SizedBox(height: 8),
              ],
              
              // Free items
              if (freeItems.isNotEmpty) ...[
                Text('Free Items:', style: TextStyle(fontWeight: FontWeight.bold)),
                ...freeItems.map((item) => Padding(
                  padding: EdgeInsets.only(left: 8, top: 4),
                  child: Text('🆓 ${item['title']} (Free)'),
                )),
              ],
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
        title: Text('Scan Badge - ${widget.roomName}'),
      ),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.qr_code_scanner, size: 100, color: Colors.blue),
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

**Last Updated:** April 24, 2026  
**Version:** 2.0
