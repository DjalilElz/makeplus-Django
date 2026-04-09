# 📧 Email Setup Guide - Send Real Campaigns

## 🎯 Recommended Solutions

### For Development/Testing (FREE)
✅ **Gmail with App Password** - Best for testing
- Free
- Easy to set up
- 500 emails/day limit
- Perfect for development

### For Production (Recommended)
✅ **Brevo (formerly Sendinblue)** - BEST CHOICE
- 300 emails/day FREE forever
- Professional deliverability
- No credit card required
- Easy SMTP setup

✅ **SendGrid**
- 100 emails/day FREE forever
- Excellent deliverability
- Professional features

✅ **Mailgun**
- First 3 months FREE (5,000 emails/month)
- Then pay-as-you-go
- Great for scaling

---

## 🚀 QUICKEST SETUP: Gmail (5 minutes)

### Step 1: Enable App Password in Gmail

1. **Go to Google Account Settings**
   - Visit: https://myaccount.google.com/
   - Sign in with your Gmail account

2. **Enable 2-Step Verification** (required for App Passwords)
   - Go to "Security" section
   - Click "2-Step Verification"
   - Follow the setup wizard
   - Verify with your phone

3. **Generate App Password**
   - After 2-Step is enabled, go back to Security
   - Click "App passwords" (near bottom of page)
   - Select app: "Mail"
   - Select device: "Other (Custom name)"
   - Type: "MakePlus Campaign"
   - Click "Generate"
   - **Copy the 16-character password** (example: `abcd efgh ijkl mnop`)

### Step 2: Configure Your .env File

Open or create `.env` file in your project root:

```env
# Gmail SMTP Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=abcdefghijklmnop
DEFAULT_FROM_EMAIL=your-email@gmail.com
SITE_URL=http://127.0.0.1:8000
```

**Replace:**
- `your-email@gmail.com` → Your actual Gmail address
- `abcdefghijklmnop` → The 16-char App Password (remove spaces)

### Step 3: Test It!

Run in Django shell or Python script:

```python
# Test email
from django.core.mail import send_mail

send_mail(
    'Test Email from MakePlus',
    'This is a test message.',
    'your-email@gmail.com',
    ['recipient@example.com'],
    fail_silently=False,
)
```

**✅ If you see no errors, it works!**

---

## 🌟 RECOMMENDED FOR PRODUCTION: Brevo (Free Forever)

### Why Brevo?
- ✅ 300 emails/day FREE (forever)
- ✅ No credit card required
- ✅ Professional email deliverability
- ✅ Tracking & analytics included
- ✅ Easy SMTP setup

### Step 1: Create Brevo Account

1. **Sign Up**: https://www.brevo.com/
2. Click "Sign up free"
3. Enter email, create password
4. Verify your email address
5. Complete onboarding (skip optional steps)

### Step 2: Get SMTP Credentials

1. **Go to SMTP & API Settings**
   - Click your name (top right)
   - Select "SMTP & API"
   
2. **Create SMTP Key**
   - Scroll to "SMTP" section
   - Click "Generate a new SMTP key"
   - Name it: "MakePlus Campaign"
   - Click "Generate"
   - **Copy the password shown** (only shown once!)

3. **Note Your Credentials**
   ```
   SMTP Server: smtp-relay.brevo.com
   Port: 587
   Username: Your Brevo email (login email)
   Password: The SMTP key you just generated
   ```

### Step 3: Configure .env File

```env
# Brevo SMTP Configuration
EMAIL_HOST=smtp-relay.brevo.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-brevo-email@example.com
EMAIL_HOST_PASSWORD=your-smtp-key-here
DEFAULT_FROM_EMAIL=your-brevo-email@example.com
SITE_URL=http://127.0.0.1:8000
```

### Step 4: Verify Sender Domain (Optional but Recommended)

1. In Brevo dashboard, go to "Senders & IP"
2. Add your domain
3. Add DNS records (SPF, DKIM)
4. Verify domain

**Without domain verification**: You can still send 300 emails/day
**With domain verification**: Better deliverability, professional appearance

---

## 🎯 Alternative: SendGrid (100 emails/day free)

### Step 1: Create SendGrid Account

1. **Sign Up**: https://signup.sendgrid.com/
2. Enter details, verify email
3. Complete "Tell us about yourself" form
4. Wait for account approval (~5 minutes)

### Step 2: Create API Key

1. **Go to Settings → API Keys**
2. Click "Create API Key"
3. Name: "MakePlus SMTP"
4. Permissions: "Full Access"
5. Click "Create & View"
6. **Copy the API key** (starts with `SG.`)

### Step 3: Configure .env

```env
# SendGrid SMTP Configuration
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=SG.your-actual-api-key-here
DEFAULT_FROM_EMAIL=your-verified-email@yourdomain.com
SITE_URL=http://127.0.0.1:8000
```

**Note**: 
- Username is literally `apikey` (don't change it)
- Password is your SendGrid API key

---

## 🧪 Testing Your Email Setup

### Method 1: Django Shell (Recommended)

```bash
cd E:\makeplus\makeplus_backend\makeplus_api
..\venv\Scripts\python.exe manage.py shell
```

Then run:

```python
from django.core.mail import send_mail

# Send test email
send_mail(
    subject='Test Email - MakePlus Campaign System',
    message='If you receive this, email setup is working!',
    from_email='your-configured-email@example.com',
    recipient_list=['your-test-email@example.com'],
    fail_silently=False,
)
```

**Success**: You'll see `1` printed (1 email sent)
**Error**: You'll see error message explaining what's wrong

### Method 2: Test Campaign

```python
from dashboard.models_email import EmailCampaign, EmailRecipient
from dashboard.utils_campaign import send_campaign_email

# Create test campaign
campaign = EmailCampaign.objects.create(
    name="Test Campaign",
    subject="Testing Email Delivery",
    body_html="""
    <html>
        <body>
            <h1>Hello!</h1>
            <p>This is a test email from MakePlus.</p>
            <p><a href="https://google.com">Click here to test link tracking</a></p>
        </body>
    </html>
    """,
    from_email="your-configured-email@example.com",
    track_opens=True,
    track_clicks=True,
    status='draft'
)

# Add yourself as recipient
recipient = EmailRecipient.objects.create(
    campaign=campaign,
    email="your-test-email@example.com",
    name="Test User"
)

# Send the email
send_campaign_email(recipient)

# Check status
recipient.refresh_from_db()
print(f"Status: {recipient.status}")
print(f"Sent at: {recipient.sent_at}")
```

### Method 3: Send Full Campaign

```python
from dashboard.utils_campaign import send_campaign

# Send to all recipients in campaign
result = send_campaign(campaign_id=1)
print(f"✅ Sent: {result['sent']}")
print(f"❌ Failed: {result['failed']}")
```

---

## 🔧 Troubleshooting

### Error: "SMTPAuthenticationError"

**Problem**: Wrong username or password

**Solutions**:
- Gmail: Make sure you're using App Password, not regular password
- Check for typos in .env file
- Remove any spaces from password
- Make sure 2-Step Verification is enabled (Gmail)

### Error: "SMTPSenderRefused" or "Sender not verified"

**Problem**: Sending from unverified email address

**Solutions**:
- Use the same email as your account email
- For SendGrid/Brevo: Verify your sender email in dashboard
- For Gmail: Use your actual Gmail address

### Error: "Connection refused" or "Connection timeout"

**Problem**: Wrong host or port

**Solutions**:
- Check EMAIL_HOST spelling
- Confirm port is 587 (or 465 for SSL)
- Check firewall/antivirus blocking port
- Try EMAIL_PORT=465 with EMAIL_USE_SSL=True

### Error: "Daily sending limit exceeded"

**Gmail**: 500 emails/day limit
**Brevo Free**: 300 emails/day limit
**SendGrid Free**: 100 emails/day limit

**Solution**: Wait 24 hours or upgrade plan

---

## 📊 Comparison Table

| Service | Free Tier | Setup Difficulty | Deliverability | Best For |
|---------|-----------|------------------|----------------|----------|
| **Gmail** | 500/day | ⭐ Easy | Good | Development |
| **Brevo** | 300/day forever | ⭐⭐ Moderate | Excellent | Production (Small-Medium) |
| **SendGrid** | 100/day forever | ⭐⭐ Moderate | Excellent | Production (All sizes) |
| **Mailgun** | 3 months free | ⭐⭐⭐ Advanced | Excellent | Production (Large scale) |
| **AWS SES** | 62,000/month (with EC2) | ⭐⭐⭐⭐ Complex | Excellent | Enterprise |

---

## 🎯 My Recommendation

### For Your Situation:

**BEST CHOICE: Brevo (Sendinblue)**

**Why:**
1. ✅ 300 emails/day FREE forever (no credit card)
2. ✅ Professional deliverability (won't go to spam)
3. ✅ Easy setup (10 minutes)
4. ✅ Tracking included (open rates, click rates)
5. ✅ Can upgrade later if needed

**Quick Start:**
1. Sign up at https://www.brevo.com/
2. Get SMTP credentials (Settings → SMTP & API)
3. Update .env file with credentials
4. Test with Django shell
5. Start sending campaigns!

---

## 🚀 Production Checklist

Before sending real campaigns:

- [ ] Email configuration tested and working
- [ ] Sender email verified
- [ ] SPF/DKIM records added (if using custom domain)
- [ ] Unsubscribe link in all emails
- [ ] Test email rendering in different clients
- [ ] Tracking pixels working
- [ ] Link tracking working
- [ ] Error handling in place
- [ ] Monitor bounce rates
- [ ] Comply with anti-spam laws (CAN-SPAM, GDPR)

---

## 📧 Complete .env Example

```env
# Database
DATABASE_URL=sqlite:///db.sqlite3

# Django
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Email Configuration (Choose one)
# Option 1: Gmail (Development)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-gmail@gmail.com
EMAIL_HOST_PASSWORD=your-16-char-app-password
DEFAULT_FROM_EMAIL=your-gmail@gmail.com

# Option 2: Brevo (Production - Recommended)
# EMAIL_HOST=smtp-relay.brevo.com
# EMAIL_PORT=587
# EMAIL_USE_TLS=True
# EMAIL_HOST_USER=your-brevo-email@example.com
# EMAIL_HOST_PASSWORD=your-brevo-smtp-key
# DEFAULT_FROM_EMAIL=your-brevo-email@example.com

# Option 3: SendGrid (Production)
# EMAIL_HOST=smtp.sendgrid.net
# EMAIL_PORT=587
# EMAIL_USE_TLS=True
# EMAIL_HOST_USER=apikey
# EMAIL_HOST_PASSWORD=SG.your-sendgrid-api-key
# DEFAULT_FROM_EMAIL=your-verified-email@yourdomain.com

# Site Configuration
SITE_URL=http://127.0.0.1:8000
```

---

## 🎓 Next Steps After Setup

1. **Send test campaign** to yourself
2. **Check tracking**: Open email, click links
3. **Verify statistics** in admin panel
4. **View detailed stats** at `/dashboard/campaigns/<id>/stats/`
5. **Create real campaign** with multiple recipients
6. **Monitor delivery rates** and engagement

---

## 💡 Pro Tips

### Better Deliverability
- Use a real "From" name (not just email)
- Include unsubscribe link in footer
- Don't use spam trigger words
- Keep HTML clean and simple
- Test with mail-tester.com before sending

### Avoid Spam Folder
- Verify your domain (SPF, DKIM, DMARC)
- Use professional email service (Brevo, SendGrid)
- Don't buy email lists
- Only send to people who opted in
- Include physical address in footer

### Track Performance
- Monitor open rates (20-30% is good)
- Monitor click rates (2-5% is good)
- Check bounce rates (keep under 2%)
- Review unsubscribe rates (keep under 0.5%)

---

## ✅ Status Check

After configuration, verify:

```python
# In Django shell
from django.conf import settings

print("Email Backend:", settings.EMAIL_BACKEND)
print("Email Host:", settings.EMAIL_HOST)
print("Email Port:", settings.EMAIL_PORT)
print("Email Use TLS:", settings.EMAIL_USE_TLS)
print("Default From Email:", settings.DEFAULT_FROM_EMAIL)
```

---

**Ready to send campaigns!** 🚀

Choose your email service → Configure .env → Test → Send! 📧
