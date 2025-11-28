# Backend-Frontend Integration Analysis

**Date:** November 25, 2025  
**Frontend:** Flutter (Dart)  
**Backend:** Django REST Framework  
**Status:** 🟡 Partial Integration - Needs Updates

---

## Current Integration Status

### ✅ What's Already Working

1. **Authentication System**
   - ✅ Login endpoint integrated (`POST /api/auth/login/`)
   - ✅ JWT token handling with refresh mechanism
   - ✅ Token storage (access & refresh tokens)
   - ✅ User model parsing (firstName, lastName, email, role)
   - ✅ Event data parsing from login response
   - ✅ Multi-role support (gestionnaire, controlleur, participant, exposant)

2. **API Client Infrastructure**
   - ✅ Dio HTTP client configured
   - ✅ JWT interceptor for automatic token attachment
   - ✅ Token refresh on 401 errors
   - ✅ Logging interceptor for debugging
   - ✅ Base URL configuration

3. **Data Models**
   - ✅ UserModel matches backend structure
   - ✅ EventModel matches backend structure
   - ✅ LoginResponse structure compatible

---

## ❌ Critical Issues & Required Changes

### 1. **Backend API Endpoint Mismatch**

**Problem:** Frontend expects `/api/auth/me/` but backend documentation doesn't list this endpoint.

**Frontend Code (django_auth_service.dart:185):**
```dart
final response = await _dio.get('/auth/me/');
```

**Backend Documentation:** Only lists `/api/auth/profile/`

**BACKEND FIX REQUIRED:**
```python
# In events/urls.py, add:
path('auth/me/', views.UserProfileView.as_view(), name='user-profile'),
# OR map /auth/me/ to the same view as /auth/profile/
```

**Alternative: Update Frontend:**
```dart
final response = await _dio.get('/auth/profile/');
```

---

### 2. **Missing Multi-Event Selection Flow**

**Backend Feature:** Multi-event support with event selection during login

**Backend Endpoints:**
- `POST /api/auth/select-event/` - Select event during login
- `POST /api/auth/switch-event/` - Switch between events  
- `GET /api/auth/my-events/` - List user's events

**Frontend Status:** ❌ Not implemented

**REQUIRED FRONTEND UPDATES:**

**Create Event Selection Service:**
```dart
// lib/data/services/event_service.dart
class EventService {
  final ApiClient _client;
  
  Future<List<EventModel>> getMyEvents() async {
    final response = await _client.get('/auth/my-events/');
    return (response.data as List)
        .map((e) => EventModel.fromJson(e))
        .toList();
  }
  
  Future<LoginResponse> selectEvent(String eventId) async {
    final response = await _client.post('/auth/select-event/', 
      data: {'event_id': eventId}
    );
    return LoginResponse.fromJson(response.data);
  }
  
  Future<LoginResponse> switchEvent(String eventId) async {
    final response = await _client.post('/auth/switch-event/', 
      data: {'event_id': eventId}
    );
    return LoginResponse.fromJson(response.data);
  }
}
```

**Create Event Selection Screen:**
```dart
// lib/presentation/screens/auth/event_selection_screen.dart
// Show list of user's events after successful login
// Let user select which event to access
```

---

### 3. **Session Management Endpoint Mismatch**

**Backend:**
- `POST /api/sessions/{id}/mark_live/` - Start session
- `POST /api/sessions/{id}/mark_completed/` - End session

**Frontend Expected (api_constants.dart:32-33):**
- `/sessions/{id}/start/`
- `/sessions/{id}/end/`

**BACKEND FIX REQUIRED:**
Add URL aliases or update views to support both endpoints:
```python
# events/urls.py
path('sessions/<uuid:pk>/start/', views.SessionViewSet.as_view({'post': 'mark_live'})),
path('sessions/<uuid:pk>/end/', views.SessionViewSet.as_view({'post': 'mark_completed'})),
```

---

### 4. **Missing Service Implementations**

**Backend Features Not Yet Integrated in Frontend:**

#### A. **Announcements (Annonces)**
**Backend:** `GET /api/annonces/` with auto-filtering by role

**REQUIRED:**
```dart
// lib/data/services/announcement_service.dart
class AnnouncementService {
  final ApiClient _client;
  
  Future<List<Announcement>> getAnnouncements({String? eventId}) async {
    final response = await _client.get('/annonces/', 
      queryParameters: {'event_id': eventId}
    );
    return (response.data as List)
        .map((e) => Announcement.fromJson(e))
        .toList();
  }
  
  Future<Announcement> createAnnouncement({
    required String eventId,
    required String title,
    required String description,
    required String target, // 'all', 'participants', 'exposants', etc.
  }) async {
    final response = await _client.post('/annonces/', data: {
      'event': eventId,
      'title': title,
      'description': description,
      'target': target,
    });
    return Announcement.fromJson(response.data);
  }
}
```

#### B. **Session Q&A System**
**Backend:** `GET /api/session-questions/`, `POST /api/session-questions/{id}/answer/`

**REQUIRED:**
```dart
// lib/data/services/question_service.dart
class QuestionService {
  final ApiClient _client;
  
  Future<List<SessionQuestion>> getQuestions(String sessionId) async {
    final response = await _client.get('/session-questions/',
      queryParameters: {'session_id': sessionId}
    );
    return (response.data as List)
        .map((e) => SessionQuestion.fromJson(e))
        .toList();
  }
  
  Future<SessionQuestion> askQuestion({
    required String sessionId,
    required String participantId,
    required String questionText,
  }) async {
    final response = await _client.post('/session-questions/', data: {
      'session': sessionId,
      'participant': participantId,
      'question_text': questionText,
    });
    return SessionQuestion.fromJson(response.data);
  }
  
  Future<SessionQuestion> answerQuestion({
    required String questionId,
    required String answerText,
  }) async {
    final response = await _client.post('/session-questions/$questionId/answer/', 
      data: {'answer_text': answerText}
    );
    return SessionQuestion.fromJson(response.data);
  }
}
```

#### C. **Exposant Scans (Booth Visit Tracking)**
**Backend:** `POST /api/exposant-scans/`, `GET /api/exposant-scans/my_scans/`

**REQUIRED:**
```dart
// lib/data/services/exposant_scan_service.dart
class ExposantScanService {
  final ApiClient _client;
  
  Future<ExposantScan> scanParticipant({
    required String exposantId,
    required String scannedParticipantId,
    required String eventId,
    String? notes,
  }) async {
    final response = await _client.post('/exposant-scans/', data: {
      'exposant': exposantId,
      'scanned_participant': scannedParticipantId,
      'event': eventId,
      'notes': notes,
    });
    return ExposantScan.fromJson(response.data);
  }
  
  Future<Map<String, dynamic>> getMyScans({required String eventId}) async {
    final response = await _client.get('/exposant-scans/my_scans/',
      queryParameters: {'event_id': eventId}
    );
    return {
      'total_visits': response.data['total_visits'],
      'today_visits': response.data['today_visits'],
      'scans': (response.data['scans'] as List)
          .map((e) => ExposantScan.fromJson(e))
          .toList(),
    };
  }
}
```

#### D. **Paid Ateliers (Session Access)**
**Backend:** `POST /api/session-access/`, `GET /api/session-access/`

**REQUIRED:**
```dart
// lib/data/services/session_access_service.dart
class SessionAccessService {
  final ApiClient _client;
  
  Future<bool> checkAccess({
    required String participantId,
    required String sessionId,
  }) async {
    final response = await _client.get('/session-access/',
      queryParameters: {
        'participant_id': participantId,
        'session_id': sessionId,
      }
    );
    
    if (response.data.isEmpty) return false;
    return response.data[0]['has_access'] == true;
  }
  
  Future<SessionAccess> grantAccess({
    required String participantId,
    required String sessionId,
    String paymentStatus = 'paid',
  }) async {
    final response = await _client.post('/session-access/', data: {
      'participant': participantId,
      'session': sessionId,
      'payment_status': paymentStatus,
      'has_access': true,
    });
    return SessionAccess.fromJson(response.data);
  }
}
```

#### E. **Room Assignments**
**Backend:** `GET /api/room-assignments/`, `POST /api/room-assignments/`

**REQUIRED:**
```dart
// lib/data/services/room_assignment_service.dart
class RoomAssignmentService {
  final ApiClient _client;
  
  Future<List<RoomAssignment>> getCurrentAssignments({
    required String eventId,
  }) async {
    final response = await _client.get('/room-assignments/',
      queryParameters: {
        'event_id': eventId,
        'current': 'true',
      }
    );
    return (response.data as List)
        .map((e) => RoomAssignment.fromJson(e))
        .toList();
  }
  
  Future<RoomAssignment> createAssignment({
    required String userId,
    required String roomId,
    required String eventId,
    required String role,
    required DateTime startTime,
    required DateTime endTime,
  }) async {
    final response = await _client.post('/room-assignments/', data: {
      'user': userId,
      'room': roomId,
      'event': eventId,
      'role': role,
      'start_time': startTime.toIso8601String(),
      'end_time': endTime.toIso8601String(),
    });
    return RoomAssignment.fromJson(response.data);
  }
}
```

---

### 5. **QR Code Integration**

**Backend:** `POST /api/qr/verify/`

**Current Frontend:** Has QR scanner UI but not connected to backend

**REQUIRED:**
```dart
// lib/data/services/qr_service.dart
class QRService {
  final ApiClient _client;
  
  Future<QRVerificationResult> verifyQRCode({
    required String qrData,
    String? roomId,
  }) async {
    final response = await _client.post('/qr/verify/', data: {
      'qr_data': qrData,
      'room_id': roomId,
    });
    
    return QRVerificationResult.fromJson(response.data);
  }
}

class QRVerificationResult {
  final bool valid;
  final Map<String, dynamic>? participant;
  final bool accessGranted;
  
  QRVerificationResult({
    required this.valid,
    this.participant,
    required this.accessGranted,
  });
  
  factory QRVerificationResult.fromJson(Map<String, dynamic> json) {
    return QRVerificationResult(
      valid: json['valid'] ?? false,
      participant: json['participant'],
      accessGranted: json['access_granted'] ?? false,
    );
  }
}
```

**Update Scanner Screens:**
```dart
// In exposant_scanner_screen.dart
void _onBarcodeDetect(BarcodeCapture capture) async {
  final barcode = capture.barcodes.first;
  if (barcode.rawValue != null) {
    try {
      final result = await QRService().verifyQRCode(
        qrData: barcode.rawValue!,
      );
      
      if (result.valid && result.participant != null) {
        // Navigate to participant info with real data
        Navigator.pushNamed(
          context,
          '/exposant/participant-info',
          arguments: result.participant,
        );
      } else {
        // Show error
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('QR Code invalide')),
        );
      }
    } catch (e) {
      // Handle error
    }
  }
}
```

---

### 6. **Session Status Management**

**Backend Statuses:**
- `pas_encore` - Not started
- `en_cours` - In progress (live)
- `termine` - Finished

**Frontend:** Currently using hardcoded mock data

**REQUIRED:**
```dart
// lib/data/services/session_service.dart
class SessionService {
  final ApiClient _client;
  
  Future<List<Session>> getSessions({
    String? roomId,
    String? eventId,
    String? status,
    String? sessionType,
  }) async {
    final queryParams = <String, dynamic>{};
    if (roomId != null) queryParams['room_id'] = roomId;
    if (eventId != null) queryParams['event_id'] = eventId;
    if (status != null) queryParams['status'] = status;
    if (sessionType != null) queryParams['session_type'] = sessionType;
    
    final response = await _client.get('/sessions/',
      queryParameters: queryParams,
    );
    
    return (response.data as List)
        .map((e) => Session.fromJson(e))
        .toList();
  }
  
  Future<Session> markSessionLive(String sessionId) async {
    final response = await _client.post('/sessions/$sessionId/mark_live/');
    return Session.fromJson(response.data);
  }
  
  Future<Session> markSessionCompleted(String sessionId) async {
    final response = await _client.post('/sessions/$sessionId/mark_completed/');
    return Session.fromJson(response.data);
  }
  
  Future<Session> cancelSession(String sessionId) async {
    final response = await _client.post('/sessions/$sessionId/cancel/');
    return Session.fromJson(response.data);
  }
}
```

---

## 🔧 Required Backend Modifications

### 1. **Add URL Aliases for Frontend Compatibility**

**File:** `makeplus_api/events/urls.py`

```python
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
# ... existing routes ...

urlpatterns = [
    path('', include(router.urls)),
    
    # ADD THESE ALIASES FOR FRONTEND COMPATIBILITY:
    
    # User profile endpoint (frontend expects /auth/me/)
    path('auth/me/', views.UserProfileView.as_view(), name='user-me'),
    
    # Session action aliases
    path('sessions/<uuid:pk>/start/', 
         views.SessionViewSet.as_view({'post': 'mark_live'}), 
         name='session-start'),
    path('sessions/<uuid:pk>/end/', 
         views.SessionViewSet.as_view({'post': 'mark_completed'}), 
         name='session-end'),
]
```

### 2. **Add User Profile View**

**File:** `makeplus_api/events/views.py`

```python
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        # Get user's current event assignment
        try:
            assignment = UserEventAssignment.objects.get(
                user=user,
                is_active=True
            )
            event_data = EventSerializer(assignment.event).data
            role = assignment.role
        except UserEventAssignment.DoesNotExist:
            event_data = None
            role = 'participant'
        
        return Response({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'role': role,
            'event': event_data,
        })
```

### 3. **Update CORS Settings**

**File:** `makeplus_api/makeplus_api/settings.py`

```python
# Add your Flutter app's URL to CORS allowed origins
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:8080",
    # Add your production URLs
]

# Allow credentials for JWT
CORS_ALLOW_CREDENTIALS = True

# Allow these headers
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]
```

---

## 📋 Required Frontend Data Models

Create these models to match backend responses:

### 1. **Announcement Model**
```dart
// lib/data/models/announcement_model.dart
class Announcement {
  final String id;
  final String eventId;
  final String title;
  final String description;
  final String target;
  final int createdBy;
  final DateTime createdAt;
  final DateTime updatedAt;
  
  Announcement({
    required this.id,
    required this.eventId,
    required this.title,
    required this.description,
    required this.target,
    required this.createdBy,
    required this.createdAt,
    required this.updatedAt,
  });
  
  factory Announcement.fromJson(Map<String, dynamic> json) {
    return Announcement(
      id: json['id'],
      eventId: json['event'],
      title: json['title'],
      description: json['description'],
      target: json['target'],
      createdBy: json['created_by'],
      createdAt: DateTime.parse(json['created_at']),
      updatedAt: DateTime.parse(json['updated_at']),
    );
  }
}
```

### 2. **Session Question Model**
```dart
// lib/data/models/session_question_model.dart
class SessionQuestion {
  final String id;
  final String sessionId;
  final String participantId;
  final String questionText;
  final DateTime askedAt;
  final bool isAnswered;
  final String? answerText;
  final int? answeredBy;
  final DateTime? answeredAt;
  
  SessionQuestion({
    required this.id,
    required this.sessionId,
    required this.participantId,
    required this.questionText,
    required this.askedAt,
    required this.isAnswered,
    this.answerText,
    this.answeredBy,
    this.answeredAt,
  });
  
  factory SessionQuestion.fromJson(Map<String, dynamic> json) {
    return SessionQuestion(
      id: json['id'],
      sessionId: json['session'],
      participantId: json['participant'],
      questionText: json['question_text'],
      askedAt: DateTime.parse(json['asked_at']),
      isAnswered: json['is_answered'] ?? false,
      answerText: json['answer_text'],
      answeredBy: json['answered_by'],
      answeredAt: json['answered_at'] != null 
          ? DateTime.parse(json['answered_at']) 
          : null,
    );
  }
}
```

### 3. **Exposant Scan Model**
```dart
// lib/data/models/exposant_scan_model.dart
class ExposantScan {
  final String id;
  final String exposantId;
  final String scannedParticipantId;
  final String eventId;
  final DateTime scannedAt;
  final String? notes;
  
  ExposantScan({
    required this.id,
    required this.exposantId,
    required this.scannedParticipantId,
    required this.eventId,
    required this.scannedAt,
    this.notes,
  });
  
  factory ExposantScan.fromJson(Map<String, dynamic> json) {
    return ExposantScan(
      id: json['id'],
      exposantId: json['exposant'],
      scannedParticipantId: json['scanned_participant'],
      eventId: json['event'],
      scannedAt: DateTime.parse(json['scanned_at']),
      notes: json['notes'],
    );
  }
}
```

### 4. **Session Model** (Update existing)
```dart
// lib/data/models/session_model.dart
class Session {
  final String id;
  final String eventId;
  final String roomId;
  final String title;
  final String description;
  final String speakerName;
  final String speakerTitle;
  final DateTime startTime;
  final DateTime endTime;
  final String theme;
  final String status; // 'pas_encore', 'en_cours', 'termine'
  final String sessionType; // 'conference', 'atelier'
  final bool isPaid;
  final double? price;
  final String? youtubeLiveUrl;
  
  Session({
    required this.id,
    required this.eventId,
    required this.roomId,
    required this.title,
    required this.description,
    required this.speakerName,
    required this.speakerTitle,
    required this.startTime,
    required this.endTime,
    required this.theme,
    required this.status,
    required this.sessionType,
    required this.isPaid,
    this.price,
    this.youtubeLiveUrl,
  });
  
  factory Session.fromJson(Map<String, dynamic> json) {
    return Session(
      id: json['id'],
      eventId: json['event'],
      roomId: json['room'],
      title: json['title'],
      description: json['description'],
      speakerName: json['speaker_name'],
      speakerTitle: json['speaker_title'],
      startTime: DateTime.parse(json['start_time']),
      endTime: DateTime.parse(json['end_time']),
      theme: json['theme'],
      status: json['status'],
      sessionType: json['session_type'],
      isPaid: json['is_paid'],
      price: json['price'] != null ? double.parse(json['price'].toString()) : null,
      youtubeLiveUrl: json['youtube_live_url'],
    );
  }
}
```

---

## 🎯 Priority Implementation Order

### Phase 1: Critical Fixes (Week 1)
1. ✅ Fix `/auth/me/` endpoint in backend
2. ✅ Add session start/end URL aliases
3. ✅ Test login/logout flow end-to-end
4. ✅ Implement event selection flow

### Phase 2: Core Features (Week 2)
1. ✅ Integrate announcements system
2. ✅ Connect QR scanner to backend
3. ✅ Implement exposant scan tracking
4. ✅ Add session status management

### Phase 3: Advanced Features (Week 3)
1. ✅ Implement Session Q&A
2. ✅ Add paid atelier access control
3. ✅ Implement room assignments
4. ✅ Add file uploads (PDFs)

### Phase 4: Polish & Testing (Week 4)
1. ✅ Error handling improvements
2. ✅ Offline support with caching
3. ✅ Performance optimization
4. ✅ End-to-end testing

---

## 📝 Testing Checklist

### Backend Testing
- [ ] Test `/auth/me/` endpoint returns user with role
- [ ] Test event selection flow
- [ ] Test announcement filtering by role
- [ ] Test QR code verification
- [ ] Test exposant scan creation
- [ ] Test session status transitions
- [ ] Test paid atelier access control

### Frontend Testing
- [ ] Login with all 4 roles (gestionnaire, controlleur, participant, exposant)
- [ ] Event selection after login
- [ ] Switch between events
- [ ] Scan QR codes
- [ ] Create announcements
- [ ] Ask/answer questions
- [ ] Track booth visits (exposant)
- [ ] Mark sessions live/completed (gestionnaire)

---

## 🚀 Next Steps

1. **Immediate Actions:**
   - Add `/auth/me/` endpoint to backend
   - Add session URL aliases
   - Test current login flow

2. **Short Term (This Week):**
   - Implement event selection screen
   - Create announcement service
   - Connect QR scanner

3. **Medium Term (Next 2 Weeks):**
   - Complete all missing services
   - Add all data models
   - Integrate real-time features

4. **Long Term (Next Month):**
   - Add offline support
   - Implement push notifications
   - Add analytics

---

## 📞 Support

For questions or issues:
- Backend Repo: makeplus-Django (main branch)
- Frontend Repo: makeplus-flutter (develop branch)
- Owner: DjalilElz

---

**End of Analysis**
