# 📘 MakePlus API - Complete Database Structure & Workflow Documentation

## 🏗️ Database Structure

### Core Entities

#### 1. **Event** (Main Entity)
Each event is completely independent with its own users, rooms, and sessions.

```python
Event:
  - id (UUID)
  - name
  - description
  - start_date, end_date
  - location, location_details
  - logo_url, banner_url
  - status (upcoming/active/completed/cancelled)
  - settings (JSON)
  - themes (JSON Array)
  - total_participants, total_exhibitors, total_rooms (auto-calculated)
  - organizer_contact
  - created_at, updated_at
  - created_by → User
```

#### 2. **UserEventAssignment** (User-Event-Role Relationship)
Links users to events with specific roles. **Each user can have different roles in different events.**

```python
UserEventAssignment:
  - user → User
  - event → Event
  - role: 'organisateur' | 'controlleur_des_badges' | 'participant' | 'exposant'
  - is_active (boolean)
  - assigned_at
  - assigned_by → User
  
Unique Constraint: (user, event) - One user can only have ONE role per event
```

**User Roles Explained:**
- **Organisateur** (Organizer): Full control over event, can create/edit everything
- **Contrôleur des Badges** (Badge Controller): Can verify QR codes, grant room access
- **Participant**: Regular attendee with a badge, can access allowed rooms
- **Exposant** (Exhibitor): Similar to participant but represents exhibitors/vendors

#### 3. **Room** (Event Spaces)
Physical spaces within an event venue.

```python
Room:
  - id (UUID)
  - event → Event
  - name
  - description
  - capacity (integer)
  - location (within venue)
  - current_participants (auto-updated)
  - is_active
  - created_at, updated_at
  - created_by → User
  
Unique Constraint: (event, name) - Room names unique per event
```

#### 4. **Session** (Conference/Workshop)
Scheduled activities within rooms.

```python
Session:
  - id (UUID)
  - event → Event
  - room → Room
  - title, description
  - start_time, end_time
  - speaker_name, speaker_title, speaker_bio, speaker_photo_url
  - theme
  - status (scheduled/live/completed/cancelled)
  - cover_image_url
  - metadata (JSON)
  - created_at, updated_at
  - created_by → User
```

#### 5. **Participant** (Badge Holder)
Represents participants and exhibitors who have badges for entry.

```python
Participant:
  - user → User
  - event → Event
  - badge_id (unique, e.g., "TECH-175A318B")
  - qr_code_data (for scanning)
  - is_checked_in (boolean)
  - checked_in_at
  - allowed_rooms ← ManyToMany → Room
  - created_at, updated_at
  
Unique Constraint: (user, event) - One badge per user per event
```

#### 6. **RoomAccess** (Access Logs)
Tracks room entry/exit for participants.

```python
RoomAccess:
  - participant → Participant
  - room → Room
  - session → Session (optional)
  - accessed_at
  - verified_by → User (controller who verified)
  - status (granted/denied)
  - denial_reason
```

---

## 🔄 Data Flow & Relationships

### Event-Centric Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        EVENT                                │
│  (TechSummit Algeria 2025)                                  │
└─────────────────────────────────────────────────────────────┘
        │
        ├──→ UserEventAssignments (Who belongs to this event)
        │       ├─→ Organisateur (tech_organisateur)
        │       ├─→ Contrôleur (tech_controleur)
        │       ├─→ Participants (tech_participant1, tech_participant2)
        │       └─→ Exposants (tech_exposant1, tech_exposant2)
        │
        ├──→ Rooms (Event spaces)
        │       ├─→ Salle Principale (capacity: 300)
        │       ├─→ Salle Atelier A (capacity: 100)
        │       ├─→ Salle Atelier B (capacity: 80)
        │       └─→ Hall Exposition (capacity: 500)
        │
        ├──→ Sessions (Scheduled activities)
        │       ├─→ Cérémonie d'Ouverture
        │       ├─→ Intelligence Artificielle - Tendances 2025
        │       └─→ Développement Web Moderne
        │
        └──→ Participants (Badge holders)
                ├─→ tech_participant1 (Badge: TECH-175A318B)
                ├─→ tech_participant2 (Badge: TECH-C29D27A5)
                ├─→ tech_exposant1 (Badge: TECH-D4E5DB88)
                └─→ tech_exposant2 (Badge: TECH-F051C722)
```

### User Workflow Example

**Scenario: A user attending multiple events**

```
User: karim@example.com
│
├──→ Event 1: TechSummit Algeria 2025
│    └─→ Role: Participant (tech_participant1)
│        └─→ Badge: TECH-175A318B
│        └─→ Can access: All 4 rooms
│
└──→ Event 2: StartupWeek Oran 2025
     └─→ Role: Organisateur (different role!)
         └─→ Can manage: All event aspects
```

---

## 🔐 Authentication & Authorization

### Login Process

1. **User Login** → POST `/api/auth/login/`
   ```json
   {
     "username": "tech_organisateur",
     "password": "makeplus2025"
   }
   ```

2. **Response** → JWT Tokens + User Info
   ```json
   {
     "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
     "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
     "user": {
       "id": 1,
       "username": "tech_organisateur",
       "email": "tech_organisateur@makeplus.com",
       "first_name": "Ahmed",
       "last_name": "Benali"
     }
   }
   ```

3. **Access Resources** → Use access token in header
   ```
   Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
   ```

### Permission System

**Role-Based Permissions:**

| Action | Organisateur | Contrôleur | Participant | Exposant |
|--------|--------------|------------|-------------|----------|
| View Events | ✅ | ✅ | ✅ | ✅ |
| Create Event | ✅ | ❌ | ❌ | ❌ |
| Edit Event | ✅ | ❌ | ❌ | ❌ |
| Manage Rooms | ✅ | ❌ | ❌ | ❌ |
| Manage Sessions | ✅ | ❌ | ❌ | ❌ |
| Verify QR Codes | ✅ | ✅ | ❌ | ❌ |
| Grant Room Access | ✅ | ✅ | ❌ | ❌ |
| View Own Badge | ❌ | ❌ | ✅ | ✅ |
| Check Into Event | ❌ | ❌ | ✅ | ✅ |

---

## 📊 Current Test Data

### Events Created (3 Total)

#### Event 1: **TechSummit Algeria 2025**
- **Location:** Centre des Congrès, Alger
- **Start Date:** ~30 days from now
- **Duration:** 3 days
- **Users:** 6 (1 organisateur, 1 contrôleur, 2 participants, 2 exposants)
- **Rooms:** 4
- **Sessions:** 3
- **Participants with Badges:** 4

#### Event 2: **StartupWeek Oran 2025**
- **Location:** Palais des Expositions, Oran
- **Start Date:** ~60 days from now
- **Duration:** 5 days
- **Users:** 6 (1 organisateur, 1 contrôleur, 2 participants, 2 exposants)
- **Rooms:** 4
- **Sessions:** 3
- **Participants with Badges:** 4

#### Event 3: **InnoFest Constantine 2025**
- **Location:** Université Constantine 2, Constantine
- **Start Date:** ~90 days from now
- **Duration:** 2 days
- **Users:** 6 (1 organisateur, 1 contrôleur, 2 participants, 2 exposants)
- **Rooms:** 4
- **Sessions:** 3
- **Participants with Badges:** 4

### Database Statistics
- **Total Events:** 3
- **Total Users:** 18 (unique user accounts)
- **Total Rooms:** 12 (4 per event)
- **Total Sessions:** 9 (3 per event)
- **Total Participants:** 12 (badge holders)
- **Total User-Event Assignments:** 18

---

## 🔑 Test User Credentials

**Default Password for ALL users:** `makeplus2025`

### TechSummit Algeria 2025

| Role | Username | Email | Badge ID |
|------|----------|-------|----------|
| 👔 Organisateur | `tech_organisateur` | tech_organisateur@makeplus.com | - |
| 🎫 Contrôleur | `tech_controleur` | tech_controleur@makeplus.com | - |
| 👤 Participant | `tech_participant1` | tech_participant1@makeplus.com | TECH-175A318B |
| 👤 Participant | `tech_participant2` | tech_participant2@makeplus.com | TECH-C29D27A5 |
| 🏢 Exposant | `tech_exposant1` | tech_exposant1@makeplus.com | TECH-D4E5DB88 |
| 🏢 Exposant | `tech_exposant2` | tech_exposant2@makeplus.com | TECH-F051C722 |

### StartupWeek Oran 2025

| Role | Username | Email | Badge ID |
|------|----------|-------|----------|
| 👔 Organisateur | `startup_organisateur` | startup_organisateur@makeplus.com | - |
| 🎫 Contrôleur | `startup_controleur` | startup_controleur@makeplus.com | - |
| 👤 Participant | `startup_participant1` | startup_participant1@makeplus.com | STARTUP-BCF64C23 |
| 👤 Participant | `startup_participant2` | startup_participant2@makeplus.com | STARTUP-069182A3 |
| 🏢 Exposant | `startup_exposant1` | startup_exposant1@makeplus.com | STARTUP-358E73A9 |
| 🏢 Exposant | `startup_exposant2` | startup_exposant2@makeplus.com | STARTUP-BCF7C673 |

### InnoFest Constantine 2025

| Role | Username | Email | Badge ID |
|------|----------|-------|----------|
| 👔 Organisateur | `inno_organisateur` | inno_organisateur@makeplus.com | - |
| 🎫 Contrôleur | `inno_controleur` | inno_controleur@makeplus.com | - |
| 👤 Participant | `inno_participant1` | inno_participant1@makeplus.com | INNO-6ADA080A |
| 👤 Participant | `inno_participant2` | inno_participant2@makeplus.com | INNO-4348A46C |
| 🏢 Exposant | `inno_exposant1` | inno_exposant1@makeplus.com | INNO-73A92192 |
| 🏢 Exposant | `inno_exposant2` | inno_exposant2@makeplus.com | INNO-E0D6CF3A |

---

## 🎯 Testing Workflows

### 1. **Event Creation Workflow**

```python
# As Organisateur
1. Login as tech_organisateur
2. POST /api/events/ - Create new event
3. POST /api/rooms/ - Create rooms for the event
4. POST /api/sessions/ - Schedule sessions
5. POST /api/participants/ - Add participants/exhibitors
```

### 2. **Participant Check-In Workflow**

```python
# As Participant
1. Login as tech_participant1
2. GET /api/participants/me/ - View my badge info
3. QR code displayed in app (badge_id: TECH-175A318B)

# As Contrôleur
1. Login as tech_controleur
2. POST /api/qr/verify/ - Scan participant QR code
3. If valid → Mark as checked in
4. POST /api/room-access/ - Grant room access
```

### 3. **Room Access Control Workflow**

```python
# Contrôleur grants access
1. Participant arrives at room door
2. Contrôleur scans participant's QR code
3. POST /api/room-access/
   {
     "participant_id": "...",
     "room_id": "...",
     "status": "granted"
   }
4. System creates RoomAccess record
5. Room's current_participants count auto-updates
```

### 4. **Session Management Workflow**

```python
# As Organisateur
1. GET /api/sessions/?event=<event_id> - List all sessions
2. PATCH /api/sessions/<session_id>/ - Update session status to 'live'
3. GET /api/sessions/<session_id>/statistics/ - View attendance
4. PATCH /api/sessions/<session_id>/ - Mark as 'completed'
```

---

## 📡 Key API Endpoints

### Authentication
- `POST /api/auth/login/` - Login and get JWT tokens
- `POST /api/auth/logout/` - Logout (blacklist token)
- `POST /api/auth/register/` - Register new user
- `POST /api/auth/token/refresh/` - Refresh access token
- `GET /api/auth/profile/` - Get current user profile

### Events
- `GET /api/events/` - List all events (filtered by user access)
- `POST /api/events/` - Create new event (organisateur only)
- `GET /api/events/<id>/` - Get event details
- `PATCH /api/events/<id>/` - Update event
- `GET /api/events/<id>/statistics/` - Event statistics

### Rooms
- `GET /api/rooms/?event=<id>` - List rooms for an event
- `POST /api/rooms/` - Create room (organisateur only)
- `GET /api/rooms/<id>/` - Room details
- `PATCH /api/rooms/<id>/` - Update room

### Sessions
- `GET /api/sessions/?event=<id>` - List sessions for an event
- `POST /api/sessions/` - Create session (organisateur only)
- `GET /api/sessions/<id>/` - Session details
- `PATCH /api/sessions/<id>/` - Update session

### Participants
- `GET /api/participants/?event=<id>` - List participants
- `POST /api/participants/` - Add participant
- `GET /api/participants/me/` - My badge info
- `POST /api/participants/<id>/check-in/` - Check in participant

### QR Code & Access
- `POST /api/qr/verify/` - Verify QR code
- `POST /api/qr/generate/` - Generate QR code for participant
- `POST /api/room-access/` - Grant/deny room access
- `GET /api/room-access/?room=<id>` - Room access logs

---

## 🛠️ Management Commands

### Reset Database
```bash
python manage.py reset_everything --confirm
```
Deletes ALL data (events, users, rooms, sessions, participants, access logs).

### Create Test Data
```bash
python manage.py create_multi_event_data
```
Creates 3 complete events with 6 users each, rooms, sessions, and participant badges.

### Create Single Event
```bash
python manage.py create_test_users
python manage.py create_test_data
```
Legacy commands for creating a single event with test users.

---

## 🚀 Quick Start Testing Guide

### Step 1: Access Swagger Documentation
```
http://127.0.0.1:8000/swagger/
```

### Step 2: Login as Organisateur
```json
POST /api/auth/login/
{
  "username": "tech_organisateur",
  "password": "makeplus2025"
}
```

### Step 3: Copy Access Token
```json
Response:
{
  "access": "eyJ0eXAiOiJKV1Qi...",  ← Copy this
  "refresh": "..."
}
```

### Step 4: Authorize in Swagger
1. Click "Authorize" button (🔓)
2. Enter: `Bearer eyJ0eXAiOiJKV1Qi...`
3. Click "Authorize"

### Step 5: Test Endpoints
```
GET /api/events/ - Should see all 3 events
GET /api/rooms/?event=<event_id> - See event rooms
GET /api/sessions/?event=<event_id> - See event sessions
```

---

## 📱 Mobile App Testing Scenarios

### Scenario 1: Organisateur Managing Event
1. Login as `tech_organisateur`
2. View dashboard with event statistics
3. Create/edit rooms and sessions
4. View all participants and their check-in status
5. Monitor room occupancy in real-time

### Scenario 2: Contrôleur Verifying Badges
1. Login as `tech_controleur`
2. Access QR scanner interface
3. Scan participant's QR code (badge_id)
4. Verify participant identity
5. Grant/deny room access
6. View access logs

### Scenario 3: Participant Attending Event
1. Login as `tech_participant1`
2. View my badge with QR code
3. View event schedule (sessions)
4. Check into event
5. View allowed rooms
6. Request room access via QR scan

### Scenario 4: Exposant at Exhibition
1. Login as `tech_exposant1`
2. View my exhibitor badge
3. Access exhibition hall
4. View booth assignment
5. Network with participants

---

## 🎨 Data Model Visualization

```
┌──────────────┐
│    User      │ ← Django's built-in User model
└──────┬───────┘
       │
       │ (can participate in multiple events with different roles)
       │
       ├────────────────────────────────────────┐
       │                                        │
       ▼                                        ▼
┌─────────────────────┐                ┌──────────────┐
│ UserEventAssignment │◄──────────────┤    Event     │
│  (role: string)     │                │              │
└─────────────────────┘                └──────┬───────┘
                                              │
                                              ├──→ Rooms
                                              ├──→ Sessions
                                              └──→ Participants (with badges)
```

---

## 💡 Key Insights

1. **Event Isolation**: Each event is completely independent
2. **Role Flexibility**: Same user can have different roles in different events
3. **Badge System**: Only participants and exposants get badges
4. **Access Control**: Room access tracked via RoomAccess records
5. **Auto-Updates**: Statistics auto-update via Django signals
6. **QR Codes**: Each participant badge has unique QR code
7. **Multi-Tenancy**: System supports multiple concurrent events

---

## 🔄 Next Steps for Development

1. **Frontend Integration**: Connect mobile/web app to API
2. **Real-Time Updates**: Add WebSocket for live session status
3. **Notifications**: Implement push notifications for session alerts
4. **Analytics**: Add detailed analytics dashboard
5. **Export**: Add PDF/CSV export for participant lists
6. **Email**: Send badge QR codes via email
7. **Multi-Language**: Add i18n support (FR/AR/EN)

---

## 📞 Support

For questions or issues:
- Check Swagger documentation: `/swagger/`
- Review this documentation
- Test with provided credentials
- Use management commands to reset/recreate data

---

**Last Updated:** November 19, 2025
**Database Version:** Fresh rebuild with 3 events, 18 users
**Default Password:** makeplus2025
