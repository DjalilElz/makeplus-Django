# Unlayer Email Builder - Quick Reference Card

## 🚀 Quick Start (30 Seconds)

1. **Dashboard** → **Email Templates** → **Create**
2. **Wait 2 seconds** for Unlayer to load
3. **Drag components** from left panel to canvas
4. **Click Settings** → Enter name & subject → Save Settings
5. **Click Save Template** → Done! ✅

---

## 🎨 Available Components

| Component | Use For | Icon |
|-----------|---------|------|
| **Text** | Paragraphs, headings | T |
| **Image** | Photos, logos, banners | 🖼️ |
| **Button** | Call-to-action links | 🔘 |
| **Divider** | Visual separation | — |
| **Column** | Multi-column layouts | ⫿ |
| **Social** | Social media icons | 👥 |
| **HTML** | Custom code | </> |

---

## 🏷️ Merge Tags

**How to use:**
1. Add text block
2. Click **"Merge Tags"** in toolbar
3. Select variable
4. Variable inserted: `{{event_name}}`

**Available:**
```
{{event_name}}         {{event_location}}
{{event_start_date}}   {{event_end_date}}
{{participant_name}}   {{first_name}}
{{last_name}}          {{email}}
{{telephone}}          {{etablissement}}
{{badge_id}}           {{qr_code_url}}
```

---

## ⚙️ Settings Modal

**Access:** Click **Settings** button in top bar

**Configure:**
- ✏️ Template Name (internal)
- 📧 Email Subject (recipients see this)
- 🏷️ Template Type (invitation, confirmation, etc.)
- ✅ Active Status (enable/disable)

**Required:** Name & Subject must be filled!

---

## 👁️ Preview

**Access:** Click **Preview** button in top bar

**Shows:**
- Email subject line
- Full email HTML rendering
- Exactly what recipients will see

**Note:** Merge tags show as `{{variable_name}}` in preview

---

## 💾 Saving

**What happens when you save:**
1. Unlayer exports HTML (for sending emails)
2. Unlayer exports JSON (for re-editing)
3. Both saved to database
4. Design can be re-opened and edited later

**Pro Tip:** Always configure Settings before saving!

---

## ✏️ Editing Existing Template

1. **Email Templates** → Click **Edit**
2. **Wait** for Unlayer to load
3. **Design loads automatically** (exact state restored)
4. Make changes
5. Click **Save Template**

**Note:** Only works for templates created in Unlayer!

---

## 📤 Sending Emails

1. **Events** → **[Event Name]** → **Email Templates**
2. Select template
3. Click **Send to Participants**
4. Choose target group:
   - All participants
   - Attended only
   - Paid only
   - Custom selection
5. Click **Send**
6. Merge tags automatically replaced with actual data

---

## 🎯 Best Practices

### Design
✅ **Keep it simple** - Less is more  
✅ **Use headings** - Clear hierarchy  
✅ **Big buttons** - Minimum 44x44px  
✅ **Test mobile** - Check preview  
✅ **Brand colors** - Stay consistent  

### Content
✅ **Personalize** - Use merge tags  
✅ **Clear CTA** - One main action  
✅ **Short text** - Scannable content  
✅ **Alt text** - For images  

### Technical
✅ **Name clearly** - "Invitation - TechConf 2026"  
✅ **Set type** - For easy filtering  
✅ **Preview first** - Before sending  
✅ **Test email** - Send to yourself  

---

## 🐛 Common Issues

### Editor not loading
- Check internet connection (loads from CDN)
- Disable ad blockers
- Try different browser

### Can't save
- Fill in Settings (name & subject required)
- Check browser console for errors

### Can't edit old template
- Template created before Unlayer?
- Solution: Recreate in Unlayer

### Merge tags not replacing
- Check spelling: `{{event_name}}` not `{{eventname}}`
- Verify variable exists in context

---

## ⌨️ Keyboard Shortcuts

| Action | Shortcut |
|--------|----------|
| Undo | Ctrl+Z |
| Redo | Ctrl+Y |
| Copy | Ctrl+C |
| Paste | Ctrl+V |
| Delete | Del |
| Select All | Ctrl+A |

---

## 📱 Mobile Testing

**In Unlayer:**
1. Click **device icon** in top bar
2. Switch between Desktop/Tablet/Mobile
3. See responsive layout

**Best Practice:**
- Design desktop first
- Check mobile preview
- Adjust padding/spacing if needed

---

## 🔄 Duplicating Templates

**For Events:**
1. **Events** → **[Event]** → **Email Templates**
2. Click **"Use as Base"** on global template
3. Template opens in Unlayer
4. Customize for event
5. Save as event-specific template

**Benefits:**
- Reuse proven designs
- Maintain consistency
- Save time

---

## 🎨 Styling Tips

### Colors
- Click component
- Right panel → **Colors**
- Pick from palette or custom

### Fonts
- Click text
- Right panel → **Font Family**
- Select from available fonts

### Spacing
- Click component
- Right panel → **Padding/Margin**
- Adjust with sliders

### Borders
- Click component
- Right panel → **Border**
- Set width, color, radius

---

## 📦 Template Library Ideas

**Create these templates:**
1. **Event Invitation** - Generic invite
2. **Confirmation** - Registration confirmed
3. **Reminder** - Event starting soon
4. **Thank You** - Post-event thank you
5. **Certificate** - Completion certificate
6. **Newsletter** - Monthly updates

**Save as global templates**, then duplicate for specific events!

---

## 🔗 URLs

**Create Template:**
- Global: `/dashboard/email-templates/create/`
- Event: `/dashboard/events/{id}/email-templates/create/`

**Edit Template:**
- Global: `/dashboard/email-templates/{id}/edit/`
- Event: `/dashboard/events/{event_id}/email-templates/{id}/edit/`

---

## 📊 Storage

**What's saved:**
- Template metadata (name, subject, type)
- HTML output (~50 KB)
- Design JSON (~20 KB)
- Total: ~70 KB per template

**Database field:**
- `body_html` - HTML for sending
- `builder_config` - JSON for editing

---

## 🆘 Need Help?

**Documentation:**
- [UNLAYER_EMAIL_BUILDER_GUIDE.md](UNLAYER_EMAIL_BUILDER_GUIDE.md) - Complete guide
- [UNLAYER_VISUAL_FLOW.md](UNLAYER_VISUAL_FLOW.md) - Visual diagrams
- [EVENT_REGISTRATION_SYSTEM.md](EVENT_REGISTRATION_SYSTEM.md) - Full system

**Unlayer Docs:**
- https://docs.unlayer.com/

**Support:**
- Check browser console for errors
- Test in different browser
- Contact system administrator

---

## ✅ Pre-Send Checklist

Before sending to real recipients:

- [ ] Template name is clear
- [ ] Subject line is compelling
- [ ] All text is correct (no typos)
- [ ] Images load properly
- [ ] Buttons link correctly
- [ ] Merge tags are present
- [ ] Preview looks good
- [ ] Tested on mobile view
- [ ] Sent test email to yourself
- [ ] HTML renders in email client
- [ ] Merge tags replaced correctly

---

## 🎉 Pro Tips

💡 **Save Early, Save Often** - Click Save regularly  
💡 **Use Templates** - Start from existing design  
💡 **Test Variables** - Send test email with real data  
💡 **Mobile First** - Most people read on mobile  
💡 **One CTA** - Don't overwhelm recipients  
💡 **Alt Text** - Images may be blocked  
💡 **Plain Text** - Auto-generated from HTML  
💡 **Short Lines** - 50-60 characters max  
💡 **Contrast** - Text readable on background  
💡 **Consistent** - Use same style for all emails  

---

## 📐 Recommended Sizes

**Email Width:** 600px (default, works everywhere)  
**Button Height:** 44-48px minimum  
**Text Size:** 14-16px body, 22-28px headings  
**Line Height:** 1.5-1.7 for readability  
**Image Width:** Max 600px  
**Logo Height:** 50-100px  

---

## 🌈 Color Psychology

**Primary Button:**
- 🔵 Blue - Trust, Professional
- 🟢 Green - Success, Action
- 🔴 Red - Urgency, Alert
- 🟠 Orange - Friendly, Energetic

**Background:**
- ⚪ White - Clean, Simple
- 🔲 Light Gray - Modern, Subtle
- 🎨 Brand Color - Bold, Memorable

---

## 📅 Template Naming Convention

**Format:** `[Type] - [Event/Purpose] - [Version]`

**Examples:**
- `Invitation - Tech Conference 2026 - v1`
- `Confirmation - Workshop Registration - v2`
- `Reminder - Event Tomorrow - Final`
- `Thank You - Conference Attendees`
- `Newsletter - March 2026`

**Benefits:**
- Easy to find
- Version tracking
- Clear purpose

---

## 🔍 Finding Templates

**Filters in Template List:**
- By type (invitation, confirmation, etc.)
- By active status
- By creation date
- By creator

**Search:**
- Use template name
- Use keywords in description

---

**Quick Reference Card - Print & Keep Handy!**  
*Unlayer Email Builder - MakePlus Platform*  
*January 27, 2026*
