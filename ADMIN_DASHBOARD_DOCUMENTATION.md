# 🎯 MakePlus Admin Dashboard - Complete Documentation

**Version:** 1.0  
**Last Updated:** December 17, 2025  
**Status:** ✅ Production Ready

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Features](#features)
3. [Installation](#installation)
4. [Getting Started](#getting-started)
5. [Multi-Step Event Creation](#multi-step-event-creation)
6. [User Management](#user-management)
7. [Event Dashboard](#event-dashboard)
8. [Technical Architecture](#technical-architecture)
9. [Troubleshooting](#troubleshooting)
10. [API Integration](#api-integration)

---

## 🎯 Overview

The MakePlus Admin Dashboard is a web-based control panel for managing events, users, rooms, sessions, and all backend operations. It provides a user-friendly interface for creating and managing multi-day events with multiple rooms, sessions, and participants.

### Key Purpose

- **Event Creation:** Multi-step wizard for creating comprehensive events
- **User Management:** Create users, assign roles, generate QR codes
- **Analytics:** View statistics and insights for each event
- **Administration:** Manage rooms, sessions, participants, and staff

### Who Should Use This?

- **Event Organizers:** Create and manage events
- **System Administrators:** Manage users and system configuration
- **Staff:** Monitor event statistics and participant activity

---

## ✨ Features

### 🎪 Event Management

- ✅ **Multi-Step Event Creation Wizard**
  - Step 1: Event details (name, dates, location)
  - Step 2: Add rooms/salles (multiple rooms)
  - Step 3: Add sessions/conferences/ateliers to each room
  - Step 4: Create users and assign roles

- ✅ **Event Dashboard**
  - View all events with statistics
  - Filter by status (upcoming, active, completed)
  - Quick access to event details

- ✅ **Event Detail Page**
  - Comprehensive event overview
  - Rooms list with session counts
  - Sessions list with registration stats
  - User assignments by role
  - Real-time statistics

### 👥 User Management

- ✅ **User Creation**
  - Quick user creation form
  - Automatic QR code generation
  - Event assignment with role selection
  - Password management

- ✅ **User Details**
  - View user profile
  - Display QR code
  - Download QR code as PNG
  - Event assignments list
  - Role history

- ✅ **Role System**
  - Organisateur (Organizer)
  - Gestionnaire des Salles (Room Manager)
  - Contrôleur des Badges (Badge Controller)
  - Participant (Attendee)
  - Exposant (Exhibitor)

### 🏢 Room & Session Management

- ✅ **Room Configuration**
  - Room name, capacity, floor
  - Room type (auditorium, workshop, conference)
  - Equipment list
  - Session assignment

- ✅ **Session Management**
  - Conference, Atelier, Workshop types
  - Date/time scheduling
  - Speaker information
  - YouTube live integration
  - Paid/free session configuration
  - Max participant limits

### 📊 Analytics & Statistics

- ✅ **Dashboard Statistics**
  - Total events, users, sessions
  - Active vs upcoming events
  - Recent activity tracking

- ✅ **Event Statistics**
  - Participant count & check-ins
  - Room access tracking
  - Exposant scan statistics
  - Session registration counts
  - Q&A activity

---

## 🚀 Installation

### Prerequisites

- Python 3.9 or higher
- Django 5.2.7
- PostgreSQL (production) or SQLite (development)
- Virtual environment

### Step 1: Install Dependencies

```bash
# Navigate to project directory
cd E:\makeplus\makeplus_backend

# Activate virtual environment
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Install required packages
pip install -r requirements.txt
```

### Step 2: Database Setup

```bash
# Navigate to Django project
cd makeplus_api

# Run migrations
python manage.py migrate

# Create superuser for dashboard access
python manage.py createsuperuser
```

### Step 3: Collect Static Files

```bash
# Collect static files for production
python manage.py collectstatic --noinput
```

### Step 4: Run Development Server

```bash
# Start server
python manage.py runserver

# Dashboard will be available at:
# http://127.0.0.1:8000/dashboard/
```

---

## 🎬 Getting Started

### 1. First Login

1. Navigate to `http://127.0.0.1:8000/dashboard/login/`
2. Enter your superuser credentials
3. Click "Sign In"

**Note:** Only staff users (is_staff=True) can access the dashboard.

### 2. Dashboard Home

After login, you'll see:
- **Statistics Cards:** Total events, active events, users, sessions
- **Quick Actions:** Create event, add user, Django admin, API docs
- **Events List:** All events with status and quick access

### 3. Navigation

The sidebar provides quick access to:
- 🏠 **Dashboard:** Home page
- ➕ **Create Event:** Start multi-step wizard
- 👥 **Users:** View all users
- ➕ **Create User:** Add new user
- ⚙️ **Django Admin:** Native Django admin
- 📚 **API Docs:** Swagger documentation
- 🚪 **Logout:** Sign out

---

## 🎪 Multi-Step Event Creation

### Overview

The event creation wizard guides you through 4 steps to create a complete event with rooms, sessions, and users.

### Step 1: Event Details

**Purpose:** Define basic event information

**Fields:**
- **Event Name** *(required)*: e.g., "TechSummit Algeria 2025"
- **Description**: Brief event description
- **Start Date** *(required)*: Event start date and time
- **End Date** *(required)*: Event end date and time
- **Location** *(required)*: e.g., "Centre des Congrès, Alger"
- **Location Details**: Additional location information
- **Status**: upcoming, active, completed, cancelled
- **Logo URL**: Event logo image URL
- **Banner URL**: Event banner image URL
- **Organizer Email**: Contact email
- **Number of Rooms** *(required)*: How many rooms the event will have

**Example:**
```
Event Name: TechSummit Algeria 2025
Description: Le plus grand sommet technologique d'Algérie
Start Date: 2025-03-15 09:00
End Date: 2025-03-17 18:00
Location: Centre des Congrès, Alger
Number of Rooms: 3
```

**Action:** Click "Next: Add Rooms" →

---

### Step 2: Add Rooms/Salles

**Purpose:** Configure each room/salle for the event

You'll add rooms one at a time based on the number specified in Step 1.

**Fields:**
- **Room Name** *(required)*: e.g., "Salle Principale", "Auditorium A"
- **Capacity** *(required)*: Maximum people
- **Description**: Room features and purpose
- **Floor**: Ground Floor, 2nd Floor, etc.
- **Room Type**: auditorium, workshop, conference, meeting
- **Equipment**: Available equipment list

**Example - Room 1 of 3:**
```
Room Name: Salle Principale
Capacity: 500
Description: Grande salle avec écran géant
Floor: Ground Floor
Room Type: Auditorium
Equipment: Projector, Microphone, Sound System
```

**Progress Bar:** Shows "Room 1 of 3", "Room 2 of 3", etc.

**Actions:**
- **Add Room & Continue:** Saves room and moves to next one
- **Cancel:** Abandons event creation

After adding all rooms → Automatically moves to Step 3

---

### Step 3: Add Sessions to Rooms

**Purpose:** Add conferences, ateliers, and workshops to each room

You'll configure sessions for each room. You can:
- Add multiple sessions per room
- Skip rooms with no sessions
- Move to next room when done

**Session Fields:**
- **Session Title** *(required)*: e.g., "Introduction to AI"
- **Type** *(required)*: Conference, Atelier, Workshop
- **Theme**: e.g., "Artificial Intelligence", "Blockchain"
- **Description**: Session details
- **Start Time** *(required)*: Session start
- **End Time** *(required)*: Session end
- **Speaker Name**: e.g., "Dr. Ahmed Benali"
- **Speaker Title**: e.g., "AI Research Scientist"
- **Speaker Bio**: Speaker background
- **Speaker Photo URL**: Speaker image
- **Max Participants**: Capacity limit
- **YouTube Live URL**: For hybrid events (optional)
- **Paid Session**: Checkbox for paid ateliers
- **Price (DZD)**: If paid session

**Example - Conference:**
```
Title: AI & Machine Learning Workshop
Type: Conference
Theme: Artificial Intelligence
Start Time: 2025-03-15 10:00
End Time: 2025-03-15 12:00
Speaker: Dr. Yasmine Khelifi
Speaker Title: AI Research Scientist
Max Participants: 200
YouTube Live URL: https://youtube.com/watch?v=...
Paid: No
```

**Example - Paid Atelier:**
```
Title: Hands-on Blockchain Development
Type: Atelier
Theme: Blockchain
Start Time: 2025-03-15 14:00
End Time: 2025-03-15 17:00
Speaker: Ahmed Boudiaf
Max Participants: 50
Paid: Yes
Price: 2500.00 DZD
```

**Left Panel:** Shows sessions already added to current room

**Actions:**
- **Add Session:** Adds session to current room (can add multiple)
- **Done with this room:** Moves to next room
- **Skip this room:** Skips to next room without adding sessions

---

### Step 4: Add Users & Assign Roles

**Purpose:** Create users and assign them to the event

**User Fields:**
- **Username** *(required)*: Unique username
- **Email** *(required)*: User email
- **First Name** *(required)*
- **Last Name** *(required)*
- **Password** *(required)*
- **Confirm Password** *(required)*
- **Role** *(required)*:
  - **Organisateur:** Full event management
  - **Gestionnaire des Salles:** Manage sessions and rooms
  - **Contrôleur des Badges:** Verify QR codes
  - **Participant:** Attend sessions
  - **Exposant:** Exhibitor/booth owner

**Example:**
```
Username: ahmed.benali
Email: ahmed.benali@techsummit.dz
First Name: Ahmed
Last Name: Benali
Password: ••••••••••
Role: Organisateur
```

**Automatic Actions:**
- ✅ User account created
- ✅ QR code generated automatically
- ✅ User assigned to event with selected role
- ✅ Participant profile created

**Left Panel:** Shows users already added

**Actions:**
- **Create User:** Adds user (can add multiple)
- **Finish & View Event:** Complete creation and view event details
- **Skip & Finish:** Complete without adding more users

**Success!** 🎉 Event created with all rooms, sessions, and users!

---

## 👥 User Management

### Create User (Quick Method)

**URL:** `/dashboard/users/create/`

1. Click "Create User" in sidebar or quick actions
2. Fill in user details
3. Select event and role
4. Click "Create User"

**Automatic:**
- Username generated from email
- QR code created
- User assigned to event
- Participant profile created

### View User Details

**URL:** `/dashboard/users/<user_id>/`

**Features:**
- User profile information
- QR code display
- Download QR code button
- Event assignments list
- Role history

### QR Code System

**How it works:**
1. Each user gets ONE unique QR code
2. QR code works across ALL events
3. Badge ID format: `USER-<user_id>-<unique_hash>`
4. QR code contains: user_id, badge_id

**Download QR Code:**
- Click "Download QR Code" button
- PNG image downloaded
- Ready to print on badges

---

## 📊 Event Dashboard

### Event Detail Page

**URL:** `/dashboard/events/<event_id>/`

**Statistics Cards:**
- **Participants:** Total + checked-in count
- **Rooms:** Total rooms
- **Sessions:** Total + breakdown by type
- **Exposants:** Count + scan statistics

**Tabs:**

#### 1. Overview Tab
- Event information
- Status, dates, location
- Description and contact
- Quick statistics

#### 2. Rooms Tab
- List all rooms
- Capacity, floor, type
- Session count per room

#### 3. Sessions Tab
- All sessions with details
- Session type, room, time
- Speaker information
- Registration counts
- YouTube live indicator

#### 4. Users Tab
- Users by role:
  - Organisateurs
  - Gestionnaires des Salles
  - Contrôleurs des Badges
  - Exposants

**Actions:**
- **Edit Event:** Modify event details
- **Delete Event:** Remove event (confirmation required)

---

## 🏗️ Technical Architecture

### Technology Stack

**Frontend:**
- HTML5, CSS3
- Bootstrap 5.3.0 (responsive design)
- Bootstrap Icons
- JavaScript (ES6)

**Backend:**
- Django 5.2.7
- Django Templates
- Session management
- Form handling

**Dependencies:**
```python
Django==5.2.7
qrcode==8.0          # QR code generation
Pillow==11.0.0       # Image processing
```

### Project Structure

```
makeplus_api/
├── dashboard/               # Admin dashboard app
│   ├── __init__.py
│   ├── admin.py            # Django admin config
│   ├── apps.py             # App configuration
│   ├── models.py           # (uses events models)
│   ├── views.py            # Dashboard views
│   ├── forms.py            # Form definitions
│   ├── urls.py             # URL routing
│   ├── templates/
│   │   └── dashboard/
│   │       ├── base.html           # Base template
│   │       ├── login.html          # Login page
│   │       ├── home.html           # Dashboard home
│   │       ├── event_create_step1.html
│   │       ├── event_create_step2.html
│   │       ├── event_create_step3.html
│   │       ├── event_create_step4.html
│   │       ├── event_detail.html
│   │       ├── event_edit.html
│   │       ├── event_delete.html
│   │       ├── user_list.html
│   │       ├── user_detail.html
│   │       └── user_create.html
│   └── static/
│       └── dashboard/
│           ├── css/
│           └── js/
├── events/                 # Main API app
│   └── models.py          # Data models
└── makeplus_api/
    ├── settings.py        # Project settings
    └── urls.py            # Main URL config
```

### URL Structure

```
/dashboard/                              → Dashboard home
/dashboard/login/                        → Login page
/dashboard/logout/                       → Logout

/dashboard/events/create/step1/          → Event creation step 1
/dashboard/events/create/step2/          → Event creation step 2
/dashboard/events/create/step3/          → Event creation step 3
/dashboard/events/create/step4/          → Event creation step 4

/dashboard/events/<uuid>/                → Event detail
/dashboard/events/<uuid>/edit/           → Edit event
/dashboard/events/<uuid>/delete/         → Delete event

/dashboard/users/                        → User list
/dashboard/users/create/                 → Create user
/dashboard/users/<id>/                   → User detail
/dashboard/users/<id>/qr-code/download/  → Download QR
```

### Session Management

The multi-step wizard uses Django sessions to store temporary data:

```python
# Session variables:
session['event_id']                    # Current event being created
session['number_of_rooms']             # Total rooms to add
session['rooms_data']                  # List of created room IDs
session['current_room_for_sessions']   # Current room index
```

### Authentication & Security

**Login Required:**
- All dashboard views require authentication
- Staff users only (is_staff=True or is_superuser=True)

**Permissions:**
```python
@login_required
@user_passes_test(is_staff_user)
def dashboard_view(request):
    # View logic
```

**CSRF Protection:**
- All forms include `{% csrf_token %}`
- Django CSRF middleware enabled

---

## 🔧 Troubleshooting

### Common Issues

#### 1. "Permission Denied" Error

**Symptom:** Can't access dashboard after login

**Solution:**
```python
# In Django shell or admin
user = User.objects.get(username='your_username')
user.is_staff = True
user.save()
```

#### 2. QR Code Not Generating

**Symptom:** Missing QR code image

**Solution:**
```bash
# Install missing dependencies
pip install qrcode Pillow
```

#### 3. Templates Not Found

**Symptom:** TemplateDoesNotExist error

**Solution:**
- Check INSTALLED_APPS includes 'dashboard'
- Verify templates are in `dashboard/templates/dashboard/`

#### 4. Static Files Not Loading

**Symptom:** No CSS/images in dashboard

**Solution:**
```bash
# Collect static files
python manage.py collectstatic --noinput

# Check settings.py
STATIC_ROOT = BASE_DIR / 'staticfiles'
```

#### 5. Session Data Lost

**Symptom:** Multi-step wizard resets

**Solution:**
- Clear browser cookies
- Check SESSION_ENGINE in settings.py
- Restart Django server

### Debug Mode

To enable debugging:

```python
# settings.py
DEBUG = True

# Run with verbose logging
python manage.py runserver --verbosity 3
```

---

## 🔗 API Integration

The dashboard works seamlessly with the mobile API:

### Data Flow

```
Dashboard (Web)           API (Mobile)
     ↓                         ↓
Create Event     →    GET /api/events/
Create User      →    POST /api/auth/login/
Generate QR      →    POST /api/verify-qr/
Add Sessions     →    GET /api/sessions/
```

### Shared Models

Dashboard and API share the same database models:
- Event
- Room
- Session
- User / UserProfile
- UserEventAssignment
- Participant

**Changes in dashboard are immediately available in API!**

### Testing Workflow

1. **Dashboard:** Create event "TechSummit 2025"
2. **Dashboard:** Add 3 rooms
3. **Dashboard:** Add 10 sessions
4. **Dashboard:** Create user "ahmed@test.com" with role "participant"
5. **Dashboard:** Download QR code
6. **Mobile App:** Login as ahmed@test.com
7. **Mobile App:** See TechSummit 2025
8. **Mobile App:** See all 10 sessions
9. **Mobile App:** Scan QR code → Access granted

---

## 📱 Mobile App Compatibility

### What Dashboard Creates for Mobile:

1. **Events** → Mobile: Event list, event details
2. **Rooms** → Mobile: Room navigation
3. **Sessions** → Mobile: Session schedule, registration
4. **Users** → Mobile: Login, authentication
5. **QR Codes** → Mobile: Badge scanning, access control

### Dashboard → Mobile Mapping

| Dashboard Feature | Mobile API Endpoint | Mobile Screen |
|-------------------|---------------------|---------------|
| Create Event | GET /api/events/ | Events List |
| Add Room | GET /api/rooms/?event= | Room Navigator |
| Add Session | GET /api/sessions/?event= | Schedule |
| Create User | POST /api/auth/login/ | Login Screen |
| Generate QR | POST /api/verify-qr/ | Badge Scanner |
| Add YouTube Link | GET /api/sessions/<id>/ | Live Stream |
| Set Paid Atelier | GET /api/my-ateliers/ | My Ateliers |

---

## 🎨 Customization

### Branding

Update colors in `base.html`:

```css
:root {
    --primary-color: #4f46e5;  /* Change this */
    --sidebar-width: 260px;
}

.sidebar {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    /* Change gradient colors */
}
```

### Logo

Replace sidebar brand:

```html
<a href="{% url 'dashboard:home' %}" class="sidebar-brand">
    <i class="bi bi-grid-1x2-fill"></i> Your Brand
</a>
```

### Email Notifications

Add email notifications when users are created:

```python
# In user_create view
from django.core.mail import send_mail

send_mail(
    'Welcome to Our Event',
    f'Your account has been created. Username: {user.username}',
    'from@example.com',
    [user.email],
)
```

---

## 📊 Statistics & Analytics

### Current Statistics

Dashboard provides:
- Total events, users, sessions
- Active/upcoming/completed event counts
- Participant check-in rates
- Room access tracking
- Exposant scan statistics
- Session registration numbers
- Q&A activity

### Future Enhancements

Potential additions:
- Charts and graphs (Chart.js)
- Export reports (PDF, Excel)
- Email campaigns
- Attendance analytics
- Revenue tracking
- Real-time dashboards

---

## 🚀 Deployment

### Production Checklist

Before deploying to production:

```python
# settings.py
DEBUG = False
ALLOWED_HOSTS = ['yourdomain.com']

# Use PostgreSQL
USE_SUPABASE = True

# Set strong SECRET_KEY
SECRET_KEY = 'your-production-secret-key'

# Collect static files
python manage.py collectstatic --noinput

# Set up HTTPS
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

### Render.com Deployment

Dashboard is automatically deployed with your main app:

1. Push to GitHub
2. Render auto-deploys
3. Dashboard available at: `https://your-app.onrender.com/dashboard/`

---

## 📚 Additional Resources

### Related Documentation

- [BACKEND_DOCUMENTATION.md](BACKEND_DOCUMENTATION.md) - API Reference
- [FLUTTER_INTEGRATION_GUIDE.md](FLUTTER_INTEGRATION_GUIDE.md) - Mobile Integration
- [USER_ACCESS_CONTROL_SYSTEM.md](USER_ACCESS_CONTROL_SYSTEM.md) - Permission System
- [YOUTUBE_AND_QA_INTEGRATION.md](YOUTUBE_AND_QA_INTEGRATION.md) - Live Streaming

### External Links

- [Django Documentation](https://docs.djangoproject.com/)
- [Bootstrap 5 Docs](https://getbootstrap.com/docs/5.3/)
- [Bootstrap Icons](https://icons.getbootstrap.com/)

---

## 💬 Support

For issues or questions:
- Check [Troubleshooting](#troubleshooting) section
- Review Django logs
- Check browser console for JS errors
- Verify database connections

---

## ✅ Summary

The MakePlus Admin Dashboard provides a complete solution for managing events:

✅ **Multi-Step Event Creation** - Guided wizard for creating events with rooms and sessions  
✅ **User Management** - Create users, assign roles, generate QR codes  
✅ **Event Dashboard** - Comprehensive statistics and insights  
✅ **Mobile Compatible** - Works seamlessly with mobile API  
✅ **Responsive Design** - Works on desktop, tablet, mobile  
✅ **Production Ready** - Secure, tested, deployed  

**Ready to use!** Access at: `http://127.0.0.1:8000/dashboard/`

---

**Documentation Version:** 1.0  
**Last Updated:** December 17, 2025  
**Status:** ✅ Complete
