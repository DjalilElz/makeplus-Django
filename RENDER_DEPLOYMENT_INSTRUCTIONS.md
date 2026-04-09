# Render Deployment Instructions

## Prerequisites
- GitHub repository pushed successfully
- Supabase database ready
- Brevo API key

## Step 1: Create Web Service on Render

1. Go to https://render.com and sign in
2. Click "New +" → "Web Service"
3. Connect your GitHub repository: `DjalilElz/makeplus-Django`
4. Configure the service:
   - **Name**: `makeplus-api` (or your preferred name)
   - **Region**: Choose closest to your users
   - **Branch**: `main`
   - **Root Directory**: `makeplus_api`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate`
   - **Start Command**: `gunicorn makeplus_api.wsgi:application`

## Step 2: Set Environment Variables on Render

In the Render dashboard, go to "Environment" tab and add these variables:

### Django Settings
```
SECRET_KEY=your-production-secret-key-here
DEBUG=False
ALLOWED_HOSTS=your-app-name.onrender.com
```

### Database (Supabase)
```
USE_SUPABASE=True
SUPABASE_DB_NAME=postgres
SUPABASE_DB_USER=postgres.eamvpsyanliefdwoyxdd
SUPABASE_DB_PASSWORD=djalildjalil23
SUPABASE_DB_HOST=aws-1-eu-west-1.pooler.supabase.com
SUPABASE_DB_PORT=6543
```

### Email (Brevo)
```
BREVO_API_KEY=xkeysib-YOUR-ACTUAL-KEY-HERE
EMAIL_HOST=smtp-relay.brevo.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=a12933001@smtp-brevo.com
EMAIL_HOST_PASSWORD=xkeysib-YOUR-ACTUAL-KEY-HERE
DEFAULT_FROM_EMAIL=elaziziabdeldjalil@gmail.com
```

### Site URL
```
SITE_URL=https://your-app-name.onrender.com
```

## Step 3: Deploy

1. Click "Create Web Service"
2. Render will automatically:
   - Install dependencies
   - Run migrations
   - Collect static files
   - Start the server

## Step 4: Verify Deployment

1. Check the logs for any errors
2. Visit your app URL: `https://your-app-name.onrender.com`
3. Test the API: `https://your-app-name.onrender.com/api/events/`
4. Access admin: `https://your-app-name.onrender.com/admin/`

## Important Notes

- **Local Development**: Keep `USE_SUPABASE=False` in your local .env to use SQLite
- **Production**: Render environment variables override .env file
- **Secrets**: Never commit real API keys to GitHub
- **Database**: Supabase is used in production, SQLite for local dev
- **Static Files**: Served by WhiteNoise in production

## Troubleshooting

### Database Connection Issues
- Verify Supabase credentials
- Check if Supabase allows connections from Render IPs
- Ensure `USE_SUPABASE=True` on Render

### Static Files Not Loading
- Check `ALLOWED_HOSTS` includes your Render domain
- Verify `collectstatic` ran successfully in build logs

### Email Not Sending
- Verify Brevo API key is correct
- Check Brevo dashboard for sending limits
- Review email logs in Django admin

## Updating Your App

1. Push changes to GitHub `main` branch
2. Render automatically detects and redeploys
3. Monitor deployment logs for issues

## Environment Variables Summary

| Variable | Local (.env) | Render (Production) |
|----------|--------------|---------------------|
| DEBUG | True | False |
| USE_SUPABASE | False | True |
| BREVO_API_KEY | placeholder | Real key |
| ALLOWED_HOSTS | localhost | your-app.onrender.com |
