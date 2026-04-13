# MakePlus API Quick Reference

## Base URL
```
https://your-domain.com/api/
```

## Authentication Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register/` | Register new user |
| POST | `/api/auth/token/` | Login (get JWT tokens) - **Uses email field** |
| POST | `/api/auth/token/refresh/` | Refresh access token |
| POST | `/api/auth/token/verify/` | Verify token validity |
| GET | `/api/auth/me/` | Get current user profile |
| POST | `/api/auth/change-password/` | Change password |
| POST | `/api/auth/request-code/` | Request passwordless login code |
| POST | `/api/auth/login/` | Login with email code |
| GET | `/api/auth/my-events/` | Get user's assigned events |
| POST | `/api/auth/select-event/` | Select active event |
| POST | `/api/auth/switch-event/` | Switch to different event |

### Login Example (JWT Token)

**Endpoint:** `POST /api/auth/token/`

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "your_password"
}
```

**Response:** `200 OK`
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "username": "user123",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe"
  },
  "role": "controller",
  "event": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Tech Conference 2026"
  }
}
```

**Important:** The login endpoint now accepts `email` field instead of `username`.

## Event Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/events/` | List all events |
| GET | `/api/events/{id}/` | Get event details |
| POST | `/api/events/` | Create event (admin) |
| PUT | `/api/events/{id}/` | Update event (admin) |
| DELETE | `/api/events/{id}/` | Delete event (admin) |
| GET | `/api/events/{id}/statistics/` | Get event statistics |

## Room Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/rooms/` | List rooms |
| GET | `/api/rooms/{id}/` | Get room details |
| POST | `/api/rooms/` | Create room (admin) |
| PUT | `/api/rooms/{id}/` | Update room (admin) |
| DELETE | `/api/rooms/{id}/` | Delete room (admin) |
| GET | `/api/rooms/{id}/sessions/` | Get room sessions |
| GET | `/api/rooms/{id}/participants/` | Get room participants |
| GET | `/api/rooms/{id}/statistics/` | Get room statistics |
| POST | `/api/rooms/{id}/verify_access/` | Verify room access (QR) |
| GET | `/api/my-room/statistics/` | Get my room stats |

## Session Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/sessions/` | List sessions |
| GET | `/api/sessions/{id}/` | Get session details |
| POST | `/api/sessions/` | Create session (admin) |
| PUT | `/api/sessions/{id}/` | Update session (admin) |
| DELETE | `/api/sessions/{id}/` | Delete session (admin) |
| POST | `/api/sessions/{id}/start/` | Start session (mark live) |
| POST | `/api/sessions/{id}/end/` | End session (mark completed) |
| POST | `/api/sessions/{id}/cancel/` | Cancel session |
| GET | `/api/my-ateliers/` | Get my workshops |

## Participant Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/participants/` | List participants |
| GET | `/api/participants/{id}/` | Get participant details |
| POST | `/api/participants/` | Create participant (admin) |
| PUT | `/api/participants/{id}/` | Update participant (admin) |
| DELETE | `/api/participants/{id}/` | Delete participant (admin) |

## Room Access & Check-in Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/room-access/` | List access logs |
| POST | `/api/room-access/` | Create access log (check-in) |
| GET | `/api/room-access/{id}/` | Get access log details |

## QR Code Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/qr/verify/` | Verify QR code |
| GET | `/api/qr/generate/` | Generate user QR code |

## Announcement Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/annonces/` | List announcements |
| GET | `/api/annonces/{id}/` | Get announcement details |
| POST | `/api/annonces/` | Create announcement (admin) |
| PUT | `/api/annonces/{id}/` | Update announcement (admin) |
| DELETE | `/api/annonces/{id}/` | Delete announcement (admin) |

## Session Q&A Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/session-questions/` | List questions |
| POST | `/api/session-questions/` | Ask question |
| GET | `/api/session-questions/{id}/` | Get question details |
| POST | `/api/session-questions/{id}/answer/` | Answer question |

## Session Access (Paid) Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/session-access/` | List session access records |
| POST | `/api/session-access/` | Grant session access |
| GET | `/api/session-access/{id}/` | Get access details |

## Room Assignment Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/room-assignments/` | List room assignments |
| POST | `/api/room-assignments/` | Create assignment (admin) |
| GET | `/api/room-assignments/{id}/` | Get assignment details |
| PUT | `/api/room-assignments/{id}/` | Update assignment (admin) |
| DELETE | `/api/room-assignments/{id}/` | Delete assignment (admin) |

## Exposant Scan Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/exposant-scans/` | List scans |
| POST | `/api/exposant-scans/` | Create scan (record visit) |
| GET | `/api/exposant-scans/my_scans/` | Get my scans |
| GET | `/api/exposant-scans/export_excel/` | Export to Excel |

## User Assignment Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/user-assignments/` | List user assignments (admin) |
| POST | `/api/user-assignments/` | Create assignment (admin) |
| GET | `/api/user-assignments/{id}/` | Get assignment details |
| PUT | `/api/user-assignments/{id}/` | Update assignment (admin) |
| DELETE | `/api/user-assignments/{id}/` | Delete assignment (admin) |

## Dashboard & Statistics Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/dashboard/stats/` | Get dashboard statistics |

## Notification Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/notifications/` | List notifications |
| GET | `/api/notifications/{id}/` | Get notification details |
| POST | `/api/notifications/{id}/read/` | Mark as read |

## ePoster Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/eposter/submissions/` | List submissions (committee) |
| GET | `/api/eposter/submissions/{id}/` | Get submission details |
| POST | `/api/eposter/{event_id}/submit/` | Submit ePoster (public) |
| POST | `/api/eposter/submissions/{id}/validate/` | Validate submission |
| POST | `/api/eposter/submissions/{id}/set_status/` | Update status |
| GET | `/api/eposter/submissions/my_pending/` | Get my pending reviews |
| GET | `/api/eposter/submissions/statistics/` | Get statistics |
| GET | `/api/eposter/submissions/{id}/realtime/` | Get real-time status |
| GET | `/api/eposter/committee/` | List committee members |
| POST | `/api/eposter/committee/` | Add committee member |
| GET | `/api/eposter/validations/` | List validations |

## Common Query Parameters

| Parameter | Description | Example |
|-----------|-------------|---------|
| `page` | Page number | `?page=2` |
| `page_size` | Items per page | `?page_size=50` |
| `search` | Text search | `?search=conference` |
| `ordering` | Sort results | `?ordering=-created_at` |
| `event` | Filter by event | `?event=event-uuid` |
| `status` | Filter by status | `?status=active` |

## Authentication Header

All authenticated endpoints require:
```
Authorization: Bearer <your_jwt_token>
```

## Response Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 204 | No Content |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 500 | Server Error |

## User Roles

- `participant` - Regular attendee
- `exposant` - Exhibitor
- `gestionnaire` - Room manager
- `controller` - Access controller
- `admin` - Administrator
- `president` - Event president

## Event Status Values

- `upcoming` - Not started
- `active` - Currently running
- `completed` - Finished
- `cancelled` - Cancelled

## Session Status Values

- `scheduled` - Not started
- `live` - In progress
- `completed` - Finished
- `cancelled` - Cancelled

## Session Types

- `conference` - Presentation
- `atelier` - Workshop
- `workshop` - Training
- `panel` - Panel discussion
- `keynote` - Keynote speech

## ePoster Status Values

- `pending` - Awaiting review
- `accepted` - Accepted
- `rejected` - Rejected
- `revision_requested` - Needs revision

## Payment Status Values

- `pending` - Not paid
- `paid` - Completed
- `refunded` - Refunded
