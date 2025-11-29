# MakePlus Backend - Complete Documentation

**Version:** 2.0  
**Last Updated:** November 29, 2025  
**Status:** ✅ Production Ready | ✅ Flutter Compatible | ✅ User-Level QR System

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [Authentication & Authorization](#authentication--authorization)
4. [Database Models](#database-models)
5. [API Endpoints](#api-endpoints)
6. [Permissions System](#permissions-system)
7. [File Uploads](#file-uploads)
8. [Management Commands](#management-commands)
9. [Deployment Guide](#deployment-guide)
10. [API Usage Examples](#api-usage-examples)

---

## System Overview

### Technology Stack

- **Framework:** Django 5.2.7
- **API:** Django REST Framework (DRF)
- **Authentication:** JWT (JSON Web Tokens) via SimpleJWT
- **Database:** PostgreSQL (SQLite for development)
- **API Documentation:** drf-yasg (Swagger/OpenAPI)
- **CORS:** django-cors-headers
- **File Storage:** Django FileField (local/cloud storage)

### Key Features

- ✅ Multi-event management system
- ✅ Role-based access control (4 roles)
- ✅ JWT authentication with event context
- ✅ **User-level QR code system (ONE QR per user across all events)**
- ✅ QR code verification with multi-level access control (event + session)
- ✅ Real-time session status management
- ✅ File uploads (PDF: programmes, guides, plans)
- ✅ Paid atelier system with access control
- ✅ Event announcements with role-based targeting
- ✅ Session Q&A system
- ✅ Room staff assignments with time slots
- ✅ Exposant booth visit tracking
- ✅ YouTube live streaming integration
- ✅ French language support (statuses, roles)
- ✅ **Flutter frontend integration ready**
- ✅ **CORS configured for mobile/web apps**
- ✅ **URL aliases for frontend compatibility**

---

## Architecture

### Project Structure

```
makeplus_backend/
├── makeplus_api/                 # Django project
│   ├── makeplus_api/            # Project settings
│   │   ├── settings.py          # Configuration
│   │   ├── urls.py              # Main URL routing
│   │   └── wsgi.py              # WSGI application
│   ├── events/                  # Main app
│   │   ├── models.py            # Database models
│   │   ├── views.py             # API viewsets
│   │   ├── serializers.py       # DRF serializers
│   │   ├── permissions.py       # Custom permissions
│   │   ├── urls.py              # API routes
│   │   ├── utils.py             # Utility functions
│   │   ├── admin.py             # Django admin
│   │   ├── migrations/          # Database migrations
│   │   └── management/          # Management commands
│   ├── staticfiles/             # Static files (admin, DRF, swagger)
│   ├── media/                   # User uploads
│   ├── manage.py                # Django management
│   └── db.sqlite3               # SQLite database (dev)
├── venv/                        # Virtual environment
└── requirements.txt             # Python dependencies
```

### Data Flow

```
Client (Flutter/Web)
    ↓ HTTP Request + JWT Token
Django URLS (urls.py)
    ↓ Route to ViewSet
DRF ViewSet (views.py)
    ↓ Check Permissions
Custom Permissions (permissions.py)
    ↓ Authorized
Serializer (serializers.py)
    ↓ Validate Data
Model (models.py)
    ↓ Database Operation
PostgreSQL Database
    ↓ Return Data
Serializer → ViewSet → JSON Response
    ↓
Client receives response
```

---

## Authentication & Authorization

### User Model

Uses Django's built-in `User` model:
- `username` - Unique identifier
- `email` - Email address (used for login)
- `first_name` - First name
- `last_name` - Last name
- `password` - Hashed password
- `is_staff` - Admin access
- `is_active` - Account status

### JWT Authentication

**Token Structure:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "username": "ahmed.benali",
    "email": "ahmed@example.com",
    "first_name": "Ahmed",
    "last_name": "Benali"
  },
  "event": {
    "id": "uuid",
    "name": "Tech Summit 2025"
  },
  "role": "gestionnaire_des_salles"
}
```

**Token Endpoints:**
- `POST /api/auth/login/` - Login and get tokens
- `POST /api/auth/register/` - Register new user
- `POST /api/auth/logout/` - Logout (blacklist token)
- `POST /api/token/refresh/` - Refresh access token

**Token Usage:**
```http
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

### Login Flow with User-Level QR Codes (v2.0)

#### Overview
Users now have **ONE QR code** that works across all events they have access to. The login endpoint returns all accessible events with the same QR code for each.

#### Scenario 1: User with Single Event

**Request:**
```http
POST /api/auth/login/
Content-Type: application/json

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
      "badge_id": "USER-15-A1B2C3D4",
      "qr_code_data": "{\"user_id\": 15, \"badge_id\": \"USER-15-A1B2C3D4\"}",
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

#### Scenario 2: User with Multiple Events

**Request:**
```http
POST /api/auth/login/
Content-Type: application/json

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
        "badge_id": "USER-25-X9Y8Z7W6",
        "qr_code_data": "{\"user_id\": 25, \"badge_id\": \"USER-25-X9Y8Z7W6\"}",
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
        "badge_id": "USER-25-X9Y8Z7W6",
        "qr_code_data": "{\"user_id\": 25, \"badge_id\": \"USER-25-X9Y8Z7W6\"}",
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

**Note:** 
- All events show the **SAME QR code** (`USER-25-X9Y8Z7W6`)
- Controllers don't get badge info (they scan, they don't get scanned)
- User must call `/api/auth/select-event/` next

**Flow:**
```
User logs in
    ↓
Backend finds 3 events
    ↓
Return list of events with temp_token
    ↓
User selects an event
    ↓
Call /api/auth/select-event/
    ↓
Return JWT with selected event_id
    ↓
User can use the app
```

#### Event Selection Endpoint

**Request:**
```http
POST /api/auth/select-event/
Authorization: Bearer <temp_token>
Content-Type: application/json

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
    "email": "multi.event@example.com",
    "first_name": "Karim",
    "last_name": "Mansouri"
  },
  "current_event": {
    "id": "event-1-uuid",
    "name": "StartupWeek Oran 2025",
    "role": "participant",
    "start_date": "2026-01-26T00:00:00Z",
    "end_date": "2026-01-31T23:59:59Z",
    "status": "upcoming",
    "location": "Oran",
    "logo_url": "https://...",
    "banner_url": "https://...",
    "badge": {
      "badge_id": "USER-25-X9Y8Z7W6",
      "qr_code_data": "{\"user_id\": 25, \"badge_id\": \"USER-25-X9Y8Z7W6\"}",
      "is_checked_in": false,
      "checked_in_at": null
    },
    "permissions": ["view_sessions", "access_rooms", "check_in"]
  }
}
```

#### QR Code Access Control

**Multi-Level Access Verification:**

1. **Event Level** - Does user have access to this event?
   - Checked via `UserEventAssignment`
   - If no assignment: **Access Denied**

2. **Room Level** - Can user enter this specific room?
   - Checked via `Participant.allowed_rooms`
   - If empty: user can access all rooms
   - If specified: user can only access listed rooms
   - If room not in list: **Access Denied**

3. **Session Level** - For paid ateliers, has user paid?
   - Checked via `SessionAccess`
   - Free sessions: automatic access
   - Paid sessions without payment: **Payment Required**

**Example Access Check:**
```
Controller scans QR: {"user_id": 15, "badge_id": "USER-15-ABC123"}
    ↓
Backend checks UserEventAssignment
    ✓ User has access to Event A as participant
    ↓
Backend checks Participant.allowed_rooms
    ✓ No restrictions OR room is in allowed list
    ↓
If session is paid, check SessionAccess
    ✓ User has paid OR session is free
    ↓
✅ GRANT ACCESS - Create RoomAccess record
```

### Multi-Event Support

Users can be assigned to multiple events with different roles:

**Event Selection:**
- `POST /api/auth/select-event/` - Select event during login
- `POST /api/auth/switch-event/` - Switch between events
- `GET /api/auth/my-events/` - List user's events

**Event Context:**
- JWT token includes current event
- All API calls are scoped to the selected event
- Users can have different roles in different events

### Role System

| Role | Code | Description |
|------|------|-------------|
| **Gestionnaire des Salles** | `gestionnaire_des_salles` | Event and room manager - Full control over events, rooms, sessions |
| **Contrôleur des Badges** | `controlleur_des_badges` | Badge scanner - QR code verification, participant check-in |
| **Participant** | `participant` | Regular attendee - Access to sessions, Q&A, view schedule |
| **Exposant** | `exposant` | Exhibitor - Booth management, scan participant QR codes, track visits |

---

## Database Models

### Core Models

#### 1. Event
**Purpose:** Represents an event/conference

**Fields:**
- `id` (UUID) - Primary key
- `name` (String, 200) - Event name
- `description` (Text) - Event description
- `location` (String, 500) - Event location
- `start_date` (DateTime) - Event start
- `end_date` (DateTime) - Event end
- `is_active` (Boolean) - Event status
- `programme_file` (File) - PDF programme
- `guide_file` (File) - PDF participant guide
- `president` (FK User) - Event president
- `created_by` (FK User) - Creator
- `created_at` (DateTime) - Creation timestamp
- `updated_at` (DateTime) - Last update

**Relationships:**
- Has many: Rooms, Sessions, Participants, UserEventAssignments

**Example:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Tech Summit Algeria 2025",
  "description": "Annual technology conference",
  "location": "Alger Centre des Congrès",
  "start_date": "2025-12-01T09:00:00Z",
  "end_date": "2025-12-03T18:00:00Z",
  "is_active": true,
  "programme_file": "/media/programmes/tech_summit_2025.pdf",
  "guide_file": "/media/guides/participant_guide.pdf",
  "president": 5,
  "created_by": 1
}
```

---

#### 2. Room
**Purpose:** Physical rooms/venues within an event

**Fields:**
- `id` (UUID) - Primary key
- `event` (FK Event) - Parent event
- `name` (String, 100) - Room name
- `capacity` (Integer) - Max capacity
- `description` (Text) - Room description
- `is_active` (Boolean) - Room status
- `created_by` (FK User) - Creator
- `created_at` (DateTime) - Creation timestamp

**Relationships:**
- Belongs to: Event
- Has many: Sessions, RoomAccess, RoomAssignments

**Example:**
```json
{
  "id": "uuid",
  "event": "event-uuid",
  "name": "Amphithéâtre A",
  "capacity": 500,
  "description": "Capacité: 500 personnes",
  "is_active": true
}
```

---

#### 3. Session
**Purpose:** Conference sessions, ateliers, workshops

**Fields:**
- `id` (UUID) - Primary key
- `event` (FK Event) - Parent event
- `room` (FK Room) - Location
- `title` (String, 200) - Session title
- `description` (Text) - Session description
- `speaker_name` (String, 200) - Speaker name
- `speaker_title` (String, 200) - Speaker title/role
- `start_time` (DateTime) - Session start
- `end_time` (DateTime) - Session end
- `theme` (String, 100) - Session theme/category
- `status` (String, 20) - Session status
- `session_type` (String, 20) - Type: conference/atelier
- `is_paid` (Boolean) - Requires payment
- `price` (Decimal) - Atelier price
- `youtube_live_url` (URL) - Live stream URL
- `created_by` (FK User) - Creator
- `created_at` (DateTime) - Creation timestamp

**Status Choices:**
- `pas_encore` - Not started yet (scheduled)
- `en_cours` - Currently in progress (live)
- `termine` - Finished (completed)

**Type Choices:**
- `conference` - Conference session (free)
- `atelier` - Workshop/atelier (can be paid)

**Relationships:**
- Belongs to: Event, Room
- Has many: SessionAccess, SessionQuestions

**Example:**
```json
{
  "id": "uuid",
  "event": "event-uuid",
  "room": "room-uuid",
  "title": "Intelligence Artificielle et Machine Learning",
  "description": "Introduction aux concepts fondamentaux de l'IA",
  "speaker_name": "Dr. Ahmed Benali",
  "speaker_title": "Chercheur en IA",
  "start_time": "2025-12-01T10:00:00Z",
  "end_time": "2025-12-01T11:30:00Z",
  "theme": "IA",
  "status": "pas_encore",
  "session_type": "atelier",
  "is_paid": true,
  "price": "5000.00",
  "youtube_live_url": "https://youtube.com/live/abc123"
}
```

---

#### 4. UserEventAssignment
**Purpose:** Assigns users to events with specific roles

**Fields:**
- `id` (UUID) - Primary key
- `user` (FK User) - Assigned user
- `event` (FK Event) - Assigned event
- `role` (String, 50) - User's role
- `is_active` (Boolean) - Assignment status
- `assigned_by` (FK User) - Who assigned
- `assigned_at` (DateTime) - Assignment timestamp

**Role Choices:**
- `gestionnaire_des_salles` - Room manager
- `controlleur_des_badges` - Badge controller
- `participant` - Regular participant
- `exposant` - Exhibitor

**Constraints:**
- Unique together: (user, event)
- A user can only have ONE role per event

**Example:**
```json
{
  "id": "uuid",
  "user": 5,
  "event": "event-uuid",
  "role": "gestionnaire_des_salles",
  "is_active": true,
  "assigned_by": 1,
  "assigned_at": "2025-11-25T10:00:00Z"
}
```

---

#### 5. UserProfile (NEW in v2.0)
**Purpose:** Store user-level QR code (ONE per user across all events)

**Fields:**
- `id` (Auto) - Primary key
- `user` (OneToOne User) - User account
- `qr_code_data` (JSON) - User's QR code (same for all events)
- `created_at` (DateTime) - Profile creation
- `updated_at` (DateTime) - Last update

**QR Code Format:**
```json
{
  "user_id": 15,
  "badge_id": "USER-15-A1B2C3D4"
}
```

**Key Features:**
- ✅ Automatically created when needed
- ✅ Same QR code used across all events
- ✅ Badge ID format: `USER-{user_id}-{8_random_chars}`
- ✅ Simplifies user experience (one QR for everything)

**Example:**
```json
{
  "id": 1,
  "user": 15,
  "qr_code_data": {
    "user_id": 15,
    "badge_id": "USER-15-A1B2C3D4"
  },
  "created_at": "2025-11-29T10:00:00Z",
  "updated_at": "2025-11-29T10:00:00Z"
}
```

**Usage:**
```python
from events.models import UserProfile

# Get or create QR code for user
qr_data = UserProfile.get_qr_for_user(user)
# Returns: {"user_id": 15, "badge_id": "USER-15-A1B2C3D4"}
```

---

#### 6. Participant
**Purpose:** Participant profiles with badge information

**Fields:**
- `id` (UUID) - Primary key
- `user` (FK User) - User account
- `event` (FK Event) - Event
- `badge_number` (String, 50) - Unique badge number
- `qr_code_data` (String, 500) - QR code content
- `registration_date` (DateTime) - When registered
- `plan_file` (File) - PDF plan (for exposants)

**Constraints:**
- Unique together: (user, event)
- Unique: badge_number per event

**Example:**
```json
{
  "id": "uuid",
  "user": 10,
  "event": "event-uuid",
  "badge_number": "TECH2025-001",
  "qr_code_data": "PARTICIPANT:uuid:TECH2025-001",
  "registration_date": "2025-11-20T14:30:00Z",
  "plan_file": "/media/plans/exposant_plan.pdf"
}
```

---

#### 6. RoomAccess
**Purpose:** Track participant access to rooms

**Fields:**
- `id` (UUID) - Primary key
- `participant` (FK Participant) - Participant
- `room` (FK Room) - Room accessed
- `access_time` (DateTime) - When accessed
- `verified_by` (FK User) - Controller who verified

**Example:**
```json
{
  "id": "uuid",
  "participant": "participant-uuid",
  "room": "room-uuid",
  "access_time": "2025-12-01T09:45:00Z",
  "verified_by": 3
}
```

---

### Extended Models (New Features)

#### 7. SessionAccess
**Purpose:** Manage access to paid ateliers

**Fields:**
- `id` (UUID) - Primary key
- `participant` (FK Participant) - Participant
- `session` (FK Session) - Paid session
- `payment_status` (String, 20) - Payment status
- `has_access` (Boolean) - Access granted
- `granted_at` (DateTime) - When granted

**Payment Status Choices:**
- `pending` - Payment pending
- `paid` - Payment confirmed
- `refunded` - Payment refunded

**Constraints:**
- Unique together: (participant, session)

**Example:**
```json
{
  "id": "uuid",
  "participant": "participant-uuid",
  "session": "session-uuid",
  "payment_status": "paid",
  "has_access": true,
  "granted_at": "2025-11-25T15:00:00Z"
}
```

---

#### 8. Annonce
**Purpose:** Event announcements with role-based targeting

**Fields:**
- `id` (UUID) - Primary key
- `event` (FK Event) - Event
- `title` (String, 200) - Announcement title
- `description` (Text) - Announcement content
- `target` (String, 50) - Target audience
- `created_by` (FK User) - Creator
- `created_at` (DateTime) - Creation timestamp
- `updated_at` (DateTime) - Last update

**Target Choices:**
- `all` - All event participants
- `participants` - Only participants
- `exposants` - Only exhibitors
- `controlleurs` - Only badge controllers
- `gestionnaires` - Only room managers

**Example:**
```json
{
  "id": "uuid",
  "event": "event-uuid",
  "title": "Pause déjeuner",
  "description": "Le déjeuner est servi à la cafétéria, niveau 2",
  "target": "all",
  "created_by": 1,
  "created_at": "2025-12-01T12:00:00Z"
}
```

---

#### 9. SessionQuestion
**Purpose:** Q&A system for sessions

**Fields:**
- `id` (UUID) - Primary key
- `session` (FK Session) - Session
- `participant` (FK Participant) - Who asked
- `question_text` (Text) - Question content
- `asked_at` (DateTime) - When asked
- `is_answered` (Boolean) - Answer status
- `answer_text` (Text, nullable) - Answer content
- `answered_by` (FK User, nullable) - Who answered
- `answered_at` (DateTime, nullable) - When answered

**Example:**
```json
{
  "id": "uuid",
  "session": "session-uuid",
  "participant": "participant-uuid",
  "question_text": "Quelles sont les prérequis pour cet atelier?",
  "asked_at": "2025-12-01T10:15:00Z",
  "is_answered": true,
  "answer_text": "Connaissance de base en Python requise",
  "answered_by": 1,
  "answered_at": "2025-12-01T10:20:00Z"
}
```

---

#### 10. RoomAssignment
**Purpose:** Assign staff (gestionnaires/controllers) to rooms with time slots

**Fields:**
- `id` (UUID) - Primary key
- `user` (FK User) - Assigned staff
- `room` (FK Room) - Assigned room
- `event` (FK Event) - Event
- `role` (String, 50) - Staff role
- `start_time` (DateTime) - Assignment start
- `end_time` (DateTime) - Assignment end
- `is_active` (Boolean) - Assignment status
- `assigned_by` (FK User) - Who assigned
- `assigned_at` (DateTime) - When assigned

**Role Choices:**
- `gestionnaire_des_salles` - Room manager
- `controlleur_des_badges` - Badge controller

**Example:**
```json
{
  "id": "uuid",
  "user": 5,
  "room": "room-uuid",
  "event": "event-uuid",
  "role": "controlleur_des_badges",
  "start_time": "2025-12-01T09:00:00Z",
  "end_time": "2025-12-01T17:00:00Z",
  "is_active": true,
  "assigned_by": 1
}
```

---

#### 11. ExposantScan
**Purpose:** Track when exposants scan participant QR codes (booth visits)

**Fields:**
- `id` (UUID) - Primary key
- `exposant` (FK Participant) - Exposant who scanned
- `scanned_participant` (FK Participant) - Participant scanned
- `event` (FK Event) - Event
- `scanned_at` (DateTime) - Scan timestamp
- `notes` (Text, nullable) - Optional notes

**Constraints:**
- Index on: (exposant, scanned_at) for performance

**Example:**
```json
{
  "id": "uuid",
  "exposant": "exposant-participant-uuid",
  "scanned_participant": "participant-uuid",
  "event": "event-uuid",
  "scanned_at": "2025-12-01T14:30:00Z",
  "notes": "Intéressé par le produit X"
}
```

---

## API Endpoints

### Authentication Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/auth/register/` | Register new user | No |
| POST | `/api/auth/login/` | Login and get JWT tokens | No |
| POST | `/api/auth/logout/` | Logout and blacklist token | Yes |
| GET | `/api/auth/profile/` | Get user profile | Yes |
| GET | `/api/auth/me/` | Get user profile (Flutter alias) | Yes |
| PUT/PATCH | `/api/auth/profile/` | Update user profile | Yes |
| POST | `/api/auth/change-password/` | Change password | Yes |
| POST | `/api/auth/select-event/` | Select event during login | Yes |
| POST | `/api/auth/switch-event/` | Switch to different event | Yes |
| GET | `/api/auth/my-events/` | List user's events | Yes |

**Note:** `/api/auth/me/` is an alias for `/api/auth/profile/` added for Flutter frontend compatibility.

---

### Event Management Endpoints

| Method | Endpoint | Description | Permission |
|--------|----------|-------------|------------|
| GET | `/api/events/` | List all events | Authenticated |
| POST | `/api/events/` | Create event | Gestionnaire |
| GET | `/api/events/{id}/` | Get event details | Authenticated |
| PUT/PATCH | `/api/events/{id}/` | Update event | Gestionnaire |
| DELETE | `/api/events/{id}/` | Delete event | Gestionnaire |
| GET | `/api/events/{id}/statistics/` | Get event stats | Authenticated |

**Event Statistics Response:**
```json
{
  "total_participants": 250,
  "total_sessions": 45,
  "live_sessions": 3,
  "completed_sessions": 12,
  "total_rooms": 8
}
```

---

### Room Management Endpoints

| Method | Endpoint | Description | Permission |
|--------|----------|-------------|------------|
| GET | `/api/rooms/` | List rooms | Authenticated |
| POST | `/api/rooms/` | Create room | Gestionnaire |
| GET | `/api/rooms/{id}/` | Get room details | Authenticated |
| PUT/PATCH | `/api/rooms/{id}/` | Update room | Gestionnaire |
| DELETE | `/api/rooms/{id}/` | Delete room | Gestionnaire |
| GET | `/api/rooms/{id}/statistics/` | Get room statistics | Admin/Gestionnaire |
| GET | `/api/rooms/{id}/participants/` | Get today's participants | Authenticated |

**Query Parameters:**
- `event_id` - Filter by event

**Room Statistics (Admin/Gestionnaire only):**
```json
{
  "room": {
    "id": "uuid",
    "name": "Salle Principale",
    "capacity": 100
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

**Note:** Controllers should use `/api/my-room/statistics/` instead, which automatically uses their assigned room.

---

### Session Management Endpoints

| Method | Endpoint | Description | Permission |
|--------|----------|-------------|------------|
| GET | `/api/sessions/` | List sessions | Authenticated |
| POST | `/api/sessions/` | Create session | Gestionnaire |
| GET | `/api/sessions/{id}/` | Get session details | Authenticated |
| PUT/PATCH | `/api/sessions/{id}/` | Update session | Gestionnaire |
| DELETE | `/api/sessions/{id}/` | Delete session | Gestionnaire |
| POST | `/api/sessions/{id}/mark_live/` | Start session | Gestionnaire |
| POST | `/api/sessions/{id}/start/` | Start session (Flutter alias) | Gestionnaire |
| POST | `/api/sessions/{id}/mark_completed/` | End session | Gestionnaire |
| POST | `/api/sessions/{id}/end/` | End session (Flutter alias) | Gestionnaire |
| POST | `/api/sessions/{id}/cancel/` | Cancel session | Gestionnaire |

**Query Parameters:**
- `room_id` - Filter by room
- `event_id` - Filter by event
- `status` - Filter by status (pas_encore, en_cours, termine)
- `session_type` - Filter by type (conference, atelier)
- `is_paid` - Filter paid ateliers

**Session Actions:**
- **mark_live** / **start** - Sets status to `en_cours`
- **mark_completed** / **end** - Sets status to `termine`
- **cancel** - Resets status to `pas_encore`

**Note:** `/start/` and `/end/` are aliases for `mark_live` and `mark_completed` added for Flutter frontend compatibility.

---

### Participant Management Endpoints

| Method | Endpoint | Description | Permission |
|--------|----------|-------------|------------|
| GET | `/api/participants/` | List participants | Authenticated |
| POST | `/api/participants/` | Create participant | Gestionnaire |
| GET | `/api/participants/{id}/` | Get participant details | Authenticated |
| PUT/PATCH | `/api/participants/{id}/` | Update participant | Gestionnaire |
| DELETE | `/api/participants/{id}/` | Delete participant | Gestionnaire |

**Query Parameters:**
- `event_id` - Filter by event
- `badge_number` - Filter by badge

---

### User Assignment Endpoints

| Method | Endpoint | Description | Permission |
|--------|----------|-------------|------------|
| GET | `/api/user-assignments/` | List assignments | Authenticated |
| POST | `/api/user-assignments/` | Create assignment | Gestionnaire |
| GET | `/api/user-assignments/{id}/` | Get assignment details | Authenticated |
| PUT/PATCH | `/api/user-assignments/{id}/` | Update assignment | Gestionnaire |
| DELETE | `/api/user-assignments/{id}/` | Delete assignment | Gestionnaire |

**Query Parameters:**
- `user` - Filter by user
- `event` - Filter by event
- `role` - Filter by role
- `is_active` - Filter active assignments

---

### Session Access Endpoints (Paid Ateliers)

| Method | Endpoint | Description | Permission |
|--------|----------|-------------|------------|
| GET | `/api/session-access/` | List access records | Authenticated |
| POST | `/api/session-access/` | Grant access | Gestionnaire |
| GET | `/api/session-access/{id}/` | Get access details | Authenticated |
| PUT/PATCH | `/api/session-access/{id}/` | Update access | Gestionnaire |
| GET | `/api/my-ateliers/` | Get participant's paid ateliers with full details | Authenticated (Participant) |

**Query Parameters (session-access):**
- `participant_id` - Filter by participant
- `session_id` - Filter by session
- `payment_status` - Filter by payment status
- `has_access` - Filter by access status

**My Ateliers Endpoint** (`GET /api/my-ateliers/`)

Returns all paid ateliers for the authenticated participant with complete session information and payment status.

**Response Format:**
```json
{
  "participant": {
    "id": "uuid",
    "name": "Ahmed Benali",
    "email": "participant@example.com",
    "badge_id": "PART-1234"
  },
  "summary": {
    "total_ateliers": 4,
    "paid_count": 2,
    "pending_count": 2,
    "total_paid": 9500.00,
    "total_pending": 9500.00,
    "total_amount": 19000.00
  },
  "ateliers": [
    {
      "id": "access_uuid",
      "session_id": "session_uuid",
      "title": "Atelier: Pitch Deck & Levée de Fonds",
      "description": "Learn to create a convincing pitch deck...",
      "speaker_name": "Sarah Meziane",
      "speaker_title": "Venture Capitalist",
      "speaker_bio": "...",
      "speaker_photo_url": "https://...",
      "theme": "Financement",
      "room": {
        "id": "room_uuid",
        "name": "Hall Exposition",
        "capacity": 500
      },
      "start_time": "2025-11-30T20:00:00Z",
      "end_time": "2025-11-30T23:00:00Z",
      "price": 5000.00,
      "payment_status": "paid",
      "has_access": true,
      "amount_paid": 5000.00,
      "paid_at": "2025-11-28T19:00:00Z",
      "registered_at": "2025-11-28T18:00:00Z"
    }
  ]
}
```

**Payment Status Values:**
- `paid` - Payment completed, access granted
- `pending` - Payment pending, no access
- `free` - Free atelier, access granted

**Usage:**
```bash
GET /api/my-ateliers/
Authorization: Bearer <jwt_token>
```

The endpoint automatically:
- Extracts participant from authenticated user and event context
- Filters only paid ateliers (is_paid=True)
- Returns full session details including speaker info, room, dates
- Calculates payment summary (paid vs pending amounts)

---

### Annonce (Announcements) Endpoints

| Method | Endpoint | Description | Permission |
|--------|----------|-------------|------------|
| GET | `/api/annonces/` | List announcements | Authenticated (filtered by role) |
| POST | `/api/annonces/` | Create announcement | Authenticated |
| GET | `/api/annonces/{id}/` | Get announcement details | Authenticated |
| PUT/PATCH | `/api/annonces/{id}/` | Update announcement | Owner or Gestionnaire |
| DELETE | `/api/annonces/{id}/` | Delete announcement | Owner or Gestionnaire |

**Query Parameters:**
- `event_id` - Filter by event
- `target` - Filter by target audience
- `created_by` - Filter by creator
- `search` - Search in title/description

**Auto-Filtering:**
Users automatically see only announcements:
- Targeted to `all`, OR
- Targeted to their specific role in the event

---

### Session Questions (Q&A) Endpoints

| Method | Endpoint | Description | Permission |
|--------|----------|-------------|------------|
| GET | `/api/session-questions/` | List questions | Authenticated |
| POST | `/api/session-questions/` | Ask question | Authenticated |
| GET | `/api/session-questions/{id}/` | Get question details | Authenticated |
| PUT/PATCH | `/api/session-questions/{id}/` | Update question | Authenticated |
| POST | `/api/session-questions/{id}/answer/` | Answer question | Gestionnaire |

**Query Parameters:**
- `session_id` - Filter by session
- `participant` - Filter by participant
- `is_answered` - Filter answered/unanswered

**Answer Action:**
```json
POST /api/session-questions/{id}/answer/
{
  "answer_text": "Réponse à votre question..."
}
```

---

### Room Assignment Endpoints

| Method | Endpoint | Description | Permission |
|--------|----------|-------------|------------|
| GET | `/api/room-assignments/` | List assignments | Gestionnaire |
| POST | `/api/room-assignments/` | Create assignment | Gestionnaire |
| GET | `/api/room-assignments/{id}/` | Get assignment details | Gestionnaire |
| PUT/PATCH | `/api/room-assignments/{id}/` | Update assignment | Gestionnaire |
| DELETE | `/api/room-assignments/{id}/` | Delete assignment | Gestionnaire |

**Query Parameters:**
- `room_id` - Filter by room
- `user_id` - Filter by user
- `event_id` - Filter by event
- `role` - Filter by role
- `is_active` - Filter active assignments
- `current=true` - Get only current assignments (time-based)

---

### Exposant Scan Endpoints

| Method | Endpoint | Description | Permission |
|--------|----------|-------------|------------|
| GET | `/api/exposant-scans/` | List scans | Authenticated |
| POST | `/api/exposant-scans/` | Record scan | Exposant |
| GET | `/api/exposant-scans/{id}/` | Get scan details | Authenticated |
| GET | `/api/exposant-scans/my_scans/` | Get my scans with stats | Exposant |

**Query Parameters:**
- `exposant_id` - Filter by exposant
- `event_id` - Filter by event

**My Scans Response:**
```json
{
  "total_visits": 42,
  "today_visits": 15,
  "scans": [...]
}
```

---

### QR Code Endpoints

| Method | Endpoint | Description | Permission |
|--------|----------|-------------|------------|
| POST | `/api/rooms/{room_id}/verify_access/` | Verify user QR code for room access | Controller |
| POST | `/api/qr/generate/` | Generate QR code | Gestionnaire |

#### **NEW: User-Level QR Code System (v2.0)**

**Key Changes:**
- ✅ **ONE QR code per user** (stored in UserProfile model)
- ✅ Same QR code works across all events user has access to
- ✅ Multi-level access control: Event → Room → Session
- ✅ Backend determines access based on UserEventAssignment and SessionAccess

**QR Code Format:**
```json
{
  "user_id": 15,
  "badge_id": "USER-15-A1B2C3D4"
}
```

**How It Works:**
1. User logs in → receives same QR code for all their events
2. Controller scans QR code at room entrance
3. Backend checks:
   - ✓ Does user have access to this event? (UserEventAssignment)
   - ✓ Does user have access to this room? (Participant.allowed_rooms)
   - ✓ If paid session, has user paid? (SessionAccess)
4. Grant or deny access accordingly

**QR Verify Request:**
```json
POST /api/rooms/{room_id}/verify_access/
{
  "qr_data": "{\"user_id\": 15, \"badge_id\": \"USER-15-A1B2C3D4\"}",
  "session": "session-uuid"  // Optional: for session-specific access
}
```

**QR Verify Response (Access Granted):**
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

**QR Verify Response (Access Denied - No Event Access):**
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

**QR Verify Response (Access Denied - Payment Required):**
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

**Status Codes:**
- `200 OK` - Access granted
- `402 Payment Required` - Paid session, user hasn't paid
- `403 Forbidden` - No event access or room not authorized
- `404 Not Found` - User/participant/session not found
- `400 Bad Request` - Invalid QR format
- `500 Internal Server Error` - Server error

---

### Dashboard & Statistics Endpoints

| Method | Endpoint | Description | Permission |
|--------|----------|-------------|------------|
| GET | `/api/dashboard/stats/` | Dashboard statistics | Authenticated |
| GET | `/api/my-room/statistics/` | Controller's room statistics | Controller only |

**Dashboard Stats Response:**
```json
{
  "event": {...},
  "total_participants": 250,
  "total_sessions": 45,
  "live_sessions": 3,
  "completed_sessions": 12,
  "upcoming_sessions": [...],
  "my_role": "gestionnaire_des_salles"
}
```

**My Room Statistics Response (Controller):**
```json
{
  "room": {
    "id": "uuid",
    "name": "Salle Principale",
    "capacity": 100
  },
  "statistics": {
    "total_scans": 45,
    "today_scans": 12,
    "granted": 38,
    "denied": 7,
    "unique_participants": 25,
    "unique_participants_today": 8
  },
  "recent_scans": [
    {
      "id": "uuid",
      "participant": {
        "id": "uuid",
        "name": "John Doe",
        "email": "john@example.com",
        "badge_id": "BADGE123"
      },
      "session": "Innovation et Startups",
      "status": "granted",
      "accessed_at": "2025-11-28T14:30:00Z",
      "verified_by": "controller_username"
    }
  ]
}
```

**Usage Notes:**
- `/api/my-room/statistics/` automatically detects the controller's assigned room
- No room_id parameter needed - uses the room assigned to the authenticated controller
- Returns statistics only for the controller's assigned room
- Includes today's scans and all-time statistics
- Recent scans limited to last 20 entries

---

## Permissions System

### Permission Classes

#### 1. IsGestionnaire
**Description:** User must have `gestionnaire_des_salles` role

**Usage:**
```python
permission_classes = [IsAuthenticated, IsGestionnaire]
```

**Checks:**
- User is authenticated
- User has active assignment with role `gestionnaire_des_salles` for the event

**Used By:**
- Event management (create, update, delete)
- Room management
- Session management
- Session actions (mark_live, mark_completed, cancel)
- Room assignments
- Session question answers

---

#### 2. IsGestionnaireOrReadOnly
**Description:** Read-only for all, write for gestionnaires

**Usage:**
```python
permission_classes = [IsAuthenticated, IsGestionnaireOrReadOnly]
```

**Behavior:**
- GET requests: Any authenticated user
- POST/PUT/PATCH/DELETE: Gestionnaire only

**Used By:**
- Events list/detail
- Rooms list/detail
- Sessions list/detail

---

#### 3. IsController
**Description:** User must have `controlleur_des_badges` role

**Usage:**
```python
permission_classes = [IsAuthenticated, IsController]
```

**Checks:**
- User is authenticated
- User has active assignment with role `controlleur_des_badges` for the event

**Used By:**
- QR code verification
- Badge scanning
- Room access verification

**Note:** Controllers and Gestionnaires are SEPARATE roles with different responsibilities.

---

#### 4. IsParticipant
**Description:** User must have `participant` role

**Usage:**
```python
permission_classes = [IsAuthenticated, IsParticipant]
```

**Checks:**
- User is authenticated
- User has active assignment with role `participant` for the event

---

#### 5. IsExposant
**Description:** User must have `exposant` role

**Usage:**
```python
permission_classes = [IsAuthenticated, IsExposant]
```

**Checks:**
- User is authenticated
- User has active assignment with role `exposant` for the event

**Used By:**
- Exposant scan endpoints
- Booth visit tracking

---

#### 6. IsAnnonceOwner
**Description:** User must be the announcement creator or gestionnaire

**Usage:**
```python
permission_classes = [IsAuthenticated, IsAnnonceOwner]
```

**Checks:**
- User created the announcement, OR
- User is a gestionnaire for the event

**Used By:**
- Annonce update/delete

---

#### 7. IsEventMember
**Description:** User must be assigned to the event (any role)

**Usage:**
```python
permission_classes = [IsAuthenticated, IsEventMember]
```

**Checks:**
- User is authenticated
- User has any active assignment for the event

---

### Permission Matrix

| Endpoint | Gestionnaire | Contrôleur | Participant | Exposant |
|----------|--------------|------------|-------------|----------|
| **Events** |
| List/View | ✅ Read/Write | ✅ Read Only | ✅ Read Only | ✅ Read Only |
| Create/Edit/Delete | ✅ | ❌ | ❌ | ❌ |
| **Rooms** |
| List/View | ✅ Read/Write | ✅ Read Only | ✅ Read Only | ✅ Read Only |
| Create/Edit/Delete | ✅ | ❌ | ❌ | ❌ |
| **Sessions** |
| List/View | ✅ Read/Write | ✅ Read Only | ✅ Read Only | ✅ Read Only |
| Create/Edit/Delete | ✅ | ❌ | ❌ | ❌ |
| Mark Live/Complete | ✅ | ❌ | ❌ | ❌ |
| **Participants** |
| List/View | ✅ | ✅ | ✅ (Own) | ✅ (Own) |
| Create/Edit/Delete | ✅ | ❌ | ❌ | ❌ |
| **QR Codes** |
| Verify | ✅ | ✅ | ❌ | ❌ |
| Generate | ✅ | ❌ | ❌ | ❌ |
| **Session Access** |
| View | ✅ | ❌ | ✅ (Own) | ❌ |
| Grant/Revoke | ✅ | ❌ | ❌ | ❌ |
| **Annonces** |
| View | ✅ (All) | ✅ (Targeted) | ✅ (Targeted) | ✅ (Targeted) |
| Create | ✅ | ✅ | ✅ | ✅ |
| Edit/Delete | ✅ (All) | ✅ (Own) | ✅ (Own) | ✅ (Own) |
| **Session Q&A** |
| View | ✅ | ✅ | ✅ | ✅ |
| Ask Question | ✅ | ✅ | ✅ | ✅ |
| Answer Question | ✅ | ❌ | ❌ | ❌ |
| **Room Assignments** |
| View/Create/Edit | ✅ | ❌ | ❌ | ❌ |
| **Exposant Scans** |
| View | ✅ | ❌ | ❌ | ✅ (Own) |
| Create Scan | ❌ | ❌ | ❌ | ✅ |
| My Scans Stats | ❌ | ❌ | ❌ | ✅ |

---

## File Uploads

### Supported Files

| Model | Field | Type | Purpose |
|-------|-------|------|---------|
| Event | `programme_file` | PDF | Event programme |
| Event | `guide_file` | PDF | Participant guide |
| Participant | `plan_file` | PDF | Exposant booth plan |

### Upload Configuration

**File Storage:**
- Development: Local filesystem (`MEDIA_ROOT`)
- Production: AWS S3 / Azure Blob / Google Cloud Storage

**Settings:**
```python
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
```

**File Size Limits:**
- Max file size: 10MB (configurable)
- Allowed formats: PDF only

### Upload Example

**Multipart Form Data:**
```http
POST /api/events/
Content-Type: multipart/form-data

name: "Tech Summit 2025"
description: "..."
start_date: "2025-12-01T09:00:00Z"
end_date: "2025-12-03T18:00:00Z"
programme_file: [PDF file]
guide_file: [PDF file]
```

**Response:**
```json
{
  "id": "uuid",
  "name": "Tech Summit 2025",
  "programme_file": "/media/programmes/tech_summit_2025.pdf",
  "guide_file": "/media/guides/participant_guide.pdf",
  ...
}
```

### File Access

**Public URLs:**
```
http://localhost:8000/media/programmes/tech_summit_2025.pdf
http://localhost:8000/media/guides/participant_guide.pdf
```

**Serving Files:**
- Development: Django serves via `django.views.static.serve`
- Production: Nginx/Apache or CDN

---

## Management Commands

### Create Test Data

#### 1. create_multi_event_data
**Purpose:** Create 3 events with complete data (users, rooms, sessions)

**Usage:**
```bash
python manage.py create_multi_event_data
```

**Creates:**
- 3 Events: Tech Summit, Startup Week, Innovation Festival
- 5 Users per event (1 gestionnaire, 1 controller, 2 participants, 1 exposant)
- 3 Rooms per event
- 4 Sessions per event
- Participant badges with QR codes

**Events Created:**
1. **Tech Summit Algeria 2025** (tech prefix)
2. **Startup Week Algeria 2025** (startup prefix)
3. **Innovation Festival 2025** (inno prefix)

---

#### 2. create_multi_event_users
**Purpose:** Create users with assignments across multiple events

**Usage:**
```bash
python manage.py create_multi_event_users
```

**Creates:**
- Users with different roles in different events
- Demonstrates multi-event support

---

#### 3. create_test_users
**Purpose:** Create basic test users for one event

**Usage:**
```bash
python manage.py create_test_users
```

**Creates:**
- 1 Gestionnaire: organizer@makeplus.com
- 1 Controller: controller@makeplus.com
- 2 Participants
- 1 Exposant

**Credentials:**
- Password: `test123` (all users)

---

#### 4. create_test_data
**Purpose:** Create minimal test data for development

**Usage:**
```bash
python manage.py create_test_data
```

**Creates:**
- 1 Event
- 3 Rooms
- 4 Sessions

---

#### 5. reset_everything
**Purpose:** Delete all data and reset database

**Usage:**
```bash
python manage.py reset_everything
```

**Deletes:**
- All events
- All users (except superuser)
- All related data

**Warning:** This is destructive! Use only in development.

---

### Command Workflow

**Typical Setup:**
```bash
# 1. Reset database (optional)
python manage.py reset_everything

# 2. Create test data
python manage.py create_multi_event_data
python manage.py create_multi_event_users

# 3. Run server
python manage.py runserver
```

---

## Deployment Guide

### Environment Setup

**1. Install Python 3.11+**
```bash
python --version  # Should be 3.11 or higher
```

**2. Create Virtual Environment**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

**3. Install Dependencies**
```bash
pip install -r requirements.txt
```

**4. Configure Environment Variables**
Create `.env` file:
```env
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DATABASE_URL=postgresql://user:pass@localhost/dbname
CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
```

---

### Database Setup

**PostgreSQL (Production):**
```bash
# 1. Create database
createdb makeplus_db

# 2. Update settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'makeplus_db',
        'USER': 'your_user',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# 3. Run migrations
python manage.py migrate

# 4. Create superuser
python manage.py createsuperuser
```

---

### Static Files

**Collect Static Files:**
```bash
python manage.py collectstatic --noinput
```

**Configuration:**
```python
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = []
```

---

### CORS Configuration

**Production Settings:**
```python
CORS_ALLOWED_ORIGINS = [
    "https://yourdomain.com",
    "https://app.yourdomain.com",
    "http://localhost:8080",  # Flutter web development
]

CORS_ALLOW_CREDENTIALS = True  # Required for JWT authentication

CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]
```

---

### Running in Production

**Using Gunicorn:**
```bash
# Install gunicorn
pip install gunicorn

# Run server
gunicorn makeplus_api.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --timeout 120
```

**Systemd Service (Linux):**
```ini
[Unit]
Description=MakePlus Backend
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/path/to/makeplus_backend/makeplus_api
ExecStart=/path/to/venv/bin/gunicorn \
    --workers 4 \
    --bind unix:/run/makeplus.sock \
    makeplus_api.wsgi:application

[Install]
WantedBy=multi-user.target
```

---

### Nginx Configuration

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location /static/ {
        alias /path/to/makeplus_backend/makeplus_api/staticfiles/;
    }

    location /media/ {
        alias /path/to/makeplus_backend/makeplus_api/media/;
    }

    location / {
        proxy_pass http://unix:/run/makeplus.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

---

## API Usage Examples

### 1. User Registration & Login

**Register:**
```http
POST /api/auth/register/
Content-Type: application/json

{
  "username": "ahmed_benali",
  "email": "ahmed@example.com",
  "password": "securepassword123",
  "first_name": "Ahmed",
  "last_name": "Benali"
}
```

**Response:**
```json
{
  "id": 1,
  "username": "ahmed_benali",
  "email": "ahmed@example.com",
  "first_name": "Ahmed",
  "last_name": "Benali"
}
```

**Login:**
```http
POST /api/auth/login/
Content-Type: application/json

{
  "email": "ahmed@example.com",
  "password": "securepassword123",
  "event_id": "event-uuid"
}
```

**Response:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "username": "ahmed_benali",
    "email": "ahmed@example.com"
  },
  "event": {
    "id": "event-uuid",
    "name": "Tech Summit 2025"
  },
  "role": "gestionnaire_des_salles"
}
```

---

### 2. Event Management

**List Events:**
```http
GET /api/events/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

**Create Event:**
```http
POST /api/events/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
Content-Type: application/json

{
  "name": "Tech Summit 2025",
  "description": "Annual technology conference",
  "location": "Alger Centre des Congrès",
  "start_date": "2025-12-01T09:00:00Z",
  "end_date": "2025-12-03T18:00:00Z",
  "is_active": true
}
```

---

### 3. Session Management

**Create Session:**
```http
POST /api/sessions/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
Content-Type: application/json

{
  "event": "event-uuid",
  "room": "room-uuid",
  "title": "Intelligence Artificielle et ML",
  "description": "Introduction aux concepts de l'IA",
  "speaker_name": "Dr. Ahmed Benali",
  "speaker_title": "Chercheur en IA",
  "start_time": "2025-12-01T10:00:00Z",
  "end_time": "2025-12-01T11:30:00Z",
  "theme": "IA",
  "status": "pas_encore",
  "session_type": "atelier",
  "is_paid": true,
  "price": "5000.00"
}
```

**Start Session (Mark Live):**
```http
POST /api/sessions/{id}/mark_live/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

---

### 4. Announcements

**Create Announcement:**
```http
POST /api/annonces/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
Content-Type: application/json

{
  "event": "event-uuid",
  "title": "Pause déjeuner",
  "description": "Le déjeuner est servi à la cafétéria",
  "target": "all"
}
```

**List My Announcements (Auto-filtered by role):**
```http
GET /api/annonces/?event_id=event-uuid
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

---

### 5. Session Q&A

**Ask Question:**
```http
POST /api/session-questions/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
Content-Type: application/json

{
  "session": "session-uuid",
  "participant": "participant-uuid",
  "question_text": "Quelles sont les prérequis pour cet atelier?"
}
```

**Answer Question (Gestionnaire):**
```http
POST /api/session-questions/{id}/answer/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
Content-Type: application/json

{
  "answer_text": "Connaissance de base en Python requise"
}
```

---

### 6. Exposant Scans

**Scan Participant:**
```http
POST /api/exposant-scans/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
Content-Type: application/json

{
  "exposant": "exposant-uuid",
  "scanned_participant": "participant-uuid",
  "event": "event-uuid",
  "notes": "Intéressé par le produit X"
}
```

**Get My Scans with Statistics:**
```http
GET /api/exposant-scans/my_scans/?event_id=event-uuid
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

**Response:**
```json
{
  "total_visits": 42,
  "today_visits": 15,
  "scans": [
    {
      "id": "uuid",
      "scanned_participant": {...},
      "scanned_at": "2025-12-01T14:30:00Z",
      "notes": "Intéressé par le produit X"
    }
  ]
}
```

---

## System Status

### Current State: ✅ Production Ready

**Database:**
- ✅ All migrations applied (4 migrations)
- ✅ PostgreSQL compatible
- ✅ UUID primary keys
- ✅ Indexed for performance

**API:**
- ✅ 11 models fully implemented
- ✅ 50+ endpoints functional
- ✅ All CRUD operations working
- ✅ Custom actions implemented

**Security:**
- ✅ JWT authentication
- ✅ Role-based permissions
- ✅ CORS configured
- ✅ Token blacklisting

**Features:**
- ✅ Multi-event support
- ✅ File uploads (PDF)
- ✅ QR code system
- ✅ Real-time session status
- ✅ Paid ateliers
- ✅ Announcements
- ✅ Q&A system
- ✅ Room assignments
- ✅ Booth visit tracking

**Testing:**
- ✅ System check passes
- ✅ No import errors
- ✅ No syntax errors
- ✅ Test data commands working

---

## API Documentation URLs

**Interactive Documentation:**
- Swagger UI: `http://localhost:8000/swagger/`
- ReDoc: `http://localhost:8000/redoc/`
- OpenAPI Schema: `http://localhost:8000/swagger.json`

**Django Admin:**
- Admin Panel: `http://localhost:8000/admin/`

---

## Support & Maintenance

### Common Issues

**1. Migration Errors**
```bash
# Reset migrations (development only)
python manage.py reset_everything
python manage.py migrate

# Or manually
python manage.py migrate events zero
python manage.py migrate events
```

**2. JWT Token Issues**
```bash
# Token expired - get new token
POST /api/token/refresh/
{
  "refresh": "your-refresh-token"
}
```

**3. Permission Denied**
- Check user role assignment
- Verify JWT token includes correct event and role
- Ensure user has active assignment

**4. File Upload Fails**
- Check file size (max 10MB)
- Verify PDF format
- Ensure MEDIA_ROOT is writable

---

### Performance Optimization

**Database Queries:**
- Use `select_related()` for foreign keys
- Use `prefetch_related()` for many-to-many
- Add database indexes on frequently queried fields

**Caching:**
```python
# Cache event list
from django.core.cache import cache

events = cache.get('events_list')
if not events:
    events = Event.objects.all()
    cache.set('events_list', events, 300)  # 5 minutes
```

**Pagination:**
```python
# Default page size: 50
# Custom: ?page_size=100
```

---

### Monitoring

**Health Check Endpoint:**
```http
GET /api/health/
```

**Logs:**
```python
# Check Django logs
tail -f /var/log/django/makeplus.log
```

---

## Version History

**v1.1 (November 25, 2025)**
- ✅ Added Flutter frontend compatibility
- ✅ `/auth/me/` endpoint alias for user profile
- ✅ `/sessions/{id}/start/` and `/sessions/{id}/end/` aliases
- ✅ Enhanced CORS configuration with credentials support
- ✅ Updated documentation with integration notes

**v1.0 (November 25, 2025)**
- ✅ Complete backend restructure
- ✅ 11 models implemented
- ✅ 4 role system
- ✅ French language support
- ✅ Multi-event support
- ✅ File uploads
- ✅ All new features implemented

---

## Frontend Integration

**Flutter Integration Guide:** See `FLUTTER_INTEGRATION_GUIDE.md` for complete Flutter/Dart integration examples.

**Frontend Compatibility:**
- ✅ All endpoints tested with Flutter HTTP client
- ✅ URL aliases added for frontend conventions
- ✅ CORS properly configured for mobile/web apps
- ✅ JWT authentication with secure token storage
- ✅ File upload/download support

**Key Integration Points:**
1. Use `/api/auth/me/` for user profile (Flutter convention)
2. Use `/api/sessions/{id}/start/` and `/end/` for session control
3. Include `Authorization: Bearer <token>` header in all authenticated requests
4. Handle 401 errors with token refresh flow
5. Use multipart/form-data for file uploads

**Frontend Documentation:**
- Complete API integration examples
- Dart model classes for all entities
- Authentication flow implementation
- Error handling patterns
- Role-based UI examples

---

---

## Contact & Support

**Documentation:** This file  
**Repository:** makeplus-Django  
**Owner:** DjalilElz  
**Branch:** main  

---

**End of Documentation**
