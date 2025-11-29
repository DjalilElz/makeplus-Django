# QR Code System - Frontend Integration Guide

**Version:** 2.0 (User-Level QR System)  
**Last Updated:** November 29, 2025  
**Target:** Flutter/React Native/Web Frontend  
**Breaking Change:** QR codes are now user-level, not event-level

---

## Table of Contents

1. [System Overview](#system-overview)
2. [What Changed in v2.0](#what-changed-in-v20)
3. [QR Code Data Structure](#qr-code-data-structure)
4. [Access Control System](#access-control-system)
5. [Participant Side Integration](#participant-side-integration)
6. [Controller Side Integration](#controller-side-integration)
7. [API Reference](#api-reference)
8. [Flutter Code Examples](#flutter-code-examples)
9. [UI/UX Guidelines](#uiux-guidelines)
10. [Testing](#testing)

---

## System Overview

### How It Works (v2.0)

```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│   PARTICIPANT   │         │    CONTROLLER    │         │     BACKEND     │
│      APP        │         │       APP        │         │                 │
└────────┬────────┘         └────────┬─────────┘         └────────┬────────┘
         │                           │                            │
         │ 1. Login                  │                            │
         ├──────────────────────────────────────────────────────>│
         │                           │                            │
         │ 2. Get accessible events with SAME QR code for all    │
         │<──────────────────────────────────────────────────────┤
         │    [Event1 {badge: "USER-15-ABC"},                    │
         │     Event2 {badge: "USER-15-ABC"},                    │
         │     Event3 {badge: "USER-15-ABC"}]                    │
         │                           │                            │
         │ 3. Select event           │                            │
         │    (if multiple)          │                            │
         │                           │                            │
         │ 4. Display QR Code        │                            │
         │    (SAME QR for all       │                            │
         │     events)               │                            │
         │                           │                            │
         │                           │ 5. Scan QR Code            │
         │                           │    (get user-level QR)     │
         │<──────────────────────────┤                            │
         │                           │                            │
         │                           │ 6. Verify QR + Check Access│
         │                           ├───────────────────────────>│
         │                           │    POST /api/rooms/{id}/   │
         │                           │         verify_access/     │
         │                           │    {qr_data, session}      │
         │                           │                            │
         │                           │    Backend checks:         │
         │                           │    ✓ Event access?         │
         │                           │    ✓ Room access?          │
         │                           │    ✓ Session paid?         │
         │                           │                            │
         │                           │ 7. Access Decision         │
         │                           │<───────────────────────────┤
         │                           │    {status, participant,   │
         │                           │     access/denial reason}  │
         │                           │                            │
         │                           │ 8. Show Result             │
         │                           │    (Green/Red screen)      │
         │                           │                            │
```

### Key Concepts (v2.0)

- **User-Level QR Code**: ONE QR code per user across ALL events
- **Badge ID Format**: `USER-{user_id}-{8_random_chars}` (e.g., "USER-15-A1B2C3D4")
- **Multi-Level Access Control**: Event → Room → Session (paid ateliers)
- **Event Selection**: Users with multiple events select which one to use
- **Real-time Verification**: Controller scans → Backend checks all access levels → Instant response
- **Audit Trail**: Every scan logged with event context, room, session, and status

---

## What Changed in v2.0

### Before (v1.0)

❌ **Old System:**
- One QR code per (user, event) combination
- QR stored in `Participant.qr_code_data`
- User had different QR codes for different events
- Format: `{"user_id": 15, "event_id": "uuid", "badge_id": "PART-9069"}`

### After (v2.0)

✅ **New System:**
- ONE QR code per user (stored in `UserProfile.qr_code_data`)
- Same QR code works for all events user has access to
- Backend determines event access via `UserEventAssignment`
- Format: `{"user_id": 15, "badge_id": "USER-15-A1B2C3D4"}`

### Migration Impact

**Frontend Changes Required:**
1. ✅ Use `badge.qr_code_data` from login response (same for all events)
2. ✅ Don't expect different QR codes per event
3. ✅ Update QR verification endpoint: `/api/rooms/{room_id}/verify_access/`
4. ✅ Handle new access denial reasons (event access, session payment)

**Benefits:**
- ✅ Simpler UX - one QR code for everything
- ✅ Can print physical badge that works across events
- ✅ Easier event switching - same QR still valid
- ✅ More flexible access control

---

## QR Code Data Structure

### Format (v2.0)

The `qr_code_data` field now contains user-level information:

```json
{
  "user_id": 15,
  "badge_id": "USER-15-A1B2C3D4"
}
```

### Components

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `user_id` | Integer | User's database ID | `15` |
| `badge_id` | String | User's unique badge ID | `"USER-15-A1B2C3D4"` |

### Removed Fields (from v1.0)

| Field | Why Removed |
|-------|-------------|
| `event_id` | Backend determines event from JWT token and room context |

### Badge ID Format

```
USER-{user_id}-{random_8_chars}

Examples:
- USER-15-A1B2C3D4
- USER-42-X9Y8Z7W6
- USER-123-P4Q3R2S1
```

**Generation:**
```python
badge_id = f"USER-{user.id}-{uuid.uuid4().hex[:8].upper()}"
```

---

## Access Control System

### Three-Level Access Verification

```
LEVEL 1: Event Access
    ↓
Does user have access to this event?
Check: UserEventAssignment(user=user, event=event, is_active=True)
    ↓
✓ Yes → Continue
✗ No  → DENY: "No access to this event"

LEVEL 2: Room Access
    ↓
Can user enter this specific room?
Check: Participant.allowed_rooms
    ↓
✓ Empty OR room in list → Continue
✗ Room not allowed      → DENY: "Not authorized for this room"

LEVEL 3: Session Access (Paid Ateliers Only)
    ↓
Has user paid for this session?
Check: SessionAccess(participant=participant, session=session, has_access=True)
    ↓
✓ Free session OR paid → GRANT ACCESS
✗ Unpaid paid session  → DENY: "Payment required"
```

### Access Decision Matrix

| Event Access | Room Access | Session Paid | Result |
|--------------|-------------|--------------|--------|
| ✅ Yes | ✅ Yes | ✅ Yes/Free | ✅ **GRANTED** |
| ✅ Yes | ✅ Yes | ❌ No | ❌ **PAYMENT REQUIRED** (402) |
| ✅ Yes | ❌ No | - | ❌ **ROOM DENIED** (403) |
| ❌ No | - | - | ❌ **EVENT DENIED** (403) |

### HTTP Status Codes

| Code | Status | Meaning |
|------|--------|---------|
| `200` | `granted` | Access granted successfully |
| `402` | `denied` | Payment required for paid atelier |
| `403` | `denied` | No event access or room not authorized |
| `404` | `invalid` | User/participant/session not found |
| `400` | `invalid` | Invalid QR code format |

---

## Participant Side Integration

### Step 1: Login and Get Profile

**Endpoint:** `POST /api/auth/login/`

```json
POST https://makeplus-django-5.onrender.com/api/auth/login/
Content-Type: application/json

{
  "email": "participant.test@startupweek.dz",
  "password": "makeplus2025",
  "event_id": "6442555a-2295-41f7-81ee-0a902a9c4102"
}
```

**Response:**
```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 15,
    "username": "participant_test",
    "email": "participant.test@startupweek.dz",
    "first_name": "Ahmed",
    "last_name": "Benali"
  },
  "event": {
    "id": "6442555a-2295-41f7-81ee-0a902a9c4102",
    "name": "StartupWeek Oran 2025",
    "location": "Oran Convention Center",
    "start_date": "2026-01-26",
    "end_date": "2026-01-31"
  },
  "role": "participant"
}
```

### Step 2: Get Participant Profile with QR Code

**Endpoint:** `GET /api/auth/me/`

```http
GET https://makeplus-django-5.onrender.com/api/auth/me/
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response:**
```json
{
  "id": 15,
  "username": "participant_test",
  "email": "participant.test@startupweek.dz",
  "first_name": "Ahmed",
  "last_name": "Benali",
  "event": {
    "id": "6442555a-2295-41f7-81ee-0a902a9c4102",
    "name": "StartupWeek Oran 2025",
    "location": "Oran Convention Center",
    "start_date": "2026-01-26",
    "end_date": "2026-01-31"
  },
  "role": "participant",
  "participant_profile": {
    "id": "participant-uuid",
    "badge_id": "PART-9069",
    "qr_code_data": "{\"user_id\": 15, \"event_id\": \"6442555a-2295-41f7-81ee-0a902a9c4102\", \"badge_id\": \"PART-9069\"}",
    "is_checked_in": false
  }
}
```

### Step 3: Display QR Code

**Use any QR code library to generate QR image from `qr_code_data`:**

**Flutter:**
```dart
import 'package:qr_flutter/qr_flutter.dart';

// Extract qr_code_data from profile
String qrCodeData = participantProfile['qr_code_data'];
String badgeId = participantProfile['badge_id'];

// Display QR Code
QrImageView(
  data: qrCodeData,
  version: QrVersions.auto,
  size: 250.0,
  backgroundColor: Colors.white,
)

// Display Badge ID below
Text(
  'Badge: $badgeId',
  style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
)
```

**React Native:**
```jsx
import QRCode from 'react-native-qrcode-svg';

const qrCodeData = participantProfile.qr_code_data;
const badgeId = participantProfile.badge_id;

<QRCode
  value={qrCodeData}
  size={250}
  backgroundColor="white"
/>

<Text style={{fontSize: 24, fontWeight: 'bold'}}>
  Badge: {badgeId}
</Text>
```

### Step 4: Participant UI Design

```
┌─────────────────────────────────┐
│         My Badge                │
├─────────────────────────────────┤
│                                 │
│       ┌─────────────┐           │
│       │             │           │
│       │   QR CODE   │           │
│       │    IMAGE    │           │
│       │             │           │
│       └─────────────┘           │
│                                 │
│    Badge: PART-9069             │
│                                 │
│    Ahmed Benali                 │
│    participant.test@...         │
│                                 │
│    Event: StartupWeek Oran 2025 │
│    Dates: Jan 26-31, 2026       │
│                                 │
│    ℹ️ Show this QR code at      │
│       room entrances            │
│                                 │
└─────────────────────────────────┘
```

---

## Controller Side Integration

### Step 1: Login as Controller

**Endpoint:** `POST /api/auth/login/`

```json
POST https://makeplus-django-5.onrender.com/api/auth/login/
Content-Type: application/json

{
  "email": "leila.madani@startupweek.dz",
  "password": "makeplus2025",
  "event_id": "6442555a-2295-41f7-81ee-0a902a9c4102"
}
```

**Response:**
```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 8,
    "username": "startup_controleur",
    "email": "leila.madani@startupweek.dz",
    "first_name": "Leila",
    "last_name": "Madani"
  },
  "event": {
    "id": "6442555a-2295-41f7-81ee-0a902a9c4102",
    "name": "StartupWeek Oran 2025"
  },
  "role": "controlleur_des_badges"
}
```

### Step 2: Get Controller's Assigned Room

**Endpoint:** `GET /api/my-room/statistics/`

This automatically returns the controller's assigned room information.

```http
GET https://makeplus-django-5.onrender.com/api/my-room/statistics/
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response:**
```json
{
  "room": {
    "id": "room-uuid",
    "name": "Hall Exposition",
    "capacity": 500
  },
  "statistics": {
    "total_scans": 45,
    "today_scans": 12,
    "granted": 38,
    "denied": 7,
    "unique_participants": 25,
    "unique_participants_today": 8
  },
  "recent_scans": [...]
}
```

**Extract room_id for verification:**
```dart
String roomId = roomStats['room']['id'];
String roomName = roomStats['room']['name'];
```

### Step 3: Scan QR Code

**Use camera/QR scanner library:**

**Flutter:**
```dart
import 'package:mobile_scanner/mobile_scanner.dart';

MobileScanner(
  onDetect: (capture) {
    final List<Barcode> barcodes = capture.barcodes;
    for (final barcode in barcodes) {
      String? qrData = barcode.rawValue;
      if (qrData != null) {
        // Verify QR code
        verifyQRCode(qrData, roomId);
      }
    }
  },
)
```

**React Native:**
```jsx
import { Camera } from 'react-native-vision-camera';
import { useScanBarcodes, BarcodeFormat } from 'vision-camera-code-scanner';

const { scanBarcodes } = useScanBarcodes([BarcodeFormat.QR_CODE]);

<Camera
  device={device}
  isActive={true}
  frameProcessor={(frame) => {
    'worklet';
    const barcodes = scanBarcodes(frame);
    if (barcodes.length > 0) {
      // Verify QR code
      verifyQRCode(barcodes[0].rawValue, roomId);
    }
  }}
/>
```

### Step 4: Verify QR Code with Backend

**Endpoint:** `POST /api/qr/verify/`

```dart
Future<Map<String, dynamic>> verifyQRCode(String qrData, String roomId) async {
  final response = await http.post(
    Uri.parse('https://makeplus-django-5.onrender.com/api/qr/verify/'),
    headers: {
      'Authorization': 'Bearer $accessToken',
      'Content-Type': 'application/json',
    },
    body: jsonEncode({
      'qr_data': qrData,
      'room_id': roomId,
    }),
  );

  return jsonDecode(response.body);
}
```

**Request:**
```json
POST /api/qr/verify/
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "qr_data": "{\"user_id\": 15, \"event_id\": \"6442555a-2295-41f7-81ee-0a902a9c4102\", \"badge_id\": \"PART-9069\"}",
  "room_id": "room-uuid"
}
```

**Response (Access Granted):**
```json
{
  "status": "granted",
  "message": "Access granted successfully",
  "participant": {
    "id": "participant-uuid",
    "name": "Ahmed Benali",
    "email": "participant.test@startupweek.dz",
    "badge_id": "PART-9069",
    "photo_url": null
  },
  "access": {
    "id": "access-uuid",
    "accessed_at": "2025-11-29T10:30:00Z",
    "room_name": "Hall Exposition"
  }
}
```

**Response (Access Denied):**
```json
{
  "status": "denied",
  "message": "Participant not authorized for this room",
  "participant": {
    "id": "participant-uuid",
    "name": "Ahmed Benali",
    "badge_id": "PART-9069"
  }
}
```

**Response (Invalid QR Code):**
```json
{
  "status": "invalid",
  "message": "Invalid QR code or participant not found"
}
```

### Step 5: Display Verification Result

**Flutter Example:**
```dart
void showVerificationResult(Map<String, dynamic> result) {
  final status = result['status'];
  
  if (status == 'granted') {
    // Show green success screen
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: Colors.green,
        title: Row(
          children: [
            Icon(Icons.check_circle, color: Colors.white, size: 48),
            SizedBox(width: 16),
            Text('ACCESS GRANTED', style: TextStyle(color: Colors.white)),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Name: ${result['participant']['name']}',
                style: TextStyle(color: Colors.white, fontSize: 18)),
            Text('Badge: ${result['participant']['badge_id']}',
                style: TextStyle(color: Colors.white, fontSize: 16)),
            Text('Email: ${result['participant']['email']}',
                style: TextStyle(color: Colors.white, fontSize: 14)),
            SizedBox(height: 12),
            Text('Room: ${result['access']['room_name']}',
                style: TextStyle(color: Colors.white, fontSize: 14)),
            Text('Time: ${formatTime(result['access']['accessed_at'])}',
                style: TextStyle(color: Colors.white, fontSize: 14)),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: Text('OK', style: TextStyle(color: Colors.white)),
          ),
        ],
      ),
    );
  } else if (status == 'denied') {
    // Show red error screen
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: Colors.red,
        title: Row(
          children: [
            Icon(Icons.cancel, color: Colors.white, size: 48),
            SizedBox(width: 16),
            Text('ACCESS DENIED', style: TextStyle(color: Colors.white)),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Name: ${result['participant']['name']}',
                style: TextStyle(color: Colors.white, fontSize: 18)),
            Text('Badge: ${result['participant']['badge_id']}',
                style: TextStyle(color: Colors.white, fontSize: 16)),
            SizedBox(height: 12),
            Text('Reason: ${result['message']}',
                style: TextStyle(color: Colors.white, fontSize: 14)),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: Text('OK', style: TextStyle(color: Colors.white)),
          ),
        ],
      ),
    );
  } else {
    // Invalid QR code
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: Colors.orange,
        title: Row(
          children: [
            Icon(Icons.warning, color: Colors.white, size: 48),
            SizedBox(width: 16),
            Text('INVALID QR CODE', style: TextStyle(color: Colors.white)),
          ],
        ),
        content: Text(
          result['message'] ?? 'QR code is invalid or not recognized',
          style: TextStyle(color: Colors.white, fontSize: 16),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: Text('OK', style: TextStyle(color: Colors.white)),
          ),
        ],
      ),
    );
  }
}
```

### Step 6: Controller UI Design

**Scanner Screen:**
```
┌─────────────────────────────────┐
│    Hall Exposition              │
│    QR Code Scanner              │
├─────────────────────────────────┤
│                                 │
│    ┌─────────────────────┐     │
│    │                     │     │
│    │   CAMERA VIEW       │     │
│    │   WITH SCANNER      │     │
│    │   OVERLAY           │     │
│    │                     │     │
│    └─────────────────────┘     │
│                                 │
│    Point camera at QR code      │
│                                 │
│    Today's Scans: 12            │
│    Total Scans: 45              │
│                                 │
└─────────────────────────────────┘
```

**Success Screen (Green):**
```
┌─────────────────────────────────┐
│    ✅ ACCESS GRANTED             │
├─────────────────────────────────┤
│                                 │
│    Ahmed Benali                 │
│    Badge: PART-9069             │
│    participant.test@...         │
│                                 │
│    Room: Hall Exposition        │
│    Time: 10:30 AM               │
│                                 │
│    [ Scan Next ]                │
│                                 │
└─────────────────────────────────┘
```

**Denied Screen (Red):**
```
┌─────────────────────────────────┐
│    ❌ ACCESS DENIED              │
├─────────────────────────────────┤
│                                 │
│    Ahmed Benali                 │
│    Badge: PART-9069             │
│                                 │
│    Reason:                      │
│    Not authorized for this room │
│                                 │
│    [ Scan Next ]                │
│                                 │
└─────────────────────────────────┘
```

---

## API Reference

### Authentication APIs (v2.0)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/auth/login/` | POST | Login - returns accessible events with user-level QR code |
| `/api/auth/select-event/` | POST | Select event (if user has multiple events) |
| `/api/auth/my-events/` | GET | List all events user has access to |
| `/api/auth/me/` | GET | Get user profile with current event context |
| `/api/auth/logout/` | POST | Logout and blacklist token |

#### Login Response (Single Event)

```json
{
  "access": "jwt_token",
  "refresh": "refresh_token",
  "user": {...},
  "current_event": {
    "id": "event-uuid",
    "name": "StartupWeek Oran 2025",
    "role": "participant",
    "badge": {
      "badge_id": "USER-15-A1B2C3D4",
      "qr_code_data": "{\"user_id\": 15, \"badge_id\": \"USER-15-A1B2C3D4\"}",
      "is_checked_in": false
    }
  },
  "requires_event_selection": false
}
```

#### Login Response (Multiple Events)

```json
{
  "user": {...},
  "requires_event_selection": true,
  "available_events": [
    {
      "id": "event-1-uuid",
      "name": "StartupWeek Oran 2025",
      "role": "participant",
      "badge": {
        "badge_id": "USER-15-A1B2C3D4",
        "qr_code_data": "{\"user_id\": 15, \"badge_id\": \"USER-15-A1B2C3D4\"}"
      }
    },
    {
      "id": "event-2-uuid",
      "name": "Tech Summit Algeria",
      "role": "exposant",
      "badge": {
        "badge_id": "USER-15-A1B2C3D4",
        "qr_code_data": "{\"user_id\": 15, \"badge_id\": \"USER-15-A1B2C3D4\"}"
      }
    }
  ],
  "temp_token": "temporary_jwt_token"
}
```

**Note:** Same QR code (`USER-15-A1B2C3D4`) for all events!

### QR Code APIs (v2.0)

| Endpoint | Method | Description | Required Role |
|----------|--------|-------------|---------------|
| `/api/rooms/{room_id}/verify_access/` | POST | Verify user QR code with multi-level access control | Controller |

#### Verify Access Request

```json
POST /api/rooms/{room_id}/verify_access/
{
  "qr_data": "{\"user_id\": 15, \"badge_id\": \"USER-15-A1B2C3D4\"}",
  "session": "session-uuid"  // Optional: for session-specific verification
}
```

#### Verify Access Response (Granted)

```json
{
  "status": "granted",
  "message": "Access granted successfully",
  "participant": {
    "id": "participant-uuid",
    "name": "Ahmed Benali",
    "email": "participant@example.com",
    "badge_id": "USER-15-A1B2C3D4",
    "photo_url": null
  },
  "access": {
    "id": "access-uuid",
    "accessed_at": "2025-11-29T10:30:00Z",
    "room_name": "Hall Exposition"
  }
}
```

#### Verify Access Response (Denied - No Event Access)

```json
{
  "status": "denied",
  "message": "User does not have access to this event",
  "user": {
    "name": "Ahmed Benali",
    "email": "participant@example.com"
  }
}
```

#### Verify Access Response (Denied - Payment Required)

```json
{
  "status": "denied",
  "message": "Payment required for this atelier",
  "participant": {
    "id": "participant-uuid",
    "name": "Ahmed Benali",
    "badge_id": "USER-15-A1B2C3D4"
  },
  "session": {
    "title": "UX Design Workshop",
    "price": "6000.00"
  }
}
```

### Controller APIs

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/my-room/statistics/` | GET | Get assigned room statistics |

---

## Flutter Code Examples

### Complete Participant Badge Screen

```dart
import 'package:flutter/material.dart';
import 'package:qr_flutter/qr_flutter.dart';

class ParticipantBadgeScreen extends StatelessWidget {
  final Map<String, dynamic> participantProfile;
  final Map<String, dynamic> event;

  const ParticipantBadgeScreen({
    required this.participantProfile,
    required this.event,
  });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('My Badge'),
        backgroundColor: Colors.blue,
      ),
      body: Center(
        child: Padding(
          padding: EdgeInsets.all(24),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              // QR Code
              Container(
                padding: EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(12),
                  boxShadow: [
                    BoxShadow(
                      color: Colors.black26,
                      blurRadius: 10,
                      offset: Offset(0, 4),
                    ),
                  ],
                ),
                child: QrImageView(
                  data: participantProfile['qr_code_data'],
                  version: QrVersions.auto,
                  size: 250,
                  backgroundColor: Colors.white,
                ),
              ),
              
              SizedBox(height: 24),
              
              // Badge ID
              Text(
                'Badge: ${participantProfile['badge_id']}',
                style: TextStyle(
                  fontSize: 28,
                  fontWeight: FontWeight.bold,
                  color: Colors.blue,
                ),
              ),
              
              SizedBox(height: 16),
              
              // Participant Name
              Text(
                participantProfile['user']['first_name'] + ' ' + 
                participantProfile['user']['last_name'],
                style: TextStyle(
                  fontSize: 24,
                  fontWeight: FontWeight.w600,
                ),
              ),
              
              // Email
              Text(
                participantProfile['user']['email'],
                style: TextStyle(
                  fontSize: 16,
                  color: Colors.grey[600],
                ),
              ),
              
              SizedBox(height: 24),
              
              // Event Info
              Container(
                padding: EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: Colors.grey[100],
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Column(
                  children: [
                    Text(
                      event['name'],
                      style: TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.w500,
                      ),
                      textAlign: TextAlign.center,
                    ),
                    SizedBox(height: 8),
                    Text(
                      '${event['start_date']} - ${event['end_date']}',
                      style: TextStyle(
                        fontSize: 14,
                        color: Colors.grey[700],
                      ),
                    ),
                    Text(
                      event['location'],
                      style: TextStyle(
                        fontSize: 14,
                        color: Colors.grey[700],
                      ),
                    ),
                  ],
                ),
              ),
              
              SizedBox(height: 24),
              
              // Instructions
              Container(
                padding: EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.blue[50],
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: Colors.blue[200]!),
                ),
                child: Row(
                  children: [
                    Icon(Icons.info_outline, color: Colors.blue),
                    SizedBox(width: 12),
                    Expanded(
                      child: Text(
                        'Show this QR code at room entrances',
                        style: TextStyle(
                          fontSize: 14,
                          color: Colors.blue[900],
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
```

### Complete Controller Scanner Screen

```dart
import 'package:flutter/material.dart';
import 'package:mobile_scanner/mobile_scanner.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

class ControllerScannerScreen extends StatefulWidget {
  final String accessToken;
  final String roomId;
  final String roomName;

  const ControllerScannerScreen({
    required this.accessToken,
    required this.roomId,
    required this.roomName,
  });

  @override
  _ControllerScannerScreenState createState() =>
      _ControllerScannerScreenState();
}

class _ControllerScannerScreenState extends State<ControllerScannerScreen> {
  MobileScannerController cameraController = MobileScannerController();
  bool isProcessing = false;

  Future<void> verifyQRCode(String qrData) async {
    if (isProcessing) return;
    
    setState(() {
      isProcessing = true;
    });

    try {
      final response = await http.post(
        Uri.parse('https://makeplus-django-5.onrender.com/api/qr/verify/'),
        headers: {
          'Authorization': 'Bearer ${widget.accessToken}',
          'Content-Type': 'application/json',
        },
        body: jsonEncode({
          'qr_data': qrData,
          'room_id': widget.roomId,
        }),
      );

      final result = jsonDecode(response.body);
      
      // Show result dialog
      showVerificationResult(result);
    } catch (e) {
      // Show error
      showErrorDialog('Error verifying QR code: $e');
    } finally {
      setState(() {
        isProcessing = false;
      });
    }
  }

  void showVerificationResult(Map<String, dynamic> result) {
    final status = result['status'];
    Color bgColor;
    IconData icon;
    String title;

    if (status == 'granted') {
      bgColor = Colors.green;
      icon = Icons.check_circle;
      title = 'ACCESS GRANTED';
    } else if (status == 'denied') {
      bgColor = Colors.red;
      icon = Icons.cancel;
      title = 'ACCESS DENIED';
    } else {
      bgColor = Colors.orange;
      icon = Icons.warning;
      title = 'INVALID QR CODE';
    }

    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) => AlertDialog(
        backgroundColor: bgColor,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
        ),
        title: Row(
          children: [
            Icon(icon, color: Colors.white, size: 48),
            SizedBox(width: 16),
            Expanded(
              child: Text(
                title,
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 20,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (result.containsKey('participant')) ...[
              Text(
                result['participant']['name'] ?? '',
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 20,
                  fontWeight: FontWeight.bold,
                ),
              ),
              SizedBox(height: 8),
              Text(
                'Badge: ${result['participant']['badge_id']}',
                style: TextStyle(color: Colors.white, fontSize: 16),
              ),
              if (result['participant']['email'] != null)
                Text(
                  result['participant']['email'],
                  style: TextStyle(color: Colors.white70, fontSize: 14),
                ),
              SizedBox(height: 16),
            ],
            if (status == 'granted' && result.containsKey('access')) ...[
              Text(
                'Room: ${result['access']['room_name']}',
                style: TextStyle(color: Colors.white, fontSize: 14),
              ),
              Text(
                'Time: ${formatTime(result['access']['accessed_at'])}',
                style: TextStyle(color: Colors.white, fontSize: 14),
              ),
            ],
            if (status == 'denied' || status == 'invalid')
              Text(
                result['message'] ?? '',
                style: TextStyle(color: Colors.white, fontSize: 14),
              ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () {
              Navigator.pop(context);
              // Resume scanning
              cameraController.start();
            },
            child: Text(
              'SCAN NEXT',
              style: TextStyle(
                color: Colors.white,
                fontSize: 16,
                fontWeight: FontWeight.bold,
              ),
            ),
          ),
        ],
      ),
    );
  }

  void showErrorDialog(String message) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Error'),
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

  String formatTime(String isoTime) {
    final dateTime = DateTime.parse(isoTime);
    return '${dateTime.hour.toString().padLeft(2, '0')}:${dateTime.minute.toString().padLeft(2, '0')}';
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(widget.roomName),
            Text(
              'QR Code Scanner',
              style: TextStyle(fontSize: 14),
            ),
          ],
        ),
        backgroundColor: Colors.blue,
      ),
      body: Column(
        children: [
          // Camera Scanner
          Expanded(
            flex: 5,
            child: MobileScanner(
              controller: cameraController,
              onDetect: (capture) {
                final List<Barcode> barcodes = capture.barcodes;
                for (final barcode in barcodes) {
                  if (barcode.rawValue != null) {
                    cameraController.stop();
                    verifyQRCode(barcode.rawValue!);
                    break;
                  }
                }
              },
            ),
          ),
          
          // Instructions and Stats
          Expanded(
            flex: 1,
            child: Container(
              color: Colors.grey[100],
              padding: EdgeInsets.all(16),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Text(
                    'Point camera at participant\'s QR code',
                    style: TextStyle(fontSize: 16),
                    textAlign: TextAlign.center,
                  ),
                  SizedBox(height: 16),
                  if (isProcessing)
                    CircularProgressIndicator()
                  else
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceAround,
                      children: [
                        Column(
                          children: [
                            Icon(Icons.qr_code_scanner, color: Colors.blue),
                            Text('Scanning', style: TextStyle(fontSize: 12)),
                          ],
                        ),
                      ],
                    ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  @override
  void dispose() {
    cameraController.dispose();
    super.dispose();
  }
}
```

---

## UI/UX Guidelines

### Participant Badge Screen

✅ **DO:**
- Display QR code prominently (250x250 pixels minimum)
- Show badge ID in large, readable font
- Include participant name and email
- Display event information
- Use white background for QR code
- Add padding around QR code for scanning
- Include instructions ("Show at room entrances")

❌ **DON'T:**
- Make QR code too small (< 200px)
- Use colored backgrounds behind QR code
- Hide participant information
- Auto-rotate the screen during display

### Controller Scanner Screen

✅ **DO:**
- Full-screen camera view for easy scanning
- Show room name prominently
- Display scanning instructions
- Use green for success, red for denied
- Show participant details immediately
- Add sound/vibration feedback
- Auto-resume scanning after verification
- Display today's scan count

❌ **DON'T:**
- Require manual focus or capture button
- Show too many stats during scanning
- Make result dialogs dismissible by tapping outside
- Auto-close result dialogs (require user acknowledgment)

### Color Scheme

- **Success/Granted**: Green (#4CAF50)
- **Denied**: Red (#F44336)
- **Invalid**: Orange (#FF9800)
- **Primary**: Blue (#2196F3)
- **Background**: White/Light Grey

---

## Testing

### Test Credentials (v2.0)

**Single-Event Participant:**
- Email: `participant.test@startupweek.dz`
- Password: `makeplus2025`
- Events: 1 (auto-selected)
- Badge ID: Will be generated as `USER-{id}-{random}`
- Expected: Direct login without event selection

**Multi-Event User (if available):**
- Check with backend admin for test user with multiple event assignments
- Expected: Event selection screen after login
- Expected: Same QR code for all events

**Controller:**
- Email: `leila.madani@startupweek.dz`
- Password: `makeplus2025`
- Event ID: `6442555a-2295-41f7-81ee-0a902a9c4102`
- Assigned Room: Hall Exposition

### Testing Checklist (v2.0)

**Login Flow:**
- [ ] Login with single event → auto-selected, no event selection screen
- [ ] Login with multiple events → shows event list with SAME QR for all
- [ ] Event selection → successfully gets full JWT token
- [ ] Switch between events → QR code remains the same

**Participant Side:**
- [ ] Login successfully
- [ ] Retrieve profile with user-level QR code (`USER-{id}-{random}` format)
- [ ] QR code is same regardless of which event is selected
- [ ] Display QR code correctly (minimum 200x200px)
- [ ] QR code is scannable by standard QR scanners
- [ ] Badge ID matches across all events
- [ ] Can switch events without QR code changing

**Controller Side:**
- [ ] Login successfully
- [ ] Get assigned room information
- [ ] Camera permission granted
- [ ] QR scanner detects codes
- [ ] Scan user-level QR code (without event_id in QR data)
- [ ] Backend correctly determines event from controller's context
- [ ] Verification API call succeeds (`POST /api/rooms/{room_id}/verify_access/`)
- [ ] Success screen shows participant details
- [ ] Denied screen shows specific reason:
  - [ ] "No access to this event"
  - [ ] "Not authorized for this room"
  - [ ] "Payment required for this atelier"
- [ ] Invalid QR code handled properly (400 error)
- [ ] User not found handled properly (404 error)
- [ ] Can scan multiple codes in succession

**Access Control Testing:**
- [ ] User with event access → granted
- [ ] User without event access → denied (403)
- [ ] User with room restrictions → only allowed rooms granted
- [ ] Paid session without payment → payment required (402)
- [ ] Paid session with payment → granted (200)
- [ ] Free session → always granted (if event/room access OK)

**Backend:**
- [ ] QR verification endpoint responds correctly
- [ ] Event access control works (UserEventAssignment)
- [ ] Room access control works (Participant.allowed_rooms)
- [ ] Session access control works (SessionAccess for paid ateliers)
- [ ] RoomAccess records created with correct event context
- [ ] Statistics updated properly
- [ ] Audit trail includes all denial reasons

**Multi-Event Scenarios:**
- [ ] User scans same QR at different events → backend uses room's event context
- [ ] User has access to Event A but not Event B → denied at Event B
- [ ] User paid for atelier in Event A → only works at Event A, not Event B
- [ ] Same user, same QR code → different results based on event context

---

## Troubleshooting (v2.0)

### Common Issues

**1. QR Code Not Scanning**
- Ensure QR code is at least 200x200 pixels
- Use white background for QR code
- Check camera permissions
- Verify QR scanner library is properly configured
- QR data format should be: `{"user_id": 15, "badge_id": "USER-15-ABC"}`

**2. Verification Fails**
- Check JWT token is valid and not expired
- Verify `room_id` is correct in URL path
- Ensure `qr_data` is properly formatted (user-level, not event-level)
- Check network connectivity
- Verify endpoint is `/api/rooms/{room_id}/verify_access/` (not `/api/qr/verify/`)

**3. Access Denied - Event**
- Verify user has UserEventAssignment for the event
- Check `is_active=True` on assignment
- Ensure room belongs to the correct event
- Verify JWT token has correct event_id

**4. Access Denied - Room**
- Check participant's `allowed_rooms` (if empty, all rooms allowed)
- Verify room is in allowed list if restrictions exist
- Ensure participant profile exists for this event

**5. Access Denied - Payment**
- Only applies to paid sessions (`is_paid=True`)
- Check SessionAccess record exists for participant + session
- Verify `has_access=True` and `payment_status='paid'`
- Ensure session ID is passed in verification request

**6. QR Code Data Format Issues**
- ✅ Correct: `{"user_id": 15, "badge_id": "USER-15-A1B2C3D4"}`
- ❌ Wrong: `{"user_id": 15, "event_id": "uuid", "badge_id": "PART-9069"}`
- Backend expects user-level QR code (no event_id field)
- Don't modify or parse the QR data before sending to verify endpoint

**7. Multiple Events - Same QR**
- This is expected behavior in v2.0
- Backend determines event from room context and JWT token
- Same QR code should work at all events user has access to
- If denied, check event-specific access (UserEventAssignment)

---

## Support

**Backend API Base URL:**
```
Production: https://makeplus-django-5.onrender.com
```

**API Documentation:**
```
Swagger: https://makeplus-django-5.onrender.com/swagger/
ReDoc: https://makeplus-django-5.onrender.com/redoc/
```

**Repository:**
- Name: makeplus-Django
- Owner: DjalilElz
- Branch: main

---

**End of Integration Guide**
