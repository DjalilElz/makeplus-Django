# New API Endpoints - Quick Reference

## Session Access (Paid Ateliers)

### List/Create Session Access
```
GET/POST /api/session-access/
```

**Filters:**
- `participant_id` - Filter by participant
- `session_id` - Filter by session
- `payment_status` - Filter by payment status
- `has_access` - Filter by access status

**Example Response:**
```json
{
  "id": "uuid",
  "participant": "uuid",
  "session": "uuid",
  "payment_status": "paid",
  "has_access": true,
  "granted_at": "2025-11-25T10:00:00Z"
}
```

---

## Annonces (Announcements)

### List/Create Annonces
```
GET/POST /api/annonces/
```

**Filters:**
- `event_id` - Filter by event
- `target` - Filter by target audience (all, participants, exposants, controlleurs, gestionnaires)
- `created_by` - Filter by creator
- Search: `title`, `description`

**Target Options:**
- `all` - All event participants
- `participants` - Only participants
- `exposants` - Only exposants
- `controlleurs` - Only badge controllers
- `gestionnaires` - Only room managers

**Permissions:**
- List/Create: Authenticated users
- Update/Delete: Annonce owner or gestionnaire only

**Example POST:**
```json
{
  "event": "event-uuid",
  "title": "Pause déjeuner",
  "description": "Le déjeuner est servi à la cafétéria, niveau 2",
  "target": "all"
}
```

---

## Session Questions (Q&A)

### List/Create Questions
```
GET/POST /api/session-questions/
```

**Filters:**
- `session_id` - Filter by session
- `participant` - Filter by participant
- `is_answered` - Filter answered/unanswered questions

**Answer a Question (Gestionnaire only):**
```
POST /api/session-questions/{id}/answer/
{
  "answer_text": "Réponse à votre question..."
}
```

**Example Response:**
```json
{
  "id": "uuid",
  "session": "session-uuid",
  "participant": "participant-uuid",
  "question_text": "Question about the topic...",
  "asked_at": "2025-11-25T10:00:00Z",
  "is_answered": true,
  "answer_text": "Here is the answer...",
  "answered_by": "user-uuid",
  "answered_at": "2025-11-25T10:15:00Z"
}
```

---

## Room Assignments

### List/Create Room Assignments (Gestionnaire only)
```
GET/POST /api/room-assignments/
```

**Filters:**
- `room_id` - Filter by room
- `user_id` - Filter by assigned user
- `event_id` - Filter by event
- `role` - Filter by role
- `is_active` - Filter active assignments
- `current=true` - Get only current assignments (time-based)

**Example POST:**
```json
{
  "user": "user-uuid",
  "room": "room-uuid",
  "event": "event-uuid",
  "role": "gestionnaire_des_salles",
  "start_time": "2025-11-25T09:00:00Z",
  "end_time": "2025-11-25T17:00:00Z",
  "is_active": true
}
```

---

## Exposant Scans (Booth Visits)

### List/Create Scans
```
GET/POST /api/exposant-scans/
```

**Filters:**
- `exposant_id` - Filter by exposant
- `event_id` - Filter by event

**Get My Scans (Exposant only):**
```
GET /api/exposant-scans/my_scans/?event_id={event-uuid}
```

**Example Response:**
```json
{
  "total_visits": 42,
  "today_visits": 15,
  "scans": [
    {
      "id": "uuid",
      "exposant": "exposant-uuid",
      "scanned_participant": "participant-uuid",
      "event": "event-uuid",
      "scanned_at": "2025-11-25T14:30:00Z",
      "notes": "Interested in product demo"
    }
  ]
}
```

**Example POST (Scan a participant):**
```json
{
  "exposant": "exposant-uuid",
  "scanned_participant": "participant-uuid",
  "event": "event-uuid",
  "notes": "Demande d'information sur le produit X"
}
```

---

## Updated Existing Endpoints

### Sessions

**New Fields:**
- `session_type` - "conference" or "atelier"
- `is_paid` - Boolean (for paid ateliers)
- `price` - Decimal (atelier price)
- `youtube_live_url` - URL for live streaming

**New Status Values (French):**
- `pas_encore` - Not started yet (was: scheduled)
- `en_cours` - In progress (was: live)
- `termine` - Finished (was: completed)

**Session Actions:**
```
POST /api/sessions/{id}/mark_live/      # Start session (status → en_cours)
POST /api/sessions/{id}/mark_completed/ # End session (status → termine)
POST /api/sessions/{id}/cancel/         # Cancel session (status → pas_encore)
```

### Events

**New Fields:**
- `programme_file` - PDF upload URL
- `guide_file` - PDF upload URL
- `president` - User UUID (event president)

### Participants

**New Fields:**
- `plan_file` - PDF upload URL (for exposants)

### User Event Assignments

**Role Values:**
- `gestionnaire_des_salles` - Room manager (was: organisateur)
- `controlleur_des_badges` - Badge controller
- `participant` - Regular participant
- `exposant` - Exhibitor

---

## Role-Based Access Summary

| Endpoint | Permissions |
|----------|-------------|
| Session Access | Authenticated |
| Annonces (List/Create) | Authenticated |
| Annonces (Update/Delete) | Owner or Gestionnaire |
| Session Questions (List/Create) | Authenticated |
| Session Questions (Answer) | Gestionnaire only |
| Room Assignments | Gestionnaire only |
| Exposant Scans (List/Create) | Authenticated |
| Exposant Scans (My Scans) | Exposant only |

---

## Common Query Parameters

All list endpoints support:
- `page` - Page number
- `page_size` - Items per page
- Standard DRF filters as documented above

---

## File Upload Endpoints

When uploading files (programme, guide, plan):

**Content-Type:** `multipart/form-data`

**Example (Event programme):**
```
PUT/PATCH /api/events/{id}/
Content-Type: multipart/form-data

programme_file: [PDF file]
```

**Accepted formats:** PDF only
**Max file size:** As configured in Django settings

---

## Testing Endpoints

Use the interactive documentation:
- **Swagger UI:** http://localhost:8000/swagger/
- **ReDoc:** http://localhost:8000/redoc/

Or use curl/Postman with your JWT token:
```bash
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     http://localhost:8000/api/annonces/
```
