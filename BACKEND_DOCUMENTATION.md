# MakePlus Backend - Complete Documentation

**Version:** 2.2  
**Last Updated:** December 21, 2025  
**Status:** ✅ Production Ready | ✅ Flutter Compatible | ✅ User-Level QR System

---

## 📄 NEW: Event PDF Files (Programme & Guide)

**See:** [EVENT_PDF_FILES_IMPLEMENTATION.md](EVENT_PDF_FILES_IMPLEMENTATION.md) for complete implementation details

✅ **Programme PDF:** Upload event schedule/program document  
✅ **Guide PDF:** Upload participant guide/handbook  
✅ **Fast Storage:** Optimized file system storage with lazy loading  
✅ **Full API Support:** Multipart/form-data upload with complete CRUD  
✅ **Production Ready:** CDN-ready, scalable to cloud storage (S3, Azure, etc.)  

**Quick Links:**
- [Upload Event PDFs](#file-uploads)
- [Event Model with PDF Fields](#event-model)
- [Complete Implementation Guide](EVENT_PDF_FILES_IMPLEMENTATION.md)

---

## 🎥 NEW: YouTube Live Streaming & Q&A System

**See:** [YOUTUBE_AND_QA_INTEGRATION.md](YOUTUBE_AND_QA_INTEGRATION.md) for complete Flutter integration guide

✅ **YouTube Live Streaming:** Sessions can include live YouTube stream URLs for hybrid events  
✅ **Q&A System:** Participants can ask questions on sessions, gestionnaires can answer  
✅ **Real-time Support:** Poll for updates during live sessions  
✅ **Full API Coverage:** Complete endpoints documented below  

**Quick Links:**
- [Session Questions API](#session-questions-qa-system-endpoints)
- [YouTube Live Integration](#youtube-live-streaming-integration)
- [Frontend Integration Examples](#youtube-live-streaming-integration)

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
- ✅ **YouTube live streaming integration** 🆕
- ✅ **Session Q&A system (participant questions + gestionnaire answers)** 🆕
- ✅ File uploads (PDF: programmes, guides, plans)
- ✅ Paid atelier system with access control
- ✅ Event announcements with role-based targeting
- ✅ Room staff assignments with time slots
- ✅ Exposant booth visit tracking
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
- `programme_file` (File) - 📄 **PDF programme** (event schedule/program)
- `guide_file` (File) - 📄 **PDF participant guide** (event handbook)
- `president` (FK User) - Event president
- `created_by` (FK User) - Creator
- `created_at` (DateTime) - Creation timestamp
- `updated_at` (DateTime) - Last update

**PDF Files (NEW):**
- ✅ Programme PDF: Event schedule, agenda, timetable
- ✅ Guide PDF: Participant handbook, information booklet
- ✅ Storage: Organized in `media/events/programmes/` and `media/events/guides/`
- ✅ Optional: Both fields are nullable (not all events need PDFs)
- ✅ Fast Access: URLs returned in API, files served directly by web server
- 📄 See [EVENT_PDF_FILES_IMPLEMENTATION.md](EVENT_PDF_FILES_IMPLEMENTATION.md) for details

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
  "programme_file": "http://localhost:8000/media/events/programmes/tech_summit_2025.pdf",
  "guide_file": "http://localhost:8000/media/events/guides/participant_guide.pdf",
  "president": 5,
  "created_by": 1,
  "created_at": "2025-12-21T10:00:00Z",
  "updated_at": "2025-12-21T10:00:00Z"
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

**Session Fields:**
- `youtube_live_url` - YouTube live stream URL (optional, for hybrid/remote participation)
- `is_live` - Boolean indicating if session is currently running
- `status` - Current session status

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
| GET | `/api/exposant-scans/export_excel/` | Export all visits to Excel | Exposant |

**Query Parameters (my_scans):**
- `event_id` - Filter by specific event (required)

**My Scans Response:**
```json
{
  "total_visits": 42,
  "today_visits": 15,
  "scans": [...]
}
```

**Export Excel Response:**
- **Content-Type:** `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- **File Name:** `Statistiques_Visiteurs_{username}_{timestamp}.xlsx`
- **Query Parameters:**
  - `action` (optional): `download` (default) or `share`
    - `download`: Forces file download (Content-Disposition: attachment) - for web/desktop
    - `share`: Returns file inline (Content-Disposition: inline) - for mobile share sheet
- **Response Headers:**
  - `Content-Disposition`: `attachment` or `inline` based on action
  - `X-Filename`: Original filename (useful for mobile apps)
- **Sheets:**
  - **Résumé Global:** Summary of all events (event name, total visits, first/last visit)
  - **{Event Name}:** Detailed visitor list for each event (date/time, name, email, badge ID, notes)
- **Features:**
  - Professional styling with headers
  - Auto-adjusted column widths
  - Total visits across all events
  - Separate sheet per event
  - All data from all events where exposant participated

**Usage Examples:**

Desktop/Web Download:
```http
GET /api/exposant-scans/export_excel/
Authorization: Bearer <exposant_jwt_token>
```

Mobile Share (for share_plus):
```http
GET /api/exposant-scans/export_excel/?action=share
Authorization: Bearer <exposant_jwt_token>
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

### Session Questions (Q&A System) Endpoints

| Method | Endpoint | Description | Permission |
|--------|----------|-------------|------------|
| GET | `/api/session-questions/` | List questions for sessions | Authenticated |
| POST | `/api/session-questions/` | Ask a question (participant) | Participant |
| GET | `/api/session-questions/{id}/` | Get question details | Authenticated |
| PUT/PATCH | `/api/session-questions/{id}/` | Update question | Owner or Gestionnaire |
| DELETE | `/api/session-questions/{id}/` | Delete question | Owner or Gestionnaire |
| POST | `/api/session-questions/{id}/answer/` | Answer question | Gestionnaire |

**Query Parameters:**
- `session` - Filter by session ID
- `participant` - Filter by participant ID
- `is_answered` - Filter by answered status (true/false)

**Ordering:**
- Default: `-asked_at` (newest first)
- Available: `asked_at`, `answered_at`

#### **Q&A System Overview**

The Q&A system allows participants to ask questions during sessions (conferences/ateliers) and gestionnaires to answer them in real-time or later.

**Workflow:**
1. **Participant asks question** during or after session
2. **Question appears** in Q&A list (unanswered)
3. **Gestionnaire reviews** questions
4. **Gestionnaire answers** question
5. **Participant sees answer** in real-time

**Question Model Structure:**
- `session` - Which session the question is for
- `participant` - Who asked the question
- `question_text` - The question content
- `is_answered` - Boolean flag (default: false)
- `answer_text` - The answer (blank until answered)
- `answered_by` - Gestionnaire who answered
- `asked_at` - When question was asked
- `answered_at` - When question was answered

---

#### **1. Ask a Question (Participant)**

**Request:**
```http
POST /api/session-questions/
Authorization: Bearer <participant_jwt_token>
Content-Type: application/json

{
  "session": "session-uuid",
  "question_text": "What are the key differences between MVP and Prototype?"
}
```

**Note:** The `participant` field is **automatically extracted** from the authenticated user and event context. You do NOT need to include it in the request body.

**Response (201 Created):**
```json
{
  "id": "question-uuid",
  "session": "session-uuid",
  "session_title": "Atelier: Product Development",
  "participant": "participant-uuid",
  "participant_name": "Ahmed Benali",
  "question_text": "What are the key differences between MVP and Prototype?",
  "is_answered": false,
  "answer_text": "",
  "answered_by": null,
  "answered_by_name": null,
  "asked_at": "2025-11-29T14:30:00Z",
  "answered_at": null
}
```

**Validation:**
- ✅ Participant must be authenticated (JWT token required)
- ✅ Must have valid event context (from JWT token)
- ✅ Participant profile must exist for the current event
- ✅ Session must exist
- ✅ Question text is required (max 1000 characters)

**Error Response (400 Bad Request) - No Event Context:**
```json
{
  "error": "No event context found. Please select an event first."
}
```

**Error Response (400 Bad Request) - No Participant Profile:**
```json
{
  "error": "Participant profile not found for this event"
}
```

---

#### **2. List Questions (Filter by Session)**

**Request:**
```http
GET /api/session-questions/?session=session-uuid
Authorization: Bearer <jwt_token>
```

**Response (200 OK):**
```json
{
  "count": 12,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "question-1-uuid",
      "session": "session-uuid",
      "session_title": "Atelier: Product Development",
      "participant": "participant-1-uuid",
      "participant_name": "Ahmed Benali",
      "question_text": "What are the key differences between MVP and Prototype?",
      "is_answered": true,
      "answer_text": "An MVP (Minimum Viable Product) is a basic version of your product with just enough features to satisfy early customers and provide feedback for future development. A Prototype is a preliminary model built to test a concept or process, often not meant for public release.",
      "answered_by": "gestionnaire-uuid",
      "answered_by_name": "Fatima Cherif",
      "asked_at": "2025-11-29T14:30:00Z",
      "answered_at": "2025-11-29T14:45:00Z"
    },
    {
      "id": "question-2-uuid",
      "session": "session-uuid",
      "session_title": "Atelier: Product Development",
      "participant": "participant-2-uuid",
      "participant_name": "Yasmine Khelifi",
      "question_text": "How long should MVP development take?",
      "is_answered": false,
      "answer_text": "",
      "answered_by": null,
      "answered_by_name": null,
      "asked_at": "2025-11-29T15:00:00Z",
      "answered_at": null
    }
  ]
}
```

---

#### **3. Filter Unanswered Questions**

**Request:**
```http
GET /api/session-questions/?session=session-uuid&is_answered=false
Authorization: Bearer <gestionnaire_jwt_token>
```

**Response (200 OK):**
```json
{
  "count": 3,
  "results": [
    {
      "id": "question-uuid",
      "participant_name": "Yasmine Khelifi",
      "question_text": "How long should MVP development take?",
      "is_answered": false,
      "asked_at": "2025-11-29T15:00:00Z"
    }
  ]
}
```

---

#### **4. Answer a Question (Gestionnaire Only)**

**Request:**
```http
POST /api/session-questions/{question_id}/answer/
Authorization: Bearer <gestionnaire_jwt_token>
Content-Type: application/json

{
  "answer_text": "MVP development typically takes 2-3 months, but it depends on the complexity of your product and the features you include. Focus on the core value proposition first."
}
```

**Response (200 OK):**
```json
{
  "id": "question-uuid",
  "session": "session-uuid",
  "session_title": "Atelier: Product Development",
  "participant": "participant-uuid",
  "participant_name": "Yasmine Khelifi",
  "question_text": "How long should MVP development take?",
  "is_answered": true,
  "answer_text": "MVP development typically takes 2-3 months, but it depends on the complexity of your product and the features you include. Focus on the core value proposition first.",
  "answered_by": "gestionnaire-uuid",
  "answered_by_name": "Fatima Cherif",
  "asked_at": "2025-11-29T15:00:00Z",
  "answered_at": "2025-11-29T15:20:00Z"
}
```

**Validation:**
- ✅ Only Gestionnaires can answer questions
- ✅ Answer text is required
- ✅ Automatically sets `is_answered=true`, `answered_by=user`, `answered_at=now()`

---

#### **5. Get Questions for Participant**

**Request:**
```http
GET /api/session-questions/?participant=participant-uuid
Authorization: Bearer <participant_jwt_token>
```

**Use Case:** Participant viewing their own questions across all sessions

**Response:**
```json
{
  "count": 5,
  "results": [
    {
      "session_title": "Atelier: Product Development",
      "question_text": "What are the key differences between MVP and Prototype?",
      "is_answered": true,
      "answer_text": "...",
      "asked_at": "2025-11-29T14:30:00Z"
    }
  ]
}
```

---

#### **Q&A Frontend Integration Guide**

**For Participants:**
1. **Viewing Session Q&A:**
   ```dart
   // Fetch questions for a session
   GET /api/session-questions/?session={session_id}&ordering=-asked_at
   
   // Display answered and unanswered questions
   // Show participant names, timestamps
   ```

2. **Asking Question:**
   ```dart
   // Submit question during/after session
   // NOTE: participant field is auto-extracted from JWT token
   POST /api/session-questions/
   {
     "session": session_id,
     "question_text": user_input
   }
   
   // Show success message
   // No need to include participant_id in request body
   ```

3. **Viewing My Questions:**
   ```dart
   // Show all participant's questions
   GET /api/session-questions/?participant={participant_id}
   
   // Filter by answered/unanswered
   GET /api/session-questions/?participant={participant_id}&is_answered=false
   ```

**For Gestionnaires:**
1. **View Unanswered Questions:**
   ```dart
   // Dashboard: Show pending questions
   GET /api/session-questions/?is_answered=false&ordering=asked_at
   
   // Group by session
   ```

2. **Answer Questions:**
   ```dart
   // Answer modal/dialog
   POST /api/session-questions/{id}/answer/
   {
     "answer_text": gestionnaire_response
   }
   
   // Update UI immediately
   ```

**Real-time Updates (Optional):**
- Use polling: Fetch questions every 30 seconds during live sessions
- WebSocket: For real-time Q&A (future enhancement)

---

### YouTube Live Streaming Integration

#### **Overview**

Each session (conference or atelier) can have a YouTube live stream URL for remote/hybrid participation.

**Session Model Field:**
- `youtube_live_url` - URLField storing YouTube live stream URL (optional)

**Use Cases:**
- **Hybrid Events:** Participants attend physically + watch online
- **Recorded Sessions:** YouTube live streams auto-save recordings
- **Remote Access:** Participants who can't attend physically

---

#### **Session Response with YouTube Live URL**

**Example Session Response:**
```json
{
  "id": "session-uuid",
  "title": "Conférence: Fundraising Strategies",
  "description": "Learn how to raise funds for your startup",
  "speaker_name": "Karim Benyoucef",
  "speaker_title": "Angel Investor",
  "room_name": "Salle Principale",
  "start_time": "2025-11-30T09:00:00Z",
  "end_time": "2025-11-30T10:30:00Z",
  "session_type": "conference",
  "status": "en_cours",
  "is_paid": false,
  "youtube_live_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "cover_image_url": "https://...",
  "is_live": true
}
```

**Key Fields:**
- `youtube_live_url` - Full YouTube URL (null if no livestream)
- `is_live` - Boolean indicating if session is currently live
- `status` - Session status (pas_encore, en_cours, termine)

---

#### **Frontend Integration - YouTube Live**

**1. Check if Session Has Live Stream:**
```dart
// Parse session response
if (session.youtube_live_url != null && session.youtube_live_url.isNotEmpty) {
  // Show YouTube embed or "Watch Live" button
  showYouTubeLiveButton();
}
```

**2. Display YouTube Embed (Web):**
```html
<!-- Extract video ID from URL -->
<!-- https://www.youtube.com/watch?v=VIDEO_ID -->
<iframe 
  width="560" 
  height="315" 
  src="https://www.youtube.com/embed/VIDEO_ID" 
  frameborder="0" 
  allowfullscreen>
</iframe>
```

**3. Open YouTube App (Mobile Flutter):**
```dart
import 'package:url_launcher/url_launcher.dart';

Future<void> openYouTubeLive(String youtubeUrl) async {
  final Uri url = Uri.parse(youtubeUrl);
  
  if (await canLaunchUrl(url)) {
    await launchUrl(
      url,
      mode: LaunchMode.externalApplication, // Opens YouTube app
    );
  } else {
    // Show error: Cannot open YouTube
  }
}
```

**4. Embedded Player (Flutter - YouTube Player Plugin):**
```dart
import 'package:youtube_player_flutter/youtube_player_flutter.dart';

// Extract video ID from URL
String? videoId = YoutubePlayer.convertUrlToId(session.youtube_live_url);

if (videoId != null) {
  YoutubePlayerController controller = YoutubePlayerController(
    initialVideoId: videoId,
    flags: YoutubePlayerFlags(
      autoPlay: false,
      mute: false,
      isLive: true, // Enable live stream mode
    ),
  );
  
  return YoutubePlayer(
    controller: controller,
    showVideoProgressIndicator: true,
  );
}
```

**5. Show Live Indicator:**
```dart
// When session is live AND has YouTube URL
if (session.is_live && session.youtube_live_url != null) {
  return Row(
    children: [
      Container(
        decoration: BoxDecoration(
          color: Colors.red,
          borderRadius: BorderRadius.circular(4),
        ),
        padding: EdgeInsets.symmetric(horizontal: 8, vertical: 4),
        child: Row(
          children: [
            Icon(Icons.circle, color: Colors.white, size: 8),
            SizedBox(width: 4),
            Text('EN DIRECT', style: TextStyle(color: Colors.white)),
          ],
        ),
      ),
      SizedBox(width: 8),
      TextButton(
        onPressed: () => openYouTubeLive(session.youtube_live_url),
        child: Text('Regarder en ligne'),
      ),
    ],
  );
}
```

---

#### **YouTube Live URL Management (Gestionnaires)**

**Create Session with YouTube Live:**
```http
POST /api/sessions/
Authorization: Bearer <gestionnaire_jwt_token>
Content-Type: application/json

{
  "event": "event-uuid",
  "room": "room-uuid",
  "title": "Conférence: Startup Success Stories",
  "start_time": "2025-11-30T14:00:00Z",
  "end_time": "2025-11-30T16:00:00Z",
  "session_type": "conference",
  "youtube_live_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
}
```

**Update YouTube URL:**
```http
PATCH /api/sessions/{session_id}/
Authorization: Bearer <gestionnaire_jwt_token>
Content-Type: application/json

{
  "youtube_live_url": "https://www.youtube.com/watch?v=NEW_VIDEO_ID"
}
```

**Remove YouTube URL:**
```http
PATCH /api/sessions/{session_id}/
{
  "youtube_live_url": ""
}
```

---

#### **YouTube Live Best Practices**

**For Event Organizers:**
1. **Setup YouTube Live:** Create YouTube live stream before event
2. **Add URL:** Copy YouTube URL → paste in session creation/edit
3. **Test Stream:** Verify stream works before session starts
4. **Start Session:** Mark session as live when starting
5. **Recording:** YouTube auto-saves stream recording

**For Frontend Developers:**
1. **Null Checks:** Always check if `youtube_live_url` exists
2. **URL Validation:** Validate YouTube URL format
3. **Error Handling:** Handle cases where video doesn't exist
4. **Mobile UX:** Provide both "Open YouTube App" and "Embedded Player" options
5. **Live Indicator:** Show visual indicator when session is live with streaming

**YouTube URL Formats Supported:**
- `https://www.youtube.com/watch?v=VIDEO_ID`
- `https://youtu.be/VIDEO_ID`
- `https://www.youtube.com/live/VIDEO_ID`

**Example Flutter Helper:**
```dart
class YouTubeHelper {
  static String? extractVideoId(String? url) {
    if (url == null || url.isEmpty) return null;
    
    final regExp = RegExp(
      r'(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})',
    );
    
    final match = regExp.firstMatch(url);
    return match?.group(1);
  }
  
  static bool hasValidYouTubeUrl(String? url) {
    return extractVideoId(url) != null;
  }
}
```

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

### 📋 Overview

MakePlus backend supports PDF file uploads for events and participants. The system is optimized for fast response times with efficient file storage and lazy loading.

**📄 For Complete Implementation Details:** See [EVENT_PDF_FILES_IMPLEMENTATION.md](EVENT_PDF_FILES_IMPLEMENTATION.md)

### Supported Files

| Model | Field | Type | Purpose | Storage Path |
|-------|-------|------|---------|--------------|
| Event | `programme_file` | PDF | Event programme/schedule | `media/events/programmes/` |
| Event | `guide_file` | PDF | Participant guide/handbook | `media/events/guides/` |
| Participant | `plan_file` | PDF | Exposant booth plan | `media/plans/` |

### Key Features

✅ **Optimized Storage:** File system storage for fastest access  
✅ **Lazy Loading:** Only URLs returned in API (not file content)  
✅ **Organized Structure:** Separate directories per file type  
✅ **Optional Fields:** Not all events require PDF files  
✅ **Scalable:** Easy migration to cloud storage (S3, CloudFront, Azure, etc.)  
✅ **Production Ready:** Nginx/Apache/CDN support for direct file serving

### Upload Configuration

**File Storage Settings:**
```python
# settings.py
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Optional: File size limits
DATA_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB
```

**URL Configuration:**
```python
# urls.py
from django.conf import settings
from django.conf.urls.static import static

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

**Storage Structure:**
```
makeplus_api/
├── media/
│   └── events/
│       ├── programmes/
│       │   ├── event1_programme.pdf
│       │   └── event2_programme.pdf
│       └── guides/
│           ├── event1_guide.pdf
│           └── event2_guide.pdf
```

### Upload Example (Event PDFs)

**Multipart Form Data Request:**
```http
POST /api/events/
Content-Type: multipart/form-data
Authorization: Bearer YOUR_JWT_TOKEN

name: "Tech Summit 2025"
description: "Annual technology summit"
start_date: "2025-12-01T09:00:00Z"
end_date: "2025-12-03T18:00:00Z"
location: "Paris Convention Center"
status: "upcoming"
programme_file: [PDF file - event program]
guide_file: [PDF file - participant guide]
```

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Tech Summit 2025",
  "description": "Annual technology summit",
  "start_date": "2025-12-01T09:00:00Z",
  "end_date": "2025-12-03T18:00:00Z",
  "location": "Paris Convention Center",
  "status": "upcoming",
  "programme_file": "http://localhost:8000/media/events/programmes/programme_abc123.pdf",
  "guide_file": "http://localhost:8000/media/events/guides/guide_xyz789.pdf",
  "created_at": "2025-12-21T10:30:00Z",
  "updated_at": "2025-12-21T10:30:00Z"
}
```

### Update Only PDFs (PATCH Request)

```http
PATCH /api/events/{event_id}/
Content-Type: multipart/form-data
Authorization: Bearer YOUR_JWT_TOKEN

programme_file: [New PDF file]
```

### Client Examples

**Python (requests):**
```python
import requests

url = "http://localhost:8000/api/events/"
headers = {"Authorization": "Bearer YOUR_JWT_TOKEN"}

files = {
    'programme_file': open('programme.pdf', 'rb'),
    'guide_file': open('guide.pdf', 'rb')
}

data = {
    'name': 'Tech Summit 2025',
    'start_date': '2025-12-01T09:00:00Z',
    'end_date': '2025-12-03T18:00:00Z',
    'location': 'Paris Convention Center',
    'status': 'upcoming'
}

response = requests.post(url, headers=headers, data=data, files=files)
print(response.json())
```

**Flutter:**
```dart
import 'package:http/http.dart' as http;

Future<void> uploadEventPDFs() async {
  var uri = Uri.parse('http://localhost:8000/api/events/');
  var request = http.MultipartRequest('POST', uri);
  
  request.headers['Authorization'] = 'Bearer YOUR_JWT_TOKEN';
  
  request.fields['name'] = 'Tech Summit 2025';
  request.fields['start_date'] = '2025-12-01T09:00:00Z';
  request.fields['end_date'] = '2025-12-03T18:00:00Z';
  request.fields['location'] = 'Paris Convention Center';
  request.fields['status'] = 'upcoming';
  
  request.files.add(
    await http.MultipartFile.fromPath(
      'programme_file',
      '/path/to/programme.pdf',
    ),
  );
  
  request.files.add(
    await http.MultipartFile.fromPath(
      'guide_file',
      '/path/to/guide.pdf',
    ),
  );
  
  var response = await request.send();
  var responseData = await response.stream.bytesToString();
  print(responseData);
}
```

**cURL:**
```bash
curl -X POST http://localhost:8000/api/events/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "name=Tech Summit 2025" \
  -F "start_date=2025-12-01T09:00:00Z" \
  -F "end_date=2025-12-03T18:00:00Z" \
  -F "location=Paris Convention Center" \
  -F "status=upcoming" \
  -F "programme_file=@/path/to/programme.pdf" \
  -F "guide_file=@/path/to/guide.pdf"
```

### File Access & Download

**Direct URL Access:**
```
http://localhost:8000/media/events/programmes/programme_abc123.pdf
http://localhost:8000/media/events/guides/guide_xyz789.pdf
```

**In Flutter (Download/View):**
```dart
import 'package:url_launcher/url_launcher.dart';

Future<void> openPDF(String pdfUrl) async {
  if (await canLaunch(pdfUrl)) {
    await launch(pdfUrl);
  }
}

// Usage
openPDF(event.programmeFile); // Opens PDF in browser/viewer
```

### Production Deployment

**Option 1: Nginx Static Files**
```nginx
location /media/ {
    alias /path/to/makeplus_api/media/;
    expires 30d;
    add_header Cache-Control "public, immutable";
}
```

**Option 2: AWS S3**
```python
# Install: pip install boto3 django-storages
INSTALLED_APPS += ['storages']
AWS_STORAGE_BUCKET_NAME = 'makeplus-media'
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
```

**Option 3: CDN (CloudFlare, CloudFront)**
- Point CDN to media directory
- Configure CORS for cross-origin access
- Set cache headers for performance

### Performance Benefits

1. ⚡ **Fast API Response:** Only URLs returned, not file content
2. 💾 **No Database Bloat:** Files stored on filesystem, not in DB
3. 🚀 **Direct Serving:** Web server serves files directly (bypasses Django)
4. 📦 **Lazy Loading:** Clients download files only when needed
5. 🌍 **CDN Ready:** Easy integration with global CDN networks

### Security Considerations

**Current:**
- ✅ JWT authentication required for upload
- ✅ Permission checks (only authorized users can create/update events)
- ✅ Relative path storage in database

**Recommended Enhancements:**
```python
from django.core.validators import FileExtensionValidator

programme_file = models.FileField(
    upload_to='events/programmes/',
    validators=[FileExtensionValidator(['pdf'])],
    help_text="Event programme PDF (max 10MB)"
)
```

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

## Admin Dashboard (Web Interface)

### Overview

The MakePlus backend includes a web-based admin dashboard for event management. Staff users can create and manage events through an intuitive multi-step form interface.

**Access:** `http://localhost:8000/dashboard/`  
**Authentication:** Django session-based (staff users only)  
**Documentation:** See [DASHBOARD_PDF_UPLOAD.md](DASHBOARD_PDF_UPLOAD.md) for PDF upload details

### Key Features

#### 1. **Event Creation (Multi-Step)**

**Step 1: Event Details**
- Basic information (name, dates, location)
- Event status configuration
- Logo and banner URLs
- Organizer contact
- **NEW:** Programme PDF upload 📄
- **NEW:** Guide PDF upload 📄
- Number of rooms

**Step 2: Room Configuration**
- Add multiple rooms/salles
- Set capacity and descriptions

**Step 3: Session Management**
- Create sessions for each room
- Configure paid ateliers
- Set speakers and themes

**Step 4: User Assignment**
- Assign roles to users
- Create new users
- Manage event team

#### 2. **Event Management**

**Event List:**
- View all events with statistics
- Filter by status
- Quick access to details

**Event Detail:**
- Complete event overview
- Statistics dashboard
- Room and session management
- User management
- PDF document links

**Event Edit:**
- Update event information
- Replace PDF documents
- View current files with direct links

#### 3. **PDF Document Management** 🆕

**Upload PDFs During Creation:**
- Programme PDF (event schedule)
- Guide PDF (participant handbook)
- Optional fields
- PDF-only file selection

**Manage PDFs in Edit Form:**
- View current PDF files
- Download links for existing files
- Upload new files to replace old
- Keep existing files by leaving blank

**Features:**
- 📄 Clear section: "Event Documents (Optional)"
- 🎨 Icons for visual identification
- 📝 Help text for each field
- 🔗 "View PDF" links in edit form
- ✅ Browser-level PDF validation

**File Organization:**
- Programme PDFs: `media/events/programmes/`
- Guide PDFs: `media/events/guides/`
- Direct URL access
- Available via API

#### 4. **Additional Features**

- Session Q&A management
- Announcement creation
- User role assignment
- Room staff scheduling
- Statistics and analytics
- Caisse management integration

### Technical Details

**Form Implementation:**
```python
# forms.py
class EventDetailsForm(forms.ModelForm):
    fields = [
        'name', 'description', 'start_date', 'end_date',
        'location', 'status', 'organizer_contact',
        'programme_file', 'guide_file'  # PDF fields
    ]
```

**View Processing:**
```python
# views.py
def event_create_step1(request):
    if request.method == 'POST':
        form = EventDetailsForm(request.POST, request.FILES)
        # Handles file uploads automatically
```

**Template:**
```html
<!-- event_create_step1.html -->
<form method="post" enctype="multipart/form-data">
    <!-- PDF upload fields with accept=".pdf" -->
</form>
```

### Dashboard URLs

| URL | Purpose |
|-----|---------|
| `/dashboard/` | Home (event list) |
| `/dashboard/login/` | Staff login |
| `/dashboard/logout/` | Logout |
| `/dashboard/event/create/` | Create event (Step 1) |
| `/dashboard/event/{id}/` | Event detail |
| `/dashboard/event/{id}/edit/` | Edit event |
| `/dashboard/event/{id}/delete/` | Delete event |

### Access Control

**Required:** Staff or superuser status (`is_staff=True` or `is_superuser=True`)

**Login Redirect:**
- Non-staff users: Error message
- Unauthenticated: Redirect to login

---

## Version History

**v2.2 (December 21, 2025)**
- ✅ Event PDF files implementation (programme_file, guide_file)
- ✅ Event image uploads (logo, banner) - replaced URL fields with ImageField
- ✅ Dashboard PDF upload in event creation form
- ✅ Dashboard PDF upload in event edit form
- ✅ Dashboard image upload with thumbnails and preview
- ✅ Complete PDF documentation package created
- ✅ Complete image upload documentation created
- ✅ API support for multipart/form-data uploads
- ✅ Optimized file storage with lazy loading
- ✅ Image validation with Pillow
- ✅ Updated backend documentation

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

## 🚪 Room Assignment System for Organisateurs, Gestionnaires & Contrôleurs

### Overview

The system allows assigning specific rooms to users with the following roles:
- **Organisateur** (Organizer)
- **Gestionnaire des Salles** (Room Manager)
- **Contrôleur des Badges** (Badge Controller)

Room assignments are stored in the `UserEventAssignment` model's `metadata` field as JSON.

### Data Structure

**UserEventAssignment Model:**
```python
class UserEventAssignment(models.Model):
    user = models.ForeignKey(User)
    event = models.ForeignKey(Event)
    role = models.CharField()  # organisateur, gestionnaire_des_salles, controlleur_des_badges, etc.
    metadata = models.JSONField(default=dict, blank=True)  # Room assignment stored here
    assigned_at = models.DateTimeField(auto_now_add=True)
    assigned_by = models.ForeignKey(User, related_name='assigned_users')
    is_active = models.BooleanField(default=True)
```

**Room Assignment in Metadata:**
```json
{
    "assigned_room_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Retrieving Room Assignment (Backend Logic)

**Python Example (Dashboard):**
```python
# Get user's event assignment
assignment = UserEventAssignment.objects.get(user=user, event=event)

# Check if role can have room assignment
if assignment.role in ['organisateur', 'gestionnaire_des_salles', 'controlleur_des_badges']:
    # Get room ID from metadata
    room_id = assignment.metadata.get('assigned_room_id')
    
    if room_id:
        try:
            assigned_room = Room.objects.get(id=room_id)
            print(f"Assigned to: {assigned_room.name}")
        except Room.DoesNotExist:
            print("Room not found")
    else:
        print("No room assigned")
else:
    print("This role doesn't require room assignment")
```

### API Integration for Mobile Apps

#### 1. Get User's Event Assignments with Room Info

**Endpoint:** `GET /api/events/{event_id}/users/`

**Response includes UserEventAssignment data:**
```json
{
    "id": "assignment-uuid",
    "user": {
        "id": 1,
        "username": "john_manager",
        "email": "john@example.com",
        "first_name": "John",
        "last_name": "Manager"
    },
    "event": {
        "id": "event-uuid",
        "name": "Tech Conference 2025"
    },
    "role": "gestionnaire_des_salles",
    "metadata": {
        "assigned_room_id": "room-uuid"
    },
    "assigned_at": "2025-12-22T10:30:00Z",
    "assigned_by": {
        "id": 2,
        "username": "admin"
    },
    "is_active": true
}
```

#### 2. Get Room Details

**Endpoint:** `GET /api/events/{event_id}/rooms/{room_id}/`

**Response:**
```json
{
    "id": "room-uuid",
    "event": "event-uuid",
    "name": "Auditorium A",
    "capacity": 200,
    "description": "Main conference hall",
    "location": "Ground Floor, Section A",
    "created_at": "2025-12-01T09:00:00Z"
}
```

#### 3. Get All Rooms for an Event

**Endpoint:** `GET /api/events/{event_id}/rooms/`

**Response:**
```json
[
    {
        "id": "room1-uuid",
        "name": "Auditorium A",
        "capacity": 200,
        ...
    },
    {
        "id": "room2-uuid",
        "name": "Workshop Room B",
        "capacity": 50,
        ...
    }
]
```

### Flutter/Dart Implementation Guide

#### Step 1: Define Models

```dart
class UserEventAssignment {
  final String id;
  final User user;
  final Event event;
  final String role;
  final Map<String, dynamic>? metadata;
  final DateTime assignedAt;
  final bool isActive;
  
  // Helper getter for assigned room ID
  String? get assignedRoomId {
    if (metadata == null) return null;
    return metadata!['assigned_room_id'] as String?;
  }
  
  // Check if role can have room assignment
  bool get canHaveRoomAssignment {
    return ['organisateur', 'gestionnaire_des_salles', 'controlleur_des_badges']
        .contains(role);
  }
  
  factory UserEventAssignment.fromJson(Map<String, dynamic> json) {
    return UserEventAssignment(
      id: json['id'],
      user: User.fromJson(json['user']),
      event: Event.fromJson(json['event']),
      role: json['role'],
      metadata: json['metadata'] as Map<String, dynamic>?,
      assignedAt: DateTime.parse(json['assigned_at']),
      isActive: json['is_active'],
    );
  }
}

class Room {
  final String id;
  final String eventId;
  final String name;
  final int capacity;
  final String? description;
  final String? location;
  
  factory Room.fromJson(Map<String, dynamic> json) {
    return Room(
      id: json['id'],
      eventId: json['event'],
      name: json['name'],
      capacity: json['capacity'],
      description: json['description'],
      location: json['location'],
    );
  }
}
```

#### Step 2: API Service

```dart
class ApiService {
  final String baseUrl = 'https://makeplus-django-5.onrender.com/api';
  final String? authToken;
  
  // Get user's assignments for an event
  Future<List<UserEventAssignment>> getUserAssignments(String eventId) async {
    final response = await http.get(
      Uri.parse('$baseUrl/events/$eventId/users/'),
      headers: {
        'Authorization': 'Bearer $authToken',
        'Content-Type': 'application/json',
      },
    );
    
    if (response.statusCode == 200) {
      final List data = json.decode(response.body);
      return data.map((json) => UserEventAssignment.fromJson(json)).toList();
    }
    throw Exception('Failed to load assignments');
  }
  
  // Get room details
  Future<Room> getRoom(String eventId, String roomId) async {
    final response = await http.get(
      Uri.parse('$baseUrl/events/$eventId/rooms/$roomId/'),
      headers: {
        'Authorization': 'Bearer $authToken',
        'Content-Type': 'application/json',
      },
    );
    
    if (response.statusCode == 200) {
      return Room.fromJson(json.decode(response.body));
    }
    throw Exception('Failed to load room');
  }
  
  // Get all rooms for event
  Future<List<Room>> getEventRooms(String eventId) async {
    final response = await http.get(
      Uri.parse('$baseUrl/events/$eventId/rooms/'),
      headers: {
        'Authorization': 'Bearer $authToken',
        'Content-Type': 'application/json',
      },
    );
    
    if (response.statusCode == 200) {
      final List data = json.decode(response.body);
      return data.map((json) => Room.fromJson(json)).toList();
    }
    throw Exception('Failed to load rooms');
  }
}
```

#### Step 3: Usage in Widget

```dart
class UserAssignmentWidget extends StatefulWidget {
  final String eventId;
  final String userId;
  
  @override
  _UserAssignmentWidgetState createState() => _UserAssignmentWidgetState();
}

class _UserAssignmentWidgetState extends State<UserAssignmentWidget> {
  UserEventAssignment? assignment;
  Room? assignedRoom;
  bool isLoading = true;
  
  @override
  void initState() {
    super.initState();
    loadAssignmentAndRoom();
  }
  
  Future<void> loadAssignmentAndRoom() async {
    try {
      // Get user's assignment
      final assignments = await ApiService().getUserAssignments(widget.eventId);
      assignment = assignments.firstWhere((a) => a.user.id == widget.userId);
      
      // If user has room assignment capability and a room assigned
      if (assignment!.canHaveRoomAssignment && assignment!.assignedRoomId != null) {
        assignedRoom = await ApiService().getRoom(
          widget.eventId,
          assignment!.assignedRoomId!,
        );
      }
      
      setState(() {
        isLoading = false;
      });
    } catch (e) {
      print('Error loading assignment: $e');
      setState(() {
        isLoading = false;
      });
    }
  }
  
  @override
  Widget build(BuildContext context) {
    if (isLoading) {
      return CircularProgressIndicator();
    }
    
    return Card(
      child: ListTile(
        title: Text('Role: ${assignment?.role ?? "N/A"}'),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (assignment?.canHaveRoomAssignment == true)
              Text(
                assignedRoom != null
                    ? 'Assigned Room: ${assignedRoom!.name}'
                    : 'No room assigned',
                style: TextStyle(
                  color: assignedRoom != null ? Colors.green : Colors.grey,
                ),
              ),
            if (assignedRoom != null) ...[
              SizedBox(height: 4),
              Text('Capacity: ${assignedRoom!.capacity}'),
              if (assignedRoom!.location != null)
                Text('Location: ${assignedRoom!.location}'),
            ],
          ],
        ),
        leading: Icon(
          assignedRoom != null ? Icons.meeting_room : Icons.person,
          color: assignedRoom != null ? Colors.green : Colors.grey,
        ),
      ),
    );
  }
}
```

### Summary for Mobile Developers

**To retrieve assigned room information:**

1. **Fetch user's event assignment** → Get `metadata.assigned_room_id`
2. **Check if role requires room** → Only `organisateur`, `gestionnaire_des_salles`, `controlleur_des_badges`
3. **Fetch room details** → Use room ID to get full room information
4. **Display in UI** → Show room name, capacity, location

**Key Points:**
- Room assignment is **optional** even for roles that support it
- Always check if `assigned_room_id` exists in metadata before fetching room details
- Room IDs are UUIDs (e.g., `"550e8400-e29b-41d4-a716-446655440000"`)
- Use appropriate error handling for missing or invalid room IDs
- Cache room data to reduce API calls

---

## 🔧 Fixing Missing Room Assignments (Backend)

If existing users don't have room assignments in their metadata, use one of these methods:

### Method 1: Management Command (Recommended)

```bash
# List all assignments missing rooms
python manage.py fix_room_assignments

# Fix specific assignment
python manage.py fix_room_assignments \
    --assignment-id "25" \
    --room-id "room-uuid-here"

# Dry run (preview changes)
python manage.py fix_room_assignments \
    --assignment-id "25" \
    --room-id "room-uuid-here" \
    --dry-run
```

### Method 2: Quick Fix Script

For specific case (e.g., Assignment ID 25):

```bash
python manage.py shell < fix_assignment_25.py
```

Or in Django shell:
```python
from fix_assignment_25 import fix_assignment
fix_assignment()
```

### Method 3: Django Admin Panel

1. Go to **Django Admin** → **User Event Assignments**
2. Find the assignment for user in the event
3. Edit the **Metadata** field:
   ```json
   {"assigned_room_id": "your-room-uuid-here"}
   ```
4. Save

### Method 4: Direct Django Shell

```python
from events.models import UserEventAssignment, Room

# Get the assignment
assignment = UserEventAssignment.objects.get(id="25")

# Get the room
room = Room.objects.get(event=assignment.event, name="Aula")

# Assign room
assignment.metadata = assignment.metadata or {}
assignment.metadata['assigned_room_id'] = str(room.id)
assignment.save()

print(f"✓ Assigned {room.name} to {assignment.user.email}")
```

### Getting Room UUIDs

```python
from events.models import Room, Event

# List all rooms for an event
event = Event.objects.get(name="AOPA")
for room in Room.objects.filter(event=event):
    print(f"{room.name}: {room.id}")
```

**Output example:**
```
Aula: 550e8400-e29b-41d4-a716-446655440000
Workshop Room: 660e8400-e29b-41d4-a716-446655440001
```

---

## Contact & Support

**Documentation:** This file  
**Repository:** makeplus-Django  
**Owner:** DjalilElz  
**Branch:** main  

---

**End of Documentation**
