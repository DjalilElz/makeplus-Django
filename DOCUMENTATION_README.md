# 📚 Documentation Structure

## Files Overview

This project maintains **2 main documentation files** for frontend-backend coordination:

### 1. **`API_DOCUMENTATION.md`** 📖
**Purpose:** Complete API reference for the mobile app development

**Contains:**
- All API endpoints with request/response examples
- Authentication flows
- User roles and permissions
- Data models and schemas
- Error codes and handling

**When to use:**
- When implementing new features in the mobile app
- When you need to know how an endpoint works
- As a reference during development

---

### 2. **`CHANGELOG_FOR_FRONTEND.md`** 📋
**Purpose:** Track all backend changes that affect the frontend

**Contains:**
- Recent updates and changes
- New features added to the API
- Breaking changes
- Bug fixes
- Migration notes

**When to use:**
- Before starting frontend development (check for new changes)
- When backend deployment happens (see what changed)
- When troubleshooting issues (check recent fixes)

---

## Workflow

### For Backend Developer (You):
1. When you add a new API endpoint → Update **`API_DOCUMENTATION.md`**
2. When you make any change → Add entry to **`CHANGELOG_FOR_FRONTEND.md`**
3. When frontend needs update → Send **`CHANGELOG_FOR_FRONTEND.md`** to mobile developer

### For Frontend Developer:
1. Check **`CHANGELOG_FOR_FRONTEND.md`** for recent changes
2. Use **`API_DOCUMENTATION.md`** as API reference
3. Report issues or request clarifications

---

## Update Schedule

- **API_DOCUMENTATION.md**: Update when adding/modifying endpoints
- **CHANGELOG_FOR_FRONTEND.md**: Update daily/weekly with changes

---

## Quick Links

- **API Base URL:** `https://makeplus-platform.onrender.com`
- **Admin Panel:** `https://makeplus-platform.onrender.com/admin/`
- **API Swagger Docs:** `https://makeplus-platform.onrender.com/swagger/`

---

## Notes

- All other MD files have been archived/deleted for clarity
- Keep these 2 files updated and synchronized
- Send `CHANGELOG_FOR_FRONTEND.md` to mobile developer after major updates
