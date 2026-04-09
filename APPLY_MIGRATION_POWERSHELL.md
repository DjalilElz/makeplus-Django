# Apply Migration - PowerShell Commands

**For Windows PowerShell Users**

---

## Step 1: Activate Virtual Environment

```powershell
# Navigate to project root
cd E:\makeplus\makeplus_backend

# Activate virtual environment
.\venv\Scripts\Activate.ps1
```

**If you get an execution policy error:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

## Step 2: Navigate to Django Project

```powershell
cd makeplus_api
```

---

## Step 3: Apply Migration

```powershell
python manage.py migrate events
```

**Expected Output:**
```
Running migrations:
  Applying events.0010_fix_role_names... OK
Updated X gestionnaire records
Updated Y controlleur records
```

---

## Step 4: Verify Migration

```powershell
python manage.py showmigrations events
```

**Look for:**
```
events
  [X] 0001_initial
  [X] 0002_add_performance_indexes
  ...
  [X] 0010_fix_role_names  ← Should have [X]
```

---

## Complete Command Sequence (Copy & Paste)

```powershell
# From E:\makeplus\makeplus_backend
.\venv\Scripts\Activate.ps1
cd makeplus_api
python manage.py migrate events
python manage.py showmigrations events
```

---

## Alternative: If Virtual Environment Doesn't Exist

If you don't have a virtual environment, create one first:

```powershell
# From E:\makeplus\makeplus_backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
cd makeplus_api
python manage.py migrate events
```

---

## Troubleshooting

### Error: "Activate.ps1 cannot be loaded"

**Solution:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Error: "No module named 'django'"

**Solution:**
```powershell
# Make sure virtual environment is activated
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### Error: "python is not recognized"

**Solution:**
```powershell
# Use py instead
py -m venv venv
.\venv\Scripts\Activate.ps1
```

---

## Quick Reference

**Activate venv:**
```powershell
.\venv\Scripts\Activate.ps1
```

**Deactivate venv:**
```powershell
deactivate
```

**Check if venv is active:**
- Your prompt should show `(venv)` at the beginning

---

## After Migration

Test the fix:

1. **Start Django server:**
```powershell
python manage.py runserver
```

2. **Test in browser:**
- Go to http://localhost:8000/admin/
- Login as gestionnaire
- Try to create an event
- Should work now! ✅

---

**Note:** PowerShell uses `;` instead of `&&` for command chaining:

```powershell
# Wrong (Bash syntax):
cd makeplus_api && python manage.py migrate

# Correct (PowerShell syntax):
cd makeplus_api; python manage.py migrate
```

Or run commands separately:
```powershell
cd makeplus_api
python manage.py migrate events
```
