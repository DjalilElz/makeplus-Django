# 📧 Unified Email Campaign System - Complete Guide

## ✅ What Changed

### **Simplified Architecture**
- **Before**: Separate EmailTemplate and EmailCampaign models
- **After**: Single unified EmailCampaign system
- **Benefits**: 
  - Simpler workflow - no confusion between templates and campaigns
  - Each campaign has built-in Unlayer editor
  - Campaigns can be archived for reuse
  - Everything in one place

---

## 🎯 System Overview

### **What is an Email Campaign?**
An email campaign is a complete email message with:
- Design (created with Unlayer email builder)
- Campaign information (name, subject, sender)
- Recipient list
- Tracking (opens, clicks)
- Statistics
- Status (draft, sent, archived)

### **Campaign Lifecycle**
```
1. CREATE → Design email with Unlayer builder
2. DRAFT → Add recipients  
3. TEST → Send test emails
4. SEND → Deliver to all recipients
5. TRACK → Monitor opens & clicks
6. ARCHIVE → Save for future reuse (optional)
```

---

## 📚 Complete Workflow

### **Step 1: Create New Campaign** 🎨

1. Navigate to **"Email Campaigns"** from dashboard
2. Click **"Create New Campaign"** (green button)
3. Fill in campaign information:

**Required Fields:**
- **Campaign Name**: Internal reference (e.g., "Summer Event 2026 Invitation")
- **Email Subject**: What recipients see (e.g., "Join us at MakePlus Summit!")
- **From Email**: Already pre-filled from settings

**Optional Fields:**
- **Event**: Link to specific event (auto-fills event info)
- **From Name**: Display name (e.g., "MakePlus Team")
- **Reply-To**: Alternative reply address

**Tracking Options:**
- ✅ **Track Email Opens**: Monitor when recipients open
- ✅ **Track Link Clicks**: Monitor which links are clicked

4. Design your email using **Unlayer Editor**:
   - Drag & drop content blocks
   - Add text, images, buttons, dividers
   - Use template variables for personalization
   - Preview at any time

5. Click **"Create Campaign"**

### **Step 2: Add Recipients** 👥

After creating, you'll see the campaign detail page.

**Add Single Recipient:**
1. Click **"Add Recipient"** button
2. Fill in:
   - Name (required)
   - Email (required)
   - Phone (optional)
   - Organization (optional)
3. Click **"Add"**

**Bulk Add via CSV:**
1. Click **"Bulk Add Recipients"**
2. Select **"Upload CSV"** tab
3. CSV format:
```csv
name,email,telephone,etablissement
John Doe,john@example.com,+1234567890,Acme Corp
Jane Smith,jane@example.com,,Tech Inc
```
4. Upload file
5. System automatically detects and skips duplicates

**Bulk Add via Text:**
1. Click **"Bulk Add Recipients"**
2. Select **"Paste Text"** tab
3. Format: `Name <email@example.com>` (one per line)
```
John Doe <john@example.com>
Jane Smith <jane@example.com>
Bob Johnson <bob@example.com>
```
4. Click **"Add Recipients"**

### **Step 3: Send to Event Participants** 🎫

If you linked the campaign to an event:
1. Campaign automatically shows event participants
2. Bulk add all participants from event
3. System populates event-specific variables:
   - `{{event_name}}`
   - `{{event_location}}`
   - `{{event_start_date}}`
   - `{{event_end_date}}`

### **Step 4: Test Before Sending** 🧪

1. In campaign detail, click **"Send Test Email"**
2. Enter your email address
3. Review test email
4. Check:
   - Layout on desktop/mobile
   - All variables replaced correctly
   - Links working
   - Images loading

### **Step 5: Send Campaign** 🚀

1. Click **"Send Campaign"** button
2. Confirm sending (irreversible!)
3. System processes:
   - Replaces all template variables with recipient data
   - Adds tracking pixel (if enabled)
   - Wraps links for click tracking (if enabled)
   - Generates unique tracking token per recipient
4. Emails sent asynchronously
5. Status changes to "Sent"

### **Step 6: Track Performance** 📊

**Campaign Overview Statistics:**
- Total recipients
- Emails sent successfully
- Unique opens count & rate
- Unique clicks count & rate
- Bounced emails

**Detailed Statistics** (4 tabs):
1. **All Recipients**: Complete list with engagement metrics
2. **Who Opened**: Only recipients who opened the email
3. **Who Clicked**: Only recipients who clicked links
4. **Not Opened**: Recipients who haven't opened yet

**Individual Recipient Tracking:**
Click any recipient to see:
- Total open count
- Timestamps of each open
- Which specific links they clicked
- Click count per link
- Activity timeline

### **Step 7: Archive for Reuse** 📦

**To Archive:**
1. Open campaign detail
2. Click **"Archive"** button
3. Campaign status → "Archived"
4. No longer appears in active list

**To Unarchive:**
1. Filter by "Archived" in campaign list
2. Click campaign to view details
3. Click **"Unarchive"** button
4. Campaign status → "Draft"
5. Can now edit and reuse

---

## 🏷️ Template Variables

### **All Available Variables**

**Recipient Information:**
- `{{name}}` - Full name
- `{{email}}` - Email address
- `{{first_name}}` - First name only
- `{{last_name}}` - Last name only
- `{{telephone}}` - Phone number
- `{{etablissement}}` - Organization

**Event Information:**
- `{{event_name}}` - Event title
- `{{event_location}}` - Venue/location
- `{{event_start_date}}` - Start date
- `{{event_end_date}}` - End date

**Participant Data:**
- `{{participant_name}}` - Participant name
- `{{badge_id}}` - Badge ID
- `{{qr_code_url}}` - QR code image URL
- `{{unsubscribe_url}}` - Unsubscribe link

### **How to Use Variables**

**Method 1: Click to Copy**
- Click any variable pill
- Paste into Unlayer text/button/link

**Method 2: Unlayer Merge Tags**
- In Unlayer editor, select text
- Click "Merge Tags" in toolbar
- Select variable from dropdown

**Example Email:**
```html
Dear {{first_name}},

You're invited to {{event_name}}!

📍 Location: {{event_location}}
📅 Date: {{event_start_date}} - {{event_end_date}}

Your personalized badge: {{qr_code_url}}

See you there!
The {{estabelissement}} Team
```

---

## 🎨 Campaign List Features

### **Filtering**
- **All Campaigns**: Shows everything
- **Draft**: Campaigns not sent yet
- **Sent**: Successfully delivered campaigns
- **Archived**: Saved campaigns
- **Active**: All except archived
- **By Event**: Filter by specific event

### **Campaign Card Information**
Each campaign shows:
- Name & subject
- Status badge (Draft, Sent, Archived)
- Linked event (if any)
- Statistics:
  - Total recipients
  - Sent count
  - Opens count
  - Clicks count
- Creator & creation date
- Action buttons

### **Available Actions**
- **View**: See campaign details
- **Edit**: Modify design/settings (draft only)
- **Archive**: Save for later reuse
- **Unarchive**: Restore archived campaign
- **Delete**: Permanently remove (can't delete sent campaigns)

---

## 💡 Best Practices

### **Campaign Design**
✅ Use clear, action-oriented subject lines
✅ Personalize with recipient name: `Hello {{first_name}},`
✅ Include clear call-to-action buttons
✅ Always add unsubscribe link: `{{unsubscribe_url}}`
✅ Test on mobile and desktop
✅ Use high-quality images (but don't rely solely on them)
✅ Keep text concise and scannable

### **Recipient Management**
✅ Verify email addresses before adding
✅ Use bulk import for large lists (CSV recommended)
✅ Remove bounced emails from future campaigns
✅ Segment by event/organization for targeted messaging
✅ Respect unsubscribe requests immediately

### **Sending Strategy**
✅ Always send test email first
✅ Review all template variables replaced correctly
✅ Check spam score before sending
✅ Send during optimal times (Tuesday-Thursday, 10 AM-2 PM)
✅ Don't send to unengaged recipients repeatedly

### **Tracking & Analytics**
✅ Enable both open and click tracking
✅ Review statistics within 48 hours of sending
✅ Identify best-performing content
✅ Follow up with non-openers after 3-5 days
✅ A/B test subject lines on small segments first

### **Archive Management**
✅ Archive successful campaigns for templates
✅ Name campaigns descriptively for easy searching
✅ Document what worked well in campaign name
✅ Reuse archived campaigns for similar events
✅ Periodically clean up old archived campaigns

---

## 🔧 Technical Details

### **Files Modified**

1. **dashboard/forms.py**
   - Removed `email_template` field from EmailCampaignForm
   - Simplified to only campaign-specific fields

2. **dashboard/views_email.py**
   - Replaced `email_template_list()` with unified campaign list
   - Removed template references from `campaign_create()` and `campaign_edit()`
   - Added `campaign_archive()` function
   - Added `campaign_unarchive()` function
   - Campaign filtering by status and event

3. **dashboard/templates/dashboard/campaign_form.html**
   - Removed "Use Existing Template" dropdown
   - Removed template loading JavaScript handler
   - Kept full Unlayer integration
   - Kept styled template variables

4. **dashboard/templates/dashboard/campaign_list.html**
   - NEW: Unified campaign list view
   - Card-based layout with hover effects
   - Status-based coloring (green=draft, blue=sent, gray=archived)
   - Statistics overview cards
   - Filter dropdowns (status, event)
   - Action buttons per campaign
   - Empty state for first-time users

5. **dashboard/templates/dashboard/campaign_detail.html**
   - Added Archive/Unarchive buttons
   - Conditional display based on campaign status

6. **dashboard/urls.py**
   - Added `campaign_archive` route
   - Added `campaign_unarchive` route
   - `email_template_list` now shows unified campaign list

### **Database Schema**
No changes needed! Existing EmailCampaign model supports everything:
- `status` field: 'draft', 'sent', 'sending', 'archived'
- `body_html`: HTML content from Unlayer
- `builder_config`: JSON design for Unlayer
- `track_opens`, `track_clicks`: Boolean flags
- `event`: ForeignKey (optional)

---

## 📋 Campaign Status Reference

| Status | Description | Can Edit? | Can Send? | Can Archive? |
|--------|-------------|-----------|-----------|--------------|
| **draft** | Created but not sent | ✅ Yes | ✅ Yes | ✅ Yes |
| **sending** | Currently being sent | ❌ No | ❌ No | ❌ No |
| **sent** | Delivered to recipients | ❌ No | ❌ No | ✅ Yes |
| **archived** | Saved for reuse | ❌ No | ❌ No | ✅ Yes (Unarchive) |

---

## 🎯 Quick Reference

### **Navigation**
- **Campaign List**: `/dashboard/email-templates/`
- **Create Campaign**: `/dashboard/campaigns/create/`
- **Campaign Detail**: `/dashboard/campaigns/<uuid>/`
- **Campaign Stats**: `/dashboard/campaigns/<uuid>/stats/`

### **Keyboard Shortcuts**
- **Ctrl+S**: Save campaign (in form)
- **Esc**: Close modals

### **URL Structure**
```
/dashboard/email-templates/              → Campaign list
/dashboard/campaigns/create/             → Create new
/dashboard/campaigns/<uuid>/             → Campaign detail
/dashboard/campaigns/<uuid>/edit/        → Edit campaign
/dashboard/campaigns/<uuid>/archive/     → Archive
/dashboard/campaigns/<uuid>/unarchive/   → Unarchive
/dashboard/campaigns/<uuid>/stats/       → Statistics
```

---

## 🚀 Getting Started

1. **Visit**: http://127.0.0.1:8000/dashboard/email-templates/
2. Click **"Create New Campaign"**
3. Design your first email with Unlayer
4. Add test recipients
5. Send test email to yourself
6. Review and send to all recipients
7. Track performance in statistics

---

## 🎉 You're Ready!

Your unified email campaign system includes:
- ✅ Professional Unlayer email builder
- ✅ 14 personalization variables
- ✅ Bulk recipient management
- ✅ Archive/reuse functionality
- ✅ Comprehensive tracking
- ✅ Detailed statistics (4-tab interface)
- ✅ Event integration
- ✅ Mobile-responsive design

**No more confusion between templates and campaigns - everything is a campaign!** 🚀
