# Paid Sessions - Mobile App Implementation

## Overview
Some sessions (workshops/ateliers) require payment. The mobile app needs to handle this.

---

## 📋 What Mobile App Needs to Do

### 1. Display Paid Sessions
Show sessions with payment indicator:
```dart
// Session object includes:
{
  "id": "session-uuid",
  "title": "Advanced Workshop",
  "is_paid": true,        // ← Check this
  "price": 50.00,         // ← Show this
  "max_participants": 30  // ← Limited capacity
}
```

### 2. Check User Access
Before allowing user to enter a paid session:

**Step 1: Get participant ID**
```
GET /api/participants/?event={event_id}&user={user_id}
```

**Step 2: Check session access**
```
GET /api/session-access/?participant={participant_id}&session={session_id}
```

**Step 3: Verify response**
```json
// Has access ✅
{
  "count": 1,
  "results": [{
    "has_access": true,
    "payment_status": "paid",
    "amount_paid": 50.00
  }]
}

// No access ❌
{
  "count": 0,
  "results": []
}
```

---

## 🔑 Payment Status Values

- **`pending`** - User registered but hasn't paid yet (no access)
- **`paid`** - User has paid and has access ✅
- **`free`** - Free session, everyone has access ✅

---

## 💻 Implementation Example

```dart
class Session {
  final String id;
  final String title;
  final bool isPaid;
  final double? price;
  final int? maxParticipants;
}

class SessionAccess {
  final String id;
  final String sessionId;
  final bool hasAccess;
  final String paymentStatus; // 'pending', 'paid', 'free'
  final double amountPaid;
}

// Check if user can access session
bool canAccessSession(Session session, List<SessionAccess> userAccess) {
  // Free sessions - everyone can access
  if (!session.isPaid) {
    return true;
  }
  
  // Paid sessions - check if user has paid
  final access = userAccess.firstWhere(
    (a) => a.sessionId == session.id,
    orElse: () => null,
  );
  
  return access != null && 
         access.hasAccess && 
         access.paymentStatus == 'paid';
}

// Display session card
Widget buildSessionCard(Session session, bool hasAccess) {
  return Card(
    child: Column(
      children: [
        Text(session.title),
        
        // Show paid indicator
        if (session.isPaid) ...[
          Chip(
            label: Text('Paid - ${session.price}€'),
            backgroundColor: Colors.orange,
          ),
          
          // Show access status
          if (!hasAccess) 
            Container(
              padding: EdgeInsets.all(8),
              color: Colors.red[100],
              child: Row(
                children: [
                  Icon(Icons.lock, color: Colors.red),
                  SizedBox(width: 8),
                  Text(
                    'Payment required',
                    style: TextStyle(color: Colors.red),
                  ),
                ],
              ),
            ),
        ],
        
        // Show capacity if limited
        if (session.maxParticipants != null)
          Text('Max: ${session.maxParticipants} participants'),
      ],
    ),
  );
}

// Load user's session access
Future<List<SessionAccess>> loadUserSessionAccess(String participantId) async {
  final response = await http.get(
    Uri.parse('$baseUrl/api/session-access/?participant=$participantId'),
    headers: {'Authorization': 'Bearer $accessToken'},
  );
  
  if (response.statusCode == 200) {
    final data = jsonDecode(response.body);
    return (data['results'] as List)
        .map((json) => SessionAccess.fromJson(json))
        .toList();
  }
  
  return [];
}
```

---

## 🎯 User Flow

### For Participants:
1. Browse sessions
2. See which sessions are paid (with price)
3. See which sessions they have access to
4. Can only enter sessions they have access to

### For Controllers:
1. Scan participant QR code
2. Select session
3. System checks if participant has access
4. Allow/deny entry based on access

---

## 📱 UI Recommendations

### Session List Screen:
```
┌─────────────────────────────────┐
│ AI in Healthcare                │
│ 2:00 PM - 3:30 PM              │
│ Main Hall A                     │
│ [FREE] Conference               │
└─────────────────────────────────┘

┌─────────────────────────────────┐
│ Advanced Workshop               │
│ 3:00 PM - 5:00 PM              │
│ Workshop Room B                 │
│ [PAID - 50€] Atelier           │
│ 🔒 Payment required             │ ← Show if no access
└─────────────────────────────────┘

┌─────────────────────────────────┐
│ Python Masterclass              │
│ 5:30 PM - 7:30 PM              │
│ Workshop Room A                 │
│ [PAID - 75€] Atelier           │
│ ✅ Access granted               │ ← Show if has access
└─────────────────────────────────┘
```

### Session Detail Screen:
```
┌─────────────────────────────────┐
│ Advanced Workshop               │
│                                 │
│ 📅 June 15, 2026               │
│ 🕐 3:00 PM - 5:00 PM           │
│ 📍 Workshop Room B             │
│                                 │
│ 💰 Price: 50€                  │
│ 👥 Max: 30 participants        │
│                                 │
│ ❌ You don't have access       │
│                                 │
│ [Contact Admin to Register]    │
└─────────────────────────────────┘
```

---

## ⚠️ Important Notes

1. **Payment Processing**: Payment is NOT done in the mobile app. It's handled by:
   - Admin dashboard
   - External payment system
   - Event organizers

2. **Mobile App Role**: Only check if user has access, don't process payments

3. **Access Control**: Controllers must verify access before allowing entry to paid sessions

4. **Session Types**: 
   - `conference` - Usually free
   - `atelier` / `workshop` - Can be paid
   - `panel` / `keynote` - Usually free

5. **Capacity Limits**: Some paid sessions have `max_participants` - show this to users

---

## 🔗 API Endpoints

### Get All Sessions (with paid info)
```
GET /api/sessions/
```

### Get User's Session Access
```
GET /api/session-access/?participant={participant_id}
```

### Check Specific Session Access
```
GET /api/session-access/?participant={participant_id}&session={session_id}
```

---

## ✅ Checklist for Mobile Developer

- [ ] Display `is_paid` indicator on session cards
- [ ] Show `price` for paid sessions
- [ ] Load user's session access on app start
- [ ] Check access before allowing session entry
- [ ] Show payment status (pending/paid/free)
- [ ] Display "Payment required" message for inaccessible paid sessions
- [ ] Show `max_participants` if limited capacity
- [ ] Handle case where user has no access to paid session
- [ ] Test with both free and paid sessions
- [ ] Test with different payment statuses

---

## 📚 Full Documentation

See `MOBILE_APP_API_SPECIFICATION.md` for complete API documentation including:
- All 24 endpoints
- Request/response examples
- Authentication flow
- Error handling
