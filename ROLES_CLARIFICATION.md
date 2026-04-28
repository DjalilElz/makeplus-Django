# User Roles Clarification

**Date:** April 28, 2026  
**Important:** Different roles have different requirements

---

## 🎭 User Roles in the System

### 1. controlleur_des_badges (Badge Controller)

**Purpose:** Scan participant badges at event entrance or any location

**Room Assignment:** ❌ NOT NEEDED
- Can work in ANY room
- No room selection required
- Scans badges anywhere in the event

**Mobile App Behavior:**
```dart
if (role == 'controlleur_des_badges') {
  // ✅ NO room check needed
  // Navigate directly to scanner
  Navigator.push(
    context,
    MaterialPageRoute(
      builder: (context) => BadgeScannerScreen(),
    ),
  );
}
```

**API Endpoint:**
```
POST /api/participants/scan/
```
- No room_id parameter
- Returns ALL paid items from ALL rooms

---

### 2. gestionnaire_des_salles (Room Manager)

**Purpose:** Manage sessions in a specific room (start/end sessions, view room stats)

**Room Assignment:** ✅ REQUIRED
- Must be assigned to a specific room
- Manages only that room's sessions
- Room ID stored in metadata

**Mobile App Behavior:**
```dart
if (role == 'gestionnaire_des_salles') {
  // ✅ Room check IS needed
  final metadata = userAssignment['metadata'];
  final roomId = metadata?['room_id'];
  
  if (roomId == null) {
    showError("Aucune salle assignée pour cet utilisateur");
    return;
  }
  
  // Navigate to room management screen
  Navigator.push(
    context,
    MaterialPageRoute(
      builder: (context) => RoomManagementScreen(
        roomId: roomId,
        roomName: metadata['room_name'],
      ),
    ),
  );
}
```

**What Room Manager Can Do:**
- View sessions in their assigned room
- Start/end sessions
- View room statistics
- Manage room capacity

---

### 3. participant (Event Participant)

**Purpose:** Attend event, view schedule, show QR code

**Room Assignment:** ❌ NOT NEEDED
- Can view all sessions
- Has QR code for check-in
- Registers for specific sessions

**Mobile App Behavior:**
```dart
if (role == 'participant') {
  // Show participant home screen
  Navigator.push(
    context,
    MaterialPageRoute(
      builder: (context) => ParticipantHomeScreen(),
    ),
  );
}
```

---

## 🔧 Mobile App Implementation

### Role-Based Navigation

```dart
void navigateBasedOnRole(Map<String, dynamic> userAssignment) {
  final role = userAssignment['role'];
  final metadata = userAssignment['metadata'];
  
  switch (role) {
    case 'controlleur_des_badges':
      // ✅ NO room check - can work anywhere
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(
          builder: (context) => BadgeScannerScreen(),
        ),
      );
      break;
      
    case 'gestionnaire_des_salles':
      // ✅ Room check IS needed
      final roomId = metadata?['room_id'];
      
      if (roomId == null) {
        showError("Aucune salle assignée pour cet utilisateur");
        return;
      }
      
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(
          builder: (context) => RoomManagementScreen(
            roomId: roomId,
            roomName: metadata['room_name'] ?? 'Salle',
          ),
        ),
      );
      break;
      
    case 'participant':
      // ✅ NO room check - participant view
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(
          builder: (context) => ParticipantHomeScreen(),
        ),
      );
      break;
      
    default:
      showError("Rôle non reconnu: $role");
  }
}
```

---

## 📋 Summary Table

| Role | Room Assignment | Purpose | Navigation |
|------|----------------|---------|------------|
| `controlleur_des_badges` | ❌ Not needed | Scan badges anywhere | Direct to scanner |
| `gestionnaire_des_salles` | ✅ Required | Manage specific room | Check room_id first |
| `participant` | ❌ Not needed | Attend event | Direct to home |

---

## 🐛 Fixing Your Current Issue

**Your Error:**
```
❌ ERROR LOADING ROOM/SESSIONS: Exception: Aucune salle assignée pour cet utilisateur
Role: gestionnaire_des_salles
```

**The Problem:**
- User has role `gestionnaire_des_salles` (room manager)
- Room managers NEED a room assignment
- This user doesn't have a room assigned in metadata

**The Solution:**

**Option 1: Assign a Room (Backend)**
The admin needs to assign this user to a room in the dashboard.

**Option 2: Handle Gracefully (Mobile App)**
```dart
if (role == 'gestionnaire_des_salles') {
  final roomId = metadata?['room_id'];
  
  if (roomId == null) {
    // Show friendly error with instructions
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Aucune salle assignée'),
        content: Text(
          'Vous êtes gestionnaire de salle mais aucune salle ne vous a été assignée.\n\n'
          'Veuillez contacter l\'administrateur pour qu\'il vous assigne une salle.'
        ),
        actions: [
          TextButton(
            onPressed: () {
              Navigator.pop(context);
              // Go back to login or show contact info
            },
            child: Text('OK'),
          ),
        ],
      ),
    );
    return;
  }
  
  // Continue with room management
  Navigator.push(...);
}
```

---

## ✅ What You Need to Change

**For Badge Controllers (controlleur_des_badges):**
- ✅ Remove room assignment check
- ✅ Navigate directly to scanner
- ✅ Use `/api/participants/scan/` endpoint

**For Room Managers (gestionnaire_des_salles):**
- ✅ Keep room assignment check
- ✅ Show error if no room assigned
- ✅ Use room-specific endpoints

**For Participants:**
- ✅ No room check needed
- ✅ Navigate to participant home

---

## 🔍 How to Check User Role

```dart
// After getting user assignment
final role = userAssignment['role'];

print('User role: $role');

// Check role type
if (role == 'controlleur_des_badges') {
  print('This is a badge controller - no room needed');
} else if (role == 'gestionnaire_des_salles') {
  print('This is a room manager - room assignment required');
} else if (role == 'participant') {
  print('This is a participant - no room needed');
}
```

---

## 📞 Backend API Endpoints by Role

### Badge Controller (controlleur_des_badges)
```
POST /api/participants/scan/          # Scan badge (no room_id)
GET  /api/my-room/statistics/         # Get scan statistics
```

### Room Manager (gestionnaire_des_salles)
```
GET  /api/rooms/{room_id}/            # Get room details
GET  /api/rooms/{room_id}/sessions/   # Get room sessions
POST /api/sessions/{id}/start/        # Start session
POST /api/sessions/{id}/end/          # End session
GET  /api/rooms/{room_id}/statistics/ # Get room statistics
```

### Participant
```
GET  /api/auth/me/                    # Get profile with QR code
GET  /api/events/my-ateliers/         # Get paid sessions
GET  /api/events/                     # Get event list
GET  /api/sessions/                   # Get all sessions
```

---

**Last Updated:** April 28, 2026  
**Status:** ✅ Clarified
