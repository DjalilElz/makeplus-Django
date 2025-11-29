# User Access Control & QR Code System

**Version:** 2.0  
**Last Updated:** November 29, 2025  
**Breaking Changes:** QR code is now user-level, not event-level

---

## Table of Contents

1. [Overview](#overview)
2. [Access Control Levels](#access-control-levels)
3. [Login Flow](#login-flow)
4. [QR Code Structure](#qr-code-structure)
5. [Verification Flow](#verification-flow)
6. [API Integration](#api-integration)
7. [Flutter Examples](#flutter-examples)

---

## Overview

### Access Control Hierarchy

```
USER
 ├── QR Code (ONE per user, permanent)
 │
 ├── Event Access (via UserEventAssignment)
 │   ├── Event 1: StartupWeek Oran 2025 (role: participant)
 │   │   ├── ✅ Access to all free sessions
 │   │   ├── ✅ Access to paid Atelier 1 (paid)
 │   │   ├── ❌ Access to paid Atelier 2 (not paid)
 │   │   └── ✅ Access to Room A, Room B
 │   │
 │   ├── Event 2: Tech Summit Algeria (role: exposant)
 │   │   ├── ✅ Access to exhibitor hall
 │   │   └── ✅ Can scan other participants
 │   │
 │   └── ❌ Event 3: Innovation Fest (no access)
```

### Key Principles

1. **One QR Code Per User** - User has a single, permanent QR code
2. **Event-Level Access** - User can access specific events (via UserEventAssignment)
3. **Session-Level Access** - Within an event, user can access specific sessions/ateliers (via SessionAccess)
4. **Room-Level Access** - Within an event, user can access specific rooms (via Participant.allowed_rooms)

---

## Access Control Levels

### Level 1: User Authentication

**Check:** Is the user authenticated?

```python
user = authenticate(email=email, password=password)
if user is None:
    return "Invalid credentials"
```

### Level 2: Event Access

**Check:** Does the user have access to this event?

```python
assignment = UserEventAssignment.objects.filter(
    user=user,
    event=event,
    is_active=True
).first()

if assignment is None:
    return "No access to this event"
```

**Grants:**
- User can see event in their event list
- User gets a role in this event (participant, exposant, controller, gestionnaire)
- User can view event schedule and announcements

### Level 3: Session Access (for Paid Ateliers)

**Check:** Does the user have access to this specific session?

```python
session_access = SessionAccess.objects.filter(
    participant=participant,
    session=session,
    has_access=True
).first()

if session_access is None and session.is_paid:
    return "Payment required for this atelier"
```

**Grants:**
- User can enter paid ateliers
- User can view session materials
- User can ask questions in Q&A

### Level 4: Room Access

**Check:** Can the user enter this specific room?

```python
# If allowed_rooms is empty, user has access to all rooms
if participant.allowed_rooms.exists():
    if room not in participant.allowed_rooms.all():
        return "Not authorized for this room"
```

**Grants:**
- Physical room entry
- Access to room-specific sessions

---

## Login Flow

### Scenario 1: User with ONE Event

**Request:**
```json
POST /api/auth/login/
{
  "email": "participant@example.com",
  "password": "password123"
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
    "email": "participant@example.com",
    "first_name": "Ahmed",
    "last_name": "Benali"
  },
  "current_event": {
    "id": "6442555a-2295-41f7-81ee-0a902a9c4102",
    "name": "StartupWeek Oran 2025",
    "role": "participant",
    "start_date": "2026-01-26T00:00:00Z",
    "end_date": "2026-01-31T23:59:59Z",
    "status": "upcoming",
    "location": "Oran Convention Center",
    "badge": {
      "badge_id": "PART-9069",
      "qr_code_data": "{\"user_id\": 15, \"badge_id\": \"PART-9069\"}",
      "is_checked_in": false
    }
  },
  "requires_event_selection": false
}
```

**Flow:**
```
User logs in
    ↓
Backend finds 1 event
    ↓
Auto-select that event
    ↓
Return JWT with event_id in token
    ↓
User can immediately use the app
```

---

### Scenario 2: User with MULTIPLE Events

**Request:**
```json
POST /api/auth/login/
{
  "email": "multi.event@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "user": {
    "id": 25,
    "username": "multi_user",
    "email": "multi.event@example.com",
    "first_name": "Karim",
    "last_name": "Mansouri"
  },
  "requires_event_selection": true,
  "available_events": [
    {
      "id": "event-1-uuid",
      "name": "StartupWeek Oran 2025",
      "role": "participant",
      "start_date": "2026-01-26T00:00:00Z",
      "end_date": "2026-01-31T23:59:59Z",
      "status": "upcoming",
      "location": "Oran",
      "badge": {
        "badge_id": "PART-1234",
        "qr_code_data": "{\"user_id\": 25, \"badge_id\": \"PART-1234\"}",
        "is_checked_in": false
      }
    },
    {
      "id": "event-2-uuid",
      "name": "Tech Summit Algeria",
      "role": "exposant",
      "start_date": "2026-02-15T00:00:00Z",
      "end_date": "2026-02-17T23:59:59Z",
      "status": "upcoming",
      "location": "Alger",
      "badge": {
        "badge_id": "EXP-5678",
        "qr_code_data": "{\"user_id\": 25, \"badge_id\": \"EXP-5678\"}",
        "is_checked_in": false
      }
    },
    {
      "id": "event-3-uuid",
      "name": "Innovation Festival",
      "role": "controlleur_des_badges",
      "start_date": "2026-03-10T00:00:00Z",
      "end_date": "2026-03-12T23:59:59Z",
      "status": "upcoming",
      "location": "Constantine",
      "badge": null
    }
  ],
  "temp_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Flow:**
```
User logs in
    ↓
Backend finds 3 events
    ↓
Return list of events
    ↓
User selects an event
    ↓
Call /api/auth/select-event/
    ↓
Return JWT with selected event_id
    ↓
User can use the app
```

---

### Scenario 3: Select Event

**Request:**
```json
POST /api/auth/select-event/
Authorization: Bearer <temp_token>
{
  "event_id": "event-1-uuid"
}
```

**Response:**
```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 25,
    "username": "multi_user",
    "email": "multi.event@example.com"
  },
  "event": {
    "id": "event-1-uuid",
    "name": "StartupWeek Oran 2025",
    "location": "Oran",
    "start_date": "2026-01-26",
    "end_date": "2026-01-31"
  },
  "role": "participant",
  "badge": {
    "badge_id": "PART-1234",
    "qr_code_data": "{\"user_id\": 25, \"badge_id\": \"PART-1234\"}",
    "is_checked_in": false
  }
}
```

---

## QR Code Structure

### Current Implementation (Per-Event)

Each participant gets a QR code per event:

```json
{
  "user_id": 15,
  "event_id": "6442555a-2295-41f7-81ee-0a902a9c4102",
  "badge_id": "PART-9069"
}
```

### Recommended: User-Level QR Code

User should have ONE QR code across all events:

```json
{
  "user_id": 15,
  "badge_id": "USER-15-UNIQUE"
}
```

**Benefits:**
- User has one QR code for all events
- Simpler for users (don't need different QR codes)
- Backend determines event access during verification
- Same QR code can be printed on physical badge

**Backend Changes Needed:**
1. Store `qr_code_data` in User model or create a separate UserQRCode model
2. Generate QR code once when user registers
3. Return same QR code in all event contexts

---

## Verification Flow

### Complete Access Check

```python
def verify_qr_code(qr_data, room_id, session_id=None):
    # 1. Find user by QR code
    user = find_user_by_qr(qr_data)
    if not user:
        return "Invalid QR code"
    
    # 2. Get room's event
    room = Room.objects.get(id=room_id)
    event = room.event
    
    # 3. Check event access
    assignment = UserEventAssignment.objects.filter(
        user=user,
        event=event,
        is_active=True
    ).first()
    
    if not assignment:
        return "No access to this event"
    
    # 4. Get participant profile
    participant = Participant.objects.filter(
        user=user,
        event=event
    ).first()
    
    if not participant:
        return "Participant profile not found"
    
    # 5. Check room access (if allowed_rooms is specified)
    if participant.allowed_rooms.exists():
        if room not in participant.allowed_rooms.all():
            return "Not authorized for this room"
    
    # 6. Check session access (if scanning for specific session)
    if session_id:
        session = Session.objects.get(id=session_id)
        
        # If paid session, check payment
        if session.is_paid:
            session_access = SessionAccess.objects.filter(
                participant=participant,
                session=session,
                has_access=True
            ).first()
            
            if not session_access:
                return "Payment required for this atelier"
    
    # 7. Grant access
    RoomAccess.objects.create(
        participant=participant,
        room=room,
        session=session if session_id else None,
        verified_by=controller,
        status='granted'
    )
    
    return "Access granted"
```

---

## API Integration

### 1. Login

**Endpoint:** `POST /api/auth/login/`

**Purpose:** Authenticate user and get list of accessible events

**Request:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response Cases:**

**A) Single Event (Auto-selected):**
```json
{
  "access": "jwt_token",
  "refresh": "refresh_token",
  "user": {...},
  "current_event": {
    "id": "uuid",
    "name": "Event Name",
    "role": "participant",
    "badge": {
      "badge_id": "PART-1234",
      "qr_code_data": "..."
    }
  },
  "requires_event_selection": false
}
```

**B) Multiple Events:**
```json
{
  "user": {...},
  "requires_event_selection": true,
  "available_events": [...],
  "temp_token": "temporary_jwt"
}
```

---

### 2. Select Event (if multiple)

**Endpoint:** `POST /api/auth/select-event/`

**Purpose:** Select which event to use

**Request:**
```json
{
  "event_id": "uuid"
}
```

**Response:**
```json
{
  "access": "jwt_token",
  "refresh": "refresh_token",
  "user": {...},
  "event": {...},
  "role": "participant",
  "badge": {
    "badge_id": "PART-1234",
    "qr_code_data": "..."
  }
}
```

---

### 3. Get My Events

**Endpoint:** `GET /api/auth/my-events/`

**Purpose:** List all events user has access to

**Response:**
```json
{
  "events": [
    {
      "id": "uuid",
      "name": "StartupWeek Oran 2025",
      "role": "participant",
      "start_date": "2026-01-26",
      "end_date": "2026-01-31",
      "location": "Oran",
      "badge": {
        "badge_id": "PART-9069",
        "qr_code_data": "..."
      }
    },
    {
      "id": "uuid-2",
      "name": "Tech Summit",
      "role": "exposant",
      "badge": {...}
    }
  ]
}
```

---

### 4. Get My Ateliers (Paid Sessions)

**Endpoint:** `GET /api/my-ateliers/`

**Purpose:** Get all paid ateliers for current event with payment status

**Response:**
```json
{
  "participant": {
    "id": "uuid",
    "name": "Ahmed Benali",
    "badge_id": "PART-9069"
  },
  "summary": {
    "total_ateliers": 4,
    "paid_count": 2,
    "pending_count": 2,
    "total_paid": 9500.00,
    "total_pending": 9500.00
  },
  "ateliers": [
    {
      "id": "uuid",
      "session_id": "uuid",
      "title": "Pitch Deck Workshop",
      "payment_status": "paid",
      "has_access": true,
      "price": 5000.00,
      "amount_paid": 5000.00
    },
    {
      "title": "UX Design Workshop",
      "payment_status": "pending",
      "has_access": false,
      "price": 6000.00
    }
  ]
}
```

---

### 5. QR Code Verification

**Endpoint:** `POST /api/qr/verify/`

**Purpose:** Controller scans participant's QR code

**Request:**
```json
{
  "qr_data": "{\"user_id\": 15, \"badge_id\": \"PART-9069\"}",
  "room_id": "room-uuid",
  "session_id": "session-uuid"  // optional
}
```

**Response (Access Granted):**
```json
{
  "status": "granted",
  "message": "Access granted successfully",
  "participant": {
    "id": "uuid",
    "name": "Ahmed Benali",
    "email": "participant@example.com",
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

**Response (Access Denied - No Event Access):**
```json
{
  "status": "denied",
  "message": "User does not have access to this event",
  "participant": {
    "id": "uuid",
    "name": "Ahmed Benali",
    "badge_id": "PART-9069"
  }
}
```

**Response (Access Denied - Payment Required):**
```json
{
  "status": "denied",
  "message": "Payment required for this atelier",
  "participant": {
    "name": "Ahmed Benali",
    "badge_id": "PART-9069"
  },
  "session": {
    "title": "UX Design Workshop",
    "price": 6000.00,
    "payment_status": "pending"
  }
}
```

---

## Flutter Examples

### Login Screen with Event Selection

```dart
class LoginScreen extends StatefulWidget {
  @override
  _LoginScreenState createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  bool _isLoading = false;

  Future<void> login() async {
    setState(() => _isLoading = true);

    try {
      final response = await http.post(
        Uri.parse('https://makeplus-django-5.onrender.com/api/auth/login/'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'email': _emailController.text,
          'password': _passwordController.text,
        }),
      );

      final data = jsonDecode(response.body);

      if (response.statusCode == 200) {
        if (data['requires_event_selection'] == true) {
          // User has multiple events - show event selection
          Navigator.push(
            context,
            MaterialPageRoute(
              builder: (context) => EventSelectionScreen(
                user: data['user'],
                events: data['available_events'],
                tempToken: data['temp_token'],
              ),
            ),
          );
        } else {
          // User has single event - proceed to home
          await saveUserData(data);
          Navigator.pushReplacement(
            context,
            MaterialPageRoute(builder: (context) => HomeScreen()),
          );
        }
      } else {
        showError(data['detail'] ?? 'Login failed');
      }
    } catch (e) {
      showError('Network error: $e');
    } finally {
      setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Padding(
        padding: EdgeInsets.all(24),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            TextField(
              controller: _emailController,
              decoration: InputDecoration(labelText: 'Email'),
              keyboardType: TextInputType.emailAddress,
            ),
            SizedBox(height: 16),
            TextField(
              controller: _passwordController,
              decoration: InputDecoration(labelText: 'Password'),
              obscureText: true,
            ),
            SizedBox(height: 24),
            ElevatedButton(
              onPressed: _isLoading ? null : login,
              child: _isLoading
                  ? CircularProgressIndicator(color: Colors.white)
                  : Text('Login'),
              style: ElevatedButton.styleFrom(
                minimumSize: Size(double.infinity, 50),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
```

### Event Selection Screen

```dart
class EventSelectionScreen extends StatelessWidget {
  final Map<String, dynamic> user;
  final List<dynamic> events;
  final String tempToken;

  const EventSelectionScreen({
    required this.user,
    required this.events,
    required this.tempToken,
  });

  Future<void> selectEvent(BuildContext context, String eventId) async {
    try {
      final response = await http.post(
        Uri.parse('https://makeplus-django-5.onrender.com/api/auth/select-event/'),
        headers: {
          'Authorization': 'Bearer $tempToken',
          'Content-Type': 'application/json',
        },
        body: jsonEncode({'event_id': eventId}),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        await saveUserData(data);
        
        Navigator.pushReplacement(
          context,
          MaterialPageRoute(builder: (context) => HomeScreen()),
        );
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error: $e')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Select Event'),
      ),
      body: ListView.builder(
        itemCount: events.length,
        itemBuilder: (context, index) {
          final event = events[index];
          return Card(
            margin: EdgeInsets.all(8),
            child: ListTile(
              title: Text(event['name']),
              subtitle: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Role: ${event['role']}'),
                  Text('${event['start_date']} - ${event['end_date']}'),
                  Text('Location: ${event['location']}'),
                  if (event['badge'] != null)
                    Text('Badge: ${event['badge']['badge_id']}'),
                ],
              ),
              trailing: Icon(Icons.arrow_forward_ios),
              onTap: () => selectEvent(context, event['id']),
            ),
          );
        },
      ),
    );
  }
}
```

---

## Summary

### Access Control Flow

```
1. User Login
   ↓
2. Backend returns accessible events
   ↓
3. User selects event (if multiple)
   ↓
4. JWT token includes event_id
   ↓
5. User sees event-specific content:
   - Sessions they have access to
   - Rooms they can enter
   - Ateliers (paid/unpaid status)
   ↓
6. Controller scans QR code
   ↓
7. Backend verifies:
   ✓ User has access to this event
   ✓ User has access to this room (if restricted)
   ✓ User has paid for this session (if paid atelier)
   ↓
8. Grant or Deny access
```

### Key Points

✅ **User has ONE QR code** (recommendation)  
✅ **Access controlled at multiple levels**: Event → Room → Session  
✅ **Login returns all accessible events**  
✅ **JWT token contains event context**  
✅ **Backend enforces all access rules during verification**  
✅ **Frontend displays appropriate content based on access**  

---

**End of Document**
