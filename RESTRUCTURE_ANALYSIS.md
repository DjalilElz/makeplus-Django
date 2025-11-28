# 🔄 Backend Restructure Analysis

## 📋 Current vs Required Structure Comparison

### ✅ **ALREADY IMPLEMENTED** (No Changes Needed)

#### 1. **Event Structure**
- ✅ Event has: name, time (start_date, end_date), location
- ✅ Event has president/creator (created_by field)
- ✅ Event status tracking

#### 2. **User Roles**
- ⚠️ Four roles needed: `gestionnaire_des_salles`, `controlleur_des_badges`, `participant`, `exposant`
- ✅ Users can belong to multiple events with different roles (UserEventAssignment)
- ✅ Multi-event support via UserEventAssignment model
- ⚠️ Currently has `organisateur` - needs to be renamed to `gestionnaire_des_salles`

#### 3. **Rooms (Salles)**
- ✅ Event has multiple rooms
- ✅ Room has: name, description, capacity, location
- ✅ Room tracking (current_participants)

#### 4. **Sessions (Conferences/Ateliers)**
- ✅ Sessions linked to rooms and events
- ✅ Session has: title, description, speaker info, start_time, end_time
- ⚠️ Session status: needs to be changed to French (pas_encore, en_cours, termine) 

#### 5. **Participant QR Codes**
- ✅ Participant model with badge_id and qr_code_data
- ✅ Check-in functionality (is_checked_in, checked_in_at)
- ✅ Room access tracking via RoomAccess model

#### 6. **Room Access Control**
- ✅ RoomAccess model tracks who accessed which room
- ✅ Status: granted/denied
- ✅ Verified by controller

---

## 🆕 **NEW FEATURES REQUIRED**

### 1. **Event Files** (NEW)
```python
Event needs:
- programme (PDF file)
- guide (PDF file)
```
**Status:** ❌ NOT IMPLEMENTED  
**Solution:** Add FileField to Event model

---

### 2. **Session Types** (MODIFICATION REQUIRED)
```python
Current: Generic "Session" model
Required: Distinguish between:
- Conference (free for all participants)
- Atelier (can be free OR paid)
```
**Status:** ⚠️ NEEDS MODIFICATION  
**Solution:** Add `session_type` and `is_paid` fields to Session model

---

### 3. **Paid Atelier Access** (NEW)
```python
Required: Track which participants paid for specific ateliers
```
**Status:** ❌ NOT IMPLEMENTED  
**Solution:** Create `AtelierPayment` or `SessionAccess` model

---

### 4. **Annonces (Announcements)** (NEW)
```python
Required:
- Title, description, target (cible), timestamp
- Created by gestionnaire_des_salles
- Only creator can edit/delete
- Target: participants, exposants, all, etc.
```
**Status:** ❌ NOT IMPLEMENTED  
**Solution:** Create `Annonce` model

---

### 5. **YouTube Live Integration** (NEW)
```python
Required: Sessions need YouTube live link
```
**Status:** ❌ NOT IMPLEMENTED  
**Solution:** Add `youtube_live_url` field to Session

---

### 6. **Session Questions** (NEW)
```python
Required:
- Participants can ask questions on sessions they have access to
- Questions linked to specific session
```
**Status:** ❌ NOT IMPLEMENTED  
**Solution:** Create `SessionQuestion` model

---

### 7. **Room Assignment for Controllers/Gestionnaires** (NEW)
```python
Required:
- Assign gestionnaire_des_salles to specific room at specific time
- Can change room assignment over time
- One room at a time (morning: salle3, evening: salle4)
- Same logic for controlleur_des_badges
```
**Status:** ❌ NOT IMPLEMENTED  
**Solution:** Create `RoomAssignment` model with time_slot support

---

### 8. **Gestionnaire des Salles Role** (MODIFICATION)
```python
Current: Role is "organisateur"
Required: Rename to "gestionnaire_des_salles"
- Can only see/edit sessions of assigned room
- Creates annonces
- Full control over the event (same permissions as old organisateur)
```
**Status:** ⚠️ NEEDS ROLE RENAME  
**Solution:** Rename `organisateur` to `gestionnaire_des_salles` in UserEventAssignment.ROLE_CHOICES

---

### 9. **Controller Statistics** (NEW)
```python
Required:
- Total scans for assigned room only
- Number of blocks (denied access)
- List of scans for that room
```
**Status:** ⚠️ PARTIAL (RoomAccess exists, but no aggregated stats)  
**Solution:** Add API endpoint for room-specific statistics

---

### 10. **Exposant Features** (NEW)
```python
Required:
- Plan (PDF file)
- Statistics:
  - Total visits
  - Today's visits
  - List of scanned participants
- Can scan participant QR codes
- Scanned participants added to visit list
- Can see targeted annonces
```
**Status:** ❌ NOT IMPLEMENTED  
**Solution:** 
- Add `plan_file` to Exposant/Participant model
- Create `ExposantScan` model to track participant visits
- Create statistics API endpoint

---

## 📊 **REQUIRED DATABASE CHANGES**

### **Modified Models:**

#### 1. **Event Model** (ADD FIELDS)
```python
class Event(models.Model):
    # ... existing fields ...
    
    # NEW FIELDS
    programme_file = models.FileField(upload_to='events/programmes/', blank=True, null=True)
    guide_file = models.FileField(upload_to='events/guides/', blank=True, null=True)
    president = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='presided_events')
```

#### 2. **UserEventAssignment** (RENAME ROLE)
```python
ROLE_CHOICES = [
    ('gestionnaire_des_salles', 'Gestionnaire des Salles'),  # RENAMED from 'organisateur'
    ('controlleur_des_badges', 'Contrôleur des Badges'),
    ('participant', 'Participant'),
    ('exposant', 'Exposant'),
]
```

#### 3. **Session Model** (MODIFY + ADD FIELDS)
```python
class Session(models.Model):
    # ... existing fields ...
    
    # MODIFIED FIELD - Change status choices to French
    status = models.CharField(
        max_length=20,
        choices=[
            ('pas_encore', 'Pas Encore'),
            ('en_cours', 'En Cours'),
            ('termine', 'Terminé')
        ],
        default='pas_encore'
    )
    
    # NEW FIELDS
    session_type = models.CharField(
        max_length=20,
        choices=[('conference', 'Conférence'), ('atelier', 'Atelier')],
        default='conference'
    )
    is_paid = models.BooleanField(default=False, help_text="Paid atelier (participants must pay)")
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    youtube_live_url = models.URLField(blank=True)
```

#### 4. **Participant Model** (ADD EXPOSANT PLAN)
```python
class Participant(models.Model):
    # ... existing fields ...
    
    # NEW FIELD (for exposants only)
    plan_file = models.FileField(upload_to='exposants/plans/', blank=True, null=True)
```

---

### **New Models to Create:**

#### 5. **SessionAccess** (TRACK PAID ATELIER ACCESS)
```python
class SessionAccess(models.Model):
    """Track participant access to paid ateliers"""
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE)
    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    has_access = models.BooleanField(default=False)
    payment_status = models.CharField(
        max_length=20,
        choices=[('pending', 'Pending'), ('paid', 'Paid'), ('free', 'Free')],
        default='pending'
    )
    paid_at = models.DateTimeField(null=True, blank=True)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('participant', 'session')
```

#### 6. **Annonce** (ANNOUNCEMENTS)
```python
class Annonce(models.Model):
    """Event announcements targeted to specific user groups"""
    TARGET_CHOICES = [
        ('all', 'Tous'),
        ('participants', 'Participants'),
        ('exposants', 'Exposants'),
        ('controlleurs', 'Contrôleurs'),
        ('gestionnaires', 'Gestionnaires'),
    ]
    
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='annonces')
    title = models.CharField(max_length=200)
    description = models.TextField()
    target = models.CharField(max_length=20, choices=TARGET_CHOICES)
    
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['event', 'target', '-created_at']),
        ]
```

#### 7. **SessionQuestion** (QUESTIONS ON SESSIONS)
```python
class SessionQuestion(models.Model):
    """Questions asked by participants during sessions"""
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='questions')
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE)
    question_text = models.TextField()
    is_answered = models.BooleanField(default=False)
    answer_text = models.TextField(blank=True)
    answered_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    asked_at = models.DateTimeField(auto_now_add=True)
    answered_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['asked_at']
        indexes = [
            models.Index(fields=['session', 'asked_at']),
        ]
```

#### 8. **RoomAssignment** (ASSIGN CONTROLLERS/GESTIONNAIRES TO ROOMS)
```python
class RoomAssignment(models.Model):
    """Assign gestionnaires/controllers to specific rooms at specific times"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='room_assignments')
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='assigned_staff')
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    
    role = models.CharField(
        max_length=30,
        choices=[
            ('gestionnaire_des_salles', 'Gestionnaire des Salles'),
            ('controlleur_des_badges', 'Contrôleur des Badges'),
        ]
    )
    
    # Time slot for assignment
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    
    is_active = models.BooleanField(default=True)
    assigned_at = models.DateTimeField(auto_now_add=True)
    assigned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='room_assignments_made')
    
    class Meta:
        ordering = ['start_time']
        indexes = [
            models.Index(fields=['user', 'room', 'start_time']),
            models.Index(fields=['event', 'is_active']),
        ]
```

#### 9. **ExposantScan** (EXPOSANT SCANNING PARTICIPANTS)
```python
class ExposantScan(models.Model):
    """Track exposant scanning participant QR codes (for booth visits)"""
    exposant = models.ForeignKey(Participant, on_delete=models.CASCADE, related_name='scanned_participants')
    scanned_participant = models.ForeignKey(Participant, on_delete=models.CASCADE, related_name='exposant_scans')
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    
    scanned_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, help_text="Optional notes about the visit")
    
    class Meta:
        ordering = ['-scanned_at']
        indexes = [
            models.Index(fields=['exposant', '-scanned_at']),
            models.Index(fields=['event', '-scanned_at']),
        ]
```

---

## 🎯 **SUMMARY OF CHANGES**

### **Database Modifications Required:**

1. ✏️ **Modify Event**: Add `programme_file`, `guide_file`, `president`
2. ✏️ **Modify UserEventAssignment**: Rename `organisateur` → `gestionnaire_des_salles` role
3. ✏️ **Modify Session**: Change `status` choices to French (pas_encore, en_cours, termine) + Add `session_type`, `is_paid`, `price`, `youtube_live_url`
4. ✏️ **Modify Participant**: Add `plan_file` (for exposants)

5. ➕ **Create SessionAccess**: Track paid atelier access
6. ➕ **Create Annonce**: Event announcements with targeting
7. ➕ **Create SessionQuestion**: Questions on sessions
8. ➕ **Create RoomAssignment**: Assign staff to rooms with time slots
9. ➕ **Create ExposantScan**: Track exposant-participant interactions

### **Data Migration Required:**
- Update existing `UserEventAssignment` records: `organisateur` → `gestionnaire_des_salles`
- Update existing `Session` records status:
  - `scheduled` → `pas_encore`
  - `live` → `en_cours`
  - `completed` → `termine`
  - Remove `cancelled` status (not needed)
- Update existing test data to use new role name and French status

---

## 📝 **NEXT STEPS**

### **What I Need from You:**

1. **Confirm Understanding**: Does this analysis match your requirements?

2. **Clarifications Needed**:
   - Should "place" be a separate model, or is it just the collection of rooms?   
   it is just a collection of room we dont need to create a model for it 
   - Should exposants have a separate model or continue using Participant with role=exposant? the app has 4 roles xposant cotrolleur des badge gestionaire des salles and participant
   - Payment integration: Do you need payment gateway or just manual marking as "paid"? no i dont need payment integration 
   - File storage: Should we use Django's FileField or external storage (S3, etc.)?
   
3. **Priority Order**: Which features should I implement first?
   - Option A: All at once (complete restructure)
   - Option B: Step by step (you guide priority) we will modify the backend step by step and ask me befor any changes 

4. **Testing**: Should I create new test data after restructure?
yes 

---

## 🚀 **IMPLEMENTATION PLAN**

If you approve, I will:

1. **Phase 1**: Modify existing models (Event, Session, UserEventAssignment, Participant)
2. **Phase 2**: Create new models (SessionAccess, Annonce, SessionQuestion, RoomAssignment, ExposantScan)
3. **Phase 3**: Update permissions and views
4. **Phase 4**: Create new API endpoints
5. **Phase 5**: Update serializers
6. **Phase 6**: Create migrations
7. **Phase 7**: Update test data commands
8. **Phase 8**: Update documentation

---

**Please review and confirm before I proceed with implementation.**

and give me a full documentation after finishing the update of the app 