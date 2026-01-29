# Event PDF Files - Quick Reference Card

## 🎯 Quick Start

### Upload Event with PDFs
```bash
curl -X POST http://localhost:8000/api/events/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "name=Event Name" \
  -F "start_date=2025-12-01T09:00:00Z" \
  -F "end_date=2025-12-03T18:00:00Z" \
  -F "location=Location" \
  -F "status=upcoming" \
  -F "programme_file=@programme.pdf" \
  -F "guide_file=@guide.pdf"
```

### Response
```json
{
  "id": "uuid",
  "name": "Event Name",
  "programme_file": "http://localhost:8000/media/events/programmes/file.pdf",
  "guide_file": "http://localhost:8000/media/events/guides/file.pdf"
}
```

---

## 📱 Client Code Examples

### Python (requests)
```python
import requests

files = {
    'programme_file': open('programme.pdf', 'rb'),
    'guide_file': open('guide.pdf', 'rb')
}
data = {'name': 'Event', 'start_date': '2025-12-01T09:00:00Z', ...}
response = requests.post(
    'http://localhost:8000/api/events/',
    headers={'Authorization': 'Bearer TOKEN'},
    data=data,
    files=files
)
```

### Flutter
```dart
var request = http.MultipartRequest('POST', uri);
request.headers['Authorization'] = 'Bearer TOKEN';
request.fields['name'] = 'Event Name';
request.files.add(
  await http.MultipartFile.fromPath('programme_file', pdfPath)
);
var response = await request.send();
```

### JavaScript (Fetch)
```javascript
const formData = new FormData();
formData.append('name', 'Event Name');
formData.append('programme_file', programmeFile);
formData.append('guide_file', guideFile);

fetch('http://localhost:8000/api/events/', {
  method: 'POST',
  headers: {'Authorization': 'Bearer TOKEN'},
  body: formData
});
```

---

## 🔄 Common Operations

### Get Event with PDFs
```bash
GET /api/events/{id}/
Authorization: Bearer TOKEN
```

### Update PDFs Only
```bash
PATCH /api/events/{id}/
Authorization: Bearer TOKEN
Content-Type: multipart/form-data

programme_file: [new PDF]
```

### Remove PDF
```bash
PATCH /api/events/{id}/
Authorization: Bearer TOKEN
Content-Type: multipart/form-data

programme_file: ""
```

---

## 📂 File Structure

```
media/
└── events/
    ├── programmes/
    │   └── programme_*.pdf
    └── guides/
        └── guide_*.pdf
```

---

## ⚙️ Configuration

### Django Settings
```python
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
```

### Model
```python
programme_file = models.FileField(
    upload_to='events/programmes/',
    blank=True, null=True
)
guide_file = models.FileField(
    upload_to='events/guides/',
    blank=True, null=True
)
```

---

## ✅ Verification Checklist

- [ ] Model has `programme_file` and `guide_file` fields
- [ ] Serializer includes both fields
- [ ] `MEDIA_ROOT` and `MEDIA_URL` configured
- [ ] Directories exist: `media/events/programmes/` and `media/events/guides/`
- [ ] URL serving configured in `urls.py`
- [ ] Authentication working (JWT)
- [ ] Permissions configured

**Run:** `python verify_pdf_implementation.py` to check all

---

## 🚀 Performance Tips

1. ⚡ API returns URLs only (not file content)
2. 💾 Files stored on filesystem (not in database)
3. 🌐 Use CDN for global distribution
4. 🗜️ Compress PDFs before uploading
5. 📦 Set cache headers for better performance

---

## 🔒 Security Best Practices

1. ✅ Validate file extensions (.pdf only)
2. ✅ Limit file size (10MB recommended)
3. ✅ Use authentication for uploads
4. ✅ Check permissions before serving
5. ✅ Consider virus scanning

---

## 🆘 Troubleshooting

### Upload fails
- Check JWT token is valid
- Verify user has permissions
- Check file size limits
- Ensure content-type is multipart/form-data

### Files not accessible
- Check MEDIA_URL configured
- Verify URL patterns include static()
- Check file permissions
- Ensure directories exist

### URLs are broken
- Check MEDIA_URL has leading/trailing slashes
- Verify domain in production
- Check nginx/apache configuration

---

## 📚 Documentation

- **Complete Guide:** [EVENT_PDF_FILES_IMPLEMENTATION.md](EVENT_PDF_FILES_IMPLEMENTATION.md)
- **Backend Docs:** [BACKEND_DOCUMENTATION.md](BACKEND_DOCUMENTATION.md)
- **Architecture:** [EVENT_PDF_ARCHITECTURE.md](EVENT_PDF_ARCHITECTURE.md)
- **Summary:** [EVENT_PDF_FILES_SUMMARY.md](EVENT_PDF_FILES_SUMMARY.md)

---

## 📊 API Endpoints Summary

| Method | Endpoint | Purpose | Auth |
|--------|----------|---------|------|
| POST | `/api/events/` | Create with PDFs | Yes |
| GET | `/api/events/` | List events | Yes |
| GET | `/api/events/{id}/` | Get event + URLs | Yes |
| PUT | `/api/events/{id}/` | Full update | Yes |
| PATCH | `/api/events/{id}/` | Partial update | Yes |
| DELETE | `/api/events/{id}/` | Delete event | Yes |

---

**Quick Reference Card - Version 1.0**  
**Last Updated:** December 21, 2025
