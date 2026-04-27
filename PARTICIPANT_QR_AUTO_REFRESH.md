# Participant QR Code Auto-Refresh Solution

## The Problem

- QR code (badge_id) never changes ✅
- QR code data is stored in participant's app locally
- When transaction is cancelled, database is updated
- But participant's app still has old data ❌

## The Solution: Auto-Refresh

The participant's mobile app should automatically refresh QR code data in the background.

### Implementation in Mobile App

#### 1. Store QR Code Data with Timestamp

```dart
class QRCodeData {
  final String badgeId;
  final List<PaidItem> paidItems;
  final DateTime lastUpdated;
  
  // Save to local storage
  Future<void> save() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('qr_code_data', jsonEncode({
      'badge_id': badgeId,
      'paid_items': paidItems.map((i) => i.toJson()).toList(),
      'last_updated': lastUpdated.toIso8601String(),
    }));
  }
  
  // Load from local storage
  static Future<QRCodeData?> load() async {
    final prefs = await SharedPreferences.getInstance();
    final data = prefs.getString('qr_code_data');
    if (data == null) return null;
    
    final json = jsonDecode(data);
    return QRCodeData(
      badgeId: json['badge_id'],
      paidItems: (json['paid_items'] as List).map((i) => PaidItem.fromJson(i)).toList(),
      lastUpdated: DateTime.parse(json['last_updated']),
    );
  }
}
```

#### 2. Auto-Refresh on App Launch

```dart
class QRCodeScreen extends StatefulWidget {
  @override
  _QRCodeScreenState createState() => _QRCodeScreenState();
}

class _QRCodeScreenState extends State<QRCodeScreen> with WidgetsBindingObserver {
  QRCodeData? qrData;
  bool isRefreshing = false;
  
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _loadAndRefreshQRCode();
  }
  
  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    super.dispose();
  }
  
  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    // Refresh when app comes to foreground
    if (state == AppLifecycleState.resumed) {
      _refreshQRCode();
    }
  }
  
  Future<void> _loadAndRefreshQRCode() async {
    // Load from local storage first (for offline mode)
    final cached = await QRCodeData.load();
    if (cached != null) {
      setState(() {
        qrData = cached;
      });
    }
    
    // Then refresh from server
    await _refreshQRCode();
  }
  
  Future<void> _refreshQRCode() async {
    if (isRefreshing) return;
    
    setState(() {
      isRefreshing = true;
    });
    
    try {
      // Call backend to get fresh QR code data
      final response = await http.get(
        Uri.parse('$baseUrl/api/auth/me/'),
        headers: {
          'Authorization': 'Bearer $accessToken',
        },
      );
      
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final freshQRData = QRCodeData.fromJson(data['qr_code']);
        
        // Save to local storage
        await freshQRData.save();
        
        setState(() {
          qrData = freshQRData;
        });
        
        print('✅ QR code data refreshed');
      }
    } catch (e) {
      print('⚠️ Failed to refresh QR code: $e');
      // Keep using cached data
    } finally {
      setState(() {
        isRefreshing = false;
      });
    }
  }
  
  @override
  Widget build(BuildContext context) {
    if (qrData == null) {
      return Center(child: CircularProgressIndicator());
    }
    
    return Scaffold(
      appBar: AppBar(
        title: Text('Mon Badge'),
        actions: [
          IconButton(
            icon: Icon(Icons.refresh),
            onPressed: _refreshQRCode,
          ),
        ],
      ),
      body: Column(
        children: [
          // QR Code Image
          QrImage(
            data: qrData!.badgeId,  // QR code contains only badge_id
            version: QrVersions.auto,
            size: 200.0,
          ),
          
          SizedBox(height: 16),
          
          // Badge ID
          Text('Badge: ${qrData!.badgeId}',
            style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
          
          SizedBox(height: 8),
          
          // Last updated
          Text('Mis à jour: ${_formatTime(qrData!.lastUpdated)}',
            style: TextStyle(fontSize: 12, color: Colors.grey)),
          
          SizedBox(height: 16),
          
          // Paid Items
          Expanded(
            child: ListView.builder(
              itemCount: qrData!.paidItems.length,
              itemBuilder: (context, index) {
                final item = qrData!.paidItems[index];
                return ListTile(
                  leading: Icon(Icons.check_circle, color: Colors.green),
                  title: Text(item.title),
                  subtitle: Text('${item.amountPaid} DA'),
                );
              },
            ),
          ),
          
          // Refresh indicator
          if (isRefreshing)
            Padding(
              padding: EdgeInsets.all(8),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  SizedBox(
                    width: 16,
                    height: 16,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  ),
                  SizedBox(width: 8),
                  Text('Actualisation...', style: TextStyle(fontSize: 12)),
                ],
              ),
            ),
        ],
      ),
    );
  }
  
  String _formatTime(DateTime time) {
    final now = DateTime.now();
    final diff = now.difference(time);
    
    if (diff.inMinutes < 1) return 'À l\'instant';
    if (diff.inMinutes < 60) return 'Il y a ${diff.inMinutes} min';
    if (diff.inHours < 24) return 'Il y a ${diff.inHours}h';
    return 'Il y a ${diff.inDays}j';
  }
}
```

#### 3. Periodic Background Refresh (Optional)

```dart
import 'package:workmanager/workmanager.dart';

// Setup background task
void setupBackgroundRefresh() {
  Workmanager().initialize(callbackDispatcher);
  
  // Refresh every 15 minutes when app is in background
  Workmanager().registerPeriodicTask(
    "qr-refresh",
    "refreshQRCode",
    frequency: Duration(minutes: 15),
  );
}

void callbackDispatcher() {
  Workmanager().executeTask((task, inputData) async {
    // Refresh QR code data
    await refreshQRCodeInBackground();
    return Future.value(true);
  });
}
```

## For Controller App

Controller app should **ALWAYS** call the backend API, never trust QR code data:

```dart
Future<void> scanBadge(String roomId) async {
  // 1. Scan QR code
  final qrCodeString = await BarcodeScanner.scan();
  
  // 2. Parse to get badge_id
  final qrData = jsonDecode(qrCodeString);
  final badgeId = qrData['badge_id'];
  
  // 3. Call backend API (ALWAYS!)
  final response = await http.post(
    Uri.parse('$baseUrl/api/events/rooms/$roomId/scan_participant/'),
    headers: {
      'Authorization': 'Bearer $controllerToken',
      'Content-Type': 'application/json',
    },
    body: jsonEncode({
      'qr_data': qrCodeString,
    }),
  );
  
  // 4. Display FRESH data from API
  final result = jsonDecode(response.body);
  if (result['status'] == 'success') {
    showAccessGranted(result);  // Shows fresh data from database
  }
}
```

## Backend Changes (Already Done)

✅ QR code data is updated when:
- Transaction is created
- Transaction is cancelled
- User logs in
- User requests profile

✅ QR code generation queries only completed transactions

## Summary

### Participant App:
- ✅ Stores QR code data locally (for offline)
- ✅ Auto-refreshes when app opens
- ✅ Auto-refreshes when app comes to foreground
- ✅ Shows "Last updated" timestamp
- ✅ Manual refresh button available
- ✅ Optional: Background refresh every 15 minutes

### Controller App:
- ✅ Always calls backend API
- ✅ Never trusts QR code data
- ✅ Always shows fresh data from database

### Backend:
- ✅ Updates QR code data on transaction create/cancel
- ✅ Returns fresh data via API endpoints
- ✅ Only includes completed transactions

## Result

- ✅ QR code (badge_id) never changes
- ✅ Participant sees updated data automatically
- ✅ Controller always sees correct data
- ✅ No manual refresh needed (happens automatically)
- ✅ Works offline (uses cached data)
- ✅ Syncs when online

## Testing

1. Participant pays for items
2. Participant's app auto-refreshes (within seconds)
3. Participant sees new items in their app
4. Controller scans → Sees all items ✅

5. Transaction is cancelled
6. Participant's app auto-refreshes (within seconds)
7. Participant sees items removed
8. Controller scans → Items not shown ✅
