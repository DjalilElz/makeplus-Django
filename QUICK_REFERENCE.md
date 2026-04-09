# MakePlus Backend - Quick Reference Guide

## 🚀 Quick Start Commands

### Development Setup
```bash
# Clone and setup
cd makeplus_backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Database setup
cd makeplus_api
python manage.py migrate
python manage.py createsuperuser

# Run server
python manage.py runserver
```

### Common Management Commands
```bash
# Database
python manage.py makemigrations
python manage.py migrate
python manage.py showmigrations

# Static files
python manage.py collectstatic --noinput

# Create superuser
python manage.py createsuperuser

# Shell
python manage.py shell

# Clear cache
python manage.py clear_cache  # If available
```

## 🔑 API Authentication

### Login
```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123"
  }'
```

### Use JWT Token
```bash
curl -X GET http://localhost:8000/api/events/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Refresh Token
```bash
curl -X POST http://localhost:8000/api/auth/token/refresh/ \
  -H "Content-Type: application/json" \
  -d '{
    "refresh": "YOUR_REFRESH_TOKEN"
  }'
```

## 📋 Common API Endpoints

### Events
```bash
# List events
GET /api/events/

# Create event
POST /api/events/
{
  "name": "Tech Summit 2025",
  "description": "Annual tech conference",
  "start_date": "2025-12-01T09:00:00Z",
  "end_date": "2025-12-03T18:00:00Z",
  "location": "Alger"
}

# Get event details
GET /api/events/{event_id}/

# Update event
PATCH /api/events/{event_id}/
{
  "name": "Updated Event Name"
}

# Delete event
DELETE /api/events/{event_id}/
```

### Rooms
```bash
# List rooms
GET /api/rooms/?event_id={event_id}

# Create room
POST /api/rooms/
{
  "event": "event_uuid",
  "name": "Salle Principale",
  "capacity": 100,
  "description": "Main conference hall"
}
```

### Sessions
```bash
# List sessions
GET /api/sessions/?event_id={event_id}

# Create session
POST /api/sessions/
{
  "event": "event_uuid",
  "room": "room_uuid",
  "title": "AI Workshop",
  "start_time": "2025-12-01T10:00:00Z",
  "end_time": "2025-12-01T12:00:00Z",
  "session_type": "atelier",
  "is_paid": true,
  "price": "5000.00"
}

# Start session
POST /api/sessions/{session_id}/mark_live/

# End session
POST /api/sessions/{session_id}/mark_completed/
```

### QR Code Verification
```bash
# Verify QR code
POST /api/rooms/{room_id}/verify_access/
{
  "qr_data": "{\"user_id\": 15, \"badge_id\": \"USER-15-ABC123\"}",
  "session": "session_uuid"  # Optional
}
```

### Session Q&A
```bash
# Ask question
POST /api/session-questions/
{
  "session": "session_uuid",
  "question_text": "What are the prerequisites?"
}

# List questions
GET /api/session-questions/?session={session_id}

# Answer question (Gestionnaire only)
POST /api/session-questions/{question_id}/answer/
{
  "answer_text": "Basic Python knowledge required"
}
```

### Exposant Features
```bash
# Get my booth visits
GET /api/exposant-scans/my_scans/?event_id={event_id}

# Export to Excel
GET /api/exposant-scans/export_excel/
GET /api/exposant-scans/export_excel/?action=share  # For mobile
```

## 🗄️ Database Models Quick Reference

### Event
```python
Event(
    name="Tech Summit 2025",
    description="Annual conference",
    start_date=datetime,
    end_date=datetime,
    location="Alger",
    logo=ImageField,
    banner=ImageField,
    programme_file=FileField,
    guide_file=FileField,
    status="upcoming"  # upcoming, active, completed, cancelled
)
```

### Room
```python
Room(
    event=Event,
    name="Salle Principale",
    capacity=100,
    description="Main hall",
    is_active=True
)
```

### Session
```python
Session(
    event=Event,
    room=Room,
    title="AI Workshop",
    speaker_name="Dr. Ahmed",
    start_time=datetime,
    end_time=datetime,
    session_type="atelier",  # conference, atelier, communication, etc.
    status="pas_encore",  # pas_encore, en_cours, termine
    is_paid=True,
    price=5000.00,
    youtube_live_url="https://youtube.com/..."
)
```

### UserEventAssignment
```python
UserEventAssignment(
    user=User,
    event=Event,
    role="participant",  # gestionnaire_salle, controlleur, participant, exposant
    is_active=True
)
```

### Participant
```python
Participant(
    user=User,
    event=Event,
    badge_id="USER-15-ABC123",
    qr_code_data='{"user_id": 15, "badge_id": "USER-15-ABC123"}',
    is_checked_in=False
)
```

## 🔐 Roles & Permissions

### Role Hierarchy
```
Gestionnaire de Salle (gestionnaire_salle)
├── Full event management
├── Create/edit/delete events, rooms, sessions
├── Manage users and assignments
├── View all statistics
└── Answer session questions

Contrôleur (controlleur)
├── QR code verification
├── Room access control
├── View room statistics
└── Read-only access to events/sessions

Participant (participant)
├── View events and sessions
├── Ask session questions
├── Access allowed rooms
└── View own profile and QR code

Exposant (exposant)
├── Scan participant QR codes
├── Track booth visits
├── Export visitor data
└── View own statistics
```

### Permission Checks
```python
# In views.py
from events.permissions import IsGestionnaire, IsController, IsParticipant

class MyViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsGestionnaire]
```

## 🎨 Dashboard URLs

### Main Dashboard
```
http://localhost:8000/dashboard/
http://localhost:8000/dashboard/login/
http://localhost:8000/dashboard/logout/
```

### Event Management
```
http://localhost:8000/dashboard/event/{event_id}/
http://localhost:8000/dashboard/event/create/step1/
http://localhost:8000/dashboard/event/{event_id}/edit/
http://localhost:8000/dashboard/event/{event_id}/delete/
```

### User Management
```
http://localhost:8000/dashboard/users/
http://localhost:8000/dashboard/user/create/
http://localhost:8000/dashboard/user/{user_id}/
http://localhost:8000/dashboard/event/{event_id}/users/
```

### Email Campaigns
```
http://localhost:8000/dashboard/email/campaigns/
http://localhost:8000/dashboard/email/campaign/create/
http://localhost:8000/dashboard/email/campaign/{campaign_id}/
```

### ePoster Management
```
http://localhost:8000/dashboard/eposter/submissions/
http://localhost:8000/dashboard/eposter/submission/{submission_id}/
```

## 📊 Useful Queries

### Django ORM Examples
```python
# Get all events
from events.models import Event
events = Event.objects.all()

# Get active events
active_events = Event.objects.filter(status='active')

# Get user's events
user_events = Event.objects.filter(
    user_assignments__user=user,
    user_assignments__is_active=True
)

# Get sessions for an event
sessions = Session.objects.filter(event=event).order_by('start_time')

# Get live sessions
live_sessions = Session.objects.filter(status='en_cours')

# Get participant by badge
participant = Participant.objects.get(badge_id='USER-15-ABC123')

# Get room accesses today
from django.utils import timezone
today = timezone.now().date()
accesses = RoomAccess.objects.filter(
    accessed_at__date=today,
    room=room
)

# Get unanswered questions
questions = SessionQuestion.objects.filter(
    session=session,
    is_answered=False
).order_by('asked_at')
```

### SQL Queries (for debugging)
```sql
-- Get all events with participant count
SELECT e.name, COUNT(DISTINCT p.id) as participant_count
FROM events_event e
LEFT JOIN events_participant p ON p.event_id = e.id
GROUP BY e.id, e.name;

-- Get sessions by status
SELECT s.title, s.status, r.name as room_name
FROM events_session s
JOIN events_room r ON s.room_id = r.id
WHERE s.event_id = 'event_uuid'
ORDER BY s.start_time;

-- Get user roles in events
SELECT u.username, e.name, uea.role
FROM events_usereventassignment uea
JOIN auth_user u ON uea.user_id = u.id
JOIN events_event e ON uea.event_id = e.id
WHERE uea.is_active = true;
```

## 🐛 Debugging Tips

### Check JWT Token
```python
# In Django shell
from rest_framework_simplejwt.tokens import AccessToken

token = AccessToken("your_token_here")
print(token.payload)
# Shows: user_id, event_id, role, exp, etc.
```

### Check User Permissions
```python
# In Django shell
from django.contrib.auth.models import User
from events.models import UserEventAssignment

user = User.objects.get(username='ahmed')
assignments = UserEventAssignment.objects.filter(user=user, is_active=True)
for a in assignments:
    print(f"{a.event.name}: {a.role}")
```

### Check QR Code Data
```python
# In Django shell
from events.models import UserProfile

profile = UserProfile.objects.get(user__username='ahmed')
print(profile.qr_code_data)
# Shows: {"user_id": 15, "badge_id": "USER-15-ABC123"}
```

### View Logs
```bash
# Django development server logs
# Automatically shown in terminal

# Check database queries
# In settings.py, add:
LOGGING = {
    'version': 1,
    'handlers': {
        'console': {'class': 'logging.StreamHandler'},
    },
    'loggers': {
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

## 🔧 Configuration Quick Reference

### Environment Variables
```env
# Required
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (Production)
USE_SUPABASE=True
SUPABASE_DB_NAME=postgres
SUPABASE_DB_USER=postgres.xxx
SUPABASE_DB_PASSWORD=your-password
SUPABASE_DB_HOST=xxx.pooler.supabase.com
SUPABASE_DB_PORT=6543

# Email
MAILERLITE_API_TOKEN=your-token
MAILERLITE_FROM_EMAIL=noreply@yourdomain.com
SENDGRID_API_KEY=your-key

# Site
SITE_URL=http://localhost:8000
```

### CORS Settings
```python
# In settings.py
CORS_ALLOW_ALL_ORIGINS = True  # Development only

# Production:
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "https://yourdomain.com",
]
```

### JWT Settings
```python
# In settings.py
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}
```

## 📝 Testing

### Run Tests
```bash
# All tests
python manage.py test

# Specific app
python manage.py test events

# Specific test
python manage.py test events.tests.TestEventModel
```

### Test API with curl
```bash
# Login and save token
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"admin"}' \
  | jq -r '.access')

# Use token
curl -X GET http://localhost:8000/api/events/ \
  -H "Authorization: Bearer $TOKEN"
```

### Test Email Setup
```bash
python test_email_setup.py
```

## 🚨 Common Issues & Solutions

### Issue: CORS errors
```python
# Solution: Check CORS settings in settings.py
CORS_ALLOW_ALL_ORIGINS = True  # For development
```

### Issue: JWT token expired
```bash
# Solution: Refresh token
curl -X POST http://localhost:8000/api/auth/token/refresh/ \
  -d '{"refresh": "YOUR_REFRESH_TOKEN"}'
```

### Issue: Static files not loading
```bash
# Solution: Collect static files
python manage.py collectstatic --noinput
```

### Issue: Database migrations
```bash
# Solution: Reset migrations (development only!)
python manage.py migrate events zero
python manage.py migrate
```

### Issue: Permission denied
```python
# Solution: Check user role assignment
UserEventAssignment.objects.filter(user=user, event=event)
```

## 📚 Documentation Links

- **Complete API Reference**: BACKEND_DOCUMENTATION.md
- **Architecture**: ARCHITECTURE_DIAGRAM.md
- **Project Overview**: PROJECT_OVERVIEW.md
- **Flutter Integration**: FLUTTER_INTEGRATION_GUIDE.md
- **YouTube & Q&A**: YOUTUBE_AND_QA_INTEGRATION.md
- **Event Registration**: EVENT_REGISTRATION_SYSTEM.md

## 🔗 Useful URLs

- **API Root**: http://localhost:8000/api/
- **Swagger UI**: http://localhost:8000/swagger/
- **ReDoc**: http://localhost:8000/redoc/
- **Admin Panel**: http://localhost:8000/admin/
- **Dashboard**: http://localhost:8000/dashboard/

---

**Pro Tip**: Bookmark this page for quick reference during development!
