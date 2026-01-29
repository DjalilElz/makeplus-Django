# Email Campaign & Form Analytics - WORKING!

## ✅ System Status

**Django Server**: Running on http://127.0.0.1:8000/
**Admin Panel**: http://127.0.0.1:8000/admin/
**All Migrations**: Applied successfully
**All Models**: Created and registered

---

## 📧 Email Campaign Tracking (Mailerlite-like)

### Features Implemented

1. **Email Open Tracking**
   - 1x1 transparent tracking pixel
   - Records every time recipient opens email
   - Tracks first_opened_at, last_opened_at, open_count
   - IP address and user agent logging

2. **Link Click Tracking**
   - All links in email automatically tracked
   - Unique tracking per recipient per link
   - Records total clicks and unique clicks
   - IP address and user agent for each click

3. **Per-Recipient Statistics**
   - Individual open count for each recipient
   - Individual click count for each recipient
   - First and last opened timestamps
   - Delivery status tracking

4. **Per-Link Statistics**
   - Total clicks per link across all recipients
   - Unique recipients who clicked each link
   - Click-through rate calculation
   - Link-level analytics

5. **Campaign-Level Statistics**
   - Total sent/delivered/failed counts
   - Overall open rate percentage
   - Overall click rate percentage
   - Unique opens vs total opens
   - Unique clicks vs total clicks

6. **Unsubscribe Functionality**
   - One-click unsubscribe link in emails
   - Automatic status update to 'unsubscribed'

---

## 📊 Form Analytics System

### Features Implemented

1. **Form View Tracking**
   - Session-based tracking
   - Device type detection (desktop/mobile/tablet)
   - Browser detection
   - UTM parameter capture (source, medium, campaign)
   - Referer URL tracking
   - IP address logging

2. **Field-Level Interaction Tracking**
   - Time spent on each field
   - Number of changes per field
   - Field completion tracking
   - Helps identify problem fields

3. **Conversion Tracking**
   - Automatic conversion rate calculation
   - Total views vs submissions
   - Device breakdown (desktop vs mobile submissions)
   - Traffic source analysis
   - Top performing UTM campaigns

4. **Automatic Confirmation Emails**
   - Send email automatically after form submission
   - Template variable replacement ({{name}}, {{email}}, etc.)
   - Uses FormConfiguration.confirmation_email_template
   - Configurable per form

---

## 🗂️ Database Models Created

### Email Campaign Models
1. **EmailCampaign** - Campaign management with statistics
2. **EmailRecipient** - Individual recipient tracking with tokens
3. **EmailLink** - Per-link click tracking
4. **EmailClick** - Individual click events
5. **EmailOpen** - Individual open events

### Form Analytics Models
6. **FormAnalytics** - Aggregate form statistics
7. **FormView** - Individual form view sessions
8. **FormFieldInteraction** - Field-level engagement data

---

## 🔗 API Endpoints

### Email Tracking
```
GET  /track/email/open/<token>/
     - Returns 1x1 transparent PNG
     - Records email open event

GET  /track/email/click/<link_token>/<recipient_token>/
     - Records click event
     - Redirects to original URL

GET  /track/email/unsubscribe/<token>/
     - Unsubscribes recipient
     - Returns confirmation message
```

### Form Analytics
```
POST /track/form/view/<form_id>/
     - Records form view
     - Body: {
         "session_id": "string",
         "device_type": "desktop|mobile|tablet",
         "browser": "string",
         "ip_address": "string",
         "referer": "string",
         "utm_source": "string",
         "utm_medium": "string",
         "utm_campaign": "string"
     }

POST /track/form/interaction/<form_id>/
     - Records field interaction
     - Body: {
         "session_id": "string",
         "field_name": "string",
         "time_spent": 10,
         "changes_count": 3,
         "completed": true
     }
```

---

## 🎯 How to Use

### Creating an Email Campaign

1. **Go to Admin Panel**
   - Navigate to http://127.0.0.1:8000/admin/
   - Login with your admin credentials

2. **Create Email Campaign**
   ```
   - Click "Email campaigns" → "Add"
   - Fill in:
     * Name: "Newsletter January 2026"
     * Subject: "Check out our latest updates!"
     * Body: HTML content with links
     * Event: Select event (optional)
     * Track Opens: ✓
     * Track Clicks: ✓
   - Save
   ```

3. **Add Recipients**
   ```
   - Click "Email recipients" → "Add"
   - Select the campaign
   - Enter email address and name
   - Save (tracking_token generated automatically)
   - Repeat for all recipients
   ```

4. **Send Campaign (Python)**
   ```python
   from dashboard.utils_campaign import send_campaign
   
   # Send to all recipients
   send_campaign(campaign_id=1)
   ```

5. **View Statistics**
   ```
   - Go to "Email campaigns" in admin
   - See Open Rate, Click Rate columns
   - Click campaign → View detailed stats
   - Check "Email opens" for individual opens
   - Check "Email clicks" for individual clicks
   ```

---

### Tracking Form Analytics

1. **Configure Form**
   ```python
   from dashboard.models_form import FormConfiguration
   
   form = FormConfiguration.objects.get(id=YOUR_FORM_ID)
   form.send_confirmation_email = True
   form.confirmation_email_template = email_template  # Select template
   form.save()
   ```

2. **Frontend Integration**
   ```javascript
   // When form loads
   fetch('/track/form/view/FORM_ID/', {
       method: 'POST',
       headers: {'Content-Type': 'application/json'},
       body: JSON.stringify({
           session_id: 'unique_session_id',
           device_type: 'desktop',
           browser: 'Chrome',
           utm_source: 'facebook',
           utm_medium: 'cpc',
           utm_campaign: 'summer_sale'
       })
   });
   
   // When user interacts with field
   fetch('/track/form/interaction/FORM_ID/', {
       method: 'POST',
       headers: {'Content-Type': 'application/json'},
       body: JSON.stringify({
           session_id: 'unique_session_id',
           field_name: 'email',
           time_spent: 5,
           changes_count: 2,
           completed: true
       })
   });
   ```

3. **View Analytics**
   ```
   - Go to "Form analytics" in admin
   - See conversion rates, device breakdown
   - Check "Form views" for session details
   - Check "Form field interactions" for field problems
   ```

---

## 🧪 Testing the System

### Test Email Tracking

1. **Create Test Campaign**
   ```python
   from dashboard.models_email import EmailCampaign, EmailRecipient
   
   campaign = EmailCampaign.objects.create(
       name="Test Campaign",
       subject="Test Email",
       body="""
       <h1>Hello!</h1>
       <p>This is a test email.</p>
       <a href="https://example.com">Click here</a>
       """,
       track_opens=True,
       track_clicks=True
   )
   
   recipient = EmailRecipient.objects.create(
       campaign=campaign,
       email="test@example.com",
       name="Test User"
   )
   ```

2. **Send Test Email**
   ```python
   from dashboard.utils_campaign import send_campaign_email
   send_campaign_email(recipient)
   ```

3. **Test Tracking URLs**
   ```
   # Open tracking (copy recipient.tracking_token)
   http://127.0.0.1:8000/track/email/open/RECIPIENT_TOKEN/
   
   # Click tracking (get tokens from EmailLink model)
   http://127.0.0.1:8000/track/email/click/LINK_TOKEN/RECIPIENT_TOKEN/
   ```

4. **Check Statistics**
   ```python
   # Refresh from database
   recipient.refresh_from_db()
   print(f"Opens: {recipient.open_count}")
   print(f"Clicks: {recipient.click_count}")
   
   campaign.refresh_from_db()
   print(f"Open Rate: {campaign.get_open_rate()}%")
   print(f"Click Rate: {campaign.get_click_rate()}%")
   ```

---

## 📁 File Structure

```
makeplus_api/
├── dashboard/
│   ├── models_email.py          # Email campaign models
│   ├── models_form.py           # Form analytics models
│   ├── views_tracking.py        # Tracking endpoints
│   ├── urls_tracking.py         # Tracking URL routes
│   ├── utils_campaign.py        # Campaign utilities
│   └── admin.py                 # Admin registrations
├── makeplus_api/
│   ├── settings.py              # Email config added
│   └── urls.py                  # Tracking routes included
└── migrations/
    └── 0006_...                 # All tracking tables
```

---

## ⚙️ Configuration

### Email Settings (in settings.py)

```python
# SMTP Configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST', default='localhost')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@makeplus.com')

# Site URL for tracking links
SITE_URL = config('SITE_URL', default='http://127.0.0.1:8000')
```

### Environment Variables (.env)

```env
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@makeplus.com
SITE_URL=https://yourdomain.com
```

---

## 🔧 Utility Functions

### Send Campaign to All Recipients
```python
from dashboard.utils_campaign import send_campaign

# Sends to all recipients in campaign
result = send_campaign(campaign_id=1)
print(f"Sent: {result['sent']}, Failed: {result['failed']}")
```

### Send to Single Recipient
```python
from dashboard.utils_campaign import send_campaign_email
from dashboard.models_email import EmailRecipient

recipient = EmailRecipient.objects.get(id=1)
send_campaign_email(recipient)
```

### Process Links for Tracking
```python
from dashboard.utils_campaign import process_email_links_for_tracking

links = process_email_links_for_tracking(campaign)
print(f"Found {len(links)} links in email")
```

### Send Form Confirmation
```python
from dashboard.utils_campaign import send_form_confirmation_email

send_form_confirmation_email(
    form_submission=submission,
    recipient_email="user@example.com",
    context={'name': 'John', 'email': 'john@example.com'}
)
```

---

## 📈 Admin Panel Features

### EmailCampaign Admin
- List display: Name, Event, Status, Total Sent, Opens, Clicks, Open Rate, Click Rate
- Filters: Status, Event, Created Date, Track Opens, Track Clicks
- Search: Name, Subject, From Email
- Readonly: Statistics fields, timestamps

### EmailRecipient Admin
- List display: Email, Campaign, Status, Open Count, Click Count, Sent Date, First Opened
- Filters: Status, Campaign, Sent Date
- Search: Email, Name, Tracking Token

### EmailLink Admin
- List display: URL, Campaign, Total Clicks, Unique Clicks, Click Rate
- Filters: Campaign, Created Date
- Search: URL, Tracking Token

### FormAnalytics Admin
- List display: Form, Total Views, Total Submissions, Conversion Rate, Last Updated
- Filters: Form, Last Updated
- Search: Form Name

---

## ✨ Key Features Summary

✅ **Email Open Tracking** - Pixel-based tracking like Mailerlite
✅ **Link Click Tracking** - Every link tracked individually
✅ **Per-Recipient Stats** - Detailed metrics for each person
✅ **Per-Link Stats** - Click-through rates for each URL
✅ **Campaign Statistics** - Overall open/click rates
✅ **Form View Tracking** - Session-based analytics
✅ **Field Interaction Tracking** - Identify problem fields
✅ **Conversion Tracking** - Automatic rate calculation
✅ **Device/Browser Analytics** - Understand your audience
✅ **UTM Campaign Tracking** - Track marketing effectiveness
✅ **Auto Confirmation Emails** - Send after form submission
✅ **Template Variables** - {{name}}, {{email}} replacement
✅ **Unsubscribe Links** - One-click opt-out
✅ **Admin Dashboard** - Beautiful statistics display

---

## 🚀 Next Steps

1. **Configure Production Email**
   - Set up SMTP credentials in .env
   - Test email delivery

2. **Integrate Frontend**
   - Add form view tracking
   - Add field interaction tracking
   - Implement session ID generation

3. **Create Email Templates**
   - Design professional email templates
   - Add unsubscribe links
   - Test across email clients

4. **Set Up Celery (Optional)**
   - Background task processing
   - Scheduled campaign sending
   - Better performance for large campaigns

5. **Add Email Verification**
   - Verify recipient email addresses
   - Bounce handling
   - Spam prevention

---

## 📞 Support

For issues or questions:
- Check Django admin logs
- Review terminal output for errors
- Verify email configuration in .env
- Test tracking URLs directly in browser
- Check database for recorded events

---

**Status**: ✅ FULLY IMPLEMENTED AND WORKING
**Server**: 🟢 RUNNING
**Database**: ✅ MIGRATED
**Admin Panel**: ✅ ACCESSIBLE
