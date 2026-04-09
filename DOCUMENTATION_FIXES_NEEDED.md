# Documentation Fixes Needed

**Date:** December 22, 2025  
**Priority:** LOW - These are minor inconsistencies that don't affect functionality

---

## 1. Role Name Standardization ⚠️ MINOR

### Issue
Documentation uses different role names than the actual code in some places.

### Current State

**In Code (`models.py`):**
```python
ROLE_CHOICES = [
    ('gestionnaire_salle', 'Gestionnaire de Salle'),
    ('controlleur', 'Contrôleur'),
    ('exposant', 'Exposant'),
    ('committee', 'Committee'),
    ('participant', 'Participant'),
]
```

**In Documentation:**
- Sometimes uses: `gestionnaire_des_salles`
- Sometimes uses: `controlleur_des_badges`

### Fix Required

Search and replace in `BACKEND_DOCUMENTATION.md`:

1. Replace `gestionnaire_des_salles` → `gestionnaire_salle`
2. Replace `controlleur_des_badges` → `controlleur`

### Locations to Update

- Permission class descriptions
- Role tables
- API examples
- Code snippets

### Impact
LOW - Both versions are understood, but consistency is better for developers

---

## 2. EventRegistration Model Not Documented

### Issue
The `EventRegistration` model exists in code but is not documented in main backend docs.

### Model Details

```python
class EventRegistration(models.Model):
    """Public event registration submissions"""
    event = models.ForeignKey(Event)
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    email = models.EmailField()
    telephone = models.CharField(max_length=20)
    pays = models.CharField(max_length=100)
    wilaya = models.CharField(max_length=100)
    secteur = models.CharField(max_length=20)
    etablissement = models.CharField(max_length=200)
    specialite = models.CharField(max_length=200)
    ateliers_selected = models.JSONField()
    is_confirmed = models.BooleanField(default=False)
    user = models.ForeignKey(User, null=True)
    participant = models.ForeignKey(Participant, null=True)
    # ... more fields
```

### Endpoints

```python
# urls.py
path('events/<uuid:event_id>/register/', views_registration.event_registration_page),
path('events/<uuid:event_id>/register/submit/', views_registration.event_registration_submit),
path('registration/success/<uuid:registration_id>/', views_registration.registration_success),
path('api/events/<uuid:event_id>/register/', views_registration.event_registration_api),
```

### Fix Required

Add a new section to `BACKEND_DOCUMENTATION.md`:

```markdown
### Public Event Registration

#### EventRegistration Model
**Purpose:** Store public registration submissions before user account creation

**Fields:**
- Personal info: nom, prenom, email, telephone
- Location: pays, wilaya
- Professional: secteur, etablissement, specialite
- Workshop selection: ateliers_selected (JSON)
- Status: is_confirmed, is_spam
- Links: user, participant (created after confirmation)

#### Registration Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/events/{id}/register/` | Registration form page |
| POST | `/events/{id}/register/submit/` | Submit registration |
| GET | `/registration/success/{id}/` | Success page |
| POST | `/api/events/{id}/register/` | API registration (JSON) |

#### Registration Flow
1. User fills public registration form
2. System creates EventRegistration record
3. Email confirmation sent
4. User confirms email
5. System creates User + Participant accounts
6. User can login with credentials
```

### Impact
LOW - This is a separate feature, main API is fully documented

---

## 3. Dashboard & Caisse Apps Not in Main Docs

### Issue
These are separate Django apps with their own functionality but not documented in main backend docs.

### Apps Found

1. **Dashboard App** (`makeplus_api/dashboard/`)
   - Email campaigns
   - Form builder
   - ePoster system
   - Has its own views, models, templates

2. **Caisse App** (`makeplus_api/caisse/`)
   - Point of sale system
   - Badge printing
   - Has its own views, models, templates

### Fix Required

Add a note in `BACKEND_DOCUMENTATION.md`:

```markdown
## Additional Django Apps

This project includes additional Django apps with separate functionality:

### Dashboard App
**Purpose:** Admin dashboard for event management, email campaigns, and ePoster submissions

**Documentation:** See separate documentation files:
- `EMAIL_CAMPAIGN_SYSTEM_COMPLETE.md`
- `EPOSTER_README.md`
- `EPOSTER_USER_GUIDE.md`

**Features:**
- Email campaign management
- Form builder
- ePoster submission system
- Committee review system

### Caisse App
**Purpose:** Point of sale and badge printing system

**Access:** `/caisse/`

**Features:**
- Badge printing
- Payment processing
- Participant check-in
```

### Impact
LOW - These are separate systems with their own docs

---

## 4. Minor Documentation Improvements

### Add Cross-References

Add links between related sections:

```markdown
**See Also:**
- [Authentication](#authentication--authorization)
- [Permissions](#permissions-system)
- [File Uploads](#file-uploads)
```

### Add Quick Start Section

Add at the beginning:

```markdown
## Quick Start

**For Developers:**
1. Clone repository
2. Install dependencies: `pip install -r requirements.txt`
3. Run migrations: `python manage.py migrate`
4. Create superuser: `python manage.py createsuperuser`
5. Run server: `python manage.py runserver`

**For API Users:**
1. Register: `POST /api/auth/register/`
2. Login: `POST /api/auth/login/`
3. Use JWT token in Authorization header
4. See [API Endpoints](#api-endpoints) for available operations
```

### Add Troubleshooting Section

```markdown
## Troubleshooting

### Common Issues

**1. "No event context found"**
- Cause: JWT token doesn't include event_id
- Solution: Call `/api/auth/select-event/` first

**2. "Permission denied"**
- Cause: User doesn't have required role
- Solution: Check user's role in UserEventAssignment

**3. "File upload fails"**
- Cause: File too large or wrong format
- Solution: Check file size (<10MB) and format (PDF only)

**4. "Token expired"**
- Cause: JWT access token expired (default: 60 minutes)
- Solution: Use refresh token: `POST /api/token/refresh/`
```

---

## Priority Summary

### Critical (None) ✅
No critical issues found

### High Priority (None) ✅
No high priority issues found

### Medium Priority
1. **Standardize role names** - 15 minutes
2. **Document EventRegistration** - 30 minutes

### Low Priority
3. **Add Dashboard/Caisse notes** - 10 minutes
4. **Add cross-references** - 20 minutes
5. **Add Quick Start** - 15 minutes
6. **Add Troubleshooting** - 20 minutes

**Total Time Estimate:** ~2 hours for all fixes

---

## Conclusion

The documentation is production-ready as-is. These fixes are cosmetic improvements that would make it even better, but they're not blocking any functionality.

**Recommendation:** Deploy as-is, fix during next documentation update cycle.
