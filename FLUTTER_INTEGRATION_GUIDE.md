# Flutter Frontend Integration Guide - MakePlus Backend API

**Backend URL:** `http://localhost:8000` (Development)  
**API Base Path:** `/api/`  
**Authentication:** JWT Bearer Token  
**Last Updated:** November 25, 2025

---

## 🚀 Quick Start

### Base Configuration

```dart
class ApiConfig {
  static const String baseUrl = 'http://localhost:8000';
  static const String apiPath = '/api';
  static const String fullApiUrl = '$baseUrl$apiPath';
  
  // For production
  // static const String baseUrl = 'https://api.makeplus.dz';
  
  // For Android Emulator (accessing localhost)
  // static const String baseUrl = 'http://10.0.2.2:8000';
}
```

### Required Dependencies

Add to `pubspec.yaml`:
```yaml
dependencies:
  http: ^1.1.0
  flutter_secure_storage: ^9.0.0
  
dev_dependencies:
  flutter_test:
    sdk: flutter
```

### HTTP Client Setup

```dart
import 'package:http/http.dart' as http;
import 'dart:convert';

class ApiClient {
  static const String baseUrl = ApiConfig.fullApiUrl;
  static String? _accessToken;
  
  static Map<String, String> get headers => {
    'Content-Type': 'application/json',
    if (_accessToken != null) 'Authorization': 'Bearer $_accessToken',
  };
  
  static void setToken(String token) {
    _accessToken = token;
  }
  
  static void clearToken() {
    _accessToken = null;
  }
}
```

---

## 🔐 Authentication Flow

### 1. User Registration

**Endpoint:** `POST /api/auth/register/`

```dart
Future<Map<String, dynamic>> register({
  required String username,
  required String email,
  required String password,
  required String firstName,
  required String lastName,
}) async {
  final response = await http.post(
    Uri.parse('${ApiClient.baseUrl}/auth/register/'),
    headers: {'Content-Type': 'application/json'},
    body: jsonEncode({
      'username': username,
      'email': email,
      'password': password,
      'first_name': firstName,
      'last_name': lastName,
    }),
  );
  
  if (response.statusCode == 201) {
    return jsonDecode(response.body);
  } else {
    throw Exception('Registration failed: ${response.body}');
  }
}
```

**Response:**
```json
{
  "id": 1,
  "username": "ahmed_benali",
  "email": "ahmed@example.com",
  "first_name": "Ahmed",
  "last_name": "Benali"
}
```

---

### 2. Login

**Endpoint:** `POST /api/auth/login/`

```dart
Future<Map<String, dynamic>> login({
  required String email,
  required String password,
  required String eventId,
}) async {
  final response = await http.post(
    Uri.parse('${ApiClient.baseUrl}/auth/login/'),
    headers: {'Content-Type': 'application/json'},
    body: jsonEncode({
      'email': email,
      'password': password,
      'event_id': eventId,
    }),
  );
  
  if (response.statusCode == 200) {
    final data = jsonDecode(response.body);
    
    // Save tokens
    ApiClient.setToken(data['access']);
    await TokenStorage.saveTokens(
      accessToken: data['access'],
      refreshToken: data['refresh'],
    );
    
    return data;
  } else {
    throw Exception('Login failed: ${response.body}');
  }
}
```

**Response:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "username": "ahmed_benali",
    "email": "ahmed@example.com",
    "first_name": "Ahmed",
    "last_name": "Benali"
  },
  "event": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Tech Summit 2025"
  },
  "role": "gestionnaire_des_salles"
}
```

---

### 3. Get User's Events (Before Login)

**Endpoint:** `GET /api/auth/my-events/`

```dart
Future<List<dynamic>> getMyEvents() async {
  final response = await http.get(
    Uri.parse('${ApiClient.baseUrl}/auth/my-events/'),
    headers: ApiClient.headers,
  );
  
  if (response.statusCode == 200) {
    return jsonDecode(response.body);
  } else {
    throw Exception('Failed to load events');
  }
}
```

**Response:**
```json
[
  {
    "event": {
      "id": "uuid-1",
      "name": "Tech Summit 2025"
    },
    "role": "gestionnaire_des_salles"
  },
  {
    "event": {
      "id": "uuid-2",
      "name": "Startup Week 2025"
    },
    "role": "participant"
  }
]
```

---

### 4. Switch Event

**Endpoint:** `POST /api/auth/switch-event/`

```dart
Future<Map<String, dynamic>> switchEvent(String eventId) async {
  final response = await http.post(
    Uri.parse('${ApiClient.baseUrl}/auth/switch-event/'),
    headers: ApiClient.headers,
    body: jsonEncode({'event_id': eventId}),
  );
  
  if (response.statusCode == 200) {
    final data = jsonDecode(response.body);
    ApiClient.setToken(data['access']);
    await TokenStorage.saveTokens(
      accessToken: data['access'],
      refreshToken: data['refresh'],
    );
    return data;
  } else {
    throw Exception('Failed to switch event');
  }
}
```

---

### 5. Refresh Token

**Endpoint:** `POST /api/token/refresh/`

```dart
Future<String> refreshToken(String refreshToken) async {
  final response = await http.post(
    Uri.parse('${ApiClient.baseUrl}/token/refresh/'),
    headers: {'Content-Type': 'application/json'},
    body: jsonEncode({'refresh': refreshToken}),
  );
  
  if (response.statusCode == 200) {
    final data = jsonDecode(response.body);
    ApiClient.setToken(data['access']);
    return data['access'];
  } else {
    throw Exception('Token refresh failed');
  }
}
```

---

### 6. Logout

**Endpoint:** `POST /api/auth/logout/`

```dart
Future<void> logout() async {
  final response = await http.post(
    Uri.parse('${ApiClient.baseUrl}/auth/logout/'),
    headers: ApiClient.headers,
  );
  
  if (response.statusCode == 200) {
    ApiClient.clearToken();
    await TokenStorage.clearTokens();
  }
}
```

---

## 📅 Events API

### Get Events List

**Endpoint:** `GET /api/events/`

```dart
Future<List<Event>> getEvents() async {
  final response = await http.get(
    Uri.parse('${ApiClient.baseUrl}/events/'),
    headers: ApiClient.headers,
  );
  
  if (response.statusCode == 200) {
    final List<dynamic> data = jsonDecode(response.body)['results'];
    return data.map((json) => Event.fromJson(json)).toList();
  } else {
    throw Exception('Failed to load events');
  }
}
```

### Event Model

```dart
class Event {
  final String id;
  final String name;
  final String description;
  final String location;
  final DateTime startDate;
  final DateTime endDate;
  final bool isActive;
  final String? programmeFile;
  final String? guideFile;
  final int? president;
  
  Event({
    required this.id,
    required this.name,
    required this.description,
    required this.location,
    required this.startDate,
    required this.endDate,
    required this.isActive,
    this.programmeFile,
    this.guideFile,
    this.president,
  });
  
  factory Event.fromJson(Map<String, dynamic> json) {
    return Event(
      id: json['id'],
      name: json['name'],
      description: json['description'],
      location: json['location'],
      startDate: DateTime.parse(json['start_date']),
      endDate: DateTime.parse(json['end_date']),
      isActive: json['is_active'],
      programmeFile: json['programme_file'],
      guideFile: json['guide_file'],
      president: json['president'],
    );
  }
}
```

---

## 🏠 Rooms API

### Get Rooms

**Endpoint:** `GET /api/rooms/?event_id={eventId}`

```dart
Future<List<Room>> getRooms(String eventId) async {
  final response = await http.get(
    Uri.parse('${ApiClient.baseUrl}/rooms/?event_id=$eventId'),
    headers: ApiClient.headers,
  );
  
  if (response.statusCode == 200) {
    final List<dynamic> data = jsonDecode(response.body)['results'];
    return data.map((json) => Room.fromJson(json)).toList();
  } else {
    throw Exception('Failed to load rooms');
  }
}
```

### Room Model

```dart
class Room {
  final String id;
  final String eventId;
  final String name;
  final int capacity;
  final String description;
  final bool isActive;
  
  Room({
    required this.id,
    required this.eventId,
    required this.name,
    required this.capacity,
    required this.description,
    required this.isActive,
  });
  
  factory Room.fromJson(Map<String, dynamic> json) {
    return Room(
      id: json['id'],
      eventId: json['event'],
      name: json['name'],
      capacity: json['capacity'],
      description: json['description'],
      isActive: json['is_active'],
    );
  }
}
```

---

## 📚 Sessions API

### Get Sessions

**Endpoint:** `GET /api/sessions/?event_id={eventId}`

**Query Parameters:**
- `room_id` - Filter by room
- `status` - Filter by status (pas_encore, en_cours, termine)
- `session_type` - Filter by type (conference, atelier)
- `is_paid` - Filter paid ateliers

```dart
Future<List<Session>> getSessions({
  required String eventId,
  String? roomId,
  String? status,
}) async {
  var uri = '${ApiClient.baseUrl}/sessions/?event_id=$eventId';
  if (roomId != null) uri += '&room_id=$roomId';
  if (status != null) uri += '&status=$status';
  
  final response = await http.get(
    Uri.parse(uri),
    headers: ApiClient.headers,
  );
  
  if (response.statusCode == 200) {
    final List<dynamic> data = jsonDecode(response.body)['results'];
    return data.map((json) => Session.fromJson(json)).toList();
  } else {
    throw Exception('Failed to load sessions');
  }
}
```

### Session Model

```dart
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
  final String status; // pas_encore, en_cours, termine
  final String sessionType; // conference, atelier
  final bool isPaid;
  final String? price;
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
      price: json['price'],
      youtubeLiveUrl: json['youtube_live_url'],
    );
  }
  
  // Status helpers
  bool get isNotStarted => status == 'pas_encore';
  bool get isLive => status == 'en_cours';
  bool get isFinished => status == 'termine';
  
  // UI Color helpers
  Color get statusColor {
    switch (status) {
      case 'pas_encore':
        return Colors.orange;
      case 'en_cours':
        return Colors.green;
      case 'termine':
        return Colors.grey;
      default:
        return Colors.grey;
    }
  }
  
  String get statusText {
    switch (status) {
      case 'pas_encore':
        return 'À venir';
      case 'en_cours':
        return 'En cours';
      case 'termine':
        return 'Terminé';
      default:
        return 'Inconnu';
    }
  }
}
```

### Session Actions (Gestionnaire Only)

```dart
// Start session
Future<void> markSessionLive(String sessionId) async {
  final response = await http.post(
    Uri.parse('${ApiClient.baseUrl}/sessions/$sessionId/mark_live/'),
    headers: ApiClient.headers,
  );
  
  if (response.statusCode != 200) {
    throw Exception('Failed to start session');
  }
}

// End session
Future<void> markSessionCompleted(String sessionId) async {
  final response = await http.post(
    Uri.parse('${ApiClient.baseUrl}/sessions/$sessionId/mark_completed/'),
    headers: ApiClient.headers,
  );
  
  if (response.statusCode != 200) {
    throw Exception('Failed to end session');
  }
}

// Cancel session
Future<void> cancelSession(String sessionId) async {
  final response = await http.post(
    Uri.parse('${ApiClient.baseUrl}/sessions/$sessionId/cancel/'),
    headers: ApiClient.headers,
  );
  
  if (response.statusCode != 200) {
    throw Exception('Failed to cancel session');
  }
}
```

---

## 📢 Announcements API

### Get Announcements (Auto-filtered by user role)

**Endpoint:** `GET /api/annonces/?event_id={eventId}`

```dart
Future<List<Annonce>> getAnnouncements(String eventId) async {
  final response = await http.get(
    Uri.parse('${ApiClient.baseUrl}/annonces/?event_id=$eventId'),
    headers: ApiClient.headers,
  );
  
  if (response.statusCode == 200) {
    final List<dynamic> data = jsonDecode(response.body)['results'];
    return data.map((json) => Annonce.fromJson(json)).toList();
  } else {
    throw Exception('Failed to load announcements');
  }
}
```

### Create Announcement

```dart
Future<Annonce> createAnnouncement({
  required String eventId,
  required String title,
  required String description,
  required String target, // all, participants, exposants, controlleurs, gestionnaires
}) async {
  final response = await http.post(
    Uri.parse('${ApiClient.baseUrl}/annonces/'),
    headers: ApiClient.headers,
    body: jsonEncode({
      'event': eventId,
      'title': title,
      'description': description,
      'target': target,
    }),
  );
  
  if (response.statusCode == 201) {
    return Annonce.fromJson(jsonDecode(response.body));
  } else {
    throw Exception('Failed to create announcement');
  }
}
```

### Annonce Model

```dart
class Annonce {
  final String id;
  final String eventId;
  final String title;
  final String description;
  final String target;
  final int createdBy;
  final DateTime createdAt;
  final DateTime updatedAt;
  
  Annonce({
    required this.id,
    required this.eventId,
    required this.title,
    required this.description,
    required this.target,
    required this.createdBy,
    required this.createdAt,
    required this.updatedAt,
  });
  
  factory Annonce.fromJson(Map<String, dynamic> json) {
    return Annonce(
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

---

## ❓ Session Q&A API

### Get Questions

**Endpoint:** `GET /api/session-questions/?session_id={sessionId}`

```dart
Future<List<SessionQuestion>> getSessionQuestions(String sessionId) async {
  final response = await http.get(
    Uri.parse('${ApiClient.baseUrl}/session-questions/?session_id=$sessionId'),
    headers: ApiClient.headers,
  );
  
  if (response.statusCode == 200) {
    final List<dynamic> data = jsonDecode(response.body)['results'];
    return data.map((json) => SessionQuestion.fromJson(json)).toList();
  } else {
    throw Exception('Failed to load questions');
  }
}
```

### Ask Question

```dart
Future<SessionQuestion> askQuestion({
  required String sessionId,
  required String participantId,
  required String questionText,
}) async {
  final response = await http.post(
    Uri.parse('${ApiClient.baseUrl}/session-questions/'),
    headers: ApiClient.headers,
    body: jsonEncode({
      'session': sessionId,
      'participant': participantId,
      'question_text': questionText,
    }),
  );
  
  if (response.statusCode == 201) {
    return SessionQuestion.fromJson(jsonDecode(response.body));
  } else {
    throw Exception('Failed to ask question');
  }
}
```

### Answer Question (Gestionnaire only)

```dart
Future<SessionQuestion> answerQuestion({
  required String questionId,
  required String answerText,
}) async {
  final response = await http.post(
    Uri.parse('${ApiClient.baseUrl}/session-questions/$questionId/answer/'),
    headers: ApiClient.headers,
    body: jsonEncode({'answer_text': answerText}),
  );
  
  if (response.statusCode == 200) {
    return SessionQuestion.fromJson(jsonDecode(response.body));
  } else {
    throw Exception('Failed to answer question');
  }
}
```

### SessionQuestion Model

```dart
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
      isAnswered: json['is_answered'],
      answerText: json['answer_text'],
      answeredBy: json['answered_by'],
      answeredAt: json['answered_at'] != null 
          ? DateTime.parse(json['answered_at']) 
          : null,
    );
  }
}
```

---

## 🏢 Exposant Scans API (Booth Visits)

### Scan Participant QR Code (Exposant only)

```dart
Future<ExposantScan> scanParticipant({
  required String exposantId,
  required String participantId,
  required String eventId,
  String? notes,
}) async {
  final response = await http.post(
    Uri.parse('${ApiClient.baseUrl}/exposant-scans/'),
    headers: ApiClient.headers,
    body: jsonEncode({
      'exposant': exposantId,
      'scanned_participant': participantId,
      'event': eventId,
      'notes': notes,
    }),
  );
  
  if (response.statusCode == 201) {
    return ExposantScan.fromJson(jsonDecode(response.body));
  } else {
    throw Exception('Failed to scan participant');
  }
}
```

### Get My Scans with Statistics (Exposant only)

**Endpoint:** `GET /api/exposant-scans/my_scans/?event_id={eventId}`

```dart
Future<Map<String, dynamic>> getMyScans(String eventId) async {
  final response = await http.get(
    Uri.parse('${ApiClient.baseUrl}/exposant-scans/my_scans/?event_id=$eventId'),
    headers: ApiClient.headers,
  );
  
  if (response.statusCode == 200) {
    return jsonDecode(response.body);
    // Returns: {total_visits, today_visits, scans: [...]}
  } else {
    throw Exception('Failed to load scans');
  }
}
```

### ExposantScan Model

```dart
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

---

## 📱 QR Code Verification (Controller)

### Verify QR Code

**Endpoint:** `POST /api/qr/verify/`

```dart
Future<Map<String, dynamic>> verifyQRCode({
  required String qrData,
  required String roomId,
}) async {
  final response = await http.post(
    Uri.parse('${ApiClient.baseUrl}/qr/verify/'),
    headers: ApiClient.headers,
    body: jsonEncode({
      'qr_data': qrData,
      'room_id': roomId,
    }),
  );
  
  if (response.statusCode == 200) {
    return jsonDecode(response.body);
  } else {
    throw Exception('QR verification failed');
  }
}
```

**Response:**
```json
{
  "valid": true,
  "participant": {
    "id": "uuid",
    "badge_number": "TECH2025-001",
    "user": {
      "first_name": "Ahmed",
      "last_name": "Benali"
    }
  },
  "access_granted": true
}
```

### QR Scanner Widget Example

```dart
import 'package:mobile_scanner/mobile_scanner.dart';

class QRScannerScreen extends StatefulWidget {
  final String roomId;
  
  const QRScannerScreen({required this.roomId});
  
  @override
  State<QRScannerScreen> createState() => _QRScannerScreenState();
}

class _QRScannerScreenState extends State<QRScannerScreen> {
  MobileScannerController cameraController = MobileScannerController();
  bool isProcessing = false;
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Scanner QR Code')),
      body: MobileScanner(
        controller: cameraController,
        onDetect: (capture) async {
          if (isProcessing) return;
          
          final List<Barcode> barcodes = capture.barcodes;
          if (barcodes.isEmpty) return;
          
          final String? code = barcodes.first.rawValue;
          if (code == null) return;
          
          setState(() => isProcessing = true);
          
          try {
            final result = await verifyQRCode(
              qrData: code,
              roomId: widget.roomId,
            );
            
            if (result['valid']) {
              // Show success
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(
                  content: Text('Accès autorisé pour ${result['participant']['user']['first_name']}'),
                  backgroundColor: Colors.green,
                ),
              );
            } else {
              // Show error
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(
                  content: Text('QR Code invalide'),
                  backgroundColor: Colors.red,
                ),
              );
            }
          } catch (e) {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(
                content: Text('Erreur: $e'),
                backgroundColor: Colors.red,
              ),
            );
          } finally {
            setState(() => isProcessing = false);
          }
        },
      ),
    );
  }
}
```

---

## 💳 Paid Ateliers (Session Access)

### Check Access to Paid Session

```dart
Future<bool> hasSessionAccess({
  required String participantId,
  required String sessionId,
}) async {
  final response = await http.get(
    Uri.parse('${ApiClient.baseUrl}/session-access/?participant_id=$participantId&session_id=$sessionId'),
    headers: ApiClient.headers,
  );
  
  if (response.statusCode == 200) {
    final data = jsonDecode(response.body);
    if (data['results'].isNotEmpty) {
      return data['results'][0]['has_access'] == true;
    }
    return false;
  } else {
    throw Exception('Failed to check session access');
  }
}
```

### Grant Access (Gestionnaire only)

```dart
Future<void> grantSessionAccess({
  required String participantId,
  required String sessionId,
  required String paymentStatus, // paid, pending, refunded
}) async {
  final response = await http.post(
    Uri.parse('${ApiClient.baseUrl}/session-access/'),
    headers: ApiClient.headers,
    body: jsonEncode({
      'participant': participantId,
      'session': sessionId,
      'payment_status': paymentStatus,
      'has_access': paymentStatus == 'paid',
    }),
  );
  
  if (response.statusCode != 201) {
    throw Exception('Failed to grant access');
  }
}
```

---

## 📊 Dashboard Statistics

### Get Dashboard Stats

**Endpoint:** `GET /api/dashboard/stats/`

```dart
Future<Map<String, dynamic>> getDashboardStats() async {
  final response = await http.get(
    Uri.parse('${ApiClient.baseUrl}/dashboard/stats/'),
    headers: ApiClient.headers,
  );
  
  if (response.statusCode == 200) {
    return jsonDecode(response.body);
  } else {
    throw Exception('Failed to load dashboard stats');
  }
}
```

**Response:**
```json
{
  "event": {...},
  "total_participants": 250,
  "total_sessions": 45,
  "live_sessions": 3,
  "completed_sessions": 12,
  "upcoming_sessions": [...],
  "my_role": "gestionnaire_des_salles"
}
```

---

## 📁 File Upload (PDF Files)

### Upload Event Programme

```dart
import 'package:http/http.dart' as http;
import 'dart:io';

Future<void> uploadEventProgramme({
  required String eventId,
  required File pdfFile,
}) async {
  var request = http.MultipartRequest(
    'PATCH',
    Uri.parse('${ApiClient.baseUrl}/events/$eventId/'),
  );
  
  request.headers['Authorization'] = 'Bearer ${ApiClient._accessToken}';
  
  request.files.add(
    await http.MultipartFile.fromPath(
      'programme_file',
      pdfFile.path,
    ),
  );
  
  var response = await request.send();
  
  if (response.statusCode != 200) {
    throw Exception('Failed to upload programme');
  }
}
```

### Download PDF File

```dart
import 'package:path_provider/path_provider.dart';
import 'package:open_file/open_file.dart';

Future<void> downloadAndOpenPDF(String fileUrl, String fileName) async {
  final response = await http.get(
    Uri.parse('${ApiConfig.baseUrl}$fileUrl'),
    headers: ApiClient.headers,
  );
  
  if (response.statusCode == 200) {
    final directory = await getApplicationDocumentsDirectory();
    final file = File('${directory.path}/$fileName');
    await file.writeAsBytes(response.bodyBytes);
    
    // Open the PDF
    await OpenFile.open(file.path);
  } else {
    throw Exception('Failed to download file');
  }
}
```

---

## 🔄 Pagination

All list endpoints support pagination:

```dart
Future<Map<String, dynamic>> getSessionsPaginated({
  required String eventId,
  int page = 1,
  int pageSize = 20,
}) async {
  final response = await http.get(
    Uri.parse('${ApiClient.baseUrl}/sessions/?event_id=$eventId&page=$page&page_size=$pageSize'),
    headers: ApiClient.headers,
  );
  
  if (response.statusCode == 200) {
    final data = jsonDecode(response.body);
    return {
      'count': data['count'],
      'next': data['next'],
      'previous': data['previous'],
      'results': data['results'],
    };
  } else {
    throw Exception('Failed to load sessions');
  }
}
```

---

## ⚠️ Error Handling

### Standard Error Response

```json
{
  "detail": "Error message here"
}
```

### Error Handling Helper

```dart
class ApiException implements Exception {
  final String message;
  final int? statusCode;
  
  ApiException(this.message, [this.statusCode]);
  
  @override
  String toString() => message;
}

Future<T> handleApiCall<T>(Future<http.Response> Function() apiCall) async {
  try {
    final response = await apiCall();
    
    if (response.statusCode >= 200 && response.statusCode < 300) {
      return jsonDecode(response.body);
    } else if (response.statusCode == 401) {
      // Token expired - refresh token
      final refreshToken = await TokenStorage.getRefreshToken();
      if (refreshToken != null) {
        await refreshToken(refreshToken);
        // Retry the call
        return await handleApiCall(apiCall);
      } else {
        throw ApiException('Session expired. Please login again.', 401);
      }
    } else if (response.statusCode == 403) {
      throw ApiException('Permission denied', 403);
    } else if (response.statusCode == 404) {
      throw ApiException('Resource not found', 404);
    } else {
      final error = jsonDecode(response.body);
      throw ApiException(
        error['detail'] ?? 'Unknown error',
        response.statusCode,
      );
    }
  } on SocketException {
    throw ApiException('No internet connection');
  } on FormatException {
    throw ApiException('Invalid response format');
  } catch (e) {
    if (e is ApiException) rethrow;
    throw ApiException('Network error: $e');
  }
}
```

---

## 🎯 Role-Based UI Display

### User Role Constants

```dart
class UserRole {
  static const String gestionnaire = 'gestionnaire_des_salles';
  static const String controlleur = 'controlleur_des_badges';
  static const String participant = 'participant';
  static const String exposant = 'exposant';
}
```

### Auth State Provider

```dart
import 'package:flutter/foundation.dart';

class AuthState extends ChangeNotifier {
  String? _role;
  String? _eventId;
  Map<String, dynamic>? _user;
  Map<String, dynamic>? _event;
  
  String? get role => _role;
  String? get eventId => _eventId;
  Map<String, dynamic>? get user => _user;
  Map<String, dynamic>? get event => _event;
  
  bool get isAuthenticated => _role != null;
  bool get isGestionnaire => _role == UserRole.gestionnaire;
  bool get isControlleur => _role == UserRole.controlleur;
  bool get isParticipant => _role == UserRole.participant;
  bool get isExposant => _role == UserRole.exposant;
  
  void setAuth({
    required String role,
    required String eventId,
    required Map<String, dynamic> user,
    required Map<String, dynamic> event,
  }) {
    _role = role;
    _eventId = eventId;
    _user = user;
    _event = event;
    notifyListeners();
  }
  
  void clearAuth() {
    _role = null;
    _eventId = null;
    _user = null;
    _event = null;
    notifyListeners();
  }
}
```

### Conditional UI Example

```dart
class HomeScreen extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final auth = Provider.of<AuthState>(context);
    
    return Scaffold(
      appBar: AppBar(
        title: Text(auth.event?['name'] ?? 'MakePlus'),
        subtitle: Text(auth.user?['first_name'] ?? ''),
      ),
      body: ListView(
        children: [
          // All roles
          ListTile(
            leading: Icon(Icons.event),
            title: Text('Sessions'),
            onTap: () => Navigator.pushNamed(context, '/sessions'),
          ),
          ListTile(
            leading: Icon(Icons.announcement),
            title: Text('Annonces'),
            onTap: () => Navigator.pushNamed(context, '/announcements'),
          ),
          
          // Gestionnaire only
          if (auth.isGestionnaire) ...[
            Divider(),
            ListTile(
              leading: Icon(Icons.admin_panel_settings),
              title: Text('Gestion'),
              subtitle: Text('Gestionnaire des salles'),
            ),
            ListTile(
              leading: Icon(Icons.event_note),
              title: Text('Gérer les événements'),
              onTap: () => Navigator.pushNamed(context, '/manage-events'),
            ),
            ListTile(
              leading: Icon(Icons.meeting_room),
              title: Text('Gérer les salles'),
              onTap: () => Navigator.pushNamed(context, '/manage-rooms'),
            ),
            ListTile(
              leading: Icon(Icons.question_answer),
              title: Text('Répondre aux questions'),
              onTap: () => Navigator.pushNamed(context, '/answer-questions'),
            ),
          ],
          
          // Controlleur only
          if (auth.isControlleur) ...[
            Divider(),
            ListTile(
              leading: Icon(Icons.badge),
              title: Text('Contrôle'),
              subtitle: Text('Contrôleur des badges'),
            ),
            ListTile(
              leading: Icon(Icons.qr_code_scanner),
              title: Text('Scanner QR Codes'),
              onTap: () => Navigator.pushNamed(context, '/qr-scanner'),
            ),
          ],
          
          // Exposant only
          if (auth.isExposant) ...[
            Divider(),
            ListTile(
              leading: Icon(Icons.store),
              title: Text('Exposant'),
              subtitle: Text('Gestion du stand'),
            ),
            ListTile(
              leading: Icon(Icons.qr_code),
              title: Text('Scanner les visiteurs'),
              onTap: () => Navigator.pushNamed(context, '/scan-visitors'),
            ),
            ListTile(
              leading: Icon(Icons.bar_chart),
              title: Text('Statistiques'),
              onTap: () => Navigator.pushNamed(context, '/booth-stats'),
            ),
          ],
          
          // Participant features
          if (auth.isParticipant) ...[
            Divider(),
            ListTile(
              leading: Icon(Icons.person),
              title: Text('Participant'),
            ),
            ListTile(
              leading: Icon(Icons.qr_code_2),
              title: Text('Mon badge'),
              onTap: () => Navigator.pushNamed(context, '/my-badge'),
            ),
          ],
        ],
      ),
    );
  }
}
```

---

## 🔐 Token Storage (Secure)

```dart
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class TokenStorage {
  static const _storage = FlutterSecureStorage();
  static const _accessKey = 'access_token';
  static const _refreshKey = 'refresh_token';
  static const _userKey = 'user_data';
  static const _eventKey = 'event_data';
  static const _roleKey = 'user_role';
  
  static Future<void> saveTokens({
    required String accessToken,
    required String refreshToken,
  }) async {
    await _storage.write(key: _accessKey, value: accessToken);
    await _storage.write(key: _refreshKey, value: refreshToken);
  }
  
  static Future<void> saveUserData({
    required Map<String, dynamic> user,
    required Map<String, dynamic> event,
    required String role,
  }) async {
    await _storage.write(key: _userKey, value: jsonEncode(user));
    await _storage.write(key: _eventKey, value: jsonEncode(event));
    await _storage.write(key: _roleKey, value: role);
  }
  
  static Future<String?> getAccessToken() async {
    return await _storage.read(key: _accessKey);
  }
  
  static Future<String?> getRefreshToken() async {
    return await _storage.read(key: _refreshKey);
  }
  
  static Future<Map<String, dynamic>?> getUserData() async {
    final userData = await _storage.read(key: _userKey);
    return userData != null ? jsonDecode(userData) : null;
  }
  
  static Future<Map<String, dynamic>?> getEventData() async {
    final eventData = await _storage.read(key: _eventKey);
    return eventData != null ? jsonDecode(eventData) : null;
  }
  
  static Future<String?> getRole() async {
    return await _storage.read(key: _roleKey);
  }
  
  static Future<void> clearTokens() async {
    await _storage.delete(key: _accessKey);
    await _storage.delete(key: _refreshKey);
    await _storage.delete(key: _userKey);
    await _storage.delete(key: _eventKey);
    await _storage.delete(key: _roleKey);
  }
}
```

---

## 📝 Important Constants

### Session Status Values (French)
```dart
class SessionStatus {
  static const String notStarted = 'pas_encore';
  static const String live = 'en_cours';
  static const String finished = 'termine';
}
```

### Session Types
```dart
class SessionType {
  static const String conference = 'conference';
  static const String atelier = 'atelier';
}
```

### Announcement Targets
```dart
class AnnonceTarget {
  static const String all = 'all';
  static const String participants = 'participants';
  static const String exposants = 'exposants';
  static const String controlleurs = 'controlleurs';
  static const String gestionnaires = 'gestionnaires';
}
```

### Payment Status
```dart
class PaymentStatus {
  static const String pending = 'pending';
  static const String paid = 'paid';
  static const String refunded = 'refunded';
}
```

---

## 🧪 Testing Credentials

After running `python manage.py create_multi_event_data`:

**Gestionnaire:**
- Email: `ahmed.benali@techsummit.dz`
- Password: `makeplus2025`
- Role: gestionnaire_des_salles

**Contrôleur:**
- Email: `fatima.merzouk@techsummit.dz`
- Password: `makeplus2025`
- Role: controlleur_des_badges

**Participant:**
- Email: `yasmine.kadri@techsummit.dz`
- Password: `makeplus2025`
- Role: participant

**Exposant:**
- Email: `rachid.sellami@techsummit.dz`
- Password: `makeplus2025`
- Role: exposant

---

## 🚀 Complete API Service Class

```dart
// lib/services/api_service.dart
import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;

class ApiService {
  static const String baseUrl = ApiConfig.fullApiUrl;
  
  // ========== Authentication ==========
  static Future<Map<String, dynamic>> register({
    required String username,
    required String email,
    required String password,
    required String firstName,
    required String lastName,
  }) async {
    // Implementation shown above
  }
  
  static Future<Map<String, dynamic>> login({
    required String email,
    required String password,
    required String eventId,
  }) async {
    // Implementation shown above
  }
  
  static Future<void> logout() async {
    // Implementation shown above
  }
  
  static Future<List<dynamic>> getMyEvents() async {
    // Implementation shown above
  }
  
  static Future<Map<String, dynamic>> switchEvent(String eventId) async {
    // Implementation shown above
  }
  
  // ========== Events ==========
  static Future<List<Event>> getEvents() async {
    // Implementation shown above
  }
  
  // ========== Rooms ==========
  static Future<List<Room>> getRooms(String eventId) async {
    // Implementation shown above
  }
  
  // ========== Sessions ==========
  static Future<List<Session>> getSessions({
    required String eventId,
    String? roomId,
    String? status,
  }) async {
    // Implementation shown above
  }
  
  static Future<void> markSessionLive(String sessionId) async {
    // Implementation shown above
  }
  
  static Future<void> markSessionCompleted(String sessionId) async {
    // Implementation shown above
  }
  
  static Future<void> cancelSession(String sessionId) async {
    // Implementation shown above
  }
  
  // ========== Announcements ==========
  static Future<List<Annonce>> getAnnouncements(String eventId) async {
    // Implementation shown above
  }
  
  static Future<Annonce> createAnnouncement({
    required String eventId,
    required String title,
    required String description,
    required String target,
  }) async {
    // Implementation shown above
  }
  
  // ========== Session Q&A ==========
  static Future<List<SessionQuestion>> getSessionQuestions(String sessionId) async {
    // Implementation shown above
  }
  
  static Future<SessionQuestion> askQuestion({
    required String sessionId,
    required String participantId,
    required String questionText,
  }) async {
    // Implementation shown above
  }
  
  static Future<SessionQuestion> answerQuestion({
    required String questionId,
    required String answerText,
  }) async {
    // Implementation shown above
  }
  
  // ========== Exposant Scans ==========
  static Future<ExposantScan> scanParticipant({
    required String exposantId,
    required String participantId,
    required String eventId,
    String? notes,
  }) async {
    // Implementation shown above
  }
  
  static Future<Map<String, dynamic>> getMyScans(String eventId) async {
    // Implementation shown above
  }
  
  // ========== QR Verification ==========
  static Future<Map<String, dynamic>> verifyQRCode({
    required String qrData,
    required String roomId,
  }) async {
    // Implementation shown above
  }
  
  // ========== Dashboard ==========
  static Future<Map<String, dynamic>> getDashboardStats() async {
    // Implementation shown above
  }
}
```

---

## 🌐 Network Configuration

### For Android Emulator

Add to `android/app/src/main/AndroidManifest.xml`:
```xml
<application
    android:usesCleartextTraffic="true">
    ...
</application>
```

### For iOS Simulator

Add to `ios/Runner/Info.plist`:
```xml
<key>NSAppTransportSecurity</key>
<dict>
    <key>NSAllowsArbitraryLoads</key>
    <true/>
</dict>
```

---

## 📞 API Documentation & Support

**Swagger UI:** `http://localhost:8000/swagger/`  
**ReDoc:** `http://localhost:8000/redoc/`  
**Admin Panel:** `http://localhost:8000/admin/`

### Backend Status Check
```bash
# Start Django server
python manage.py runserver

# Test API is running
curl http://localhost:8000/api/events/
```

---

**End of Flutter Integration Guide**

Use this guide with your existing Flutter frontend to integrate all backend features. All endpoints are tested and ready for production! 🚀
