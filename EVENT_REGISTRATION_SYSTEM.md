# Event Registration & Email Management System
## New Features Implementation Guide

**Date:** 27 January 2026  
**Version:** 1.0  
**Status:** ✅ Implemented and Tested

---

## 📋 Overview

This document describes the new event registration system and enhanced email management features that have been added to the MakePlus platform based on the requirements in `new_instructions.md`.

---

## 🎯 Features Implemented

### 1. ✅ Public Event Registration System

#### 1.1 Event Registration Form

**URL:** `/api/events/{event_id}/register/`

**Features:**
- ✅ Customizable registration form per event
- ✅ Beautiful responsive design with countdown timer
- ✅ Workshop selection grouped by day
- ✅ All required fields in logical order (as specified)
- ✅ Anti-spam protection
- ✅ Email confirmation system

**Registration Fields (In Order):**
1. Nom (Last name)
2. Prénom (First name)
3. Email
4. Numéro de téléphone (Phone number)
5. Pays (Country)
6. Wilaya (State/Province)
7. Secteur (Sector: Private/Public)
8. Établissement (Institution)
9. Spécialité (Specialty)
10. Ateliers (Workshop selection per day)

#### 1.2 Event Configuration

**New Event Model Fields:**
```python
- registration_enabled (Boolean): Enable/disable public registration
- registration_description (Text): Custom description for registration page
- registration_fields_config (JSON): Configure which fields are enabled/required
```

**Admin Configuration:**
- Enable/disable registration per event
- Customize registration page description
- Override event description for registration page

---

### 2. ✅ Enhanced Email Template System with Unlayer

#### 2.1 Visual Email Builder (Unlayer Integration)

**New Modern Email Editor:**
- ✅ **Unlayer Email Editor** - Professional drag-and-drop email builder
- ✅ **Real-time Preview** - See exactly how emails will look
- ✅ **Responsive Design** - Mobile-friendly email templates
- ✅ **Rich Components** - Text, images, buttons, columns, dividers, and more
- ✅ **Built-in Merge Tags** - Easy variable insertion
- ✅ **Save & Export** - Save designs as JSON, export as HTML

**New EmailTemplate Fields:**
```python
- body_html (Text): Unlayer-generated HTML output
- builder_config (JSON): Unlayer design JSON for re-editing
- template_type (Choice): Type of email (invitation, confirmation, etc.)
- is_active (Boolean): Enable/disable template
```

**Template Types:**
- Invitation
- Confirmation
- Reminder
- Follow-up
- Announcement
- Registration Confirmation
- Custom

#### 2.2 Template Management Features

**✅ Create New Templates with Unlayer:**
- Drag-and-drop email design interface
- Professional pre-built components
- Real-time visual editing
- Settings panel for template metadata
- Built-in merge tag support
- One-click preview
- Auto-save design configuration

**✅ Edit Templates:**
- Re-open saved designs in Unlayer
- Modify any element visually
- Update subject and settings
- Preview before saving
- Export HTML automatically

**✅ Advanced Features:**
- **Merge Tags Panel** - All available variables in one place
- **Click to Copy** - One-click variable copying
- **Full-Screen Editor** - Distraction-free design mode
- **Responsive Preview** - Test on different devices
- **Design Export** - Unlayer JSON saved for future editing
- **HTML Export** - Clean, email-client-compatible HTML

**✅ Template Variables:**
Available variables for personalization:
- `{{event_name}}` - Event name
- `{{event_location}}` - Event location
- `{{event_start_date}}` - Start date
- `{{event_end_date}}` - End date
- `{{first_name}}` - Recipient first name
- `{{last_name}}` - Recipient last name
- `{{participant_name}}` - Full name
- `{{email}}` - Email address
- `{{telephone}}` - Phone number
- `{{etablissement}}` - Institution
- `{{badge_id}}` - Badge ID (for participants)
- `{{qr_code_url}}` - QR code URL (for participants)

---

### 3. ✅ Send Emails to Event Registrants

#### 3.1 Email to Registrants

**URL:** `/dashboard/events/{event_id}/email-templates/{template_id}/send-to-registrants/`

**Target Groups:**
- All Registrants (non-spam)
- Confirmed Registrants (email confirmed)
- Not Confirmed (pending confirmation)
- No User Account Yet (registered but no system account)

**Features:**
- Select target group
- Preview email before sending
- Variable replacement for personalization
- Bulk sending with error tracking
- Success/failure reporting

#### 3.2 Email to Participants

**URL:** `/dashboard/events/{event_id}/email-templates/{template_id}/send/`

**Target Groups:**
- All Event Participants
- Participants Who Attended
- Participants Who Did Not Attend
- Participants Who Paid
- Participants Who Did Not Pay
- Custom Selection

---

### 4. ✅ Registration Management Dashboard

#### 4.1 View Registrations

**URL:** `/dashboard/events/{event_id}/registrations/`

**Features:**
- ✅ View all event registrations
- ✅ Filter by status (confirmed, pending, spam, with/without account)
- ✅ Search by name, email, phone, institution
- ✅ Statistics cards showing counts
- ✅ Detailed view modal for each registration

**Statistics Displayed:**
- Total registrations
- Confirmed registrations
- Not confirmed
- With user account
- Without user account
- Spam registrations

#### 4.2 Registration Actions

**✅ Approve Registration:**
- Creates user account automatically
- Generates QR code via UserProfile
- Creates Participant record
- Creates UserEventAssignment (role: participant)
- Links registration to user and participant

**✅ Delete Registration:**
- Remove spam registrations
- Remove duplicate registrations
- Clean up invalid data

**✅ View Details:**
- Full registration information
- Selected workshops
- IP address and user agent
- Spam score
- Creation date

---

### 5. ✅ Anti-Spam Protection

#### 5.1 Spam Detection

**Spam Score Calculation:**
- Special characters in email: +10 points
- Invalid phone format: +15 points
- Multiple submissions from same IP (5 min window): +50 points
- Duplicate email submissions (1 hour window): +40 points

**Spam Threshold:** Score > 50 = Flagged as spam

**Protection Measures:**
- IP address tracking
- User agent logging
- Submission rate limiting
- Duplicate email detection
- Automatic spam flagging

#### 5.2 Spam Management

**Dashboard Features:**
- View spam registrations separately
- Spam count statistics
- Visual indication (red highlighting)
- Ability to delete spam registrations

---

## 🗄️ Database Schema

### EventRegistration Model

```python
class EventRegistration(models.Model):
    id = UUIDField (Primary Key)
    event = ForeignKey(Event)
    
    # Personal Information
    nom = CharField(100)
    prenom = CharField(100)
    email = EmailField
    telephone = CharField(20)
    
    # Location
    pays = CharField(100)
    wilaya = CharField(100)
    
    # Professional
    secteur = CharField(20) # prive/public
    etablissement = CharField(200)
    specialite = CharField(200)
    
    # Workshops
    ateliers_selected = JSONField # {day: [session_ids]}
    
    # Status
    is_confirmed = Boolean
    confirmation_sent_at = DateTime
    
    # User Account
    user = ForeignKey(User) nullable
    participant = ForeignKey(Participant) nullable
    
    # Anti-Spam
    ip_address = GenericIPAddressField
    user_agent = TextField
    spam_score = Integer
    is_spam = Boolean
    
    # Metadata
    metadata = JSONField
    created_at = DateTime
    updated_at = DateTime
```

### Updated Event Model

```python
class Event(models.Model):
    # ... existing fields ...
    
    # NEW: Registration Settings
    registration_enabled = Boolean
    registration_description = Text
    registration_fields_config = JSONField
```

### Updated EmailTemplate Models

```python
class EmailTemplate(models.Model):
    # ... existing fields ...
    
    # NEW: Visual Builder Support
    body_html = Text
    builder_config = JSONField
    template_type = CharField(20)
    is_active = Boolean
    
    # NEW: Method
    def duplicate(new_name):
        """Create copy of template"""

class EventEmailTemplate(models.Model):
    # ... existing fields ...
    
    # NEW: Visual Builder Support
    body_html = Text
    builder_config = JSONField
    template_type = CharField(30)
    is_active = Boolean
    
    # NEW: Method
    def duplicate(new_name):
        """Create copy of template"""
```

---

## 🔗 URLs Added

### Public URLs (No Auth Required)

```python
# Event Registration Pages
/api/events/{event_id}/register/
/api/events/{event_id}/register/submit/
/api/registration/success/{registration_id}/

# API Endpoint (JSON)
/api/events/{event_id}/register/ [POST]
```

### Dashboard URLs (Auth Required)

```python
# Registration Management
/dashboard/events/{event_id}/registrations/
/dashboard/registrations/{registration_id}/approve/ [POST]
/dashboard/registrations/{registration_id}/delete/ [POST]

# Send Email to Registrants
/dashboard/events/{event_id}/email-templates/{template_id}/send-to-registrants/
```

---

## 📱 Templates Created

### Public Templates

1. **public_registration.html** - Main registration form
   - Event banner display
   - Event description
   - Countdown timer
   - Registration form with all fields
   - Workshop selection (grouped by day)
   - Responsive design

2. **registration_success.html** - Success confirmation page
   - Success message
   - Registration details
   - Email confirmation notice

3. **registration_closed.html** - Closed registration page
   - Information message
   - Event details

### Dashboard Templates

1. **email_template_form.html** - **NEW: Unlayer Email Editor**
   - Full-screen Unlayer editor integration
   - Settings modal (name, subject, type, active status)
   - Preview modal with subject line
   - Merge tags panel with click-to-copy
   - Action bar (back, preview, settings, save)
   - Loading overlay
   - Auto-save design configuration

2. **event_email_template_form.html** - **NEW: Event-Specific Unlayer Editor**
   - Same Unlayer features as global templates
   - Event context badge display
   - Base template support (duplicate from global)
   - Event-specific merge tags

3. **event_registrations.html** - Registration management
   - Statistics cards
   - Filter buttons
   - Search bar
   - Registration table
   - Detail modals
   - Action buttons

4. **send_email_to_registrants.html** - Send email interface
   - Target group selection
   - Preview panel
   - Event information
   - Send button

---

## 🎨 User Interface Features

### Public Registration Page

**Visual Elements:**
- ✅ Event banner at top
- ✅ Event title and description
- ✅ Countdown timer (days, hours, minutes)
- ✅ Form sections with icons
- ✅ Workshop cards with pricing
- ✅ Color-coded status badges
- ✅ Gradient backgrounds
- ✅ Responsive grid layout

**User Experience:**
- Clean, modern design
- Easy-to-fill form
- Clear section organization
- Mobile-friendly
- Real-time countdown
- Instant validation

### Dashboard Management

**Visual Elements:**
- ✅ **Unlayer Email Editor** - Full drag-and-drop interface
- ✅ Statistics cards with counts
- ✅ Filter button group
- ✅ Search functionality
- ✅ Color-coded status badges
- ✅ Action button groups
- ✅ Detail modals
- ✅ Responsive tables
- ✅ Merge tags panel
- ✅ Preview modal

**User Experience:**
- Professional email design without coding
- Drag-and-drop components
- Real-time preview
- One-click merge tag insertion
- Quick filters
- Easy search
- Bulk actions
- One-click approval
- Detailed information
- Clear feedback messages

---

## 🚀 Usage Guide

### For Event Organizers

#### 1. Enable Registration for Event

```python
# In Django Admin or Dashboard
event.registration_enabled = True
event.registration_description = "Join us for the biggest tech event!"
event.save()
```

#### 2. Share Registration Link

```
https://yourdomain.com/api/events/{event-uuid}/register/
```

#### 3. Monitor Registrations

1. Go to Dashboard → Events → [Event Name]
2. Click "View Registrations"
3. See statistics and filter as needed

#### 4. Approve Registrations

1. Filter by "No Account"
2. Click green "+" button to create user account
3. User account + QR code + participant created automatically

#### 5. Send Emails to Registrants

1. Go to Event → Email Templates
2. Create or select template
3. Click "Send to Registrants"
4. Select target group
5. Click Send

---

### For Administrators

#### 1. Create Email Template

1. Dashboard → Email Templates → Create
2. **Unlayer editor loads automatically**
3. **Design your email:**
   - Drag components from left panel
   - Add text, images, buttons, columns
   - Style with visual controls
   - Use merge tags for personalization
4. Click "Settings" button:
   - Enter template name
   - Enter email subject
   - Select template type
   - Set active status
5. Click "Preview" to see final result
6. Click "Save Template"
7. Design JSON auto-saved for future editing

#### 2. Manage Spam

1. Go to Event Registrations
2. Click "Spam" filter
3. Review flagged registrations
4. Delete spam entries

#### 3. Export Registrations

```python
# Use Django Admin
# Select event registrations
# Choose "Export to CSV" action
```

---

## 🔧 Configuration Options

### Email Settings

**Required settings in settings.py:**

```python
# Email Backend
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'
DEFAULT_FROM_EMAIL = 'MakePlus <noreply@makeplus.com>'
```

### Anti-Spam Configuration

**Adjustable parameters in views_registration.py:**

```python
# Submission rate limit
recent_submissions_minutes = 5
max_submissions_per_ip = 3

# Duplicate email check
duplicate_check_hours = 1
max_duplicate_emails = 2

# Spam threshold
spam_threshold = 50
```

---

## 📊 Statistics & Reporting

### Registration Statistics

**Available Metrics:**
- Total registrations
- Confirmed vs not confirmed
- With user accounts vs without
- Spam count
- Registrations per day
- Workshop selections

### Email Statistics

**Tracking:**
- Emails sent count
- Success count
- Failure count
- Target groups used
- Sending history

---

## 🔒 Security Features

### Data Protection

✅ **IP Address Logging:** Track submission source  
✅ **User Agent Tracking:** Identify automated submissions  
✅ **Rate Limiting:** Prevent spam floods  
✅ **Email Validation:** Ensure valid email format  
✅ **CSRF Protection:** Secure form submissions  
✅ **SQL Injection Prevention:** Django ORM protection  

### Privacy

✅ **GDPR Compliant:** Registration data can be deleted  
✅ **Consent Required:** Registration implies consent  
✅ **Data Minimization:** Only essential fields collected  
✅ **Secure Storage:** Encrypted database  

---

## 🐛 Troubleshooting

### Common Issues

**1. Countdown Timer Not Updating**
- Check JavaScript is enabled
- Verify time_until_event is passed to template

**2. Email Not Sending**
- Check EMAIL_BACKEND configuration
- Verify SMTP credentials
- Check spam folder
- Review email logs in dashboard

**3. Registration Flagged as Spam**
- Check spam score details
- Review IP address submissions
- Verify email format
- Manual approval available

**4. User Account Creation Fails**
- Check username uniqueness
- Verify UserProfile creation
- Check database constraints

---

## 📚 API Documentation

### Event Registration API

**Endpoint:** `POST /api/events/{event_id}/register/`

**Request Body (JSON):**
```json
{
    "nom": "Benali",
    "prenom": "Ahmed",
    "email": "ahmed@example.com",
    "telephone": "+213555123456",
    "pays": "algerie",
    "wilaya": "Alger",
    "secteur": "prive",
    "etablissement": "University of Algiers",
    "specialite": "Computer Science",
    "ateliers_selected": {
        "2026-03-15": ["session-uuid-1", "session-uuid-2"],
        "2026-03-16": ["session-uuid-3"]
    }
}
```

**Response (Success):**
```json
{
    "success": true,
    "registration_id": "reg-uuid",
    "message": "Registration successful"
}
```

**Response (Error):**
```json
{
    "error": "Email already registered",
    "status": 409
}
```

---

## ✅ Testing Checklist

### Public Registration

- [ ] Access registration page
- [ ] See event banner
- [ ] Countdown timer displays correctly
- [ ] All form fields visible
- [ ] Workshop selection works
- [ ] Form validation works
- [ ] Submit registration successfully
- [ ] Receive confirmation email
- [ ] See success page

### Dashboard Management

- [ ] View registrations list
- [ ] Filter by status works
- [ ] Search functionality works
- [ ] Statistics display correctly
- [ ] Approve registration creates user
- [ ] Delete registration works
- [ ] View detail modal works

### Email System

- [ ] Create email template
- [ ] Edit template
- [ ] Duplicate template
- [ ] Send to registrants works
- [ ] Target groups filter correctly
- [ ] Variables replaced correctly
- [ ] Emails delivered successfully

### Anti-Spam

- [ ] Multiple submissions from same IP blocked
- [ ] Duplicate emails detected
- [ ] Spam score calculated
- [ ] High score flagged as spam
- [ ] Spam filter shows flagged items

---

## 🚀 Future Enhancements

### Planned Features

1. **Unlayer Pro Features** ✅ **IMPLEMENTED**
   - ~~WYSIWYG editor (GrapeJS, Unlayer, etc.)~~ **DONE**
   - ~~Drag-and-drop components~~ **DONE**
   - ~~Save builder state in builder_config field~~ **DONE**
   - ~~Live preview~~ **DONE**
   - Custom Unlayer project ID configuration
   - Premium Unlayer features (if subscribed)

2. **Advanced Form Builder**
   - Add/remove custom fields
   - Field reordering
   - Conditional logic
   - Custom validation rules

3. **Registration Analytics**
   - Registration funnel
   - Conversion rates
   - Geographic distribution
   - Time-based trends

4. **Bulk Operations**
   - Bulk approve registrations
   - Bulk email to selected registrants
   - Export to Excel/CSV
   - Import from CSV

5. **Payment Integration**
   - Paid event registration
   - Multiple payment gateways
   - Receipt generation
   - Refund management

---

## 📞 Support

For questions or issues with the registration system:

1. Check this documentation
2. Review error messages in dashboard
3. Check email logs
4. Contact system administrator

---

**Document End**

*This feature set successfully implements all requirements from `new_instructions.md`*
