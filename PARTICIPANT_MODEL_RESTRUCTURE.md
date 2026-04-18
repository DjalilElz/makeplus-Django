# Participant Model Restructure

## Overview

The Participant model has been restructured to support the requirement that **one user = one participant**, with the ability to register for multiple events.

---

## Old Structure (Before)

```
User ──┬── Participant (Event A)
       ├── Participant (Event B)
       └── Participant (Event C)
```

- One User could have MULTIPLE Participant records (one per event)
- `Participant` had ForeignKey to both `User` and `Event`
- `unique_together = ('user', 'event')`

---

## New Structure (After)

```
User ──── Participant ──┬── EventRegistration (Event A)
                        ├── EventRegistration (Event B)
                        └── EventRegistration (Event C)
```

- One User has ONE Participant record (OneToOne relationship)
- `Participant` has ManyToMany relationship with `Event` through `EventRegistration`
- Event-specific data (check-in, allowed_rooms) moved to `EventRegistration`

---

## Models

### Participant Model

```python
class Participant(models.Model):
    """One participant per user, can register for multiple events"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    events = models.ManyToManyField(Event, through='EventRegistration')
    
    badge_id = models.CharField(max_length=100, unique=True)
    qr_code_data = models.TextField()
    role = models.CharField(max_length=30, default='participant')
    plan_file = models.FileField(...)
    metadata = models.JSONField(default=dict)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

### EventRegistration Model (New)

```python
class EventRegistration(models.Model):
    """Links participant to specific event with event-specific data"""
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    
    # Event-specific status
    is_checked_in = models.BooleanField(default=False)
    checked_in_at = models.DateTimeField(null=True, blank=True)
    
    # Event-specific access
    allowed_rooms = models.ManyToManyField(Room, blank=True)
    
    registered_at = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(default=dict)
    
    class Meta:
        unique_together = ('participant', 'event')
```

---

## Flow

### 1. Sign Up (Mobile App)

```python
# User signs up
user = User.objects.create(...)

# Participant profile created automatically
participant = Participant.objects.create(
    user=user,
    badge_id=generate_badge_id(),
    role='participant'
)
```

**Result:** User has a Participant profile, but not registered for any events yet.

### 2. Register for Event A (Website Form)

```python
# Get existing participant
participant = Participant.objects.get(user=user)

# Create event registration
EventRegistration.objects.create(
    participant=participant,
    event=event_a
)
```

**Result:** Participant is now registered for Event A.

### 3. Register for Event B (Website Form)

```python
# Same participant
participant = Participant.objects.get(user=user)

# Create another event registration
EventRegistration.objects.create(
    participant=participant,
    event=event_b
)
```

**Result:** Same participant, now registered for both Event A and Event B.

---

## Benefits

1. **One Participant Per User**: Cleaner data model, no duplicate participant records
2. **Multiple Events**: User can register for unlimited events
3. **Event-Specific Data**: Check-in status and room access are per-event
4. **Automatic Creation**: Participant profile created on signup
5. **Consistent Badge ID**: Same badge ID across all events

---

## Migration

Migration `0025_restructure_participant_model.py` handles:

1. Creates `EventRegistration` table
2. Backs up existing participant data
3. Removes duplicate participants (keeps most recent per user)
4. Migrates data to new structure
5. Removes old columns and constraints
6. Adds new foreign keys and indexes

---

## API Changes

### Login Response

```json
{
  "access": "...",
  "refresh": "...",
  "user": {...},
  "role": "participant",
  "event": null,  // or most recent event if registered
  "qr_code": {...}
}
```

### Participant Endpoint

```json
{
  "id": 1,
  "user": {...},
  "badge_id": "USER-1-ABC123",
  "role": "participant",
  "registered_events": [
    {"id": "uuid-1", "name": "Event A"},
    {"id": "uuid-2", "name": "Event B"}
  ],
  "events_count": 2
}
```

---

## Updated Files

1. `makeplus_api/events/models.py` - Restructured Participant and added EventRegistration
2. `makeplus_api/events/signup_service.py` - Auto-create Participant on signup
3. `makeplus_api/events/form_validation_service.py` - Create EventRegistration instead of Participant
4. `makeplus_api/events/serializers.py` - Updated serializers for new structure
5. `makeplus_api/events/admin.py` - Updated admin for new models
6. `makeplus_api/events/migrations/0025_restructure_participant_model.py` - Migration

---

## Testing

After deployment:

1. Sign up new user → Check Participant created automatically
2. Register for Event A → Check EventRegistration created
3. Register for Event B → Check second EventRegistration created
4. Login → Check response includes participant data
5. Admin panel → Verify Participant and EventRegistration models

---

**Status:** Ready for deployment
**Date:** April 18, 2026
