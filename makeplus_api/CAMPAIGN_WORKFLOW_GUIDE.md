# 📧 Email Campaign System - Complete Usage Guide

## ✅ What's Been Fixed

### 1. **Unlayer Email Editor Integration** ✨
- Professional drag-and-drop email builder now loads properly
- Loading overlay shows while editor initializes
- Full Unlayer features: image editor, text formatting, tables, emojis
- Merge tags/template variables integrated into editor toolbar

### 2. **Template Variables UI** 🎨
- Styled pills with hover effects (matching email template form)
- Click-to-copy functionality with visual feedback
- Organized in 3 categories:
  - 📧 Recipient Information (6 variables)
  - 🎯 Event Information (4 variables)
  - 🎫 Participant Data (4 variables)

### 3. **Template Loading** 📥
- Dropdown to select existing email templates
- Confirmation dialog before loading (prevents accidental overwrites)
- Loads saved designs from templates into editor

### 4. **All Template Variables Available** 📋
```
{{name}}              - Recipient's full name
{{email}}             - Recipient's email address
{{first_name}}        - First name only
{{last_name}}         - Last name only
{{telephone}}         - Phone number
{{etablissement}}     - Organization/Institution
{{event_name}}        - Event title
{{event_location}}    - Event venue/location
{{event_start_date}}  - Event start date
{{event_end_date}}    - Event end date
{{participant_name}}  - Participant name
{{badge_id}}          - Badge ID
{{qr_code_url}}       - QR code image URL
{{unsubscribe_url}}   - Unsubscribe link
```

---

## 📚 Complete Campaign Workflow

### **Step 1: Create a Campaign** 🎯

1. Go to **Email Templates & Campaigns** page
2. Click the **green "Create Campaign"** button
3. You'll see the campaign creation form

### **Step 2: Fill Campaign Information** 📝

**Required Fields:**
- **Campaign Name**: Internal name (e.g., "Summer Event Invitation 2026")
- **Email Subject**: What recipients see (e.g., "You're Invited to MakePlus Summit!")
- **From Email**: Already filled from settings (elaziziabdeldjalil@gmail.com)

**Optional Fields:**
- **Event**: Link campaign to specific event (shows event name in recipient list)
- **From Name**: Display name (e.g., "MakePlus Team")
- **Reply-To Email**: Where replies go (if different from From Email)
- **Use Existing Template**: Load a saved template as starting point

**Tracking Options:**
- ✅ **Track Email Opens**: Monitor when recipients open emails (uses invisible pixel)
- ✅ **Track Link Clicks**: Monitor which links recipients click (wraps URLs)

### **Step 3: Use Template Variables** 🏷️

**Method 1: Click to Copy**
1. Scroll to "Available Template Variables" section
2. Click any blue/cyan pill (e.g., `{{name}}`)
3. You'll see "✓ Copied!" confirmation
4. Paste into Unlayer editor (in text blocks, buttons, links)

**Method 2: Use Merge Tags in Unlayer**
1. In the Unlayer editor, click on any text block
2. Look for **"Merge Tags"** in the toolbar
3. Select from dropdown (e.g., "Recipient Name", "Event Name")
4. Merge tag automatically inserted

**Example Usage:**
```html
Hello {{first_name}},

You're invited to {{event_name}} at {{event_location}}!

Event Dates: {{event_start_date}} - {{event_end_date}}

Your Badge ID: {{badge_id}}
```

### **Step 4: Design Your Email** 🎨

The **Unlayer Editor** gives you:

**Content Blocks:**
- Text
- Image
- Button
- Divider
- Social icons
- Video
- HTML code

**Design Options:**
- Drag & drop interface
- Responsive design (mobile-friendly)
- Custom colors, fonts, spacing
- Image editor built-in
- Pre-built templates

**How to Use:**
1. Wait for editor to load (loading overlay disappears)
2. Drag blocks from left panel into canvas
3. Click any block to edit (right panel shows settings)
4. Use merge tags for personalization
5. Preview button shows how email looks

### **Step 5: Load Existing Template (Optional)** 📥

If you want to start from a saved template:
1. Select template from **"Use Existing Template"** dropdown
2. Click **"OK"** in confirmation dialog
3. Template design loads into editor
4. Edit as needed

**Note:** This replaces any unsaved work in editor!

### **Step 6: Preview Your Email** 👁️

1. Click **"Preview"** button (top right)
2. Modal shows:
   - Email subject
   - Full HTML render in iframe
3. Check layout, colors, text
4. Close modal to continue editing

### **Step 7: Save Your Campaign** 💾

1. Click **"Create Campaign"** button (green, top right)
2. Form validates required fields
3. Button shows "Saving..." with spinner
4. Success: Redirects to Campaign Detail page

---

## 📊 Campaign Management

### **View Campaign Details**

After creating, you see:
- Campaign name, status, dates
- Statistics: Total sent, opens, clicks, bounces
- Recipient list with engagement data
- Edit/Delete buttons

### **Add Recipients** 👥

**Method 1: Add Single Recipient**
1. Click **"Add Recipient"** button
2. Enter: Name, Email, Phone (optional), Organization (optional)
3. Click **"Add"**
4. Recipient appears in list with "Pending" status

**Method 2: Bulk Add (CSV)**
1. Click **"Bulk Add Recipients"**
2. Select **"Upload CSV"** tab
3. CSV format:
   ```csv
   name,email,telephone,etablissement
   John Doe,john@example.com,+1234567890,Acme Corp
   Jane Smith,jane@example.com,,Tech Inc
   ```
4. Upload file
5. System detects duplicates automatically

**Method 3: Bulk Add (Text)**
1. Click **"Bulk Add Recipients"**
2. Select **"Paste Text"** tab
3. Format: `Name <email@example.com>` (one per line)
   ```
   John Doe <john@example.com>
   Jane Smith <jane@example.com>
   ```
4. Click **"Add Recipients"**
5. Duplicates are skipped

### **Manage Recipients** ✏️

- **View**: Table shows name, email, status, opens, clicks
- **Delete**: Click trash icon, confirm deletion
- **Filter**: (Future) Filter by status, opens, clicks

---

## 🚀 Send Campaign

**Steps:**
1. Add recipients to campaign
2. Preview email one last time
3. Click **"Send Campaign"** button
4. Confirm sending
5. System queues emails
6. Status changes to "Sent"

**What Happens:**
- Each recipient gets personalized email
- Variables replaced with actual data
- Tracking pixel added (if enabled)
- Links wrapped for click tracking (if enabled)
- Unique tracking token per recipient

---

## 📈 Track Campaign Performance

### **Campaign Statistics**

View on Campaign Detail page:
- **Total Recipients**: How many added
- **Sent**: Successfully delivered
- **Opens**: Unique recipients who opened
- **Open Rate**: Percentage
- **Clicks**: Unique recipients who clicked
- **Click Rate**: Percentage
- **Bounces**: Failed deliveries

### **Individual Recipient Tracking**

Click recipient name to see:
- How many times they opened
- Timestamps of each open
- Which links they clicked
- How many times per link
- Timestamps of each click

### **Detailed Statistics Page**

Navigate to **"Campaign Statistics"**:

**4 Tabs:**
1. **All Recipients**: Complete list with engagement
2. **Who Opened**: Only recipients who opened
3. **Who Clicked**: Only recipients who clicked links
4. **Not Opened**: Recipients who didn't open yet

**Each shows:**
- Name, email
- Total opens, total clicks
- Last activity timestamp
- Quick actions

---

## 💡 Best Practices

### **Email Design**
✅ Use clear, compelling subject lines
✅ Include unsubscribe link: `{{unsubscribe_url}}`
✅ Test with "Preview" before sending
✅ Use responsive design (Unlayer does this automatically)
✅ Include both text and images (don't rely solely on images)

### **Personalization**
✅ Always use `{{first_name}}` or `{{name}}` in greeting
✅ Include event details when relevant
✅ Use recipient organization if available
✅ Add badge ID/QR code for event attendees

### **Tracking**
✅ Enable both open and click tracking
✅ Check statistics regularly
✅ Follow up with non-openers
✅ Analyze which links get most clicks

### **Recipients**
✅ Verify email addresses before adding
✅ Use bulk import for large lists
✅ Remove bounced addresses
✅ Respect unsubscribe requests immediately

---

## 🛠️ Technical Details

### **File Modified:**
- `dashboard/templates/dashboard/campaign_form.html` (Completely rewritten)

### **What Changed:**
1. **Added Unlayer CDN**: `<script src="https://editor.unlayer.com/embed.js"></script>`
2. **Proper Initialization**:
   ```javascript
   emailEditor = unlayer.createEditor({
       id: 'email-editor-container',
       mergeTags: { ... },
       features: { preview: true, imageEditor: true }
   });
   ```
3. **Editor Ready Event**: Hides loading overlay when ready
4. **Merge Tags Config**: All 14 variables with sample data
5. **Form Submission**: Exports HTML and design JSON
6. **Template Loading**: Fetch and confirm before loading
7. **Preview Modal**: Shows email with subject line
8. **Variable Pills**: Click-to-copy with visual feedback

### **Dependencies:**
- Bootstrap 5 (already included in base.html)
- Unlayer Email Editor (CDN, free to use)
- Bootstrap Icons (for UI)

---

## 🎯 Quick Reference

### **Campaign Status:**
- **Draft**: Created but not sent
- **Scheduled**: Queued for sending
- **Sending**: Currently being sent
- **Sent**: Completed
- **Paused**: Temporarily stopped

### **Recipient Status:**
- **Pending**: Added but campaign not sent
- **Sent**: Email delivered
- **Opened**: Recipient opened email
- **Clicked**: Recipient clicked link
- **Bounced**: Delivery failed
- **Unsubscribed**: Opted out

### **Keyboard Shortcuts:**
- **Ctrl+S**: Save campaign (in form)
- **Esc**: Close modals

---

## 📞 Need Help?

### **Common Issues:**

**Unlayer not loading?**
- Check internet connection (Unlayer loads from CDN)
- Try refreshing page
- Check browser console for errors

**Template variables not working?**
- Ensure proper format: `{{variable_name}}`
- Don't add spaces: ❌ `{{ name }}`, ✅ `{{name}}`
- Check variable spelling

**Emails not sending?**
- Verify Gmail SMTP settings in .env
- Check recipient email addresses
- Ensure campaign has recipients added

**Tracking not working?**
- Ensure tracking options enabled in campaign form
- Check that links use proper format
- Verify tracking pixel in sent emails

---

## 🎉 You're Ready!

You now have a **complete email campaign system** with:
- ✅ Professional drag-and-drop email builder (Unlayer)
- ✅ 14 template variables for personalization
- ✅ Styled variable pills with copy functionality
- ✅ Template loading from saved designs
- ✅ Preview before sending
- ✅ Recipient management (single + bulk)
- ✅ Mailerlite-style tracking (opens + clicks)
- ✅ Detailed statistics with 4 tabs
- ✅ Individual recipient analytics

**Start creating your first campaign now!** 🚀

Visit: http://127.0.0.1:8000/dashboard/email-templates/ and click **"Create Campaign"**
