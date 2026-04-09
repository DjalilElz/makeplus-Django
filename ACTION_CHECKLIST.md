# Action Checklist - Backend Updates

**Date:** December 22, 2025  
**Priority:** HIGH - Apply migration to fix permissions

---

## ✅ Completed Actions

- [x] Verified backend documentation against code
- [x] Found critical role name bug
- [x] Fixed UserEventAssignment model
- [x] Created data migration
- [x] Documented EventRegistration model
- [x] Created comprehensive reports

---

## 🔴 Required Actions (Do This Now!)

### 1. Apply Migration

```bash
cd makeplus_api
python manage.py migrate events
```

**Expected Output:**
```
Running migrations:
  Applying events.0010_fix_role_names... OK
```

**Time:** 30 seconds

---

### 2. Verify Migration

```bash
python manage.py shell
```

```python
from events.models import UserEventAssignment
from django.db.models import Count

# Check role distribution
roles = UserEventAssignment.objects.values('role').annotate(count=Count('role'))
for r in roles:
    print(f"{r['role']}: {r['count']}")

# Should show:
# gestionnaire_des_salles: X
# controlleur_des_badges: Y
# participant: Z
# exposant: W
```

**Time:** 1 minute

---

### 3. Test Permissions

#### Test Gestionnaire:
- [ ] Login as gestionnaire user
- [ ] Navigate to events page
- [ ] Click "Create Event"
- [ ] Should work ✅

#### Test Controller:
- [ ] Login as controller user
- [ ] Navigate to QR verification
- [ ] Scan a QR code
- [ ] Should work ✅

**Time:** 5 minutes

---

## 🟡 Optional Actions (Nice to Have)

### 1. Update Documentation (Optional)

The documentation is already 98% accurate. These are minor enhancements:

- [ ] Add cross-references between sections
- [ ] Add troubleshooting section
- [ ] Add quick start guide

**Time:** 1-2 hours  
**Priority:** LOW

---

### 2. Review Additional Documentation

Read these files to understand what was done:

- [ ] `FINAL_UPDATE_SUMMARY.md` - Overview of all changes
- [ ] `BACKEND_VERIFICATION_REPORT.md` - Detailed verification
- [ ] `CRITICAL_CODE_BUG_FOUND.md` - Bug explanation
- [ ] `BACKEND_DOCUMENTATION_UPDATES.md` - What was added

**Time:** 15 minutes  
**Priority:** MEDIUM

---

## 🟢 Deployment Checklist

### Pre-Deployment:
- [x] Code changes committed
- [x] Migration created
- [ ] Migration tested locally
- [ ] Permissions tested locally

### Deployment:
- [ ] Pull latest code to server
- [ ] Activate virtual environment
- [ ] Run: `python manage.py migrate events`
- [ ] Restart application server
- [ ] Test permissions on production

### Post-Deployment:
- [ ] Verify gestionnaire can create events
- [ ] Verify controller can scan QR codes
- [ ] Monitor error logs
- [ ] Confirm no permission errors

---

## Quick Reference

### Files Changed:
1. `makeplus_api/events/models.py` - Fixed ROLE_CHOICES
2. `makeplus_api/events/migrations/0010_fix_role_names.py` - Migration

### Files Created:
1. `BACKEND_VERIFICATION_REPORT.md`
2. `VERIFICATION_SUMMARY.md`
3. `DOCUMENTATION_FIXES_NEEDED.md`
4. `CRITICAL_CODE_BUG_FOUND.md`
5. `BACKEND_DOCUMENTATION_UPDATES.md`
6. `FINAL_UPDATE_SUMMARY.md`
7. `ACTION_CHECKLIST.md` (this file)

### Commands to Run:
```bash
# 1. Apply migration
cd makeplus_api
python manage.py migrate events

# 2. Verify (optional)
python manage.py showmigrations events

# 3. Test in shell (optional)
python manage.py shell
>>> from events.models import UserEventAssignment
>>> UserEventAssignment.objects.values('role').distinct()
```

---

## Troubleshooting

### Migration Fails?

**Error:** "No such table: events_usereventassignment"
```bash
# Run all migrations first
python manage.py migrate
```

**Error:** "Migration already applied"
```bash
# Check migration status
python manage.py showmigrations events
# Should show [X] next to 0010_fix_role_names
```

### Permissions Still Don't Work?

1. **Check migration applied:**
```bash
python manage.py showmigrations events | grep 0010
# Should show: [X] 0010_fix_role_names
```

2. **Check role names in database:**
```bash
python manage.py shell
>>> from events.models import UserEventAssignment
>>> UserEventAssignment.objects.values_list('role', flat=True).distinct()
# Should show: gestionnaire_des_salles, controlleur_des_badges, etc.
```

3. **Clear cache (if using Redis/Memcached):**
```bash
python manage.py shell
>>> from django.core.cache import cache
>>> cache.clear()
```

### Need to Rollback?

```bash
# Rollback to previous migration
python manage.py migrate events 0009

# Reapply if needed
python manage.py migrate events 0010
```

---

## Success Criteria

You'll know it's working when:

✅ Migration applies without errors  
✅ Gestionnaire can create events  
✅ Controller can verify QR codes  
✅ No permission errors in logs  
✅ All role-based features work  

---

## Timeline

**Total Time Required:** ~10 minutes

- Apply migration: 30 seconds
- Verify migration: 1 minute
- Test permissions: 5 minutes
- Deploy to production: 3 minutes

---

## Support

If you need help:

1. Check `CRITICAL_CODE_BUG_FOUND.md` for detailed explanation
2. Check `BACKEND_DOCUMENTATION_UPDATES.md` for migration guide
3. Check `FINAL_UPDATE_SUMMARY.md` for overview

---

## Status Tracking

### Current Status:
- [x] Bug identified
- [x] Fix implemented
- [x] Migration created
- [ ] Migration applied ← **YOU ARE HERE**
- [ ] Tested
- [ ] Deployed

### Next Step:
**Run:** `cd makeplus_api && python manage.py migrate events`

---

**That's it! Simple and straightforward.** 🚀
