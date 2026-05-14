# 🚀 FTP Storage Deployment - ACTION REQUIRED (UPDATED)

## ✅ What I Just Did

1. ✅ Fixed package error - using `django-storages` (correct package)
2. ✅ Configured Django settings for FTP storage
3. ✅ Pushed fix to GitHub
4. ✅ Render is now deploying automatically (should succeed this time)

**Note:** The first deployment failed because `django-ftp-storage` doesn't exist. I've fixed it to use `django-storages` which has built-in FTP support.

---

## 📋 PART 1: cPanel Setup (DO THIS FIRST)

### Step 1: Upload .htaccess Security File

1. Open **CoreFTP** or **FileZilla**
2. Connect with these credentials:
   - Host: `ftp.wemakeplus.com`
   - Username: `wemaszv1`
   - Password: `v5v?KQRf0P77`
   - Port: `21`

3. Navigate to: `/home/wemaszvr/wemakeplus.com/makeplus-media/`

4. Create a new file named: `.htaccess`

5. Copy and paste this content into the file:

```apache
# Security configuration for makeplus-media folder

# Allow access to image and PDF files only
<FilesMatch "\.(jpg|jpeg|png|gif|pdf|svg|webp|doc|docx)$">
    Order Allow,Deny
    Allow from all
</FilesMatch>

# Prevent directory listing
Options -Indexes

# Prevent execution of PHP files (security)
<FilesMatch "\.php$">
    Order Deny,Allow
    Deny from all
</FilesMatch>

# Enable CORS for file access
<IfModule mod_headers.c>
    Header set Access-Control-Allow-Origin "*"
    Header set Access-Control-Allow-Methods "GET, OPTIONS"
</IfModule>

# Set proper MIME types
<IfModule mod_mime.c>
    AddType image/jpeg .jpg .jpeg
    AddType image/png .png
    AddType image/gif .gif
    AddType image/svg+xml .svg
    AddType image/webp .webp
    AddType application/pdf .pdf
    AddType application/msword .doc
    AddType application/vnd.openxmlformats-officedocument.wordprocessingml.document .docx
</IfModule>
```

6. Save the file

7. Set file permissions to **644** (right-click → Permissions)

---

## 📋 PART 2: Render Environment Variables (DO THIS SECOND)

### Step 1: Go to Render Dashboard

1. Open: https://dashboard.render.com
2. Click on your service: **makeplus-platform**
3. Click on **Environment** tab (left sidebar)

### Step 2: Add These Environment Variables

Click **Add Environment Variable** for each of these:

```
USE_FTP_STORAGE=True
```

```
FTP_HOST=ftp.wemakeplus.com
```

```
FTP_USER=wemaszv1
```

```
FTP_PASSWORD=v5v?KQRf0P77
```

```
FTP_PORT=21
```

```
FTP_DOMAIN=wemakeplus.com
```

```
FTP_PATH=/home/wemaszvr/wemakeplus.com/makeplus-media
```

### Step 3: Save Changes

1. Click **Save Changes** button at the bottom
2. Render will automatically redeploy with the new environment variables

---

## 🔍 PART 3: Verify Deployment

### Check Render Deployment Status

1. Go to **Logs** tab in Render
2. Wait for deployment to complete (usually 2-3 minutes)
3. Look for: `Build successful` and `Your service is live`

### Check for Errors

If you see any errors related to `django-ftp-storage`, let me know immediately.

---

## 🧪 PART 4: Test File Upload

### Test 1: Upload Event Logo

1. Go to: `https://makeplus-platform.onrender.com/admin/`
2. Login with your admin credentials
3. Go to **Events** → Select any event
4. Upload a logo image
5. Save the event
6. Check if the logo appears on the event page

### Test 2: Verify File on FTP Server

1. Open CoreFTP/FileZilla
2. Connect to your FTP server
3. Navigate to: `/home/wemaszvr/wemakeplus.com/makeplus-media/`
4. You should see a new folder: `events/logos/`
5. Inside, you should see the uploaded logo file

### Test 3: Access File via Browser

1. Copy the file URL from the event (right-click on logo → Copy image address)
2. It should look like: `https://wemakeplus.com/makeplus-media/events/logos/filename.jpg`
3. Open this URL in a new browser tab
4. The image should display correctly

---

## ✅ Success Checklist

- [ ] .htaccess file uploaded to cPanel
- [ ] All 7 environment variables added to Render
- [ ] Render deployment completed successfully
- [ ] Event logo upload works
- [ ] File appears on FTP server
- [ ] File accessible via browser URL

---

## 🐛 Troubleshooting

### Issue: "Connection refused" error in Render logs
**Solution:** Double-check FTP credentials in Render environment variables

### Issue: Files upload but return 404
**Solution:** 
1. Verify .htaccess file is uploaded
2. Check file permissions (should be 644)
3. Verify FTP_PATH is correct

### Issue: "Permission denied" when uploading
**Solution:** 
1. Check FTP user has write permissions
2. Verify folder permissions are 755

---

## 📞 Need Help?

If you encounter any issues:
1. Check Render logs for error messages
2. Verify FTP connection with CoreFTP
3. Let me know the exact error message

---

## 🎯 Summary

**What happens now:**
1. User uploads a file → Django API receives it
2. Django connects to FTP → Uploads to cPanel
3. File saved at: `https://wemakeplus.com/makeplus-media/[path]/[file]`
4. File persists forever (survives Render deployments)

**Your tasks:**
1. ✅ Upload .htaccess to cPanel (5 minutes)
2. ✅ Add environment variables to Render (5 minutes)
3. ✅ Test file upload (2 minutes)

**Total time:** ~12 minutes

---

**Ready? Start with PART 1 (cPanel), then PART 2 (Render), then PART 3 (Test)!** 🚀
