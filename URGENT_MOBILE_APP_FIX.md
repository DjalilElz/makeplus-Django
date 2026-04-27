# 🚨 URGENT: Mobile App Not Calling Backend API

## Problem Identified

The mobile app is displaying QR code data **directly from the QR code** instead of calling the backend API. This causes stale data to be shown.

### Current (Wrong) Flow:
```
1. Scan QR code
2. Parse QR code JSON
3. Display paid_items from QR code ❌ WRONG!
```

### Correct Flow:
```
1. Scan QR code
2. Parse QR code JSON (get user_id and badge_id)
3. Call backend API: POST /api/events/rooms/{room_id}/scan_participant/
4. Display paid_items from API response ✅ CORRECT!
```

## Evidence from Logs

The Flutter logs show:
```
💰 PAID ITEMS COUNT: 1
💰 PAID ITEMS DETAILS:
   Item 1:
      - type: session
      - title: Intro to Ai
      - amount_paid: 6000.0
```

This is coming from the QR code's `paid_items` array, NOT from the backend API.

## What the Mobile App Should Do

### Step 1: Parse QR Code (for identification only)
```dart
final qrData = jsonDecode(qrCodeString);
final userId = qrData['user_id'];
final badgeId = qrData['badge_id'];
final email = qrData['email'];
final fullName = qrData['full_name'];

// ❌ DO NOT USE: qrData['paid_items']
// This data is STALE and may be outdated!
```

### Step 2: Call Backend API
```dart
final response = await http.post(
  Uri.parse('$baseUrl/api/events/rooms/$roomId/scan_participant/'),
  headers: {
    'Authorization': 'Bearer $controllerToken',
    'Content-Type': 'application/json',
  },
  body: jsonEncode({
    'qr_data': qrCodeString,  // Send the entire QR code
  }),
);

final result = jsonDecode(response.body);
```

### Step 3: Display Data from API Response
```dart
if (result['status'] == 'success') {
  // ✅ USE THIS DATA - It's fresh from the database!
  final paidItems = result['paid_items'] ?? [];
  final freeItems = result['free_items'] ?? [];
  
  print('💰 PAID ITEMS COUNT: ${paidItems.length}');
  
  for (var item in paidItems) {
    print('   - ${item['title']} (${item['type']}) - ${item['amount_paid']} DA');
  }
  
  // Display in UI
  _showAccessGranted(result);
}
```

## Complete Example

```dart
Future<void> scanBadge(String roomId) async {
  try {
    // 1. Scan QR code
    final qrCodeString = await BarcodeScanner.scan();
    
    if (qrCodeString.isEmpty) return;
    
    // 2. Parse for display purposes only (show name while loading)
    final qrData = jsonDecode(qrCodeString);
    final participantName = qrData['full_name'];
    
    // Show loading with participant name
    showLoading('Vérification de $participantName...');
    
    // 3. Call backend API to get FRESH data
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
    
    hideLoading();
    
    final result = jsonDecode(response.body);
    
    // 4. Display data from API response (NOT from QR code!)
    if (result['status'] == 'success') {
      final paidItems = result['paid_items'] ?? [];
      final freeItems = result['free_items'] ?? [];
      
      // Group by type
      final sessions = paidItems.where((i) => i['type'] == 'session').toList();
      final access = paidItems.where((i) => i['type'] == 'access').toList();
      final dinners = paidItems.where((i) => i['type'] == 'dinner').toList();
      final others = paidItems.where((i) => i['type'] == 'other').toList();
      
      // Show success dialog with ALL items
      showDialog(
        context: context,
        builder: (context) => AlertDialog(
          title: Text('✅ Accès Autorisé'),
          content: SingleChildScrollView(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Nom: ${result['participant']['name']}',
                  style: TextStyle(fontWeight: FontWeight.bold)),
                Text('Email: ${result['participant']['email']}'),
                Text('Badge: ${result['participant']['badge_id']}'),
                
                SizedBox(height: 16),
                
                // Show paid workshops
                if (sessions.isNotEmpty) ...[
                  Text('Ateliers Payés:', 
                    style: TextStyle(fontWeight: FontWeight.bold)),
                  ...sessions.map((item) => Padding(
                    padding: EdgeInsets.only(left: 8, top: 4),
                    child: Text('✅ ${item['title']} (${item['amount_paid']} DA)'),
                  )),
                  SizedBox(height: 8),
                ],
                
                // Show access passes
                if (access.isNotEmpty) ...[
                  Text('Accès:', 
                    style: TextStyle(fontWeight: FontWeight.bold)),
                  ...access.map((item) => Padding(
                    padding: EdgeInsets.only(left: 8, top: 4),
                    child: Text('✅ ${item['title']} (${item['amount_paid']} DA)'),
                  )),
                  SizedBox(height: 8),
                ],
                
                // Show meals
                if (dinners.isNotEmpty) ...[
                  Text('Repas:', 
                    style: TextStyle(fontWeight: FontWeight.bold)),
                  ...dinners.map((item) => Padding(
                    padding: EdgeInsets.only(left: 8, top: 4),
                    child: Text('✅ ${item['title']} (${item['amount_paid']} DA)'),
                  )),
                  SizedBox(height: 8),
                ],
                
                // Show other items
                if (others.isNotEmpty) ...[
                  Text('Autres:', 
                    style: TextStyle(fontWeight: FontWeight.bold)),
                  ...others.map((item) => Padding(
                    padding: EdgeInsets.only(left: 8, top: 4),
                    child: Text('✅ ${item['title']} (${item['amount_paid']} DA)'),
                  )),
                  SizedBox(height: 8),
                ],
                
                // Show free items
                if (freeItems.isNotEmpty) ...[
                  Text('Gratuit:', 
                    style: TextStyle(fontWeight: FontWeight.bold)),
                  ...freeItems.map((item) => Padding(
                    padding: EdgeInsets.only(left: 8, top: 4),
                    child: Text('🆓 ${item['title']}'),
                  )),
                ],
                
                SizedBox(height: 12),
                
                // Summary
                Container(
                  padding: EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: Colors.green.shade50,
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('Résumé:', 
                        style: TextStyle(fontWeight: FontWeight.bold)),
                      Text('${paidItems.length} articles payés'),
                      Text('${freeItems.length} articles gratuits'),
                      Text('Total: ${paidItems.fold(0.0, (sum, item) => sum + item['amount_paid'])} DA',
                        style: TextStyle(
                          fontWeight: FontWeight.bold, 
                          color: Colors.green
                        )),
                    ],
                  ),
                ),
              ],
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: Text('OK'),
            ),
          ],
        ),
      );
      
    } else if (result['status'] == 'error') {
      showError('Erreur: ${result['message']}');
    } else {
      showError('QR Code invalide');
    }
    
  } catch (e) {
    hideLoading();
    showError('Erreur de scan: $e');
  }
}
```

## Why This Matters

### Current Behavior (Wrong):
- Participant pays for 2 items: "access" (2000 DA) + "Intro to AI" (6000 DA)
- QR code shows only 1 item (stale data)
- Controller sees only 1 item ❌

### After Fix (Correct):
- Participant pays for 2 items: "access" (2000 DA) + "Intro to AI" (6000 DA)
- Backend queries database and returns 2 items (fresh data)
- Controller sees both items ✅

## Action Required

**Mobile Developer:** Please update the controller app to:
1. ❌ Stop displaying `qrData['paid_items']` directly
2. ✅ Call `POST /api/events/rooms/{room_id}/scan_participant/`
3. ✅ Display `result['paid_items']` from API response

This is critical for the system to work correctly!

## Testing After Fix

1. Scan djalil azizi's QR code
2. Mobile app should call the API
3. API will return 2 items (if backend fix is deployed)
4. Controller should see both items

## Backend Status

The backend fix has been pushed to GitHub. Check Render deployment status:
- Go to https://dashboard.render.com
- Verify latest commit is deployed
- Look for commit: "Fix: Ensure transaction items are properly saved to database"

Once both fixes are deployed (backend + mobile app), the system will work correctly.
