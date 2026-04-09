# 📝 ePoster System - Complete User Guide

## 🎯 Overview
The ePoster system allows participants to submit scientific abstracts for events, and enables committee members to review and validate submissions in real-time.

---

## 🚀 Quick Access to ePoster

### Option 1: From Dashboard Home
1. Go to **Dashboard Home**
2. In the **All Events** table, each event has an **ePoster button** (📄 icon)
3. Click the green **ePoster button** to go directly to that event's ePoster dashboard

### Option 2: From Event Detail Page
1. Go to **Dashboard Home**
2. Click **View** on any event
3. In the event detail page tabs, click the **ePoster tab**
4. This takes you to the ePoster dashboard for that event

---

## 👥 User Roles

### 1. **Event Administrator**
- Manages ePoster settings for the event
- Adds/removes committee members
- Views all submissions
- Exports submissions to CSV
- Configures email templates

### 2. **Committee Member**
- Reviews submissions
- Votes to accept/reject submissions
- Adds comments and ratings
- Sees real-time voting status from other committee members

### 3. **Participant/Submitter**
- Fills out the public submission form
- Receives email notifications about submission status

---

## 📋 For Event Administrators

### Step 1: Set Up Committee Members
Before accepting submissions, add committee members who will review them:

1. Go to **ePoster Dashboard** for your event
2. Click **"Gérer le Comité"** (Manage Committee)
3. Click **"Ajouter un Membre"** (Add Member)
4. Fill in the form:
   - **User**: Select from existing users
   - **Role**: Choose Member, President, or Secretary
5. Click **Save**

**Roles:**
- **Member**: Regular committee member who can vote
- **President**: Lead committee member (ceremonial, same voting rights)
- **Secretary**: Administrative support (same voting rights)

### Step 2: Configure Email Templates (Optional)
Customize automated emails sent to participants:

1. From **ePoster Dashboard**, click **"Templates d'emails"**
2. You'll see 4 template types:
   - **Submission Received**: Sent when participant submits
   - **Accepted**: Sent when submission is accepted
   - **Rejected**: Sent when submission is rejected
   - **Revision Requested**: Sent when revisions are needed

3. To create/edit a template:
   - Click **"Créer un Template"** for a specific type
   - Fill in:
     - **Subject**: Email subject line
     - **Body**: Email content (supports variables like `{nom}`, `{prenom}`, `{titre_travail}`)
   - Click **Save**

### Step 3: Share Public Form Link
Give this link to participants who want to submit:

```
https://yourdomain.com/eposter/<event-id>/
```

Replace `<event-id>` with your event's UUID (found in event details).

### Step 4: Review Submissions
1. From **ePoster Dashboard**, click **"Voir toutes les soumissions"**
2. You'll see a list with:
   - Submission title
   - Author name
   - Status (Pending, Accepted, Rejected, etc.)
   - Submission date
   - Validation progress

3. **Filter submissions** using the dropdown:
   - All submissions
   - Pending only
   - Accepted only
   - Rejected only

### Step 5: View Submission Details
Click **"Voir Détails"** on any submission to see:
- Personal information (name, email, phone, specialty)
- Professional information (institution, department, city, country)
- Abstract sections (Introduction, Materials & Methods, Results, Conclusion)
- Uploaded files
- Committee voting panel (who voted and their decisions)

### Step 6: Export Data
From the submissions list, click **"Exporter CSV"** to download all submissions in Excel format.

---

## 🗳️ For Committee Members

### How to Review a Submission
1. Access the **ePoster Dashboard** for your event
2. Click **"Voir toutes les soumissions"**
3. Click **"Voir Détails"** on a submission

### Voting Panel
On the submission detail page, you'll see:

#### Real-Time Committee Status
- **Green checkmarks (✓)**: Members who voted to accept
- **Red X marks (✗)**: Members who voted to reject
- **Gray circles (○)**: Members who haven't voted yet
- **Updates every 10 seconds automatically**

#### Your Vote Form
Fill in:
1. **Decision**:
   - ✅ **Accept**: Approve the submission
   - ❌ **Reject**: Decline the submission

2. **Comments** (optional but recommended):
   - Provide feedback for the submitter
   - Explain your decision
   - Suggest improvements

3. **Rating** (1-5 stars):
   - 5 stars: Excellent
   - 4 stars: Good
   - 3 stars: Average
   - 2 stars: Below average
   - 1 star: Poor

4. Click **"Soumettre Validation"** (Submit Validation)

### Automatic Status Updates
- When **majority of committee votes Accept** → Status changes to "Accepté"
- When **majority of committee votes Reject** → Status changes to "Rejeté"
- Email is automatically sent to the participant

---

## 📝 For Participants

### How to Submit an ePoster

1. **Get the submission link** from event organizers:
   ```
   https://yourdomain.com/eposter/<event-id>/
   ```

2. **Fill out the 4-step form**:

#### Step 1: Personal Information
- Last name (Nom) *required
- First name (Prénom) *required
- Email *required
- Phone number *required
- Specialty (Spécialité) *required

#### Step 2: Professional Information
- Institution *required
- Department/Service
- City *required
- Country *required

#### Step 3: Work Details
- Work title (Titre du travail) *required
- Keywords (Mots clés) - comma separated *required
- Work type:
  - Communication orale (Oral presentation)
  - Communication affichée (Poster presentation)
  - E-poster
- Additional files (optional, max 10MB)

#### Step 4: Abstract
Write your scientific abstract in 4 sections:
- **Introduction**: Background and objectives *required
- **Matériels et Méthodes**: Materials and methods *required
- **Résultats**: Results *required
- **Conclusion**: Conclusion *required

3. **Review and Submit**: Check all information and click **"Soumettre"**

4. **Receive Confirmation Email**: You'll receive an automated email confirming your submission

### What Happens Next?
1. ✉️ **Immediate**: Confirmation email
2. ⏳ **Review Period**: Committee reviews your submission
3. ✅ **Accepted**: You receive acceptance email with next steps
4. ❌ **Rejected**: You receive rejection email with feedback (if provided)

---

## 📊 Dashboard Features

### ePoster Dashboard Overview
Shows at a glance:
- **Total Submissions**: All submissions received
- **Acceptées** (Accepted): Approved submissions
- **En Attente** (Pending): Awaiting committee review
- **Rejetées** (Rejected): Declined submissions

### Recent Submissions Panel
- Shows the 5 most recent submissions
- Quick links to view details
- Visual status indicators

### Committee Members Panel
- Lists all active committee members
- Shows their roles
- Quick link to manage committee

### Quick Actions
- **Voir toutes les soumissions**: View all submissions
- **Gérer le Comité**: Manage committee members
- **Templates d'emails**: Configure email templates
- **Exporter CSV**: Download all submissions

---

## 🔧 Technical Details

### API Endpoints (for developers)

#### Public Submission
```
POST /api/eposter/<event_id>/submit/
```

#### List Submissions (authenticated)
```
GET /api/eposter/submissions/?event=<event_id>&status=pending
```

#### Validate Submission (committee only)
```
POST /api/eposter/submissions/<submission_id>/validate/
Body: {
  "decision": "accept",
  "comments": "Excellent work",
  "rating": 5
}
```

#### Real-time Status
```
GET /api/eposter/submissions/<submission_id>/realtime-status/
```

### Database Models

- **EPosterSubmission**: Stores participant submissions
- **EPosterValidation**: Stores individual committee votes
- **EPosterCommitteeMember**: Committee member assignments
- **EPosterEmailTemplate**: Custom email templates

---

## ⚙️ Configuration & Settings

### Email Configuration
Ensure your Django email settings are configured in `settings.py`:
```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'
DEFAULT_FROM_EMAIL = 'your-email@gmail.com'
```

### Submission Dates
In the Event model, you can set:
- **eposter_start_date**: When submissions open
- **eposter_end_date**: When submissions close

If current date is outside this range, participants see a "Submissions Closed" message.

---

## 🎨 Customization

### Email Template Variables
Use these placeholders in email templates (they'll be replaced automatically):

- `{nom}` - Last name
- `{prenom}` - First name
- `{email}` - Email address
- `{telephone}` - Phone number
- `{specialite}` - Specialty
- `{institution}` - Institution
- `{titre_travail}` - Work title
- `{type_travail}` - Work type
- `{event_name}` - Event name
- `{submission_date}` - Submission date

Example:
```
Bonjour {prenom} {nom},

Votre soumission "{titre_travail}" pour l'événement {event_name} a été acceptée!

Cordialement,
Le Comité
```

---

## 📞 Support & Troubleshooting

### Common Issues

**Q: I can't see the ePoster button**
- Make sure you're logged in as an administrator
- Check that the event exists in the database
- Try refreshing the page

**Q: Emails are not being sent**
- Check Django email configuration in settings.py
- Verify email templates are created
- Check email server credentials

**Q: Real-time voting updates not working**
- The page automatically refreshes every 10 seconds
- Ensure JavaScript is enabled in your browser
- Check browser console for errors

**Q: Can't add committee members**
- Users must exist in the system first
- Create users in User Management before adding to committee

**Q: Submission form shows "Closed"**
- Check event's eposter_start_date and eposter_end_date
- Current date must be within submission period
- Contact event administrator to update dates

---

## 🎯 Best Practices

### For Administrators
1. ✅ Add committee members **before** opening submissions
2. ✅ Test email templates by sending yourself a test
3. ✅ Set clear submission deadlines
4. ✅ Export submissions regularly for backup
5. ✅ Review committee voting progress daily

### For Committee Members
1. ✅ Review submissions promptly
2. ✅ Provide constructive feedback in comments
3. ✅ Use rating scale consistently
4. ✅ Communicate with other committee members
5. ✅ Check for conflicts of interest

### For Participants
1. ✅ Save your work frequently (form doesn't auto-save)
2. ✅ Use clear, concise language
3. ✅ Proofread before submitting
4. ✅ Follow abstract structure guidelines
5. ✅ Submit well before the deadline

---

## 📚 Summary

| Feature | Access Path |
|---------|------------|
| ePoster Dashboard | Home → Event ePoster Button (📄) |
| Manage Committee | ePoster Dashboard → Gérer le Comité |
| View Submissions | ePoster Dashboard → Voir toutes les soumissions |
| Email Templates | ePoster Dashboard → Templates d'emails |
| Public Form | Share link: `/eposter/<event-id>/` |
| Export CSV | Submissions List → Exporter CSV |

**Quick Tips:**
- 🟢 Green ePoster button = Direct access from home page
- 📄 ePoster tab = Available in event detail page  
- 🔄 Auto-refresh = Real-time voting updates every 10 seconds
- 📧 Auto-email = Sent when majority vote is reached
- 📊 CSV Export = Available anytime from submissions list

---

**Need Help?** Check Django admin panel (`/admin/`) for database-level management or contact your system administrator.
