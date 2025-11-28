# Controller Room Statistics API - Implementation Guide

## ✅ Changes Completed

### 1. New API Endpoint for Controllers
**Endpoint:** `GET /api/my-room/statistics/`

**Purpose:** Controllers can get statistics for their assigned room without needing to know the room ID.

**How it works:**
1. Detects the authenticated controller from JWT token
2. Finds the room assigned to that controller
3. Returns comprehensive statistics for that room only

---

## 🔑 Authentication

The endpoint uses JWT authentication with event context:

```
Authorization: Bearer <your_jwt_token>
X-Event-ID: <event_uuid>
```

---

## 📊 API Response

### Success Response (200 OK)
```json
{
  "room": {
    "id": "uuid",
    "name": "Hall Exposition",
    "capacity": 100
  },
  "statistics": {
    "total_scans": 45,
    "today_scans": 12,
    "granted": 38,
    "denied": 7,
    "unique_participants": 25,
    "unique_participants_today": 8
  },
  "recent_scans": [
    {
      "id": "uuid",
      "participant": {
        "id": "uuid",
        "name": "Rania Khelifa",
        "email": "rania.khelifa@participant.dz",
        "badge_id": "BADGE-001"
      },
      "session": "Innovation et Startups",
      "status": "granted",
      "accessed_at": "2025-11-28T14:30:00Z",
      "verified_by": "startup_controleur"
    }
  ]
}
```

### Error Responses

**403 Forbidden - Not a Controller**
```json
{
  "detail": "You must be a controller to access room statistics."
}
```

**404 Not Found - No Room Assignment**
```json
{
  "detail": "You have no room assigned. Please contact the administrator."
}
```

**404 Not Found - No Event Context**
```json
{
  "detail": "No event context found. Please select an event first."
}
```

---

## 📱 Flutter Implementation

### 1. Model Classes

```dart
class RoomStatistics {
  final RoomInfo room;
  final Statistics statistics;
  final List<RecentScan> recentScans;

  RoomStatistics({
    required this.room,
    required this.statistics,
    required this.recentScans,
  });

  factory RoomStatistics.fromJson(Map<String, dynamic> json) {
    return RoomStatistics(
      room: RoomInfo.fromJson(json['room']),
      statistics: Statistics.fromJson(json['statistics']),
      recentScans: (json['recent_scans'] as List)
          .map((e) => RecentScan.fromJson(e))
          .toList(),
    );
  }
}

class RoomInfo {
  final String id;
  final String name;
  final int capacity;

  RoomInfo({
    required this.id,
    required this.name,
    required this.capacity,
  });

  factory RoomInfo.fromJson(Map<String, dynamic> json) {
    return RoomInfo(
      id: json['id'],
      name: json['name'],
      capacity: json['capacity'],
    );
  }
}

class Statistics {
  final int totalScans;
  final int todayScans;
  final int granted;
  final int denied;
  final int uniqueParticipants;
  final int uniqueParticipantsToday;

  Statistics({
    required this.totalScans,
    required this.todayScans,
    required this.granted,
    required this.denied,
    required this.uniqueParticipants,
    required this.uniqueParticipantsToday,
  });

  factory Statistics.fromJson(Map<String, dynamic> json) {
    return Statistics(
      totalScans: json['total_scans'],
      todayScans: json['today_scans'],
      granted: json['granted'],
      denied: json['denied'],
      uniqueParticipants: json['unique_participants'],
      uniqueParticipantsToday: json['unique_participants_today'],
    );
  }
}

class RecentScan {
  final String id;
  final ParticipantInfo participant;
  final String? session;
  final String status;
  final DateTime accessedAt;
  final String? verifiedBy;

  RecentScan({
    required this.id,
    required this.participant,
    this.session,
    required this.status,
    required this.accessedAt,
    this.verifiedBy,
  });

  factory RecentScan.fromJson(Map<String, dynamic> json) {
    return RecentScan(
      id: json['id'],
      participant: ParticipantInfo.fromJson(json['participant']),
      session: json['session'],
      status: json['status'],
      accessedAt: DateTime.parse(json['accessed_at']),
      verifiedBy: json['verified_by'],
    );
  }
}

class ParticipantInfo {
  final String id;
  final String name;
  final String email;
  final String? badgeId;

  ParticipantInfo({
    required this.id,
    required this.name,
    required this.email,
    this.badgeId,
  });

  factory ParticipantInfo.fromJson(Map<String, dynamic> json) {
    return ParticipantInfo(
      id: json['id'],
      name: json['name'],
      email: json['email'],
      badgeId: json['badge_id'],
    );
  }
}
```

### 2. API Service

```dart
import 'package:http/http.dart' as http;
import 'dart:convert';

class StatisticsService {
  final String baseUrl = 'YOUR_BACKEND_URL';
  
  Future<RoomStatistics> getMyRoomStatistics() async {
    final token = await getStoredToken(); // Your token storage
    final eventId = await getStoredEventId(); // Your event ID storage
    
    final response = await http.get(
      Uri.parse('$baseUrl/api/my-room/statistics/'),
      headers: {
        'Authorization': 'Bearer $token',
        'X-Event-ID': eventId,
        'Content-Type': 'application/json',
      },
    );
    
    if (response.statusCode == 200) {
      return RoomStatistics.fromJson(json.decode(response.body));
    } else if (response.statusCode == 403) {
      throw Exception('You must be a controller to access statistics');
    } else if (response.statusCode == 404) {
      final error = json.decode(response.body);
      throw Exception(error['detail']);
    } else {
      throw Exception('Failed to load statistics');
    }
  }
}
```

### 3. UI Implementation

```dart
class ControllerStatisticsPage extends StatefulWidget {
  @override
  State<ControllerStatisticsPage> createState() => _ControllerStatisticsPageState();
}

class _ControllerStatisticsPageState extends State<ControllerStatisticsPage> {
  late Future<RoomStatistics> _statistics;
  final StatisticsService _service = StatisticsService();
  
  @override
  void initState() {
    super.initState();
    _loadStatistics();
  }
  
  void _loadStatistics() {
    setState(() {
      _statistics = _service.getMyRoomStatistics();
    });
  }
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Room Statistics'),
        actions: [
          IconButton(
            icon: Icon(Icons.refresh),
            onPressed: _loadStatistics,
          ),
        ],
      ),
      body: FutureBuilder<RoomStatistics>(
        future: _statistics,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return Center(child: CircularProgressIndicator());
          }
          
          if (snapshot.hasError) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.error_outline, size: 48, color: Colors.red),
                  SizedBox(height: 16),
                  Text(
                    snapshot.error.toString(),
                    textAlign: TextAlign.center,
                  ),
                  SizedBox(height: 16),
                  ElevatedButton(
                    onPressed: _loadStatistics,
                    child: Text('Retry'),
                  ),
                ],
              ),
            );
          }
          
          final stats = snapshot.data!;
          
          return RefreshIndicator(
            onRefresh: () async => _loadStatistics(),
            child: SingleChildScrollView(
              physics: AlwaysScrollableScrollPhysics(),
              padding: EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Room Info Card
                  Card(
                    child: Padding(
                      padding: EdgeInsets.all(16),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            stats.room.name,
                            style: Theme.of(context).textTheme.headlineSmall,
                          ),
                          SizedBox(height: 4),
                          Text('Capacity: ${stats.room.capacity} persons'),
                        ],
                      ),
                    ),
                  ),
                  
                  SizedBox(height: 16),
                  
                  // Statistics Grid
                  GridView.count(
                    crossAxisCount: 2,
                    shrinkWrap: true,
                    physics: NeverScrollableScrollPhysics(),
                    mainAxisSpacing: 12,
                    crossAxisSpacing: 12,
                    childAspectRatio: 1.5,
                    children: [
                      _buildStatCard(
                        'Today Scans',
                        '${stats.statistics.todayScans}',
                        Icons.today,
                        Colors.blue,
                      ),
                      _buildStatCard(
                        'Total Scans',
                        '${stats.statistics.totalScans}',
                        Icons.qr_code_scanner,
                        Colors.purple,
                      ),
                      _buildStatCard(
                        'Granted',
                        '${stats.statistics.granted}',
                        Icons.check_circle,
                        Colors.green,
                      ),
                      _buildStatCard(
                        'Denied',
                        '${stats.statistics.denied}',
                        Icons.cancel,
                        Colors.red,
                      ),
                      _buildStatCard(
                        'Unique Today',
                        '${stats.statistics.uniqueParticipantsToday}',
                        Icons.people,
                        Colors.orange,
                      ),
                      _buildStatCard(
                        'Unique Total',
                        '${stats.statistics.uniqueParticipants}',
                        Icons.groups,
                        Colors.teal,
                      ),
                    ],
                  ),
                  
                  SizedBox(height: 24),
                  
                  // Recent Scans Section
                  Text(
                    'Recent Scans',
                    style: Theme.of(context).textTheme.titleLarge,
                  ),
                  Text(
                    'Last 20 scans',
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                  SizedBox(height: 12),
                  
                  // Recent Scans List
                  ...stats.recentScans.map((scan) => Card(
                    margin: EdgeInsets.only(bottom: 8),
                    child: ListTile(
                      leading: CircleAvatar(
                        backgroundColor: scan.status == 'granted'
                            ? Colors.green
                            : Colors.red,
                        child: Icon(
                          scan.status == 'granted'
                              ? Icons.check
                              : Icons.close,
                          color: Colors.white,
                        ),
                      ),
                      title: Text(scan.participant.name),
                      subtitle: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(scan.participant.email),
                          if (scan.session != null)
                            Text('Session: ${scan.session}'),
                          Text(
                            _formatDateTime(scan.accessedAt),
                            style: TextStyle(fontSize: 12),
                          ),
                        ],
                      ),
                      trailing: Text(
                        scan.participant.badgeId ?? '',
                        style: TextStyle(
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                  )),
                ],
              ),
            ),
          );
        },
      ),
    );
  }
  
  Widget _buildStatCard(String title, String value, IconData icon, Color color) {
    return Card(
      elevation: 2,
      child: Padding(
        padding: EdgeInsets.all(12),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, size: 28, color: color),
            SizedBox(height: 8),
            Text(
              value,
              style: TextStyle(
                fontSize: 24,
                fontWeight: FontWeight.bold,
                color: color,
              ),
            ),
            SizedBox(height: 4),
            Text(
              title,
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 12),
            ),
          ],
        ),
      ),
    );
  }
  
  String _formatDateTime(DateTime dt) {
    final now = DateTime.now();
    final today = DateTime(now.year, now.month, now.day);
    final scanDate = DateTime(dt.year, dt.month, dt.day);
    
    if (scanDate == today) {
      return 'Today at ${dt.hour}:${dt.minute.toString().padLeft(2, '0')}';
    } else {
      return '${dt.day}/${dt.month}/${dt.year} ${dt.hour}:${dt.minute.toString().padLeft(2, '0')}';
    }
  }
}
```

---

## 🧪 Testing Credentials

**Controller Account:**
- **Email:** leila.madani@startupweek.dz
- **Password:** makeplus2025
- **Assigned Room:** Hall Exposition
- **Event:** StartupWeek Oran 2025

**Test Data Created:**
- 4 room access records (all granted)
- All from today's date
- 4 unique participants

---

## 🔍 Key Differences from Admin Endpoint

| Feature | `/api/my-room/statistics/` (Controller) | `/api/rooms/{id}/statistics/` (Admin) |
|---------|----------------------------------------|--------------------------------------|
| **Who can use** | Controllers only | Admin/Gestionnaire only |
| **Room ID** | Auto-detected from assignment | Must provide in URL |
| **Permission** | Based on room assignment | Based on role |
| **Use case** | Controller viewing their room | Admin viewing any room |

---

## 📝 Backend Changes Summary

1. **New View:** `MyRoomStatisticsView` in `events/auth_views.py`
2. **New URL:** `/api/my-room/statistics/` in `events/urls.py`
3. **Permission Check:** Only controllers with room assignments
4. **Auto-detection:** Finds controller's assigned room automatically
5. **Documentation:** Updated `BACKEND_DOCUMENTATION.md`

---

## ✅ Ready for Production

The endpoint is now live and ready to use. No additional configuration needed.
