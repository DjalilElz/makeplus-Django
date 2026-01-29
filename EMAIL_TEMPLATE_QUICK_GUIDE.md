# Quick Start Guide: Email Templates & Registration Form Builder

## 🚀 Quick Access

**Email Templates Dashboard:**
```
http://localhost:8000/dashboard/email-templates/
```

**Registration Form Builder:**
```
http://localhost:8000/dashboard/registration-form-builder/
```

## 📧 Email Template Actions

### 1️⃣ Test Email (Blue Button)
**Use when:** You want to preview how your email looks before sending to real users

**Steps:**
1. Click **"Test"** button on any template
2. Enter your test email address
3. Click **"Send Test Email"**
4. Check your inbox

**Sample Data Used:**
- Event Name: "Sample Event Name"
- Participant: "John Doe"
- Badge ID: "BADGE-12345"

---

### 2️⃣ Send Email (Green Button)
**Use when:** Ready to send emails to all registered participants

**Steps:**
1. Click **"Send"** button on template
2. Select target event from dropdown
3. Review recipient count (shows how many will receive email)
4. Click **"Send to All Registered Users"**
5. Wait for confirmation message

**Important:**
- Only sends to **approved** registrations
- Each email is personalized with participant data
- All sends are logged for tracking

---

### 3️⃣ View Statistics (Yellow Button)
**Use when:** You want to track email performance

**Shows:**
- Total emails sent
- Failed attempts
- Success rate %
- Unique recipients
- Daily sending trends (chart)
- Recent activity log (last 50 emails)

**Steps:**
1. Click **"Stats"** button
2. Review dashboard metrics
3. Check chart for trends
4. Scroll to see recent logs

---

### 4️⃣ Edit Template (Blue Pencil)
**Use when:** Need to modify email content or settings

**Steps:**
1. Click **"Edit"** button
2. Update name, subject, or description
3. Modify email design in Unlayer editor
4. Click **"Save Template"**

---

### 5️⃣ Archive Template (Gray Button)
**Use when:** Want to hide template without deleting

**Steps:**
1. Click **"Archive"** button
2. Confirm action
3. Template is hidden from main list (but not deleted)

**To Unarchive:**
- Use Django admin or database to set `is_active = True`

---

### 6️⃣ Delete Template (Red Button)
**Use when:** Permanently removing a template

**Steps:**
1. Click **"Delete"** button
2. Confirm deletion (cannot be undone!)
3. Template is permanently removed

---

## 📋 Registration Form Builder

### Access:
Click **"Build Registration Form"** button at top of Email Templates page

### Features:

#### Event Selection
- **All Events (Global)**: Form applies to all events
- **Specific Event**: Form only for selected event

#### Available Fields:
✅ **First Name** - Required (cannot disable)
✅ **Last Name** - Required (cannot disable)
✅ **Email** - Always required (locked)
📱 **Phone Number** - Optional
🏢 **Institution/Organization** - Optional
🏠 **Address** - Optional (disabled by default)
🌍 **Country** - Optional (disabled by default)

#### Field Controls:
- **Toggle Switch**: Enable/disable field
- **Drag Handle** (⋮⋮): Reorder fields
- **Required/Optional Dropdown**: Set field requirement

#### Real-Time Preview:
- Right panel shows live form preview
- Updates as you make changes
- Shows required fields with red asterisk (*)

### Steps to Build Form:
1. Select event (or leave as "All Events")
2. Toggle fields you want to show
3. Drag fields to reorder
4. Set each field as Required or Optional
5. Review preview panel
6. Click **"Save Form Configuration"**

---

## 🎯 Common Workflows

### Workflow 1: Create & Test New Template
```
1. Create Template
   → Design in Unlayer
   → Add merge tags ({{participant_name}}, etc.)
   → Save

2. Test Template
   → Click "Test" button
   → Enter your email
   → Verify email looks correct

3. Send to Event
   → Click "Send" button
   → Select event
   → Confirm send

4. Monitor Results
   → Click "Stats" button
   → Check success rate
   → Review any errors
```

### Workflow 2: Bulk Email Campaign
```
1. Select Template
   → Choose existing template OR create new

2. Verify Content
   → Click "Edit" to review
   → Make any needed changes
   → Test email to yourself

3. Send to Event
   → Click "Send"
   → Choose event
   → Note: Shows "X registered users"
   → Confirm send

4. Track Performance
   → Click "Stats"
   → Monitor send completion
   → Check for failures
```

### Workflow 3: Configure Registration Form
```
1. Access Form Builder
   → Click "Build Registration Form"

2. Select Event
   → Choose specific event OR
   → Leave as "All Events"

3. Configure Fields
   → Enable needed fields
   → Disable unnecessary fields
   → Reorder by dragging
   → Set required/optional

4. Preview & Save
   → Review right panel
   → Adjust as needed
   → Save configuration
```

---

## 🏷️ Merge Tags Guide

### Usage in Email Templates:
Type merge tags directly in Unlayer editor text blocks:

**Example:**
```html
Hello {{first_name}},

Welcome to {{event_name}}!

Your event details:
- Location: {{event_location}}
- Date: {{event_start_date}} to {{event_end_date}}
- Your Badge ID: {{badge_id}}

See you soon!
```

**Becomes:**
```
Hello Ahmed,

Welcome to MakePlus Conference 2026!

Your event details:
- Location: Casablanca Convention Center
- Date: March 15, 2026 to March 17, 2026
- Your Badge ID: BADGE-A1B2C3

See you soon!
```

### Available Merge Tags:

**Event Info:**
- `{{event_name}}` - Event title
- `{{event_location}}` - Event venue
- `{{event_start_date}}` - Start date
- `{{event_end_date}}` - End date

**Participant Info:**
- `{{participant_name}}` - Full name
- `{{first_name}}` - First name only
- `{{last_name}}` - Last name only
- `{{email}}` - Email address
- `{{telephone}}` - Phone number
- `{{etablissement}}` - Organization
- `{{badge_id}}` - Badge ID
- `{{qr_code_url}}` - QR code image URL

---

## ⚠️ Important Notes

### Email Sending:
- Only approved registrations receive emails
- Spam-flagged registrations are excluded
- Each email is logged for auditing
- Check SMTP settings if emails fail

### SMTP Configuration:
Ensure `settings.py` has:
```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'
DEFAULT_FROM_EMAIL = 'noreply@makeplus.com'
```

### Testing Best Practices:
1. **Always test before bulk sending**
2. **Send to yourself first**
3. **Verify merge tags work correctly**
4. **Check mobile rendering**
5. **Review spam score**

### Monitoring:
- Check Stats page regularly
- Review failed emails
- Monitor success rate
- Export logs if needed

---

## 🆘 Troubleshooting

### Email Not Sending?
1. Check SMTP settings in `settings.py`
2. Verify EMAIL_HOST_PASSWORD is correct
3. Check spam folder
4. Review error messages in Stats page
5. Test with simple plain text email first

### Merge Tags Not Working?
1. Verify double curly braces: `{{tag_name}}`
2. Check spelling matches exactly
3. Ensure tag is in available list
4. Test with "Test Email" first

### Form Builder Not Saving?
1. Check browser console for errors
2. Verify CSRF token present
3. Ensure user is authenticated
4. Check server logs for backend errors

### Modal Not Opening?
1. Check browser console
2. Verify Bootstrap JS loaded
3. Clear browser cache
3. Try different browser

---

## 📞 Support

**Documentation:**
- Main: [EMAIL_TEMPLATE_ENHANCEMENTS.md](./EMAIL_TEMPLATE_ENHANCEMENTS.md)
- Backend: [BACKEND_DOCUMENTATION.md](./makeplus_api/BACKEND_DOCUMENTATION.md)

**Files to Check:**
- Views: `dashboard/views_email.py`
- Templates: `dashboard/templates/dashboard/`
- URLs: `dashboard/urls.py`

**Common Locations:**
```
Email Templates: /dashboard/email-templates/
Form Builder: /dashboard/registration-form-builder/
Stats: /dashboard/email-templates/<id>/stats/
Test: /dashboard/email-templates/<id>/test/
Send: /dashboard/email-templates/<id>/send/
```

---

## ✅ Quick Checklist

Before going live:
- [ ] SMTP configured and tested
- [ ] Test email sent successfully
- [ ] All merge tags working
- [ ] Registration form configured
- [ ] Bulk send tested with small group
- [ ] Statistics tracking verified
- [ ] Error handling tested
- [ ] Mobile email rendering checked
- [ ] Spam score acceptable
- [ ] Backup templates created

---

**Last Updated:** January 28, 2026
**Version:** 1.0
