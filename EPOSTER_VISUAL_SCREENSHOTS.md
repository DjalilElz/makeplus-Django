# 📸 ePoster Access - Visual Screenshots Guide

## 🎯 Where to Click - Annotated Guide

### 1️⃣ HOME PAGE - Events Table (PRIMARY ACCESS)

```
════════════════════════════════════════════════════════════════════
                         DASHBOARD HOME
════════════════════════════════════════════════════════════════════

┌─ Statistics Cards ─────────────────────────────────────────────┐
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│  │  EVENTS  │  │  ACTIVE  │  │  USERS   │  │ SESSIONS │      │
│  │    15    │  │    5     │  │   342    │  │    28    │      │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘      │
└────────────────────────────────────────────────────────────────┘

┌─ All Events - ePoster Access ──────────────────────────────────┐
│                                                                  │
│  Event Name      Status   Dates       Participants  Actions     │
│  ─────────────────────────────────────────────────────────────  │
│  Medical Conf    Active   Jan 15-20   125          👁️  📄  🗑️ │
│                                                       │   │   │  │
│                                                       │   │   └──┼─ Delete
│                                                       │   └──────┼─ ePOSTER ⭐
│                                                       └──────────┼─ View Event
│                                                                  │
│  Tech Summit     Upcoming Feb 10-12   89           👁️  📄  🗑️  │
│                                                           ▲      │
│  Science Forum   Active   Jan 25-27   200          👁️  📄  🗑️  │
│                                                           │      │
│                                                           │      │
│  Academic Conf   Completed Dec 1-5    156          👁️  📄  🗑️  │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘

                        CLICK HERE! ──────────┘
                      (Green Button with 📄 Icon)

Visual Cues:
• Color: 🟩 Bright Green (Success color)
• Icon: 📄 Document/File icon
• Position: Between "View" (blue) and "Delete" (red)
• Hover: Button highlights when you move mouse over it
• Tooltip: Shows "ePoster Management" when you hover
```

---

### 2️⃣ SIDEBAR NAVIGATION

```
┌────────────────────────┐
│  SIDEBAR              │
├────────────────────────┤
│                        │
│  🏠 Dashboard         │
│  ➕ Create Event      │
│  👥 Users             │
│  ➕ Create User       │
│  💰 Caisses           │
│                        │
│  📄 ePoster Management │ ← CLICK HERE!
│     ─────────────────  │    (New item)
│                        │
│  ✉️ Email Templates   │
│  📋 Registration Form  │
│                        │
│  ⚙️ Django Admin      │
│  📚 API Docs          │
│  🚪 Logout            │
│                        │
└────────────────────────┘

What Happens:
1. Click "ePoster Management" in sidebar
2. Page scrolls to events table (smooth animation)
3. Events section briefly highlighted in green
4. Then click green 📄 button on any event
```

---

### 3️⃣ EVENT DETAIL PAGE - Tabs

```
════════════════════════════════════════════════════════════════════
                      EVENT DETAIL PAGE
                     "Medical Conference"
════════════════════════════════════════════════════════════════════

┌─ Event Header ─────────────────────────────────────────────────┐
│  Medical Conference                          [Edit] [Delete]    │
│  📅 Jan 15-20, 2026  📍 City Convention Center                │
└────────────────────────────────────────────────────────────────┘

┌─ Tabs ────────────────────────────────────────────────────────┐
│                                                                 │
│  [Overview] [Rooms] [Sessions] [Users] [Caisses] [Payables]   │
│                                                                 │
│  [Email Templates] [📄 ePoster]                               │
│                      ──────────                                │
│                      CLICK HERE!                               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

Tab Details:
• Position: After "Email Templates" tab
• Icon: 📄 Document icon + "ePoster" text
• Color: Same as other tabs (blue when active)
• Action: Navigates to ePoster dashboard for this event
```

---

## 🎨 Button Visual Reference

### Green ePoster Button (Detailed View)

```
Normal State:
┌──────────┐
│    📄    │  ← Icon: Document/File
└──────────┘
   Color: Green (#28a745)
   Border: Outlined
   Size: Small (btn-sm)

Hover State:
┌──────────┐
│    📄    │  ← Icon stays same
└──────────┘
   Color: Darker Green
   Border: Solid green
   Cursor: Pointer hand
   Tooltip: "ePoster Management"

After Click:
→ Navigates to: /dashboard/events/<event-id>/eposter/
→ Page transition with loading indicator
```

---

## 📱 Mobile View

```
┌─────────────────────┐
│  ☰  Dashboard       │
├─────────────────────┤
│                     │
│  Events (Swipe →)   │
│                     │
│  ┌────────────────┐ │
│  │ Medical Conf   │ │
│  │ Status: Active │ │
│  │                │ │
│  │ [View] [📄]   │ │ ← ePoster button
│  └────────────────┘ │
│                     │
│  ┌────────────────┐ │
│  │ Tech Summit    │ │
│  │ Status: Soon   │ │
│  │                │ │
│  │ [View] [📄]   │ │
│  └────────────────┘ │
│                     │
└─────────────────────┘

Mobile Notes:
• Buttons stack vertically
• Same green color
• Touch-friendly size
• Full functionality maintained
```

---

## 🔍 How to Recognize Each Button

### Button Comparison Table

| Feature | View Button | ePoster Button | Delete Button |
|---------|-------------|----------------|---------------|
| **Icon** | 👁️ Eye | 📄 Document | 🗑️ Trash |
| **Color** | Blue | Green | Red |
| **Purpose** | Event details | ePoster mgmt | Remove event |
| **Style** | btn-outline-primary | btn-outline-success | btn-outline-danger |

### Visual Sequence in Table

```
Actions Column Layout:

   Position 1    Position 2    Position 3
   ──────────    ──────────    ──────────
   │  👁️   │    │  📄   │    │  🗑️  │
   │ View  │    │ePoster│    │Delete │
   │ Blue  │    │ Green │    │  Red  │
   └───────┘    └───────┘    └───────┘
                    ▲
                    │
              CLICK THIS ONE
           for ePoster Access!
```

---

## 🎯 Click Targets (Exact Locations)

### Home Page Table Row

```
Full Row Layout (Horizontal spacing):

Event Name (30%) | Status (15%) | Dates (20%) | Participants | Actions (35%)
─────────────────┼──────────────┼─────────────┼──────────────┼───────────────
Medical Conf     | Active       | Jan 15-20   | 125          | [👁️] [📄] [🗑️]
                 |              |             |              |   1    2    3

Click Target #2 (ePoster):
• X-position: ~75% from left edge
• Y-position: Vertically centered in row
• Width: ~40-50px (small button)
• Height: ~30-35px
• Clickable area: Entire button + padding
```

### Sidebar Item

```
Sidebar Item Layout:

┌─────────────────────────────┐
│                             │
│ [Icon] Text Label           │ ← Full row is clickable
│   📄   ePoster Management   │
│                             │
└─────────────────────────────┘

Click Target:
• X-position: Full width of sidebar
• Y-position: Between "Caisses" and "Email Templates"
• Width: Full sidebar width (~250px)
• Height: ~40-45px
• Clickable area: Entire menu item
```

---

## 🖱️ Mouse Cursor Changes

### Cursor States

```
Over Table Text:      I     (Text cursor)
Over Green Button:    👆    (Pointer/Hand)
Over View Button:     👆    (Pointer/Hand)
Over Sidebar Link:    👆    (Pointer/Hand)
```

---

## 🎨 Color Reference (Exact Codes)

### Button Colors

```css
ePoster Button:
• Background (hover): #28a745  (Green)
• Border: #28a745
• Text: #28a745 (when outlined)
• Icon: Inherits text color

View Button:
• Background (hover): #0d6efd  (Blue)
• Border: #0d6efd
• Text: #0d6efd

Delete Button:
• Background (hover): #dc3545  (Red)
• Border: #dc3545
• Text: #dc3545
```

---

## 📏 Button Sizes

```
Small Button (btn-sm):
Height: 31px
Padding: 4px 8px
Font Size: 14px
Icon Size: 16px

Standard spacing between buttons: 4-8px
```

---

## ✨ Animation & Effects

### Hover Animation

```
Before Hover:
┌──────────┐
│    📄    │  Outline only
└──────────┘

During Hover:
┌──────────┐
│    📄    │  Background fills with green
└──────────┘  + Slight shadow appears

Duration: 0.15s (smooth transition)
```

### Click Animation

```
1. Click down:
   • Button depresses slightly (2px down)
   • Darker green background

2. Navigation starts:
   • Loading spinner appears in top-right
   • Page begins to fade

3. New page loads:
   • ePoster dashboard appears
   • Smooth fade-in effect
```

---

## 🎓 Visual Learning Path

### First Time User Journey

```
Step 1: LOGIN
   ↓
   Your browser shows dashboard home page

Step 2: LOCATE
   ↓
   Scroll down to "All Events - ePoster Access" section
   (It's below the statistics cards)

Step 3: IDENTIFY
   ↓
   Look at "Actions" column (rightmost)
   Find the GREEN button (middle of three buttons)
   It has a 📄 icon

Step 4: VERIFY
   ↓
   Hover your mouse over it
   Tooltip says "ePoster Management" ✓
   Cursor changes to pointer hand ✓
   Button background turns darker green ✓

Step 5: CLICK
   ↓
   Single left-click
   Page navigates to ePoster dashboard

Step 6: SUCCESS!
   ↓
   You're now in ePoster management for that event
```

---

## 📸 What You Should See

### After Clicking Green Button

```
Page URL changes to:
/dashboard/events/abc-123-def-456/eposter/

Page shows:
┌────────────────────────────────────────────────────┐
│  ePoster Dashboard - Medical Conference            │
├────────────────────────────────────────────────────┤
│                                                     │
│  ┌───────┐  ┌───────┐  ┌───────┐  ┌───────┐      │
│  │ TOTAL │  │ACCEPTÉ│  │ATTENTE│  │REJETÉ │      │
│  │  45   │  │  12   │  │  28   │  │   5   │      │
│  └───────┘  └───────┘  └───────┘  └───────┘      │
│                                                     │
│  [Voir toutes les soumissions]                     │
│  [Gérer le Comité]                                 │
│  ...                                                │
│                                                     │
└────────────────────────────────────────────────────┘

Breadcrumb at top:
Dashboard > Events > Medical Conference > ePoster
```

---

## 🎯 Quick Reference Card

```
╔═══════════════════════════════════════════════════╗
║         EPOSTER ACCESS QUICK GUIDE                ║
╠═══════════════════════════════════════════════════╣
║                                                   ║
║  WHERE:  Dashboard Home → Events Table            ║
║  WHAT:   Green button with 📄 icon               ║
║  WHICH:  Middle button (between View & Delete)    ║
║  COLOR:  Bright Green (#28a745)                   ║
║  ACTION: Single click                             ║
║  RESULT: Opens ePoster dashboard for event        ║
║                                                   ║
║  ALTERNATIVE PATHS:                               ║
║  • Sidebar → "ePoster Management"                 ║
║  • Event Detail → "ePoster" tab                   ║
║                                                   ║
╚═══════════════════════════════════════════════════╝
```

---

## 🔍 Troubleshooting Visual Issues

### "I don't see the green button"

**Check:**
1. ✅ Are you on Dashboard Home page? (URL ends with `/dashboard/` or `/dashboard/home/`)
2. ✅ Is there at least one event in the table?
3. ✅ Scroll down - events table is below statistics cards
4. ✅ Browser window wide enough? (Not too narrow)
5. ✅ Try refreshing page (Ctrl+F5)

### "Button is there but wrong color"

**Possible causes:**
- Browser cache issue → Clear cache (Ctrl+Shift+Delete)
- CSS not loaded → Refresh page
- Custom theme interfering → Check browser extensions

### "Button doesn't work when clicked"

**Check:**
- ✅ JavaScript enabled in browser?
- ✅ No browser errors? (F12 → Console tab)
- ✅ Event has valid UUID?
- ✅ User has permissions?

---

## 💡 Pro Tips

1. **Bookmark frequently used ePoster dashboards**
   - Right-click green button → "Open in new tab"
   - Then bookmark that tab

2. **Keyboard shortcut**
   - Ctrl+Click = Open in new tab (Windows/Linux)
   - Cmd+Click = Open in new tab (Mac)

3. **Quick navigation**
   - Middle mouse button click = Open in background tab

4. **Mobile users**
   - Tap and hold = Context menu appears
   - "Open in new tab" option available

---

**Remember**: 🟩 GREEN 📄 = ePoster Access!

Look for it in the Actions column of every event row on your dashboard home page.
