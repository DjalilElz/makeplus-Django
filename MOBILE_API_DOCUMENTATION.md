# MakePlus Mobile API Documentation

## Base URL
```
https://your-domain.com/api/
```

## Authentication

### JWT Token Authentication
All authenticated endpoints require a JWT token in the Authorization header:
```
Authorization: Bearer <your_jwt_token>
```

### 1. Register User
**Endpoint:** `POST /api/auth/register/`

**Description:** Register a new user account

**Request Body:**
```json
{
  "username": "johndoe",
  "email": "john@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "password": "SecurePass123!",
  "password2": "SecurePass123!"
}
```

**Response:** `201 Created`
```json
{
  "id": 1,
  "username": "johndoe",
  "email": "john@example.com",
  "first_name": "John",
  "last_name": "Doe"
}
```

### 2. Login (JWT Token)
**Endpoint:** `POST /api/auth/token/`

**Description:** Obtain JWT access and refresh tokens

**Request Body:**
```json
{
  "username": "john@example.com",
  "password": "SecurePass123!"
}
```

**Response:** `200 OK`
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "username": "johndoe",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "is_staff": false
  },
  "role": "participant",
  "event": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Tech Conference 2026"
  }
}
```

### 3. Refresh Token
**Endpoint:** `POST /api/auth/token/refresh/`

**Description:** Refresh expired access token

**Request Body:**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Response:** `200 OK`
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### 4. Verify Token
**Endpoint:** `POST /api/auth/token/verify/`

**Description:** Verify if a token is valid

**Request Body:**
```json
{
  "token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Response:** `200 OK` (empty body if valid)

### 5. Get User Profile
**Endpoint:** `GET /api/auth/me/`

**Description:** Get current authenticated user profile

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK`
```json
{
  "id": 1,
  "username": "johndoe",
  "email": "john@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "full_name": "John Doe"
}
```

### 6. Change Password
**Endpoint:** `POST /api/auth/change-password/`

**Description:** Change user password

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "old_password": "OldPass123!",
  "new_password": "NewPass123!",
  "new_password2": "NewPass123!"
}
```

**Response:** `200 OK`
```json
{
  "message": "Password changed successfully"
}
```

### 7. Request Login Code
**Endpoint:** `POST /api/auth/request-code/`

**Description:** Request passwordless login code via email

**Request Body:**
```json
{
  "email": "john@example.com",
  "event": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Response:** `200 OK`
```json
{
  "message": "Login code sent to your email"
}
```

### 8. Login with Code
**Endpoint:** `POST /api/auth/login/`

**Description:** Login using email and 6-digit code

**Request Body:**
```json
{
  "email": "john@example.com",
  "code": "123456",
  "event": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Response:** `200 OK` (returns JWT tokens)

---

## Events

### 9. List Events
**Endpoint:** `GET /api/events/`

**Description:** Get list of all events (filtered by user permissions)

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `status` (optional): Filter by status (upcoming, active, completed, cancelled)
- `search` (optional): Search by name or description

**Response:** `200 OK`
```json
[
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
]
```

### 10. Get Event Details
**Endpoint:** `GET /api/events/{event_id}/`

**Description:** Get detailed information about a specific event

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK` (same structure as list item above)

### 11. Get Event Statistics
**Endpoint:** `GET /api/events/{event_id}/statistics/`

**Description:** Get event statistics (admin/organizer only)

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK`
```json
{
  "total_participants": 250,
  "total_rooms": 5,
  "total_sessions": 45,
  "active_sessions": 3,
  "total_check_ins": 230
}
```

### 12. Get My Events
**Endpoint:** `GET /api/auth/my-events/`

**Description:** Get list of events assigned to current user

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK`
```json
[
  {
    "id": "assignment-uuid",
    "event": {
      "id": "event-uuid",
      "name": "Tech Conference 2026"
    },
    "role": "gestionnaire",
    "is_active": true,
    "assigned_at": "2026-01-15T10:00:00Z"
  }
]
```

---

## Rooms

### 13. List Rooms
**Endpoint:** `GET /api/rooms/`

**Description:** Get list of rooms (filtered by event and permissions)

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `event` (optional): Filter by event ID
- `is_active` (optional): Filter by active status (true/false)

**Response:** `200 OK`
```json
[
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
    "created_at": "2026-01-15T10:00:00Z",
    "updated_at": "2026-04-01T14:30:00Z"
  }
]
```

### 14. Get Room Details
**Endpoint:** `GET /api/rooms/{room_id}/`

**Description:** Get detailed information about a specific room

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK` (same structure as list item)

### 15. Get Room Sessions
**Endpoint:** `GET /api/rooms/{room_id}/sessions/`

**Description:** Get all sessions scheduled in a room

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK` (returns array of session objects)

### 16. Get Room Participants
**Endpoint:** `GET /api/rooms/{room_id}/participants/`

**Description:** Get list of participants currently in a room

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK`
```json
[
  {
    "id": "participant-uuid",
    "user": {
      "id": 1,
      "username": "johndoe",
      "email": "john@example.com",
      "first_name": "John",
      "last_name": "Doe"
    },
    "badge_id": "BADGE-001",
    "is_checked_in": true,
    "checked_in_at": "2026-06-15T09:30:00Z"
  }
]
```

### 17. Get Room Statistics
**Endpoint:** `GET /api/rooms/{room_id}/statistics/`

**Description:** Get room statistics (for room managers)

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK`
```json
{
  "total_sessions": 8,
  "completed_sessions": 3,
  "upcoming_sessions": 5,
  "total_participants": 45,
  "average_attendance": 38
}
```

### 18. Verify Room Access
**Endpoint:** `POST /api/rooms/{room_id}/verify_access/`

**Description:** Verify if a participant can access a room (QR scan)

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "qr_data": "USER-123-ABC12345",
  "session_id": "session-uuid"
}
```

**Response:** `200 OK`
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

### 19. Get My Room Statistics
**Endpoint:** `GET /api/my-room/statistics/`

**Description:** Get statistics for rooms assigned to current user

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK`
```json
{
  "assigned_rooms": 2,
  "total_sessions_today": 6,
  "current_participants": 78,
  "total_check_ins_today": 145
}
```

---

## Sessions

### 20. List Sessions
**Endpoint:** `GET /api/sessions/`

**Description:** Get list of sessions (filtered by event and permissions)

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `event` (optional): Filter by event ID
- `room` (optional): Filter by room ID
- `status` (optional): Filter by status (scheduled, live, completed, cancelled)
- `session_type` (optional): Filter by type (conference, atelier, workshop, etc.)
- `is_paid` (optional): Filter paid sessions (true/false)

**Response:** `200 OK`
```json
[
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
    "youtube_live_url": "https://youtube.com/live/xyz",
    "cover_image_url": "https://domain.com/media/sessions/cover.jpg",
    "is_live": false,
    "duration_minutes": 90,
    "created_at": "2026-01-15T10:00:00Z",
    "updated_at": "2026-04-01T14:30:00Z"
  }
]
```

### 21. Get Session Details
**Endpoint:** `GET /api/sessions/{session_id}/`

**Description:** Get detailed information about a specific session

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK` (same structure as list item)

### 22. Create Session
**Endpoint:** `POST /api/sessions/`

**Description:** Create a new session (admin/organizer only)

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "event": "event-uuid",
  "room": "room-uuid",
  "title": "AI in Healthcare",
  "description": "Exploring AI applications",
  "start_time": "2026-06-15T14:00:00Z",
  "end_time": "2026-06-15T15:30:00Z",
  "speaker_name": "Dr. Jane Smith",
  "session_type": "conference",
  "status": "scheduled"
}
```

**Response:** `201 Created` (returns created session object)

### 23. Start Session (Mark as Live)
**Endpoint:** `POST /api/sessions/{session_id}/start/`

**Description:** Mark session as live/in-progress

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK`
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

### 24. End Session (Mark as Completed)
**Endpoint:** `POST /api/sessions/{session_id}/end/`

**Description:** Mark session as completed

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK`
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

### 25. Cancel Session
**Endpoint:** `POST /api/sessions/{session_id}/cancel/`

**Description:** Cancel a scheduled session

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK`
```json
{
  "message": "Session cancelled successfully"
}
```

### 26. Get My Ateliers
**Endpoint:** `GET /api/my-ateliers/`

**Description:** Get list of workshops/ateliers for current user

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK` (returns array of session objects)

---

## Participants

### 27. List Participants
**Endpoint:** `GET /api/participants/`

**Description:** Get list of participants (filtered by event)

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `event` (optional): Filter by event ID
- `is_checked_in` (optional): Filter by check-in status (true/false)

**Response:** `200 OK`
```json
[
  {
    "id": "participant-uuid",
    "user": {
      "id": 1,
      "username": "johndoe",
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
    "allowed_rooms": ["room-uuid-1", "room-uuid-2"],
    "plan_file": "https://domain.com/media/participants/plan.pdf",
    "created_at": "2026-01-15T10:00:00Z"
  }
]
```

### 28. Get Participant Details
**Endpoint:** `GET /api/participants/{participant_id}/`

**Description:** Get detailed information about a specific participant

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK` (same structure as list item)

---

## Room Access & Check-ins

### 29. List Room Access Logs
**Endpoint:** `GET /api/room-access/`

**Description:** Get room access/check-in history

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `room` (optional): Filter by room ID
- `participant` (optional): Filter by participant ID
- `status` (optional): Filter by status (granted, denied)

**Response:** `200 OK`
```json
[
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
```

### 30. Create Room Access Log
**Endpoint:** `POST /api/room-access/`

**Description:** Log a room access attempt (check-in)

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "participant": "participant-uuid",
  "room": "room-uuid",
  "session": "session-uuid",
  "status": "granted"
}
```

**Response:** `201 Created` (returns created access log)

---

## QR Code Operations

### 31. Verify QR Code
**Endpoint:** `POST /api/qr/verify/`

**Description:** Verify a participant's QR code for room access

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "qr_data": "USER-123-ABC12345",
  "room_id": "room-uuid",
  "session_id": "session-uuid"
}
```

**Response:** `200 OK`
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

### 32. Generate QR Code
**Endpoint:** `GET /api/qr/generate/`

**Description:** Generate QR code for current user

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK`
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

## Announcements

### 33. List Announcements
**Endpoint:** `GET /api/annonces/`

**Description:** Get event announcements (filtered by target audience)

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `event` (optional): Filter by event ID
- `target` (optional): Filter by target (all, participants, exposants, gestionnaires)

**Response:** `200 OK`
```json
[
  {
    "id": "annonce-uuid",
    "event": "event-uuid",
    "event_name": "Tech Conference 2026",
    "title": "Lunch Break Extended",
    "description": "Lunch break extended by 30 minutes due to high demand",
    "target": "all",
    "created_by": 1,
    "created_by_name": "Admin User",
    "created_at": "2026-06-15T12:00:00Z",
    "updated_at": "2026-06-15T12:00:00Z"
  }
]
```

### 34. Create Announcement
**Endpoint:** `POST /api/annonces/`

**Description:** Create a new announcement (admin/organizer only)

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "event": "event-uuid",
  "title": "Important Update",
  "description": "Session moved to different room",
  "target": "participants"
}
```

**Response:** `201 Created` (returns created announcement)

---

## Session Questions (Q&A)

### 35. List Session Questions
**Endpoint:** `GET /api/session-questions/`

**Description:** Get questions for sessions

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `session` (optional): Filter by session ID
- `is_answered` (optional): Filter by answered status (true/false)

**Response:** `200 OK`
```json
[
  {
    "id": "question-uuid",
    "session": "session-uuid",
    "session_title": "AI in Healthcare",
    "participant": "participant-uuid",
    "participant_name": "John Doe",
    "question_text": "What are the ethical implications?",
    "is_answered": true,
    "answer_text": "Great question! The ethical implications include...",
    "answered_by": 2,
    "answered_by_name": "Dr. Jane Smith",
    "asked_at": "2026-06-15T14:30:00Z",
    "answered_at": "2026-06-15T14:35:00Z"
  }
]
```

### 36. Ask Question
**Endpoint:** `POST /api/session-questions/`

**Description:** Submit a question during a session

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "session": "session-uuid",
  "question_text": "What are the ethical implications?"
}
```

**Response:** `201 Created`
```json
{
  "id": "question-uuid",
  "session": "session-uuid",
  "question_text": "What are the ethical implications?",
  "is_answered": false,
  "asked_at": "2026-06-15T14:30:00Z"
}
```

### 37. Answer Question
**Endpoint:** `POST /api/session-questions/{question_id}/answer/`

**Description:** Answer a session question (speaker/moderator only)

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "answer_text": "Great question! The ethical implications include..."
}
```

**Response:** `200 OK`
```json
{
  "id": "question-uuid",
  "is_answered": true,
  "answer_text": "Great question! The ethical implications include...",
  "answered_at": "2026-06-15T14:35:00Z"
}
```

---

## Session Access (Paid Ateliers)

### 38. List Session Access
**Endpoint:** `GET /api/session-access/`

**Description:** Get session access records for paid ateliers

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `session` (optional): Filter by session ID
- `participant` (optional): Filter by participant ID
- `payment_status` (optional): Filter by payment status (pending, paid, refunded)

**Response:** `200 OK`
```json
[
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
  }
]
```

### 39. Grant Session Access
**Endpoint:** `POST /api/session-access/`

**Description:** Grant access to a paid session

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "participant": "participant-uuid",
  "session": "session-uuid",
  "has_access": true,
  "payment_status": "paid",
  "amount_paid": 50.00
}
```

**Response:** `201 Created` (returns created access record)

---

## Room Assignments

### 40. List Room Assignments
**Endpoint:** `GET /api/room-assignments/`

**Description:** Get room assignments for staff (gestionnaires, controllers)

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `event` (optional): Filter by event ID
- `room` (optional): Filter by room ID
- `user` (optional): Filter by user ID
- `role` (optional): Filter by role (gestionnaire, controller)
- `is_active` (optional): Filter by active status (true/false)

**Response:** `200 OK`
```json
[
  {
    "id": "assignment-uuid",
    "user": 2,
    "user_name": "Jane Controller",
    "room": "room-uuid",
    "room_name": "Main Hall A",
    "event": "event-uuid",
    "event_name": "Tech Conference 2026",
    "role": "controller",
    "start_time": "2026-06-15T09:00:00Z",
    "end_time": "2026-06-15T18:00:00Z",
    "is_active": true,
    "assigned_at": "2026-06-10T10:00:00Z",
    "assigned_by": 1,
    "assigned_by_name": "Admin User"
  }
]
```

### 41. Create Room Assignment
**Endpoint:** `POST /api/room-assignments/`

**Description:** Assign staff to a room (admin only)

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "user": 2,
  "room": "room-uuid",
  "event": "event-uuid",
  "role": "controller",
  "start_time": "2026-06-15T09:00:00Z",
  "end_time": "2026-06-15T18:00:00Z",
  "is_active": true
}
```

**Response:** `201 Created` (returns created assignment)

---

## Exposant Scans

### 42. List Exposant Scans
**Endpoint:** `GET /api/exposant-scans/`

**Description:** Get list of participant scans by exposants (booth visits)

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `event` (optional): Filter by event ID
- `exposant` (optional): Filter by exposant ID

**Response:** `200 OK`
```json
[
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
```

### 43. Create Exposant Scan
**Endpoint:** `POST /api/exposant-scans/`

**Description:** Record a participant scan at exposant booth

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "scanned_participant": "participant-uuid",
  "event": "event-uuid",
  "notes": "Interested in product demo"
}
```

**Response:** `201 Created` (returns created scan record)

### 44. Get My Scans
**Endpoint:** `GET /api/exposant-scans/my_scans/`

**Description:** Get scans made by current exposant user

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK` (returns array of scan objects)

### 45. Export Scans to Excel
**Endpoint:** `GET /api/exposant-scans/export_excel/`

**Description:** Export exposant scans to Excel file

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `event` (optional): Filter by event ID

**Response:** `200 OK` (returns Excel file download)

---

## User Event Assignments

### 46. List User Assignments
**Endpoint:** `GET /api/user-assignments/`

**Description:** Get user-event role assignments (admin only)

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `event` (optional): Filter by event ID
- `user` (optional): Filter by user ID
- `role` (optional): Filter by role
- `is_active` (optional): Filter by active status

**Response:** `200 OK`
```json
[
  {
    "id": "assignment-uuid",
    "user": {
      "id": 2,
      "username": "janesmith",
      "email": "jane@example.com",
      "first_name": "Jane",
      "last_name": "Smith"
    },
    "event": {
      "id": "event-uuid",
      "name": "Tech Conference 2026"
    },
    "role": "gestionnaire",
    "is_active": true,
    "assigned_at": "2026-06-10T10:00:00Z"
  }
]
```

### 47. Create User Assignment
**Endpoint:** `POST /api/user-assignments/`

**Description:** Assign a user to an event with a role (admin only)

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "user_id": 2,
  "event_id": "event-uuid",
  "role": "gestionnaire",
  "is_active": true
}
```

**Response:** `201 Created` (returns created assignment)

---

## Event Selection

### 48. Select Event
**Endpoint:** `POST /api/auth/select-event/`

**Description:** Select an event to work with

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "event_id": "event-uuid"
}
```

**Response:** `200 OK`
```json
{
  "message": "Event selected successfully",
  "event": {
    "id": "event-uuid",
    "name": "Tech Conference 2026"
  }
}
```

### 49. Switch Event
**Endpoint:** `POST /api/auth/switch-event/`

**Description:** Switch to a different event

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "event_id": "event-uuid"
}
```

**Response:** `200 OK`
```json
{
  "message": "Event switched successfully"
}
```

---

## Dashboard & Statistics

### 50. Get Dashboard Stats
**Endpoint:** `GET /api/dashboard/stats/`

**Description:** Get dashboard statistics for current user

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK`
```json
{
  "role": "gestionnaire",
  "assigned_events": 2,
  "assigned_rooms": 3,
  "active_sessions_today": 8,
  "total_participants": 250,
  "check_ins_today": 145
}
```

---

## Notifications

### 51. List Notifications
**Endpoint:** `GET /api/notifications/`

**Description:** Get notifications for current user

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `is_read` (optional): Filter by read status (true/false)

**Response:** `200 OK`
```json
[
  {
    "id": "notification-uuid",
    "title": "Session Starting Soon",
    "message": "Your session 'AI in Healthcare' starts in 15 minutes",
    "type": "session_reminder",
    "is_read": false,
    "created_at": "2026-06-15T13:45:00Z"
  }
]
```

### 52. Get Notification Details
**Endpoint:** `GET /api/notifications/{notification_id}/`

**Description:** Get detailed information about a notification

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK` (same structure as list item)

### 53. Mark Notification as Read
**Endpoint:** `POST /api/notifications/{notification_id}/read/`

**Description:** Mark a notification as read

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK`
```json
{
  "message": "Notification marked as read",
  "is_read": true
}
```

---

## ePoster Submissions

### 54. List ePoster Submissions
**Endpoint:** `GET /api/eposter/submissions/`

**Description:** Get list of ePoster submissions (committee members only)

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `event` (optional): Filter by event ID
- `status` (optional): Filter by status (pending, accepted, rejected, revision_requested)

**Response:** `200 OK`
```json
[
  {
    "id": "submission-uuid",
    "event": "event-uuid",
    "submitter_name": "Dr. John Researcher",
    "submitter_email": "john.researcher@university.edu",
    "title": "Novel Approach to Machine Learning",
    "abstract": "This research presents...",
    "authors": "John Doe, Jane Smith",
    "institution": "Tech University",
    "poster_file": "https://domain.com/media/eposters/poster.pdf",
    "status": "pending",
    "submitted_at": "2026-05-15T10:00:00Z",
    "validation_count": 0,
    "average_score": null
  }
]
```

### 55. Get ePoster Submission Details
**Endpoint:** `GET /api/eposter/submissions/{submission_id}/`

**Description:** Get detailed information about an ePoster submission

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK` (same structure as list item with additional validation details)

### 56. Submit ePoster (Public)
**Endpoint:** `POST /api/eposter/{event_id}/submit/`

**Description:** Submit an ePoster (public endpoint, no authentication required)

**Request Body:** (multipart/form-data)
```
submitter_name: "Dr. John Researcher"
submitter_email: "john.researcher@university.edu"
title: "Novel Approach to Machine Learning"
abstract: "This research presents..."
authors: "John Doe, Jane Smith"
institution: "Tech University"
poster_file: [PDF file]
```

**Response:** `201 Created`
```json
{
  "id": "submission-uuid",
  "message": "ePoster submitted successfully",
  "submission": {
    "id": "submission-uuid",
    "title": "Novel Approach to Machine Learning",
    "status": "pending",
    "submitted_at": "2026-05-15T10:00:00Z"
  }
}
```

### 57. Validate ePoster
**Endpoint:** `POST /api/eposter/submissions/{submission_id}/validate/`

**Description:** Submit validation/review for an ePoster (committee members only)

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "score": 8.5,
  "comments": "Excellent research methodology",
  "recommendation": "accept"
}
```

**Response:** `201 Created`
```json
{
  "id": "validation-uuid",
  "submission": "submission-uuid",
  "validator_name": "Dr. Jane Reviewer",
  "score": 8.5,
  "comments": "Excellent research methodology",
  "recommendation": "accept",
  "validated_at": "2026-05-20T14:00:00Z"
}
```

### 58. Set ePoster Status
**Endpoint:** `POST /api/eposter/submissions/{submission_id}/set_status/`

**Description:** Update ePoster submission status (committee members only)

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "status": "accepted",
  "admin_notes": "Congratulations! Your poster has been accepted."
}
```

**Response:** `200 OK`
```json
{
  "message": "Status updated successfully",
  "status": "accepted"
}
```

### 59. Get My Pending ePoster Reviews
**Endpoint:** `GET /api/eposter/submissions/my_pending/`

**Description:** Get ePoster submissions pending review by current committee member

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK` (returns array of submission objects)

### 60. Get ePoster Statistics
**Endpoint:** `GET /api/eposter/submissions/statistics/`

**Description:** Get ePoster submission statistics (committee members only)

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK`
```json
{
  "total_submissions": 45,
  "pending": 12,
  "accepted": 28,
  "rejected": 3,
  "revision_requested": 2,
  "average_score": 7.8
}
```

### 61. Get Real-time Validation Status
**Endpoint:** `GET /api/eposter/submissions/{submission_id}/realtime/`

**Description:** Get real-time validation status for an ePoster submission

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK`
```json
{
  "submission_id": "submission-uuid",
  "status": "pending",
  "validation_count": 3,
  "required_validations": 5,
  "average_score": 8.2,
  "validations": [
    {
      "validator_name": "Dr. Jane Reviewer",
      "score": 8.5,
      "recommendation": "accept",
      "validated_at": "2026-05-20T14:00:00Z"
    }
  ]
}
```

---

## ePoster Committee

### 62. List Committee Members
**Endpoint:** `GET /api/eposter/committee/`

**Description:** Get list of ePoster committee members

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `event` (optional): Filter by event ID

**Response:** `200 OK`
```json
[
  {
    "id": "member-uuid",
    "user": {
      "id": 3,
      "username": "drjane",
      "email": "jane@university.edu",
      "first_name": "Jane",
      "last_name": "Reviewer"
    },
    "event": "event-uuid",
    "added_at": "2026-04-01T10:00:00Z"
  }
]
```

### 63. Add Committee Member
**Endpoint:** `POST /api/eposter/committee/`

**Description:** Add a committee member (admin only)

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "user_id": 3,
  "event_id": "event-uuid"
}
```

**Response:** `201 Created` (returns created committee member)

---

## ePoster Validations

### 64. List ePoster Validations
**Endpoint:** `GET /api/eposter/validations/`

**Description:** Get list of ePoster validations/reviews

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `submission` (optional): Filter by submission ID
- `validator` (optional): Filter by validator user ID

**Response:** `200 OK`
```json
[
  {
    "id": "validation-uuid",
    "submission": "submission-uuid",
    "validator": 3,
    "validator_name": "Dr. Jane Reviewer",
    "score": 8.5,
    "comments": "Excellent research methodology",
    "recommendation": "accept",
    "validated_at": "2026-05-20T14:00:00Z"
  }
]
```

---

## Error Responses

All endpoints may return the following error responses:

### 400 Bad Request
```json
{
  "error": "Invalid request data",
  "details": {
    "field_name": ["Error message"]
  }
}
```

### 401 Unauthorized
```json
{
  "detail": "Authentication credentials were not provided."
}
```

### 403 Forbidden
```json
{
  "detail": "You do not have permission to perform this action."
}
```

### 404 Not Found
```json
{
  "detail": "Not found."
}
```

### 500 Internal Server Error
```json
{
  "error": "Internal server error",
  "message": "An unexpected error occurred"
}
```

---

## Data Models

### User Roles
- `participant`: Regular event participant
- `exposant`: Exhibitor/booth representative
- `gestionnaire`: Room manager
- `controller`: Access controller/security
- `admin`: System administrator
- `president`: Event president

### Event Status
- `upcoming`: Event not yet started
- `active`: Event currently ongoing
- `completed`: Event finished
- `cancelled`: Event cancelled

### Session Status
- `scheduled`: Session scheduled but not started
- `live`: Session currently in progress
- `completed`: Session finished
- `cancelled`: Session cancelled

### Session Types
- `conference`: Conference presentation
- `atelier`: Workshop/hands-on session
- `workshop`: Training workshop
- `panel`: Panel discussion
- `keynote`: Keynote speech

### ePoster Status
- `pending`: Awaiting review
- `accepted`: Accepted for presentation
- `rejected`: Not accepted
- `revision_requested`: Needs revisions

### Payment Status
- `pending`: Payment not yet received
- `paid`: Payment completed
- `refunded`: Payment refunded

---

## Rate Limiting

API requests are rate-limited to prevent abuse:
- Authenticated users: 1000 requests per hour
- Unauthenticated users: 100 requests per hour

Rate limit headers are included in responses:
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1622548800
```

---

## Pagination

List endpoints support pagination using query parameters:
- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 20, max: 100)

Paginated responses include:
```json
{
  "count": 150,
  "next": "https://domain.com/api/events/?page=2",
  "previous": null,
  "results": [...]
}
```

---

## Filtering & Search

Most list endpoints support filtering and search:
- Use query parameters matching field names for exact filtering
- Use `search` parameter for text search across multiple fields
- Use `ordering` parameter to sort results (prefix with `-` for descending)

Example:
```
GET /api/sessions/?event=event-uuid&status=live&ordering=-start_time
```

---

## File Uploads

File upload endpoints accept `multipart/form-data`:
- Maximum file size: 10MB
- Supported formats: PDF, JPG, PNG
- Use appropriate field names as specified in endpoint documentation

---

## Timestamps

All timestamps are in ISO 8601 format with UTC timezone:
```
2026-06-15T14:30:00Z
```

---

## API Versioning

Current API version: v1

The API version is included in the base URL. Future versions will be available at:
```
https://your-domain.com/api/v2/
```

---

## Support

For API support and questions:
- Email: api-support@makeplus.com
- Documentation: https://docs.makeplus.com
- Status Page: https://status.makeplus.com
