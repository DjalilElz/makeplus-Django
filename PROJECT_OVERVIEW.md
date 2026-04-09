# MakePlus Backend - Project Overview

## 🎯 Project Summary

MakePlus is a comprehensive Django-based event management platform designed for conferences, workshops, and exhibitions. It provides a complete backend API with JWT authentication, role-based access control, and an integrated admin dashboard.

## 📁 Project Structure

```
makeplus_backend/
├── makeplus_api/                    # Django project root
│   ├── makeplus_api/               # Project settings & configuration
│   │   ├── settings.py             # Django settings (DB, JWT, CORS, etc.)
│   │   ├── urls.py                 # Main URL routing
│   │   └── wsgi.py                 # WSGI application
│   │
│   ├── events/                     # Core API app (REST API)
│   │   ├── models.py               # Database models (Event, Room, Session, etc.)
│   │   ├── views.py                # DRF ViewSets (API endpoints)
│   │   ├── serializers.py          # DRF serializers
│   │   ├── permissions.py          # Custom permissions
│   │   ├── auth_views.py           # Authentication endpoints
│   │   ├── views_registration.py   # Public registration endpoints
│   │   └── urls.py                 # API routes
│   │
│   ├── dashboard/                  # Admin dashboard app (Web UI)
│   │   ├── views.py                # Dashboard views (event management)
│   │   ├── views_email.py          # Email campaign management
│   │   ├── views_eposter.py        # ePoster management
│   │   ├── views_stats.py          # Statistics & analytics
│   │   ├── models_email.py         # Email campaign models
│   │   ├── models_eposter.py       # ePoster submission models
│   │   ├── models_form.py          # Custom form builder models
│   │   ├── templates/              # HTML templates
│   │   └── static/                 # CSS, JS, images
│   │
│   ├── caisse/                     # Cash register system
│   │   ├── models.py               # Payment & transaction models
│   │   ├── views.py                # Caisse views
│   │   └── templates/              # Caisse templates
│   │
│   ├── media/                      # User uploads (PDFs, images, etc.)
│   ├── staticfiles/                # Collected static files
│   ├── db.sqlite3                  # SQLite database (development)
│   └── manage.py                   # Django management script
│
├── venv/                           # Python virtual environment
├── requirements.txt                # Python dependencies
├── .env                            # Environment variables
└── README.md                       # Basic setup instructions
```

## 🔑 Key Features

### 1. Multi-Event Management
- Create and manage multiple events simultaneously
- Event configuration: dates, location, themes, registration settings
- Event files: logo, banner, programme PDF, guide PDF
- Event statistics and analytics

### 2. Role-Based Access Control (4 Roles)
- **Gestionnaire de Salle** (Room Manager): Full event management
- **Contrôleur** (Controller): QR code scanning, badge verification
- **Participant**: Session access, Q&A, schedule viewing
- **Exposant** (Exhibitor): Booth management, visitor tracking

### 3. User-Level QR Code System
- ONE QR code per user (works across all events)
- Multi-level access control: Event → Room → Session
- Real-time verification with payment checks for paid ateliers

### 4. Session Management
- Multiple session types: conference, atelier, communication, symposium
- Session statuses: pas_encore, en_cours, terminé
- YouTube live streaming integration
- Q&A system (participants ask, gestionnaires answer)
- Paid ateliers with access control

### 5. Admin Dashboard (Web UI)
- Event creation wizard (4-step process)
- User management with role assignments
- Room and session management
- Registration approval system
- Email campaign builder (Unlayer integration)
- ePoster submission management
- Statistics and analytics
- Cash register (caisse) system

### 6. Public Features
- Event registration forms (customizable fields)
- ePoster submission forms
- Email tracking (opens, clicks)
- Custom form builder

### 7. API Features
- RESTful API with Django REST Framework
- JWT authentication (access + refresh tokens)
- Swagger/OpenAPI documentation
- CORS enabled for mobile/web apps
- Flutter-compatible endpoints

## 🗄️ Database Models

### Core Models (events app)
1. **Event** - Main event entity
2. **Room** - Physical rooms/venues
3. **Session** - Conferences, ateliers, workshops
4. **UserEventAssignment** - User-event-role mapping
5. **UserProfile** - User-level QR codes
6. **Participant** - Event participant profiles
7. **RoomAccess** - Room check-in tracking
8. **SessionAccess** - Paid atelier access control
9. **Annonce** - Event announcements
10. **SessionQuestion** - Q&A system
11. **RoomAssignment** - Staff room assignments
12. **ExposantScan** - Booth visit tracking
13. **EventRegistration** - Public registration submissions

### Dashboard Models
1. **EmailTemplate** - Email campaign templates
2. **EventEmailTemplate** - Event-specific email templates
3. **EmailLog** - Email delivery tracking
4. **EPosterSubmission** - ePoster submissions
5. **EPosterValidation** - ePoster review/approval
6. **EPosterCommitteeMember** - Committee members
7. **CustomForm** - Form builder
8. **FormSubmission** - Form responses

### Caisse Models
1. **Caisse** - Cash register
2. **PayableItem** - Items for sale (ateliers, etc.)
3. **Transaction** - Payment records

## 🔐 Authentication & Authorization

### JWT Token Structure
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "username": "ahmed.benali",
    "email": "ahmed@example.com"
  },
  "current_event": {
    "id": "uuid",
    "name": "Tech Summit 2025",
    "role": "participant"
  }
}
```

### Login Flow
1. User logs in with email/password
2. Backend checks user's event assignments
3. If 1 event: auto-select, return JWT
4. If multiple events: return event list, user selects
5. JWT includes event context for all API calls

## 🌐 API Endpoints

### Authentication
- `POST /api/auth/login/` - Login
- `POST /api/auth/register/` - Register
- `POST /api/auth/logout/` - Logout
- `POST /api/auth/select-event/` - Select event
- `GET /api/auth/profile/` - Get profile

### Events
- `GET /api/events/` - List events
- `POST /api/events/` - Create event
- `GET /api/events/{id}/` - Get event
- `PATCH /api/events/{id}/` - Update event
- `DELETE /api/events/{id}/` - Delete event

### Rooms & Sessions
- `GET /api/rooms/` - List rooms
- `GET /api/sessions/` - List sessions
- `POST /api/sessions/{id}/mark_live/` - Start session
- `POST /api/sessions/{id}/mark_completed/` - End session

### QR Code Verification
- `POST /api/rooms/{room_id}/verify_access/` - Verify QR code

### Q&A System
- `GET /api/session-questions/` - List questions
- `POST /api/session-questions/` - Ask question
- `POST /api/session-questions/{id}/answer/` - Answer question

### Exposant Features
- `GET /api/exposant-scans/my_scans/` - Get booth visits
- `GET /api/exposant-scans/export_excel/` - Export to Excel

## 🎨 Dashboard Features

### Event Management
- Create events (4-step wizard)
- Edit event details, images, PDFs
- View event statistics
- Manage registrations

### User Management
- Create users with roles
- Assign users to events
- Download QR codes
- Change user roles

### Room & Session Management
- Create/edit rooms
- Create/edit sessions
- Manage session status
- View room statistics

### Email Campaigns
- Visual email builder (Unlayer)
- Send to event participants
- Track opens and clicks
- Email templates

### ePoster Management
- Review submissions
- Approve/reject ePosters
- Committee member management
- Email notifications

### Cash Register (Caisse)
- Create cash registers
- Manage payable items
- Process transactions
- View transaction history

## 🛠️ Technology Stack

- **Framework**: Django 5.2.7
- **API**: Django REST Framework
- **Authentication**: JWT (SimpleJWT)
- **Database**: PostgreSQL (production), SQLite (development)
- **API Docs**: drf-yasg (Swagger/OpenAPI)
- **CORS**: django-cors-headers
- **Static Files**: WhiteNoise
- **Email**: MailerLite API, SendGrid fallback
- **File Storage**: Django FileField (local/cloud)

## 📚 Essential Documentation

### Core Documentation
- **BACKEND_DOCUMENTATION.md** - Complete API reference (3600+ lines)
- **README.md** - Basic setup instructions

### Feature-Specific Guides
- **YOUTUBE_AND_QA_INTEGRATION.md** - YouTube live + Q&A system
- **EVENT_PDF_FILES_IMPLEMENTATION.md** - PDF upload implementation
- **EVENT_REGISTRATION_SYSTEM.md** - Public registration system
- **USER_ACCESS_CONTROL_SYSTEM.md** - Access control & permissions
- **QR_CODE_FRONTEND_INTEGRATION.md** - QR code integration guide

### Frontend Integration
- **FLUTTER_INTEGRATION_GUIDE.md** - Flutter app integration
- **FRONTEND_INTEGRATION_GUIDE.md** - General frontend guide
- **FLUTTER_EXCEL_EXPORT_SHARE.md** - Excel export for mobile
- **NEW_API_ENDPOINTS.md** - Latest API additions

### Email & ePoster
- **EMAIL_CAMPAIGN_CREATION_GUIDE.md** - Email campaign guide
- **EMAIL_CAMPAIGN_SYSTEM_COMPLETE.md** - Complete email system
- **EMAIL_SETUP_GUIDE.md** - Email configuration
- **UNLAYER_EMAIL_BUILDER_GUIDE.md** - Unlayer integration
- **EPOSTER_README.md** - ePoster system overview
- **EPOSTER_QUICK_START.md** - ePoster quick start
- **EPOSTER_USER_GUIDE.md** - ePoster user guide
- **EPOSTER_VISUAL_GUIDE.md** - ePoster visual guide

### Workflow Guides
- **CAMPAIGN_WORKFLOW_GUIDE.md** - Email campaign workflow
- **TESTING_WITH_YOUR_EMAIL.md** - Email testing guide

## 🚀 Quick Start

### 1. Setup Environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Database
```bash
# Development (SQLite)
python makeplus_api/manage.py migrate

# Production (PostgreSQL)
# Set USE_SUPABASE=True in .env
# Configure SUPABASE_DB_* variables
```

### 3. Create Superuser
```bash
cd makeplus_api
python manage.py createsuperuser
```

### 4. Run Server
```bash
# Development
python manage.py runserver

# Access:
# - API: http://localhost:8000/api/
# - Swagger: http://localhost:8000/swagger/
# - Dashboard: http://localhost:8000/dashboard/
# - Admin: http://localhost:8000/admin/
```

## 🔧 Configuration

### Environment Variables (.env)
```env
# Django
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (Production)
USE_SUPABASE=False
SUPABASE_DB_NAME=postgres
SUPABASE_DB_USER=postgres
SUPABASE_DB_PASSWORD=your-password
SUPABASE_DB_HOST=your-host
SUPABASE_DB_PORT=6543

# Email
MAILERLITE_API_TOKEN=your-token
MAILERLITE_FROM_EMAIL=your-email
SENDGRID_API_KEY=your-key

# Site
SITE_URL=http://localhost:8000
```

## 📊 Key Workflows

### 1. Event Creation
1. Admin logs into dashboard
2. Creates event (4-step wizard)
3. Uploads logo, banner, PDFs
4. Configures registration settings
5. Creates rooms and sessions
6. Assigns staff (gestionnaires, controllers)

### 2. User Registration
1. User visits public registration form
2. Fills personal info, selects ateliers
3. Submits form
4. Admin approves registration
5. System creates user account + participant profile
6. User receives QR code

### 3. QR Code Verification
1. Participant arrives at room
2. Controller scans QR code
3. Backend checks:
   - Event access (UserEventAssignment)
   - Room access (Participant.allowed_rooms)
   - Session payment (SessionAccess)
4. Grant or deny access

### 4. Session Q&A
1. Participant views session
2. Asks question via API
3. Question appears in gestionnaire dashboard
4. Gestionnaire answers question
5. Participant sees answer in real-time

### 5. Exposant Booth Visits
1. Visitor arrives at booth
2. Exposant scans visitor's QR code
3. System records visit
4. Exposant can export all visits to Excel

## 🎯 Next Steps

1. Review **BACKEND_DOCUMENTATION.md** for complete API reference
2. Check **FLUTTER_INTEGRATION_GUIDE.md** for mobile app integration
3. Read **EVENT_REGISTRATION_SYSTEM.md** for registration flow
4. Explore **YOUTUBE_AND_QA_INTEGRATION.md** for live streaming
5. Test API endpoints using Swagger UI

## 📝 Notes

- All timestamps are in UTC
- French language support for statuses and roles
- CORS enabled for mobile/web apps
- JWT tokens expire after 1 hour (refresh after 7 days)
- File uploads stored in `media/` directory
- Static files served via WhiteNoise
- Production uses PostgreSQL with connection pooling
- Development uses SQLite for simplicity

---

**Last Updated**: December 2025  
**Version**: 2.2  
**Status**: Production Ready
