# Flutter Native Share Implementation for Excel Export

## 📱 Overview

This guide shows how to implement the **System Share Sheet** (iOS UIActivityViewController / Android Share Intent) for exporting Excel files from the exposant dashboard.

---

## ✅ Backend Changes (COMPLETED)

The backend now supports two modes:

1. **Download mode** (`action=download`): Traditional file download for web/desktop
2. **Share mode** (`action=share`): Returns file inline for mobile sharing

### Endpoint:
```
GET /api/exposant-scans/export_excel/?action=share
Authorization: Bearer {token}
```

### Response Headers:
- `Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- `Content-Disposition: inline; filename="Statistiques_Visiteurs_...xlsx"`
- `X-Filename: Statistiques_Visiteurs_...xlsx`

---

## 📦 Flutter Dependencies

Add to `pubspec.yaml`:

```yaml
dependencies:
  flutter:
    sdk: flutter
  
  # HTTP client
  http: ^1.1.0
  
  # Native share sheet
  share_plus: ^7.2.1
  
  # Path provider for temporary files
  path_provider: ^2.1.1
  
  # File permissions (Android)
  permission_handler: ^11.0.1
```

Then run:
```bash
flutter pub get
```

---

## 🔧 Android Configuration

### `android/app/src/main/AndroidManifest.xml`

Add these permissions:

```xml
<manifest xmlns:android="http://schemas.android.com/apk/res/android">
    <!-- Existing permissions -->
    
    <!-- Storage permissions for file sharing -->
    <uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE"
        android:maxSdkVersion="32" />
    <uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE"
        android:maxSdkVersion="32" />
    
    <application
        ...
        <!-- Add FileProvider for sharing files -->
        <provider
            android:name="androidx.core.content.FileProvider"
            android:authorities="${applicationId}.fileprovider"
            android:exported="false"
            android:grantUriPermissions="true">
            <meta-data
                android:name="android.support.FILE_PROVIDER_PATHS"
                android:resource="@xml/file_paths" />
        </provider>
    </application>
</manifest>
```

### `android/app/src/main/res/xml/file_paths.xml`

Create this file:

```xml
<?xml version="1.0" encoding="utf-8"?>
<paths>
    <cache-path name="cache" path="." />
    <external-path name="external" path="." />
    <files-path name="files" path="." />
</paths>
```

---

## 🍎 iOS Configuration

### `ios/Runner/Info.plist`

Add sharing description (optional but recommended):

```xml
<key>NSPhotoLibraryAddUsageDescription</key>
<string>We need access to save Excel files</string>
```

No other iOS configuration needed! `share_plus` handles everything.

---

## 💻 Flutter Implementation

### 1. Service Class: `ExcelExportService`

```dart
// lib/services/excel_export_service.dart

import 'dart:io';
import 'package:http/http.dart' as http;
import 'package:path_provider/path_provider.dart';
import 'package:share_plus/share_plus.dart';

class ExcelExportService {
  final String baseUrl;
  final String accessToken;

  ExcelExportService({
    required this.baseUrl,
    required this.accessToken,
  });

  /// Export and share Excel file using native share sheet
  /// Shows: iOS UIActivityViewController / Android Share Intent
  Future<ShareResult> exportAndShareExcel() async {
    try {
      // 1. Download Excel file from backend
      print('📥 Downloading Excel file...');
      final response = await http.get(
        Uri.parse('$baseUrl/api/exposant-scans/export_excel/?action=share'),
        headers: {
          'Authorization': 'Bearer $accessToken',
        },
      );

      if (response.statusCode != 200) {
        throw Exception('Failed to download Excel file: ${response.statusCode}');
      }

      // 2. Extract filename from response headers
      String filename = _extractFilename(response.headers);
      print('📄 Filename: $filename');

      // 3. Save file to temporary directory
      final bytes = response.bodyBytes;
      final tempDir = await getTemporaryDirectory();
      final filePath = '${tempDir.path}/$filename';
      
      final file = File(filePath);
      await file.writeAsBytes(bytes);
      print('💾 Saved to: $filePath');

      // 4. Share using native share sheet
      print('📤 Opening share sheet...');
      final result = await Share.shareXFiles(
        [XFile(filePath)],
        text: 'Statistiques des visiteurs du stand',
        subject: 'Export Excel - Statistiques',
      );

      print('✅ Share completed: ${result.status}');
      return result;

    } catch (e) {
      print('❌ Error sharing Excel: $e');
      rethrow;
    }
  }

  /// Extract filename from response headers
  String _extractFilename(Map<String, String> headers) {
    // Try X-Filename header first
    if (headers.containsKey('x-filename')) {
      return headers['x-filename']!;
    }
    
    // Try Content-Disposition header
    if (headers.containsKey('content-disposition')) {
      final disposition = headers['content-disposition']!;
      final filenameMatch = RegExp(r'filename="([^"]+)"').firstMatch(disposition);
      if (filenameMatch != null) {
        return filenameMatch.group(1)!;
      }
    }
    
    // Fallback filename
    final timestamp = DateTime.now().millisecondsSinceEpoch;
    return 'Statistiques_Visiteurs_$timestamp.xlsx';
  }

  /// Alternative: Export and save to device (traditional download)
  Future<String> exportAndSaveExcel() async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/api/exposant-scans/export_excel/?action=download'),
        headers: {
          'Authorization': 'Bearer $accessToken',
        },
      );

      if (response.statusCode != 200) {
        throw Exception('Failed to download Excel file');
      }

      // Save to downloads directory
      final bytes = response.bodyBytes;
      final directory = await getExternalStorageDirectory();
      final filename = _extractFilename(response.headers);
      final filePath = '${directory!.path}/$filename';
      
      final file = File(filePath);
      await file.writeAsBytes(bytes);

      return filePath;
    } catch (e) {
      rethrow;
    }
  }
}
```

---

### 2. UI Widget: Export Button

```dart
// lib/widgets/export_button.dart

import 'package:flutter/material.dart';
import '../services/excel_export_service.dart';

class ExportButton extends StatefulWidget {
  final String accessToken;
  final String baseUrl;

  const ExportButton({
    Key? key,
    required this.accessToken,
    required this.baseUrl,
  }) : super(key: key);

  @override
  State<ExportButton> createState() => _ExportButtonState();
}

class _ExportButtonState extends State<ExportButton> {
  bool _isExporting = false;

  Future<void> _handleExport() async {
    setState(() => _isExporting = true);

    try {
      final service = ExcelExportService(
        baseUrl: widget.baseUrl,
        accessToken: widget.accessToken,
      );

      // Show native share sheet
      final result = await service.exportAndShareExcel();

      if (!mounted) return;

      // Handle result
      if (result.status == ShareResultStatus.success) {
        _showSnackBar('✅ Fichier partagé avec succès!', Colors.green);
      } else if (result.status == ShareResultStatus.dismissed) {
        _showSnackBar('ℹ️ Partage annulé', Colors.grey);
      }

    } catch (e) {
      if (!mounted) return;
      _showSnackBar('❌ Erreur lors de l\'export: $e', Colors.red);
    } finally {
      if (mounted) {
        setState(() => _isExporting = false);
      }
    }
  }

  void _showSnackBar(String message, Color backgroundColor) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: backgroundColor,
        behavior: SnackBarBehavior.floating,
        duration: Duration(seconds: 3),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return ElevatedButton.icon(
      onPressed: _isExporting ? null : _handleExport,
      icon: _isExporting
          ? SizedBox(
              width: 20,
              height: 20,
              child: CircularProgressIndicator(
                strokeWidth: 2,
                valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
              ),
            )
          : Icon(Icons.share),
      label: Text(_isExporting ? 'Export en cours...' : 'Exporter'),
      style: ElevatedButton.styleFrom(
        backgroundColor: Colors.green,
        foregroundColor: Colors.white,
        padding: EdgeInsets.symmetric(horizontal: 24, vertical: 12),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(8),
        ),
      ),
    );
  }
}
```

---

### 3. Usage in Dashboard

```dart
// lib/screens/exposant_dashboard.dart

import 'package:flutter/material.dart';
import '../widgets/export_button.dart';

class ExposantDashboard extends StatelessWidget {
  final String accessToken;
  final String baseUrl;

  const ExposantDashboard({
    Key? key,
    required this.accessToken,
    required this.baseUrl,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Statistiques du Stand'),
      ),
      body: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Statistics cards
            StatsCard(title: 'Total Visites', value: '42'),
            SizedBox(height: 16),
            StatsCard(title: 'Aujourd\'hui', value: '15'),
            
            SizedBox(height: 32),
            
            // Export button
            ExportButton(
              accessToken: accessToken,
              baseUrl: baseUrl,
            ),
            
            SizedBox(height: 16),
            
            // Visitor list
            Expanded(
              child: VisitorList(),
            ),
          ],
        ),
      ),
    );
  }
}
```

---

## 🧪 Testing Steps

### 1. Test on iOS Simulator
```bash
flutter run -d "iPhone 15 Pro"
```

**Expected:**
- Tap "Exporter" button
- iOS UIActivityViewController appears
- Shows: AirDrop, Mail, Messages, Save to Files, etc.
- Select destination (e.g., "Save to Files")
- File saves successfully

### 2. Test on Android Emulator
```bash
flutter run -d emulator-5554
```

**Expected:**
- Tap "Exporter" button
- Android Share Intent chooser appears
- Shows: Gmail, Drive, WhatsApp, Bluetooth, etc.
- Select destination
- File shares successfully

### 3. Test on Physical Devices

**iOS:**
```bash
flutter run -d <device-id>
```
- Test AirDrop to Mac/iPhone
- Test "Save to Files"
- Test email attachment

**Android:**
```bash
flutter run -d <device-id>
```
- Test WhatsApp share
- Test Google Drive upload
- Test Bluetooth transfer

---

## 📊 What Appears in Share Sheet

### iOS (UIActivityViewController)
- 📤 AirDrop (to nearby devices)
- 📧 Mail
- 💬 Messages
- 📁 Save to Files
- 📋 Copy
- ➕ More Apps...

### Android (Share Intent)
- 📧 Gmail
- 💬 WhatsApp
- 📱 Telegram
- ☁️ Google Drive
- 📁 Files
- 🔵 Bluetooth
- ➕ More Apps...

---

## 🎯 User Experience Flow

1. **User taps "Exporter" button**
   - Button shows loading spinner
   - Text changes to "Export en cours..."

2. **Backend downloads Excel file**
   - ~1-2 seconds for typical data
   - File saved to temporary directory

3. **Native share sheet appears**
   - iOS: Slides up from bottom
   - Android: Dialog/bottom sheet

4. **User selects destination**
   - AirDrop to Mac
   - Email to colleague
   - Save to Google Drive
   - Share via WhatsApp
   - etc.

5. **File shared successfully**
   - Success message shows
   - Button returns to normal state

---

## ⚠️ Troubleshooting

### Issue: "Permission denied" on Android
**Solution:** Request storage permission first
```dart
import 'package:permission_handler/permission_handler.dart';

Future<void> requestPermission() async {
  if (Platform.isAndroid) {
    await Permission.storage.request();
  }
}
```

### Issue: Share sheet doesn't appear
**Solution:** Check file exists and has content
```dart
final file = File(filePath);
if (await file.exists()) {
  final size = await file.length();
  print('File size: $size bytes');
}
```

### Issue: Filename shows generic name
**Solution:** Ensure backend sends `X-Filename` header

---

## ✅ Complete Backend + Frontend Summary

### Backend Changes:
✅ Added `?action=share` parameter support
✅ Returns `Content-Disposition: inline` for mobile
✅ Adds `X-Filename` header for filename extraction

### Frontend Implementation:
✅ Uses `share_plus` package (cross-platform)
✅ Downloads file as bytes from backend
✅ Saves to temporary directory
✅ Triggers native share sheet with `Share.shareXFiles()`
✅ Handles success/error states with user feedback

### Result:
🎉 Professional native share experience on both iOS and Android!

---

## 🚀 Next Steps

1. Test on real devices (iOS + Android)
2. Add analytics tracking for exports
3. Consider adding PDF export option
4. Add share statistics (who opened file, when)

---

Need help with implementation? Let me know which part needs clarification!
