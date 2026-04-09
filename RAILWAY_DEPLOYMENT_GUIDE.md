# Railway.app Deployment Guide - Django Backend

**Time Required:** 10-15 minutes  
**Cost:** $5/month  
**Difficulty:** Easy ⭐⭐☆☆☆

---

## 🎯 Why Railway?

- ✅ Easiest Django deployment
- ✅ PostgreSQL included
- ✅ Automatic HTTPS
- ✅ Git-based deployment
- ✅ Environment variables
- ✅ Fair pricing ($5/month)

---

## 📋 Prerequisites

- GitHub account
- Railway account (sign up at railway.app)
- Your Django project pushed to GitHub

---

## 🚀 Step-by-Step Deployment

### Step 1: Prepare Your Django Project

#### 1.1 Update requirements.txt

Add these packages:
```txt
gunicorn==21.2.0
psycopg2-binary==2.9.9
whitenoise==6.6.0
dj-database-url==2.1.0
```

#### 1.2 Update settings.py

```python
# makeplus_api/makeplus_api/settings.py

import os
import dj_database_url

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-here')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = ['*']  # Railway will set proper domain

# Add whitenoise to INSTALLED_APPS
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'whitenoise.runserver_nostatic',  # Add this
    # ... your apps
]

# Add whitenoise middleware (after SecurityMiddleware)
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Add this
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    # ... rest of middleware
]

# Database configuration
DATABASES = {
    'default': dj_database_url.config(
        default='sqlite:///db.sqlite3',
        conn_max_age=600,
        conn_health_checks=True,
    )
}

# Static files configuration
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files configuration
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# CORS configuration for Railway
CORS_ALLOWED_ORIGINS = [
    'https://*.railway.app',
    'https://yourdomain.com',  # Add your custom domain
]

CSRF_TRUSTED_ORIGINS = [
    'https://*.railway.app',
    'https://yourdomain.com',  # Add your custom domain
]

# Security settings for production
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
```

#### 1.3 Create Procfile

Create a file named `Procfile` in your project root (same level as manage.py):

```
web: python manage.py migrate && python manage.py collectstatic --noinput && gunicorn makeplus_api.wsgi --log-file -
```

#### 1.4 Create runtime.txt (Optional)

Specify Python version:
```
python-3.11.7
```

#### 1.5 Create .railwayignore (Optional)

```
*.pyc
__pycache__/
db.sqlite3
.env
venv/
.git/
```

---

### Step 2: Push to GitHub

```bash
git add .
git commit -m "Prepare for Railway deployment"
git push origin main
```

---

### Step 3: Deploy on Railway

#### 3.1 Create Railway Account
1. Go to https://railway.app
2. Click "Login" → Sign in with GitHub
3. Authorize Railway

#### 3.2 Create New Project
1. Click "New Project"
2. Select "Deploy from GitHub repo"
3. Choose your repository
4. Railway will detect Django automatically

#### 3.3 Add PostgreSQL Database
1. Click "New" → "Database" → "Add PostgreSQL"
2. Railway will create a database and set DATABASE_URL automatically

#### 3.4 Set Environment Variables
1. Click on your Django service
2. Go to "Variables" tab
3. Add these variables:

```
SECRET_KEY=your-super-secret-key-here-change-this
DEBUG=False
ALLOWED_HOSTS=*.railway.app
DJANGO_SETTINGS_MODULE=makeplus_api.settings
```

To generate a secure SECRET_KEY:
```python
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

#### 3.5 Deploy
1. Railway will automatically deploy
2. Wait for build to complete (2-3 minutes)
3. Click on the generated URL to view your app

---

### Step 4: Create Superuser

#### 4.1 Open Railway CLI
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Link to your project
railway link
```

#### 4.2 Create Superuser
```bash
railway run python manage.py createsuperuser
```

Or use Railway's web terminal:
1. Go to your service in Railway dashboard
2. Click "Settings" → "Deploy Logs"
3. Use the terminal to run commands

---

### Step 5: Verify Deployment

1. **Visit your app:** `https://your-app.railway.app`
2. **Check admin:** `https://your-app.railway.app/admin/`
3. **Test API:** `https://your-app.railway.app/api/events/`
4. **Check Swagger:** `https://your-app.railway.app/swagger/`

---

## 🔧 Troubleshooting

### Issue: "Application Error"

**Check logs:**
```bash
railway logs
```

**Common causes:**
- Missing environment variables
- Database not connected
- Static files not collected

### Issue: "Static files not loading"

**Solution:**
```bash
# Run collectstatic
railway run python manage.py collectstatic --noinput
```

### Issue: "Database connection error"

**Check:**
1. PostgreSQL service is running
2. DATABASE_URL is set automatically by Railway
3. psycopg2-binary is in requirements.txt

### Issue: "CORS errors"

**Update settings.py:**
```python
CORS_ALLOWED_ORIGINS = [
    'https://your-frontend.vercel.app',
    'https://*.railway.app',
]
```

---

## 💰 Pricing

**Railway Pricing:**
- **Hobby Plan:** $5/month
  - 500 hours of usage
  - $0.000231/GB-hour for RAM
  - $0.000463/vCPU-hour
  - Includes PostgreSQL

**Typical Django app cost:** ~$5-10/month

---

## 🎯 Custom Domain

### Add Custom Domain

1. Go to your service in Railway
2. Click "Settings" → "Domains"
3. Click "Add Domain"
4. Enter your domain (e.g., api.yourdomain.com)
5. Add CNAME record to your DNS:
   - Name: `api`
   - Value: `your-app.railway.app`
6. Wait for DNS propagation (5-30 minutes)

### Update Django Settings

```python
ALLOWED_HOSTS = ['api.yourdomain.com', '*.railway.app']
CSRF_TRUSTED_ORIGINS = ['https://api.yourdomain.com']
```

---

## 🔄 Continuous Deployment

Railway automatically deploys when you push to GitHub:

```bash
# Make changes
git add .
git commit -m "Update feature"
git push origin main

# Railway automatically deploys!
```

---

## 📊 Monitoring

### View Logs
```bash
railway logs
```

### View Metrics
1. Go to Railway dashboard
2. Click on your service
3. View CPU, Memory, Network usage

---

## 🚀 Advanced: Multiple Environments

### Create Staging Environment

1. Create new Railway project
2. Connect same GitHub repo
3. Use different branch (e.g., `staging`)
4. Set different environment variables

**Production:** `main` branch → `api.yourdomain.com`  
**Staging:** `staging` branch → `staging-api.yourdomain.com`

---

## 📝 Deployment Checklist

Before deploying:
- [ ] Update requirements.txt
- [ ] Update settings.py (database, static files, security)
- [ ] Create Procfile
- [ ] Push to GitHub
- [ ] Create Railway account
- [ ] Add PostgreSQL database
- [ ] Set environment variables
- [ ] Deploy
- [ ] Create superuser
- [ ] Test all endpoints
- [ ] Set up custom domain (optional)

---

## 🎉 Success!

Your Django backend is now live on Railway! 🚀

**Next Steps:**
1. Test all API endpoints
2. Set up monitoring
3. Configure custom domain
4. Set up backups
5. Deploy frontend on Vercel

---

## 📚 Resources

- **Railway Docs:** https://docs.railway.app
- **Django Deployment:** https://docs.djangoproject.com/en/5.0/howto/deployment/
- **Railway Discord:** https://discord.gg/railway

---

## 🆘 Need Help?

**Common Commands:**
```bash
# View logs
railway logs

# Run migrations
railway run python manage.py migrate

# Create superuser
railway run python manage.py createsuperuser

# Collect static files
railway run python manage.py collectstatic

# Open shell
railway run python manage.py shell

# Restart service
railway restart
```

---

**Estimated Total Time:** 15 minutes  
**Cost:** $5/month  
**Result:** Production-ready Django backend! 🎉
