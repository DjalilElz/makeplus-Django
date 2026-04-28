# Final Mobile Developer Guide

**Date:** April 28, 2026  
**Status:** ✅ Complete and Ready

---

## 🎯 Quick Summary

### What You Need to Know

1. **Different roles have different requirements**
2. **Badge Controllers** don't need room assignment
3. **Room Managers** DO need room assignment
4. **You must implement role-based logic**

---

## 🎭 User Roles

### 1. Badge Controller (`controlleur_des_badges`)

**Purpose:** Scan participant badges at event entrance

**Room Assignment:** ❌ NOT NEEDED

**Implementation:**
```dart
if (role == 'controlleur_des_badges') {
  // ✅ NO room check
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

---

### 2. Room Manager (`gestionnaire_des_salles`)

**Purpose:** Manage sessions in a specific room

**Room Assignment:** ✅ REQUIRED

**Implementation:**
```dart
if (role == 'gestionnaire_des_salles') {
  // ✅ Room check IS needed
  final metadata = userAssignment['metadata'];
  final roomId = metadata?['room_id'];
  
  if (roomId == null) {
    showError("Aucune salle assignée pour cet utilisateur");
    return;
  }
  
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

**API Endpoints:**
```
GET  /api/rooms/{room_id}/
GET  /api/rooms/{room_id}/sessions/
POST /api/sessions/{id}/start/
POST /api/sessions/{id}/end/
```

---

### 3. Participant (`participant`)

**Purpose:** Attend event, view schedule

**Room Assignment:** ❌ NOT NEEDED

**Implementation:**
```dart
if (role == 'participant') {
  // ✅ NO room check
  Navigator.push(
    context,
    MaterialPageRoute(
      builder: (context) => ParticipantHomeScreen(),
    ),
  );
}
```

**API Endpoints:**
```
GET /api/auth/me/
GET /api/events/my-ateliers/
```

---

## 🔧 Complete Implementation

### Role-Based Navigation

```dart
void navigateBasedOnRole(Map<String, dynamic> userAssignment) {
  final role = userAssignment['role'];
  final metadata = userAssignment['metadata'];
  
  print('User role: $role');
  
  switch (role) {
    case 'controlleur_des_badges':
      // ✅ Badge Controller - No room check
      print('Badge Controller - No room assignment needed');
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(
          builder: (context) => BadgeScannerScreen(),
        ),
      );
      break;
      
    case 'gestionnaire_des_salles':
      // ✅ Room Manager - Room check required
      print('Room Manager - Checking room assignment...');
      final roomId = metadata?['room_id'];
      
      if (roomId == null) {
        print('ERROR: No room assigned');
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
                onPressed: () => Navigator.pop(context),
                child: Text('OK'),
              ),
            ],
          ),
        );
        return;
      }
      
      print('Room assigned: $roomId');
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
      // ✅ Participant - No room check
      print('Participant - No room assignment needed');
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(
          builder: (context) => ParticipantHomeScreen(),
        ),
      );
      break;
      
    default:
      print('ERROR: Unknown role: $role');
      showError("Rôle non reconnu: $role");
  }
}
```

---

## ✅ What to Change

### For Badge Controllers

**Change 1: Fix URL**
```dart
// OLD (404 error):
Uri.parse('$baseUrl/api/events/participants/scan/')

// NEW (works):
Uri.parse('$baseUrl/api/participants/scan/')
```

**Change 2: Remove Room Check**
```dart
// DELETE THIS:
if (role == 'controlleur_des_badges') {
  final roomId = metadata?['room_id'];
  if (roomId == null) {
    showError("No room assignment");
    return;
  }
}

// USE THIS:
if (role == 'controlleur_des_badges') {
  // No room check needed!
  Navigator.push(...);
}
```

**Change 3: Remove Room Parameters**
```dart
// OLD:
class BadgeScannerScreen extends StatefulWidget {
  final String roomId;
  final String roomName;
  ...
}

// NEW:
class BadgeScannerScreen extends StatefulWidget {
  // No parameters needed!
  ...
}
```

### For Room Managers

**Keep Everything As Is:**
- ✅ Keep room assignment check
- ✅ Keep room parameters
- ✅ Keep room-specific endpoints

---

## 📊 Quick Reference Table

| Role | Room Check | Navigation | Endpoint |
|------|-----------|------------|----------|
| `controlleur_des_badges` | ❌ Remove | Direct to scanner | `/api/participants/scan/` |
| `gestionnaire_des_salles` | ✅ Keep | Check room first | `/api/rooms/{room_id}/...` |
| `participant` | ❌ Remove | Direct to home | `/api/auth/me/` |

---

## 🧪 Testing Checklist

### Test Badge Controller
- [ ] Login as `controller1@wemakeplus.com`
- [ ] Should go directly to scanner (no room error)
- [ ] Scan a badge
- [ ] Should see ALL paid items from ALL rooms
- [ ] No 404 error

### Test Room Manager
- [ ] Login as `gestionaire1@wemakeplus.com`
- [ ] If no room assigned: Should show error message
- [ ] If room assigned: Should go to room management
- [ ] Can manage sessions in assigned room

### Test Participant
- [ ] Login as participant
- [ ] Should go to participant home
- [ ] Can view schedule
- [ ] Can show QR code

---

## 📚 Documentation Files

1. **FINAL_MOBILE_DEVELOPER_GUIDE.md** (this file) - Quick reference
2. **ROLES_CLARIFICATION.md** - Detailed role explanation
3. **MESSAGE_TO_MOBILE_DEVELOPER.md** - Complete developer guide
4. **MOBILE_APP_API_SPECIFICATION.md** - API reference
5. **MOBILE_DEVELOPER_SUMMARY.md** - Changes summary

---

## 🆘 Common Issues

### Issue 1: "No room assignment" error for badge controller

**Problem:** Checking for room assignment for badge controllers

**Solution:** Remove room check for `controlleur_des_badges` role

### Issue 2: 404 error when scanning

**Problem:** Wrong URL path

**Solution:** Use `/api/participants/scan/` (not `/api/events/participants/scan/`)

### Issue 3: "No room assignment" error for room manager

**Problem:** Room manager not assigned to a room

**Solution:** Admin must assign room in backend, or show friendly error message

---

## 🎉 Summary

**What Works:**
- ✅ Badge controllers can scan anywhere
- ✅ Room managers manage specific rooms
- ✅ Participants attend events
- ✅ Automatic scan logging
- ✅ Real-time statistics

**What You Need to Do:**
1. Implement role-based navigation
2. Remove room check for badge controllers
3. Keep room check for room managers
4. Fix URL for badge scanning endpoint

**That's it!** The backend is fully deployed and working. Just implement the role-based logic and everything will work perfectly.

---

**Last Updated:** April 28, 2026  
**Backend Version:** 2.2  
**Status:** ✅ Complete and Ready
