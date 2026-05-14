# ePoster Final Submission - Implementation Guide

## 📋 Overview

This feature allows users whose eposters were validated by the committee to submit a final version using a unique code they receive via email.

## 🎯 Features Implemented

### 1. **Unique Code Generation**
- When an eposter is validated (status='accepted'), a unique code is automatically generated
- Format: `EPOSTER-{EVENT_ID_SHORT}-{NUMBER}`
- Example: `EPOSTER-D3C3DE4D-001`
- Code is unique per event

### 2. **Updated Validation Email**
- Acceptance emails now include:
  - The unique eposter code
  - Link to the final submission form
  - Variables available in email template:
    - `{{eposter_code}}` - The unique code
    - `{{final_submission_url}}` - Link to the form

### 3. **Final Submission Form**
- **URL:** `/dashboard/eposter/final-submission/{event_id}/`
- **No login required** - Public form
- **Fields:**
  - Code ePoster (required - for verification)
  - Nom (required)
  - Email (required)
  - Téléphone (required)
  - Spécialité (dropdown - 30 options)
  - Domaine de communication (dropdown - 8 options)
  - Titre (required)
  - Auteurs (required)
  - Co-auteurs (optional)
  - Abstract PDF file (required)

### 4. **Eposter Gallery**
- **URL:** `/dashboard/eposter/gallery/{event_id}/`
- Displays all final submissions as cards
- Each card shows:
  - Eposter number
  - Title
  - Author
  - Specialité
  - Domaine
  - "Voir" button to view PDF

### 5. **PDF Viewer**
- **URL:** `/dashboard/eposter/view/{submission_id}/`
- Opens the submitted PDF in browser
- Can be downloaded

## 📊 Database Models

### EPosterSubmission (Updated)
```python
# New field added:
eposter_code = CharField(max_length=50, blank=True, unique=True)
```

### EPosterFinalSubmission (New)
```python
class EPosterFinalSubmission(models.Model):
    id = UUIDField(primary_key=True)
    original_submission = OneToOneField(EPosterSubmission)
    event = ForeignKey(Event)
    
    # Form fields
    nom = CharField(max_length=100)
    email = EmailField()
    telephone = CharField(max_length=20)
    specialite = CharField(choices=SPECIALITE_CHOICES)
    domaine_communication = CharField(choices=DOMAINE_COMMUNICATION_CHOICES)
    poster_number = CharField(max_length=50)  # The eposter code
    titre = CharField(max_length=500)
    auteurs = TextField()
    co_auteurs = TextField(blank=True)
    abstract_file = FileField(upload_to='eposters/final_submissions/')
    
    # Metadata
    ip_address = GenericIPAddressField()
    user_agent = TextField()
    submitted_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
```

## 🔄 Workflow

### Step 1: First Submission
1. User submits eposter through existing form
2. Submission goes to committee

### Step 2: Committee Validation
1. Committee members review and vote
2. If approved → Status changes to 'accepted'
3. **Eposter code is automatically generated**

### Step 3: Email Notification
1. System sends acceptance email
2. Email contains:
   - Congratulations message
   - **Unique eposter code**
   - **Link to final submission form**

### Step 4: Final Submission
1. User clicks link in email
2. Opens final submission form (no login needed)
3. User fills form and **enters the code** they received
4. System verifies code matches a validated eposter
5. If valid → Final submission saved
6. If invalid → Error message shown

### Step 5: Gallery Display
1. Admin/users can view gallery page
2. All final submissions displayed as cards
3. Click "Voir" to view the PDF

## 🔐 Security

- **Code Verification:** Form validates that the entered code exists and is for an accepted eposter
- **One Submission Per Code:** Each code can only be used once (OneToOneField relationship)
- **Event Validation:** Code must match the event
- **File Type Validation:** Only PDF files accepted

## 📧 Email Template Variables

Update your acceptance email template to include:

```html
<p>Félicitations! Votre ePoster a été validé.</p>

<p><strong>Votre code ePoster:</strong> {{eposter_code}}</p>

<p>Veuillez soumettre la version finale de votre ePoster en utilisant le lien ci-dessous:</p>

<p><a href="{{final_submission_url}}">Soumettre la version finale</a></p>

<p>Vous devrez entrer votre code ePoster ({{eposter_code}}) dans le formulaire.</p>
```

## 🌐 URLs

| Purpose | URL | Login Required |
|---------|-----|----------------|
| Final Submission Form | `/dashboard/eposter/final-submission/{event_id}/` | No |
| Eposter Gallery | `/dashboard/eposter/gallery/{event_id}/` | No |
| View PDF | `/dashboard/eposter/view/{submission_id}/` | No |

## 📝 Admin Tasks

### 1. Update Email Template
1. Go to: `/dashboard/events/{event_id}/eposter/email-templates/`
2. Edit the "Acceptation" template
3. Add `{{eposter_code}}` and `{{final_submission_url}}` variables
4. Save

### 2. Share Links
- Share the final submission form link with validated participants
- Share the gallery link publicly or with specific audience

### 3. Monitor Submissions
- View final submissions in Django admin
- Export data if needed

## 🎨 Specialité Options

1. Allerologie
2. Anatomique
3. Anesthésiologie
4. Biologie
5. Chirurgie cardiaque
6. Dermatologie
7. Diabétologie endocrinologie
8. Gastro-entérologie et hépatologie
9. Obstétrique et gynécologie
10. Hématologie
11. Immunologie
12. Maladies infectieuses
13. Médecine du travail
14. Médecine interne
15. Médecine générale
16. Néphrologie
17. Oncologie
18. Ophtalmologie
19. ORL
20. Professions de santé alliées
21. Pédiatrie
22. Pneumologie
23. Pharmacie hospitalière
24. Pharmacien d'officine
25. Médecine de soins intensifs
26. Psychiatrie
27. Radiologie
28. Rhumatologie
29. Urologie
30. Chirurgie dentaire
31. Chirurgie pédiatrique

## 🎯 Domaine de Communication Options

1. Rhinologie
2. Pathologie cervico-facial
3. Thyroïde et parathyroïde
4. ORL pédiatrique
5. Laryngologie trachée
6. Otologie
7. Cancérologie
8. Divers

## ✅ Testing Checklist

- [ ] Validate an eposter and check if code is generated
- [ ] Check if acceptance email contains code and link
- [ ] Access final submission form without login
- [ ] Submit form with valid code
- [ ] Try submitting with invalid code (should fail)
- [ ] Try submitting twice with same code (should fail)
- [ ] View gallery page
- [ ] Click "Voir" to view PDF
- [ ] Check PDF opens correctly

## 🚀 Deployment

The feature has been deployed to production. Migrations will run automatically on Render.

**Deployment includes:**
- New database tables
- New views and URLs
- New templates
- Updated email sending logic

## 📞 Support

If you encounter any issues:
1. Check Django admin for error logs
2. Verify email template includes new variables
3. Ensure migrations ran successfully
4. Check file upload permissions

---

**Status:** ✅ Deployed and Ready
**Date:** May 1, 2026
