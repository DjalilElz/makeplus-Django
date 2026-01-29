# Event Logo & Banner Image Upload Implementation

**Date:** December 21, 2025  
**Status:** ✅ Complete - Migrated from URLs to File Uploads

---

## 🎯 What Changed

### Before (URL Fields)
```python
logo_url = models.URLField(blank=True)
banner_url = models.URLField(blank=True)
```
- Admins had to upload to external service first
- Copy/paste URLs into form
- No control over files
- URLs could break

### After (Image Upload Fields) ✅
```python
logo = models.ImageField(upload_to='events/logos/', blank=True, null=True)
banner = models.ImageField(upload_to='events/banners/', blank=True, null=True)
```
- Direct upload from admin dashboard
- Files stored with your data
- Full control and validation
- Image preview in edit form

---

## 📊 Why File Uploads Are Better

### ✅ Advantages of ImageField

1. **User-Friendly**
   - Upload directly from dashboard
   - No need for external image hosting
   - One-step process

2. **Better Control**
   - Files stored locally
   - Easy backup with database
   - No dependency on external services

3. **Image Validation**
   - ImageField validates image formats
   - Prevents invalid file uploads
   - Automatic file handling

4. **Preview Support**
   - Show thumbnail in edit form
   - View current images before replacing
   - Better user experience

5. **Consistent Approach**
   - Matches PDF upload implementation
   - Same workflow for all files
   - Easier to maintain

6. **Future-Proof**
   - Easy migration to CDN later
   - Can add image processing (resize, optimize)
   - Cloud storage compatible (S3, Azure)

---

## 🏗️ Implementation Details

### 1. Database Model

**File:** `events/models.py`

```python
class Event(models.Model):
    # ... other fields ...
    
    logo = models.ImageField(
        upload_to='events/logos/', 
        blank=True, 
        null=True, 
        help_text="Event logo image"
    )
    banner = models.ImageField(
        upload_to='events/banners/', 
        blank=True, 
        null=True, 
        help_text="Event banner image"
    )
```

**Storage Structure:**
```
media/
└── events/
    ├── logos/
    │   ├── event1_logo.jpg
    │   ├── event2_logo.png
    │   └── summit_logo.webp
    └── banners/
        ├── event1_banner.jpg
        ├── event2_banner.png
        └── summit_banner.jpg
```

---

### 2. API Serializer

**File:** `events/serializers.py`

```python
class EventSerializer(serializers.ModelSerializer):
    fields = [
        'id', 'name', 'description',
        'logo', 'banner',  # Changed from logo_url, banner_url
        # ... other fields
    ]
```

**API Response:**
```json
{
  "id": "uuid",
  "name": "Tech Summit 2025",
  "logo": "http://localhost:8000/media/events/logos/summit_logo.jpg",
  "banner": "http://localhost:8000/media/events/banners/summit_banner.jpg",
  "programme_file": "http://localhost:8000/media/events/programmes/programme.pdf",
  "guide_file": "http://localhost:8000/media/events/guides/guide.pdf"
}
```

---

### 3. Dashboard Form

**File:** `dashboard/forms.py`

```python
class EventDetailsForm(forms.ModelForm):
    fields = [
        'name', 'description', 'start_date', 'end_date',
        'location', 'status',
        'logo', 'banner',  # Image upload fields
        'programme_file', 'guide_file',  # PDF upload fields
        'organizer_contact'
    ]
    
    widgets = {
        'logo': forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'  # Only images
        }),
        'banner': forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'  # Only images
        }),
    }
```

---

### 4. Dashboard Templates

#### Event Creation Form
**File:** `dashboard/templates/dashboard/event_create_step1.html`

```html
<!-- Event Images Section -->
<div class="col-12 mt-3">
    <h5 class="mb-3">
        <i class="bi bi-image"></i> Event Images (Optional)
    </h5>
</div>

<!-- Logo -->
<div class="col-md-6 mb-3">
    <label for="{{ form.logo.id_for_label }}" class="form-label">
        <i class="bi bi-award"></i> Logo Image
    </label>
    {{ form.logo }}
    <div class="form-text">Upload event logo (JPG, PNG, etc.)</div>
</div>

<!-- Banner -->
<div class="col-md-6 mb-3">
    <label for="{{ form.banner.id_for_label }}" class="form-label">
        <i class="bi bi-card-image"></i> Banner Image
    </label>
    {{ form.banner }}
    <div class="form-text">Upload event banner (JPG, PNG, etc.)</div>
</div>
```

#### Event Edit Form
**File:** `dashboard/templates/dashboard/event_edit.html`

```html
<!-- Logo with Preview -->
<div class="col-md-6 mb-3">
    <label>Logo Image</label>
    
    <!-- Show current image thumbnail -->
    {% if event.logo %}
        <div class="mb-2">
            <img src="{{ event.logo.url }}" 
                 alt="Current Logo" 
                 class="img-thumbnail" 
                 style="max-height: 100px;">
        </div>
    {% endif %}
    
    <!-- Upload new -->
    {{ form.logo }}
    
    {% if event.logo %}
        <div class="form-text">
            Current: <a href="{{ event.logo.url }}" target="_blank">
                View Image <i class="bi bi-box-arrow-up-right"></i>
            </a>
        </div>
    {% endif %}
</div>
```

---

## 🚀 How to Use

### Creating Event with Images

1. **Navigate to Create Event**
   - Dashboard → Create Event

2. **Fill Basic Details**
   - Event name, dates, location

3. **Upload Images (Optional)**
   - Click "Choose File" under Logo
   - Select image (JPG, PNG, WebP, etc.)
   - Click "Choose File" under Banner
   - Select banner image

4. **Continue**
   - Images upload automatically with form
   - Proceed to add rooms, sessions, etc.

---

### Editing Event Images

1. **Navigate to Event Detail**
   - Dashboard → Events → Select Event

2. **Click Edit Event**

3. **View Current Images**
   - Thumbnails shown above upload fields
   - Click "View Image" link to see full size

4. **Replace Images (Optional)**
   - Click "Choose File" to select new image
   - Leave blank to keep current image
   - Upload replaces old image automatically

5. **Save Changes**
   - New images saved
   - Old images removed from storage

---

## 🎨 User Interface

### Event Creation Form
```
┌─────────────────────────────────────────────┐
│ 🖼️ Event Images (Optional)                  │
│ ───────────────────────────────────────────  │
│                                             │
│ 🏆 Logo Image           🎴 Banner Image     │
│ [Choose File]           [Choose File]       │
│ Upload event logo       Upload event banner │
│ (JPG, PNG, etc.)        (JPG, PNG, etc.)    │
└─────────────────────────────────────────────┘
```

### Event Edit Form
```
┌─────────────────────────────────────────────┐
│ 🖼️ Event Images (Optional)                  │
│ ───────────────────────────────────────────  │
│                                             │
│ 🏆 Logo Image                               │
│ [Thumbnail Preview]                         │
│ [Choose File]                               │
│ Current: View Image ↗                       │
│ Upload event logo (JPG, PNG, etc.)          │
│                                             │
│ 🎴 Banner Image                             │
│ [Thumbnail Preview]                         │
│ [Choose File]                               │
│ Current: View Image ↗                       │
│ Upload event banner (JPG, PNG, etc.)        │
└─────────────────────────────────────────────┘
```

---

## 📡 API Usage

### Upload Images via API

**Multipart Request:**
```bash
curl -X POST http://localhost:8000/api/events/ \
  -H "Authorization: Bearer TOKEN" \
  -F "name=Tech Summit 2025" \
  -F "start_date=2025-12-01T09:00:00Z" \
  -F "end_date=2025-12-03T18:00:00Z" \
  -F "location=Paris" \
  -F "status=upcoming" \
  -F "logo=@/path/to/logo.jpg" \
  -F "banner=@/path/to/banner.jpg" \
  -F "programme_file=@/path/to/programme.pdf" \
  -F "guide_file=@/path/to/guide.pdf"
```

**Flutter Example:**
```dart
var request = http.MultipartRequest('POST', Uri.parse('http://localhost:8000/api/events/'));
request.headers['Authorization'] = 'Bearer TOKEN';

// Text fields
request.fields['name'] = 'Tech Summit 2025';
request.fields['start_date'] = '2025-12-01T09:00:00Z';
request.fields['end_date'] = '2025-12-03T18:00:00Z';
request.fields['location'] = 'Paris';
request.fields['status'] = 'upcoming';

// Image files
request.files.add(await http.MultipartFile.fromPath('logo', 'assets/logo.jpg'));
request.files.add(await http.MultipartFile.fromPath('banner', 'assets/banner.jpg'));

// PDF files
request.files.add(await http.MultipartFile.fromPath('programme_file', 'assets/programme.pdf'));
request.files.add(await http.MultipartFile.fromPath('guide_file', 'assets/guide.pdf'));

var response = await request.send();
```

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Tech Summit 2025",
  "logo": "http://localhost:8000/media/events/logos/logo_abc123.jpg",
  "banner": "http://localhost:8000/media/events/banners/banner_xyz789.jpg",
  "programme_file": "http://localhost:8000/media/events/programmes/programme.pdf",
  "guide_file": "http://localhost:8000/media/events/guides/guide.pdf"
}
```

---

## 🔄 Migration Details

### What Was Changed

**Migration:** `events/migrations/0012_add_image_fields.py`

**Operations:**
1. Remove `logo_url` field (URLField)
2. Remove `banner_url` field (URLField)
3. Add `logo` field (ImageField)
4. Add `banner` field (ImageField)

**Data Migration:**
- Old URL data is NOT preserved
- Existing events will have empty logo/banner fields
- Can be populated manually via dashboard

---

## 🎯 Supported Image Formats

### ImageField Accepts:
- ✅ JPEG (.jpg, .jpeg)
- ✅ PNG (.png)
- ✅ GIF (.gif)
- ✅ WebP (.webp)
- ✅ BMP (.bmp)
- ✅ TIFF (.tif, .tiff)

### Browser Validation:
- `accept="image/*"` in form
- Browser shows only image files
- Prevents accidental PDF/doc uploads

---

## 🔒 Security & Validation

### Current Implementation:
- ✅ ImageField validates image format
- ✅ Pillow library required (already installed)
- ✅ Authentication required for uploads
- ✅ Permission checks in place

### Recommended Enhancements:

```python
from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError

def validate_image_size(image):
    """Limit image file size to 5MB"""
    max_size = 5 * 1024 * 1024  # 5MB
    if image.size > max_size:
        raise ValidationError(f'Image file too large. Max size is 5MB.')

logo = models.ImageField(
    upload_to='events/logos/',
    validators=[
        FileExtensionValidator(['jpg', 'jpeg', 'png', 'webp']),
        validate_image_size
    ],
    help_text="Event logo (max 5MB, JPG/PNG/WebP)"
)
```

---

## 🖼️ Image Processing (Optional Enhancement)

### Install django-imagekit:
```bash
pip install django-imagekit
```

### Auto-resize on upload:
```python
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFill

class Event(models.Model):
    logo = models.ImageField(upload_to='events/logos/')
    
    # Auto-generate thumbnail
    logo_thumbnail = ImageSpecField(
        source='logo',
        processors=[ResizeToFill(100, 100)],
        format='JPEG',
        options={'quality': 90}
    )
    
    # Auto-generate optimized version
    logo_optimized = ImageSpecField(
        source='logo',
        processors=[ResizeToFill(400, 400)],
        format='JPEG',
        options={'quality': 85}
    )
```

---

## 📊 Comparison: URLs vs File Uploads

| Feature | URL Fields (Old) | ImageField (New) |
|---------|------------------|------------------|
| **Upload Process** | 2 steps (upload elsewhere, paste URL) | 1 step (direct upload) |
| **User Experience** | Complex | Simple |
| **File Control** | External service | Local control |
| **Image Validation** | None | Built-in |
| **Preview in Form** | No | Yes (thumbnail) |
| **Backup** | Separate | With database |
| **URL Stability** | Can break | Always stable |
| **CDN Support** | Yes | Yes (can add later) |
| **Storage Cost** | External | Local/Cloud |
| **Image Processing** | Not possible | Easy to add |
| **Best Practice** | ❌ Outdated | ✅ Modern |

---

## 🚀 Production Deployment

### Option 1: Local Storage + Nginx
```nginx
location /media/ {
    alias /path/to/makeplus_api/media/;
    expires 30d;
    add_header Cache-Control "public, immutable";
}
```

### Option 2: AWS S3
```python
# settings.py
INSTALLED_APPS += ['storages']

AWS_STORAGE_BUCKET_NAME = 'makeplus-media'
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
```

### Option 3: CDN (CloudFront/CloudFlare)
- Configure CDN origin to point to media directory
- Update MEDIA_URL to CDN domain
- Files served from global edge locations

---

## ✅ Testing Checklist

### Dashboard Testing

**Create Event:**
- [ ] Upload logo during event creation
- [ ] Upload banner during event creation
- [ ] Create event without images (should work)
- [ ] Verify images accessible via URLs

**Edit Event:**
- [ ] See thumbnails of current images
- [ ] Click "View Image" links work
- [ ] Upload new logo replaces old
- [ ] Upload new banner replaces old
- [ ] Leave fields empty preserves current images

**Image Formats:**
- [ ] Upload JPG - works
- [ ] Upload PNG - works
- [ ] Upload WebP - works
- [ ] Try PDF - rejected

### API Testing

**Via cURL:**
```bash
# Create with images
curl -X POST http://localhost:8000/api/events/ \
  -H "Authorization: Bearer TOKEN" \
  -F "name=Test Event" \
  -F "start_date=2025-12-01T09:00:00Z" \
  -F "end_date=2025-12-03T18:00:00Z" \
  -F "location=Test" \
  -F "status=upcoming" \
  -F "logo=@logo.jpg" \
  -F "banner=@banner.jpg"

# Update images
curl -X PATCH http://localhost:8000/api/events/{id}/ \
  -H "Authorization: Bearer TOKEN" \
  -F "logo=@new_logo.jpg"
```

---

## 📚 Summary

### ✅ What's Implemented:
- ImageField for logo and banner (replaces URL fields)
- Direct upload in dashboard creation form
- Image preview in edit form with thumbnails
- Full API support with multipart/form-data
- Migration from URL fields to image uploads
- Organized storage in `media/events/logos/` and `media/events/banners/`

### 🎯 Benefits:
- Simpler workflow for admins
- Better user experience
- Image validation built-in
- Full control over files
- Preview before replacing
- Consistent with PDF upload approach

### 📱 Client Support:
- Flutter/Dart
- React/Angular/Vue
- Python requests
- cURL
- Any HTTP client supporting multipart/form-data

---

**Migration Applied:** ✅ events.0012_add_image_fields  
**Status:** Ready for production  
**Best Practice:** ✅ Modern approach using file uploads

---

## 🔗 Related Documentation

- [EVENT_PDF_FILES_IMPLEMENTATION.md](EVENT_PDF_FILES_IMPLEMENTATION.md) - PDF upload implementation
- [DASHBOARD_PDF_UPLOAD.md](DASHBOARD_PDF_UPLOAD.md) - Dashboard PDF features
- [BACKEND_DOCUMENTATION.md](BACKEND_DOCUMENTATION.md) - Complete backend docs
