# 🚨 CRITICAL CODE BUG FOUND - Role Name Inconsistency

**Date:** December 22, 2025  
**Severity:** HIGH - Permissions may not work correctly  
**Status:** REQUIRES IMMEDIATE FIX

---

## Problem Summary

There is a **critical inconsistency** in role names across the codebase:

### UserEventAssignment Model (models.py)
```python
ROLE_CHOICES = [
    ('gestionnaire_salle', 'Gestionnaire de Salle'),      # ❌ Different!
    ('controlleur', 'Contrôleur'),                        # ❌ Different!
    ('exposant', 'Exposant'),
    ('committee', 'Committee'),
    ('participant', 'Participant'),
]
```

### Permissions File (permissions.py)
```python
# IsGestionnaire permission
role='gestionnaire_des_salles'  # ❌ This doesn't exist in ROLE_CHOICES!

# IsController permission
role='controlleur_des_badges'   # ❌ This doesn't exist in ROLE_CHOICES!
```

### Views File (views.py)
```python
# Also uses the wrong names
role='gestionnaire_des_salles'  # ❌ Wrong
role='controlleur_des_badges'   # ❌ Wrong
```

### RoomAssignment Model (models.py)
```python
ROLE_CHOICES = [
    ('gestionnaire_des_salles', 'Gestionnaire des Salles'),  # ✅ Different model
    ('controlleur_des_badges', 'Contrôleur des Badges'),     # ✅ Different model
]
```

---

## Impact

### HIGH SEVERITY ISSUES:

1. **Permissions Don't Work** ❌
   - `IsGestionnaire` permission checks for `gestionnaire_des_salles`
   - But UserEventAssignment only has `gestionnaire_salle`
   - Result: Permission checks will ALWAYS FAIL

2. **Controller Permissions Don't Work** ❌
   - `IsController` permission checks for `controlleur_des_badges`
   - But UserEventAssignment only has `controlleur`
   - Result: Controllers can't verify QR codes

3. **View Logic Broken** ❌
   - Views check for `gestionnaire_des_salles` and `controlleur_des_badges`
   - These roles don't exist in the database
   - Result: Features won't work for these users

---

## Root Cause

Two different models use different role naming conventions:
- **UserEventAssignment** (main role assignment) uses short names
- **RoomAssignment** (room-specific assignment) uses long names

The permissions and views use the long names, but the main model uses short names.

---

## Solution Options

### Option 1: Fix Models (RECOMMENDED)

Update `UserEventAssignment.ROLE_CHOICES` to match what permissions expect:

```python
# makeplus_api/events/models.py
class UserEventAssignment(models.Model):
    ROLE_CHOICES = [
        ('gestionnaire_des_salles', 'Gestionnaire de Salle'),  # ✅ Fixed
        ('controlleur_des_badges', 'Contrôleur'),              # ✅ Fixed
        ('exposant', 'Exposant'),
        ('committee', 'Committee'),
        ('participant', 'Participant'),
    ]
```

**Pros:**
- Matches existing permissions and views
- Matches RoomAssignment model
- Consistent naming across codebase

**Cons:**
- Requires database migration
- Need to update existing data

### Option 2: Fix Permissions & Views

Update all permissions and views to use short names:

```python
# makeplus_api/events/permissions.py
role='gestionnaire_salle'  # ✅ Fixed
role='controlleur'         # ✅ Fixed
```

**Pros:**
- No database migration needed
- Matches current model

**Cons:**
- More files to update
- Inconsistent with RoomAssignment

---

## Recommended Fix (Option 1)

### Step 1: Update Model

```python
# makeplus_api/events/models.py - Line 105
ROLE_CHOICES = [
    ('gestionnaire_des_salles', 'Gestionnaire de Salle'),
    ('controlleur_des_badges', 'Contrôleur'),
    ('exposant', 'Exposant'),
    ('committee', 'Committee'),
    ('participant', 'Participant'),
]

# Also update ADMIN_CREATABLE_ROLES
ADMIN_CREATABLE_ROLES = [
    ('gestionnaire_des_salles', 'Gestionnaire de Salle'),
    ('controlleur_des_badges', 'Contrôleur'),
    ('exposant', 'Exposant'),
    ('committee', 'Committee'),
]
```

### Step 2: Create Migration

```bash
python manage.py makemigrations events --name fix_role_names
```

### Step 3: Data Migration

Create a data migration to update existing records:

```python
# migrations/XXXX_fix_role_names.py
from django.db import migrations

def fix_role_names(apps, schema_editor):
    UserEventAssignment = apps.get_model('events', 'UserEventAssignment')
    
    # Update gestionnaire_salle -> gestionnaire_des_salles
    UserEventAssignment.objects.filter(
        role='gestionnaire_salle'
    ).update(role='gestionnaire_des_salles')
    
    # Update controlleur -> controlleur_des_badges
    UserEventAssignment.objects.filter(
        role='controlleur'
    ).update(role='controlleur_des_badges')

def reverse_fix(apps, schema_editor):
    UserEventAssignment = apps.get_model('events', 'UserEventAssignment')
    
    UserEventAssignment.objects.filter(
        role='gestionnaire_des_salles'
    ).update(role='gestionnaire_salle')
    
    UserEventAssignment.objects.filter(
        role='controlleur_des_badges'
    ).update(role='controlleur')

class Migration(migrations.Migration):
    dependencies = [
        ('events', 'PREVIOUS_MIGRATION'),
    ]
    
    operations = [
        migrations.RunPython(fix_role_names, reverse_fix),
    ]
```

### Step 4: Apply Migration

```bash
python manage.py migrate events
```

### Step 5: Test

```bash
# Test permissions
python manage.py shell
>>> from events.models import UserEventAssignment
>>> UserEventAssignment.objects.filter(role='gestionnaire_des_salles').count()
# Should return count > 0

# Test in views
# Login as gestionnaire and try to create an event
```

---

## Files That Need Updating

### If Using Option 1 (Recommended):

1. ✅ `makeplus_api/events/models.py` - Update ROLE_CHOICES
2. ✅ Create data migration
3. ✅ Run migration
4. ✅ Test all permissions

### If Using Option 2:

1. ❌ `makeplus_api/events/permissions.py` - Update all role checks
2. ❌ `makeplus_api/events/views.py` - Update all role checks
3. ❌ `makeplus_api/events/models.py` - Update RoomAssignment ROLE_CHOICES
4. ❌ Update documentation

---

## Testing Checklist

After fix, test these scenarios:

- [ ] Gestionnaire can create events
- [ ] Gestionnaire can create rooms
- [ ] Gestionnaire can create sessions
- [ ] Gestionnaire can mark sessions live
- [ ] Controller can verify QR codes
- [ ] Controller can access room statistics
- [ ] Participant can view sessions
- [ ] Exposant can scan QR codes
- [ ] Role-based announcement filtering works
- [ ] Room assignments work

---

## Urgency

**CRITICAL** - This bug prevents core functionality from working:
- Gestionnaires can't manage events
- Controllers can't verify badges
- Permissions are broken

**Recommendation:** Fix immediately before any production deployment.

---

## Documentation Impact

After fixing the code, the documentation is actually CORRECT! The documentation uses:
- `gestionnaire_des_salles` ✅
- `controlleur_des_badges` ✅

These are the names that SHOULD be in the code. So we need to fix the code to match the documentation, not the other way around.

---

**Priority:** 🔴 CRITICAL  
**Action Required:** Fix code immediately  
**Estimated Time:** 30 minutes  
**Risk:** HIGH - Core functionality broken
