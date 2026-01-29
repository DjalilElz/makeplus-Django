# Event PDF Files Implementation Guide

**Date:** December 21, 2025  
**Status:** Implemented and Production Ready  
**Version:** 1.0

---

## 📋 Overview

This document explains how PDF file storage is implemented for Event Programme and Guide files in the MakePlus backend system. The implementation follows Django best practices for file handling with optimized performance and security.

---

## 🎯 Features Added

### Two PDF File Types per Event:
1. **Programme File** (`programme_file`) - Event schedule/program document
2. **Guide File** (`guide_file`) - Event guide/handbook document

---

## 🏗️ Implementation Details

### 1. Database Schema (Model Layer)

**File:** `makeplus_api/events/models.py`

```python
class Event(models.Model):
    # ... other fields ...
    
    # Event files
    programme_file = models.FileField(
        upload_to='events/programmes/', 
        blank=True, 
        null=True, 
        help_text="Event programme PDF"
    )
    guide_file = models.FileField(
        upload_to='events/guides/', 
        blank=True, 
        null=True, 
        help_text="Event guide PDF"
    )
```

**Key Characteristics:**
- Uses Django's `FileField` for flexible file storage
- Organizes files in structured directories:
  - Programme PDFs: `media/events/programmes/`
  - Guide PDFs: `media/events/guides/`
- Optional fields (`blank=True, null=True`) - not all events require these files
- Descriptive help text for admin interface

---

### 2. API Serialization Layer

**File:** `makeplus_api/events/serializers.py`

```python
class EventSerializer(serializers.ModelSerializer):
    # ... other fields ...
    
    class Meta:
        model = Event
        fields = [
            # ... other fields ...
            'programme_file', 
            'guide_file',
            # ... remaining fields ...
        ]
        read_only_fields = [
            'id', 
            'total_participants', 
            'total_exhibitors', 
            'total_rooms', 
            'created_at', 
            'updated_at'
        ]
```

**API Response Format:**
```json
{
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "MakePlus Summit 2025",
    "programme_file": "http://localhost:8000/media/events/programmes/summit_programme.pdf",
    "guide_file": "http://localhost:8000/media/events/guides/summit_guide.pdf",
    // ... other fields
}
```

---

### 3. File Storage Configuration

**File:** `makeplus_api/makeplus_api/settings.py`

```python
# Media files configuration
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
```

**File:** `makeplus_api/makeplus_api/urls.py`

```python
from django.conf import settings
from django.conf.urls.static import static

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

**Storage Structure:**
```
makeplus_backend/
├── makeplus_api/
│   ├── media/
│   │   └── events/
│   │       ├── programmes/
│   │       │   ├── event1_programme.pdf
│   │       │   └── event2_programme.pdf
│   │       └── guides/
│   │           ├── event1_guide.pdf
│   │           └── event2_guide.pdf
```

---

## 🚀 Performance Optimizations

### Why This Approach is Fast:

1. **Direct File System Storage**
   - Files stored on local filesystem (fastest access)
   - No database BLOB storage (avoids DB bloat)
   - Direct HTTP serving through web server

2. **Lazy Loading**
   - URLs returned in API, not file content
   - Client downloads files only when needed
   - No impact on list/search operations

3. **Efficient Querying**
   - FileField stores only file path (VARCHAR)
   - Minimal database overhead
   - Fast API response times

4. **Static File Serving**
   - In production: Nginx/Apache serve files directly
   - In development: Django serves via `static()` helper
   - No application code involved in file delivery

5. **Scalability Options**
   - Easy migration to cloud storage (S3, CloudFront)
   - CDN integration for global distribution
   - Can add file size validation/compression

---

## 📡 API Endpoints

### Create/Update Event with PDF Files

**POST** `/api/events/`  
**PUT** `/api/events/{event_id}/`  
**PATCH** `/api/events/{event_id}/`

**Request Format:** `multipart/form-data`

**Example using cURL:**
```bash
curl -X POST http://localhost:8000/api/events/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "name=MakePlus Summit 2025" \
  -F "description=Annual tech summit" \
  -F "start_date=2025-06-01T09:00:00Z" \
  -F "end_date=2025-06-03T18:00:00Z" \
  -F "location=Paris Convention Center" \
  -F "status=upcoming" \
  -F "programme_file=@/path/to/programme.pdf" \
  -F "guide_file=@/path/to/guide.pdf"
```

**Example using Python Requests:**
```python
import requests

url = "http://localhost:8000/api/events/"
headers = {"Authorization": "Bearer YOUR_JWT_TOKEN"}

files = {
    'programme_file': open('programme.pdf', 'rb'),
    'guide_file': open('guide.pdf', 'rb')
}

data = {
    'name': 'MakePlus Summit 2025',
    'description': 'Annual tech summit',
    'start_date': '2025-06-01T09:00:00Z',
    'end_date': '2025-06-03T18:00:00Z',
    'location': 'Paris Convention Center',
    'status': 'upcoming'
}

response = requests.post(url, headers=headers, data=data, files=files)
print(response.json())
```

**Example using Flutter:**
```dart
import 'package:http/http.dart' as http;
import 'dart:io';

Future<void> createEventWithPDFs() async {
  var uri = Uri.parse('http://localhost:8000/api/events/');
  var request = http.MultipartRequest('POST', uri);
  
  // Add authorization header
  request.headers['Authorization'] = 'Bearer YOUR_JWT_TOKEN';
  
  // Add text fields
  request.fields['name'] = 'MakePlus Summit 2025';
  request.fields['description'] = 'Annual tech summit';
  request.fields['start_date'] = '2025-06-01T09:00:00Z';
  request.fields['end_date'] = '2025-06-03T18:00:00Z';
  request.fields['location'] = 'Paris Convention Center';
  request.fields['status'] = 'upcoming';
  
  // Add PDF files
  request.files.add(
    await http.MultipartFile.fromPath(
      'programme_file',
      '/path/to/programme.pdf',
    ),
  );
  
  request.files.add(
    await http.MultipartFile.fromPath(
      'guide_file',
      '/path/to/guide.pdf',
    ),
  );
  
  var response = await request.send();
  var responseData = await response.stream.bytesToString();
  print(responseData);
}
```

### Get Event with PDF URLs

**GET** `/api/events/{event_id}/`

**Response:**
```json
{
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "MakePlus Summit 2025",
    "description": "Annual tech summit",
    "start_date": "2025-06-01T09:00:00Z",
    "end_date": "2025-06-03T18:00:00Z",
    "location": "Paris Convention Center",
    "status": "upcoming",
    "programme_file": "http://localhost:8000/media/events/programmes/programme_abc123.pdf",
    "guide_file": "http://localhost:8000/media/events/guides/guide_xyz789.pdf",
    "created_at": "2025-12-21T10:30:00Z",
    "updated_at": "2025-12-21T10:30:00Z"
}
```

### Update Only PDF Files

**PATCH** `/api/events/{event_id}/`

```bash
curl -X PATCH http://localhost:8000/api/events/{event_id}/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "programme_file=@/path/to/new_programme.pdf"
```

### Remove PDF Files

**PATCH** `/api/events/{event_id}/`

```bash
curl -X PATCH http://localhost:8000/api/events/{event_id}/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "programme_file="
```

---

## 🔒 Security Considerations

### Current Implementation:
1. **Authentication Required** - JWT token needed for create/update
2. **Permission Checks** - Only authorized users can modify events
3. **File Path Storage** - Only relative paths stored in database

### Recommended Enhancements:

```python
from django.core.validators import FileExtensionValidator

class Event(models.Model):
    # ... other fields ...
    
    programme_file = models.FileField(
        upload_to='events/programmes/', 
        blank=True, 
        null=True,
        validators=[FileExtensionValidator(['pdf'])],
        max_length=255,
        help_text="Event programme PDF (max 10MB)"
    )
    
    guide_file = models.FileField(
        upload_to='events/guides/', 
        blank=True, 
        null=True,
        validators=[FileExtensionValidator(['pdf'])],
        max_length=255,
        help_text="Event guide PDF (max 10MB)"
    )
```

**File Size Validation in Settings:**
```python
# settings.py
DATA_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB
```

---

## 📦 Production Deployment

### Option 1: Static File Server (Nginx/Apache)

**Nginx Configuration:**
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    # Django application
    location / {
        proxy_pass http://localhost:8000;
    }
    
    # Serve media files directly
    location /media/ {
        alias /path/to/makeplus_backend/makeplus_api/media/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

### Option 2: Cloud Storage (AWS S3)

**Install boto3:**
```bash
pip install boto3 django-storages
```

**Update settings.py:**
```python
# settings.py
INSTALLED_APPS += ['storages']

# AWS S3 Configuration
AWS_ACCESS_KEY_ID = 'your-access-key'
AWS_SECRET_ACCESS_KEY = 'your-secret-key'
AWS_STORAGE_BUCKET_NAME = 'makeplus-media'
AWS_S3_REGION_NAME = 'eu-west-1'
AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
AWS_DEFAULT_ACL = 'public-read'

# Use S3 for media files
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/'
```

### Option 3: CDN Integration

For global distribution and faster downloads:
- CloudFlare
- Amazon CloudFront
- Azure CDN
- Google Cloud CDN

---

## 🧪 Testing

### Test File Upload:

```python
# test_event_files.py
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from events.models import Event
from django.contrib.auth.models import User

class EventFileTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser')
    
    def test_upload_programme_file(self):
        # Create a simple PDF file
        pdf_content = b'%PDF-1.4 test content'
        programme = SimpleUploadedFile(
            "programme.pdf", 
            pdf_content, 
            content_type="application/pdf"
        )
        
        event = Event.objects.create(
            name="Test Event",
            start_date="2025-06-01T09:00:00Z",
            end_date="2025-06-03T18:00:00Z",
            location="Test Location",
            programme_file=programme,
            created_by=self.user
        )
        
        self.assertTrue(event.programme_file)
        self.assertIn('events/programmes/', event.programme_file.name)
    
    def test_event_without_files(self):
        event = Event.objects.create(
            name="Test Event",
            start_date="2025-06-01T09:00:00Z",
            end_date="2025-06-03T18:00:00Z",
            location="Test Location",
            created_by=self.user
        )
        
        self.assertFalse(event.programme_file)
        self.assertFalse(event.guide_file)
```

---

## 🛠️ Maintenance Tasks

### Cleanup Old Files

```python
# cleanup_orphaned_files.py
import os
from django.conf import settings
from events.models import Event

def cleanup_orphaned_files():
    """Remove files that are no longer referenced in database"""
    
    # Get all file paths from database
    db_programmes = set(Event.objects.exclude(
        programme_file=''
    ).values_list('programme_file', flat=True))
    
    db_guides = set(Event.objects.exclude(
        guide_file=''
    ).values_list('guide_file', flat=True))
    
    # Check filesystem
    media_root = settings.MEDIA_ROOT
    programmes_dir = os.path.join(media_root, 'events', 'programmes')
    guides_dir = os.path.join(media_root, 'events', 'guides')
    
    # Remove orphaned programmes
    if os.path.exists(programmes_dir):
        for filename in os.listdir(programmes_dir):
            file_path = os.path.join('events/programmes', filename)
            if file_path not in db_programmes:
                os.remove(os.path.join(programmes_dir, filename))
                print(f"Removed orphaned file: {filename}")
    
    # Remove orphaned guides
    if os.path.exists(guides_dir):
        for filename in os.listdir(guides_dir):
            file_path = os.path.join('events/guides', filename)
            if file_path not in db_guides:
                os.remove(os.path.join(guides_dir, filename))
                print(f"Removed orphaned file: {filename}")
```

---

## 📊 Database Migration

The PDF file fields were added via migration. If you need to create the migration:

```bash
cd makeplus_api
python manage.py makemigrations events
python manage.py migrate events
```

**Migration file example:**
```python
# migrations/XXXX_add_pdf_files.py
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('events', 'previous_migration'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='programme_file',
            field=models.FileField(
                blank=True, 
                null=True, 
                upload_to='events/programmes/',
                help_text='Event programme PDF'
            ),
        ),
        migrations.AddField(
            model_name='event',
            name='guide_file',
            field=models.FileField(
                blank=True, 
                null=True, 
                upload_to='events/guides/',
                help_text='Event guide PDF'
            ),
        ),
    ]
```

---

## 🎯 Summary

### ✅ What's Implemented:
- Two PDF file fields per event (programme + guide)
- Organized file storage in structured directories
- RESTful API with multipart/form-data support
- Full CRUD operations for file management
- Optimized for fast response times
- Production-ready configuration

### 🚀 Performance Benefits:
- File system storage (fastest access)
- Lazy loading (URLs only in API)
- No database bloat
- CDN-ready architecture
- Scalable to cloud storage

### 🔐 Security:
- Authentication required
- Permission-based access
- Path-only storage in database
- Ready for file validation

### 📱 Client Integration:
- Standard multipart/form-data
- Compatible with all HTTP clients
- Flutter, React, Angular, Vue support
- Direct URL access for downloads

---

## 📞 Support

For questions or issues related to PDF file handling:
1. Check this documentation first
2. Review Django FileField documentation
3. Test with provided code examples
4. Check server logs for upload errors

**Last Updated:** December 21, 2025
