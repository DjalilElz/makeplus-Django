# cPanel FTP Storage Setup Guide

## Overview
This guide will help you configure your cPanel account to store all uploaded files (logos, banners, PDFs, etc.) from your Django application.

---

## PART 1: cPanel Configuration (YOU DO THIS)

### Step 1: Create Media Folder
1. Log in to your **cPanel account**
2. Go to **File Manager**
3. Navigate to `public_html` folder
4. Click **+ Folder** button
5. Create a new folder named: `makeplus-media`
6. Right-click on `makeplus-media` → **Permissions**
7. Set permissions to **755** (read/write/execute for owner, read/execute for others)

### Step 2: Create FTP Account
1. In cPanel, go to **FTP Accounts**
2. Click **Add FTP Account**
3. Fill in the details:
   - **Log In**: `makeplus` (or any name you prefer)
   - **Password**: Create a strong password (save it!)
   - **Directory**: Select `/public_html/makeplus-media`
   - **Quota**: Set to unlimited or a large value (e.g., 10GB)
4. Click **Create FTP Account**
5. **SAVE THESE CREDENTIALS** - you'll need them later:
   - FTP Username (usually: `makeplus@yourdomain.com`)
   - FTP Password
   - FTP Server/Host (usually: `ftp.yourdomain.com` or your domain IP)
   - FTP Port (usually: `21`)

### Step 3: Create .htaccess for Security
1. In File Manager, navigate to `public_html/makeplus-media`
2. Click **+ File** button
3. Create a file named: `.htaccess`
4. Right-click on `.htaccess` → **Edit**
5. Paste this content:

```apache
# Allow access to files
<FilesMatch "\.(jpg|jpeg|png|gif|pdf|svg|webp)$">
    Order Allow,Deny
    Allow from all
</FilesMatch>

# Prevent directory listing
Options -Indexes

# Prevent execution of PHP files
<FilesMatch "\.php$">
    Order Deny,Allow
    Deny from all
</FilesMatch>
```

6. Save the file

### Step 4: Test FTP Connection
1. Download an FTP client like **FileZilla** (free)
2. Connect using your FTP credentials:
   - Host: `ftp.yourdomain.com`
   - Username: `makeplus@yourdomain.com`
   - Password: (your password)
   - Port: `21`
3. Try uploading a test file to verify it works
4. Access the file via browser: `https://yourdomain.com/makeplus-media/testfile.jpg`

---

## PART 2: Information to Provide Me

Once you complete the cPanel setup, provide me with these details:

```
FTP_HOST=ftp.yourdomain.com
FTP_USER=makeplus@yourdomain.com
FTP_PASSWORD=your_ftp_password_here
FTP_PORT=21
DOMAIN=yourdomain.com
FTP_PATH=/public_html/makeplus-media
```

**IMPORTANT:** 
- Replace `yourdomain.com` with your actual domain
- Replace `your_ftp_password_here` with the actual FTP password you created
- Keep these credentials PRIVATE - never share them publicly

---

## PART 3: What I Will Do (AFTER YOU PROVIDE CREDENTIALS)

Once you provide the FTP credentials, I will:

1. ✅ Install `django-ftp-storage` package
2. ✅ Update `requirements.txt`
3. ✅ Configure Django settings to use FTP storage
4. ✅ Update all file upload paths to use FTP
5. ✅ Configure environment variables on Render
6. ✅ Test the implementation
7. ✅ Deploy to production

---

## Files That Will Be Stored on cPanel FTP

### Event Files:
- Event logos: `events/logos/`
- Event banners: `events/banners/`
- Event programmes: `events/programmes/`
- Event guides: `events/guides/`

### Form Files:
- Form banners: `forms/banners/`

### ePoster Files:
- ePoster resumes: `eposters/resumes/`
- ePoster posters: `eposters/posters/`
- ePoster final submissions: `eposters/final_submissions/`

All these files will be accessible via:
`https://yourdomain.com/makeplus-media/[path]/[filename]`

---

## Benefits of This Solution

✅ **Persistent Storage** - Files won't be lost on Render deployments
✅ **Free** - Uses your existing cPanel account
✅ **Fast Access** - Files served directly from your domain
✅ **Secure** - Protected by .htaccess rules
✅ **Scalable** - Can handle large file uploads
✅ **Easy Management** - Use cPanel File Manager or FTP client

---

## Security Notes

- FTP credentials will be stored as **environment variables** on Render
- Never commit credentials to Git
- .htaccess prevents PHP execution in media folder
- Only image and PDF files are accessible
- Directory listing is disabled

---

## Troubleshooting

### If FTP connection fails:
1. Check if your hosting provider allows FTP connections
2. Verify the FTP port (try 21 or 22)
3. Check if passive mode is required
4. Ensure your IP is not blocked by firewall

### If files are not accessible via browser:
1. Check folder permissions (should be 755)
2. Verify .htaccess is in place
3. Check if mod_rewrite is enabled in cPanel
4. Ensure the domain is correctly configured

---

## Next Steps

1. ✅ Complete Steps 1-4 in PART 1 (cPanel Configuration)
2. ✅ Test FTP connection with FileZilla
3. ✅ Provide me with the credentials from PART 2
4. ⏳ I will implement the Django FTP storage configuration
5. ⏳ Deploy and test in production

---

**Questions?** Let me know if you encounter any issues during the cPanel setup!
