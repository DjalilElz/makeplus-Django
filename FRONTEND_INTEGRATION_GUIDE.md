# 📱 Frontend Integration Guide - Multi-Event Login System

## 🎯 Overview

The MakePlus API now supports users who are assigned to multiple events with different roles. This guide explains how to implement the two-step login flow in your frontend application.

---

## 🔄 Login Flow Diagram

```
User enters email & password
         ↓
    POST /api/auth/login/
         ↓
    ┌────┴─────┐
    │          │
  1 event   Multiple events
    │          │
    ↓          ↓
  Direct   Event Selection
  Access      Screen
    │          │
    └────┬─────┘
         ↓
   Event Dashboard
```

---

## 📡 API Endpoints

### 1. **Login** - `POST /api/auth/login/`
### 2. **Select Event** - `POST /api/auth/select-event/`
### 3. **Switch Event** - `POST /api/auth/switch-event/`
### 4. **My Events** - `GET /api/auth/my-events/`

---

## 💻 Implementation Guide

### **Step 1: Login Request**

```javascript
// Login API call
async function login(email, password) {
  const response = await fetch('http://127.0.0.1:8000/api/auth/login/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      email: email,
      password: password
    })
  });
  
  const data = await response.json();
  
  if (!response.ok) {
    throw new Error(data.detail || 'Login failed');
  }
  
  return data;
}
```

### **Step 2: Handle Login Response**

```javascript
// Handle login response
async function handleLogin(email, password) {
  try {
    const loginData = await login(email, password);
    
    // Check if event selection is required
    if (loginData.requires_event_selection) {
      // User has multiple events - show selection screen
      showEventSelectionScreen(loginData);
    } else {
      // User has only one event - go directly to dashboard
      saveTokensAndNavigate(loginData);
    }
  } catch (error) {
    showError(error.message);
  }
}
```

---

## 📋 Response Formats

### **Case 1: User with ONE Event (Auto-login)**

**Request:**
```json
POST /api/auth/login/
{
  "email": "ahmed.benali@techsummit.dz",
  "password": "makeplus2025"
}
```

**Response:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "username": "tech_organisateur",
    "email": "ahmed.benali@techsummit.dz",
    "first_name": "Ahmed",
    "last_name": "Benali"
  },
  "current_event": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "TechSummit Algeria 2025",
    "role": "organisateur",
    "start_date": "2025-12-19T09:00:00Z",
    "end_date": "2025-12-22T18:00:00Z",
    "status": "upcoming",
    "location": "Centre des Congrès, Alger",
    "logo_url": "",
    "banner_url": "",
    "badge": null,
    "permissions": ["full_control", "manage_event", "manage_rooms", "manage_sessions", "manage_participants", "verify_qr"]
  },
  "requires_event_selection": false
}
```

**Frontend Action:**
```javascript
// Save tokens and go to dashboard
localStorage.setItem('access_token', data.access);
localStorage.setItem('refresh_token', data.refresh);
localStorage.setItem('user', JSON.stringify(data.user));
localStorage.setItem('current_event', JSON.stringify(data.current_event));

// Navigate to dashboard
window.location.href = '/dashboard';
```

---

### **Case 2: User with MULTIPLE Events (Selection Required)**

**Request:**
```json
POST /api/auth/login/
{
  "email": "multi.user@makeplus.com",
  "password": "makeplus2025"
}
```

**Response:**
```json
{
  "user": {
    "id": 19,
    "username": "multi_user1",
    "email": "multi.user@makeplus.com",
    "first_name": "Hakim",
    "last_name": "Mansouri"
  },
  "requires_event_selection": true,
  "available_events": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "TechSummit Algeria 2025",
      "role": "participant",
      "start_date": "2025-12-19T09:00:00Z",
      "end_date": "2025-12-22T18:00:00Z",
      "status": "upcoming",
      "location": "Centre des Congrès, Alger",
      "badge": {
        "badge_id": "TECH-29A781A2",
        "qr_code_data": "550e8400...:19:TECH-29A781A2",
        "is_checked_in": false
      }
    },
    {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "name": "StartupWeek Oran 2025",
      "role": "organisateur",
      "start_date": "2026-01-18T09:00:00Z",
      "end_date": "2026-01-23T18:00:00Z",
      "status": "upcoming",
      "location": "Palais des Expositions, Oran",
      "badge": null
    },
    {
      "id": "770e8400-e29b-41d4-a716-446655440002",
      "name": "InnoFest Constantine 2025",
      "role": "controlleur_des_badges",
      "start_date": "2026-02-17T09:00:00Z",
      "end_date": "2026-02-19T18:00:00Z",
      "status": "upcoming",
      "location": "Université Constantine 2, Constantine",
      "badge": null
    }
  ],
  "temp_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Frontend Action:**
```javascript
// Save user info and temp token
localStorage.setItem('user', JSON.stringify(data.user));
localStorage.setItem('temp_token', data.temp_token);
localStorage.setItem('available_events', JSON.stringify(data.available_events));

// Show event selection screen
showEventSelectionScreen(data.available_events);
```

---

### **Step 3: Event Selection**

```javascript
// Select event API call
async function selectEvent(eventId, tempToken) {
  const response = await fetch('http://127.0.0.1:8000/api/auth/select-event/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${tempToken}`
    },
    body: JSON.stringify({
      event_id: eventId
    })
  });
  
  const data = await response.json();
  
  if (!response.ok) {
    throw new Error(data.detail || 'Event selection failed');
  }
  
  return data;
}

// Handle event selection
async function handleEventSelection(selectedEventId) {
  try {
    const tempToken = localStorage.getItem('temp_token');
    const eventData = await selectEvent(selectedEventId, tempToken);
    
    // Save tokens and event data
    localStorage.setItem('access_token', eventData.access);
    localStorage.setItem('refresh_token', eventData.refresh);
    localStorage.setItem('current_event', JSON.stringify(eventData.current_event));
    
    // Clean up temp token
    localStorage.removeItem('temp_token');
    localStorage.removeItem('available_events');
    
    // Navigate to dashboard
    window.location.href = '/dashboard';
  } catch (error) {
    showError(error.message);
  }
}
```

**Request:**
```json
POST /api/auth/select-event/
Headers: {
  "Authorization": "Bearer eyJ0eXAiOiJKV1Qi..."
}
Body: {
  "event_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Response:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 19,
    "username": "multi_user1",
    "email": "multi.user@makeplus.com",
    "first_name": "Hakim",
    "last_name": "Mansouri"
  },
  "current_event": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "TechSummit Algeria 2025",
    "role": "participant",
    "start_date": "2025-12-19T09:00:00Z",
    "end_date": "2025-12-22T18:00:00Z",
    "status": "upcoming",
    "location": "Centre des Congrès, Alger",
    "logo_url": "",
    "banner_url": "",
    "badge": {
      "badge_id": "TECH-29A781A2",
      "qr_code_data": "550e8400...:19:TECH-29A781A2",
      "is_checked_in": false,
      "checked_in_at": null
    },
    "permissions": ["view_sessions", "access_rooms", "check_in"]
  }
}
```

---

## 🔄 Event Switching (Already Logged In)

```javascript
// Switch event API call
async function switchEvent(eventId) {
  const accessToken = localStorage.getItem('access_token');
  
  const response = await fetch('http://127.0.0.1:8000/api/auth/switch-event/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${accessToken}`
    },
    body: JSON.stringify({
      event_id: eventId
    })
  });
  
  const data = await response.json();
  
  if (!response.ok) {
    throw new Error(data.detail || 'Event switch failed');
  }
  
  return data;
}

// Handle event switch
async function handleEventSwitch(newEventId) {
  try {
    const eventData = await switchEvent(newEventId);
    
    // Update tokens and event data
    localStorage.setItem('access_token', eventData.access);
    localStorage.setItem('refresh_token', eventData.refresh);
    localStorage.setItem('current_event', JSON.stringify(eventData.current_event));
    
    // Reload dashboard or redirect
    window.location.reload();
  } catch (error) {
    showError(error.message);
  }
}
```

---

## 📋 Get User's Events

```javascript
// Get all user's events
async function getMyEvents() {
  const accessToken = localStorage.getItem('access_token');
  
  const response = await fetch('http://127.0.0.1:8000/api/auth/my-events/', {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${accessToken}`
    }
  });
  
  const data = await response.json();
  
  if (!response.ok) {
    throw new Error(data.detail || 'Failed to fetch events');
  }
  
  return data;
}

// Example response:
{
  "events": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "TechSummit Algeria 2025",
      "role": "participant",
      "is_current": true,
      "status": "upcoming",
      "start_date": "2025-12-19T09:00:00Z",
      "end_date": "2025-12-22T18:00:00Z",
      "location": "Centre des Congrès, Alger",
      "logo_url": "",
      "badge": {
        "badge_id": "TECH-29A781A2",
        "is_checked_in": false
      }
    },
    {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "name": "StartupWeek Oran 2025",
      "role": "organisateur",
      "is_current": false,
      "status": "upcoming",
      "start_date": "2026-01-18T09:00:00Z",
      "end_date": "2026-01-23T18:00:00Z",
      "location": "Palais des Expositions, Oran",
      "logo_url": "",
      "badge": null
    }
  ],
  "total": 2
}
```

---

## 🎨 UI Components

### **Event Selection Screen**

```jsx
// React Example
function EventSelectionScreen({ events, onSelectEvent }) {
  return (
    <div className="event-selection">
      <h2>Select Event</h2>
      <p>You have access to multiple events. Please select one to continue.</p>
      
      <div className="events-list">
        {events.map(event => (
          <div 
            key={event.id} 
            className="event-card"
            onClick={() => onSelectEvent(event.id)}
          >
            <h3>{event.name}</h3>
            <p className="role-badge">{getRoleLabel(event.role)}</p>
            <p className="location">📍 {event.location}</p>
            <p className="dates">
              📅 {formatDate(event.start_date)} - {formatDate(event.end_date)}
            </p>
            <p className="status">{event.status}</p>
            {event.badge && (
              <p className="badge">🎫 Badge: {event.badge.badge_id}</p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

function getRoleLabel(role) {
  const labels = {
    'organisateur': '👔 Organizer',
    'controlleur_des_badges': '🎫 Badge Controller',
    'participant': '👤 Participant',
    'exposant': '🏢 Exhibitor'
  };
  return labels[role] || role;
}
```

### **Event Switcher (Header/Menu)**

```jsx
// React Example
function EventSwitcher({ currentEvent, allEvents, onSwitchEvent }) {
  const [isOpen, setIsOpen] = useState(false);
  
  return (
    <div className="event-switcher">
      <button onClick={() => setIsOpen(!isOpen)}>
        {currentEvent.name} ▼
      </button>
      
      {isOpen && (
        <div className="event-dropdown">
          {allEvents.map(event => (
            <div 
              key={event.id}
              className={event.is_current ? 'current' : ''}
              onClick={() => {
                if (!event.is_current) {
                  onSwitchEvent(event.id);
                }
                setIsOpen(false);
              }}
            >
              {event.name}
              <span className="role">{getRoleLabel(event.role)}</span>
              {event.is_current && <span className="current-badge">✓</span>}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
```

---

## 🧪 Testing Credentials

### **User with ONE Event:**
- **Email:** `ahmed.benali@techsummit.dz`
- **Password:** `makeplus2025`
- **Behavior:** Direct login, no event selection

### **User with MULTIPLE Events:**
- **Email:** `multi.user@makeplus.com`
- **Password:** `makeplus2025`
- **Events:** 3 events with different roles
  - TechSummit Algeria 2025 (Participant)
  - StartupWeek Oran 2025 (Organisateur)
  - InnoFest Constantine 2025 (Contrôleur)

### **Another Multi-Event User:**
- **Email:** `cross.event@makeplus.com`
- **Password:** `makeplus2025`
- **Events:** 2 events
  - TechSummit Algeria 2025 (Exposant)
  - StartupWeek Oran 2025 (Participant)

---

## 🔐 Token Management

### **Access Token Claims:**
```json
{
  "user_id": 19,
  "username": "multi_user1",
  "email": "multi.user@makeplus.com",
  "event_id": "550e8400-e29b-41d4-a716-446655440000",
  "role": "participant",
  "exp": 1234567890
}
```

### **All API Requests:**
```javascript
// Include token in all requests
const accessToken = localStorage.getItem('access_token');

fetch('http://127.0.0.1:8000/api/events/', {
  headers: {
    'Authorization': `Bearer ${accessToken}`
  }
});

// The backend automatically filters data by the event_id in the token
```

---

## ✅ Complete Flow Example

```javascript
// Complete login flow implementation
class AuthService {
  async login(email, password) {
    const response = await fetch('http://127.0.0.1:8000/api/auth/login/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail);
    
    // Save user data
    localStorage.setItem('user', JSON.stringify(data.user));
    
    if (data.requires_event_selection) {
      // Save temp data
      localStorage.setItem('temp_token', data.temp_token);
      localStorage.setItem('available_events', JSON.stringify(data.available_events));
      return { needsEventSelection: true, events: data.available_events };
    } else {
      // Save tokens directly
      this.saveTokens(data.access, data.refresh, data.current_event);
      return { needsEventSelection: false, event: data.current_event };
    }
  }
  
  async selectEvent(eventId) {
    const tempToken = localStorage.getItem('temp_token');
    
    const response = await fetch('http://127.0.0.1:8000/api/auth/select-event/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${tempToken}`
      },
      body: JSON.stringify({ event_id: eventId })
    });
    
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail);
    
    // Save tokens
    this.saveTokens(data.access, data.refresh, data.current_event);
    
    // Cleanup
    localStorage.removeItem('temp_token');
    localStorage.removeItem('available_events');
    
    return data.current_event;
  }
  
  async switchEvent(eventId) {
    const accessToken = localStorage.getItem('access_token');
    
    const response = await fetch('http://127.0.0.1:8000/api/auth/switch-event/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${accessToken}`
      },
      body: JSON.stringify({ event_id: eventId })
    });
    
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail);
    
    // Update tokens
    this.saveTokens(data.access, data.refresh, data.current_event);
    
    return data.current_event;
  }
  
  async getMyEvents() {
    const accessToken = localStorage.getItem('access_token');
    
    const response = await fetch('http://127.0.0.1:8000/api/auth/my-events/', {
      headers: { 'Authorization': `Bearer ${accessToken}` }
    });
    
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail);
    
    return data.events;
  }
  
  saveTokens(access, refresh, event) {
    localStorage.setItem('access_token', access);
    localStorage.setItem('refresh_token', refresh);
    localStorage.setItem('current_event', JSON.stringify(event));
  }
  
  getCurrentEvent() {
    const eventData = localStorage.getItem('current_event');
    return eventData ? JSON.parse(eventData) : null;
  }
  
  logout() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    localStorage.removeItem('current_event');
    localStorage.removeItem('temp_token');
    localStorage.removeItem('available_events');
  }
}
```

---

## 🎯 Summary

1. **Login** returns either:
   - Full tokens (1 event) → Go to dashboard
   - Temp token + event list (multiple events) → Show selection

2. **Event Selection** converts temp token → full tokens

3. **Event Switching** allows changing events without re-login

4. **All tokens** include event context (event_id, role)

5. **Backend** automatically filters data by event

---

## 📞 Support

- **API Base URL:** `http://127.0.0.1:8000/api/`
- **Swagger Docs:** `http://127.0.0.1:8000/swagger/`
- **Test Users:** See CREDENTIALS.md

---

**Last Updated:** November 19, 2025
