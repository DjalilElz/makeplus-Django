# Run Database Migrations on Render

## Problem
The production database is missing the `is_used` column in the `events_emaillogincode` table.

## Solution
Run migrations on the Render production server.

## Steps

### Option 1: Using Render Dashboard (Recommended)

1. Go to your Render dashboard: https://dashboard.render.com
2. Click on your Django service (makeplus-django-5)
3. Click on "Shell" tab
4. Run these commands:
```bash
cd /opt/render/project/src/makeplus_api
python manage.py migrate
```

### Option 2: Using Render CLI

If you have Render CLI installed:
```bash
render shell makeplus-django-5
cd /opt/render/project/src/makeplus_api
python manage.py migrate
```

### Option 3: Automatic Migration on Deploy

Add this to your `render.yaml` or build command:
```bash
python makeplus_api/manage.py migrate
```

## Verify Migration

After running migrations, check if the column exists:
```bash
python manage.py dbshell
\d events_emaillogincode
```

You should see the `is_used` column listed.

## Alternative: Create Migration Manually

If migrations don't work, you can add the column manually:

1. Access Render Shell
2. Run:
```bash
python manage.py dbshell
```

3. Execute SQL:
```sql
ALTER TABLE events_emaillogincode ADD COLUMN IF NOT EXISTS is_used BOOLEAN DEFAULT FALSE;
ALTER TABLE events_emaillogincode ADD COLUMN IF NOT EXISTS used_at TIMESTAMP NULL;
ALTER TABLE events_emaillogincode ADD COLUMN IF NOT EXISTS ip_address INET NULL;
ALTER TABLE events_emaillogincode ADD COLUMN IF NOT EXISTS user_agent TEXT DEFAULT '';

-- Create index
CREATE INDEX IF NOT EXISTS events_emai_user_id_b75a1f_idx ON events_emaillogincode (user_id, event_id, is_used);
```

## After Migration

Try submitting the form again. It should work now!
