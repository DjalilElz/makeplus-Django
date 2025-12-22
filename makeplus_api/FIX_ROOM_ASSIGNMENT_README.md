# IMMEDIATE FIX NEEDED: Room Assignment for User ID 26

## Problem
User `aopagest1@gmail.com` (ID: 26) has role `gestionnaire_des_salles` for event "AOPA" but the `UserEventAssignment` (ID: 25) has `null` metadata - missing room assignment.

## Quick Fix (Choose ONE method)

### ⚡ FASTEST: Use the Quick Fix Script

```bash
cd makeplus_api
python manage.py shell < fix_assignment_25.py
```

This will automatically:
- Find assignment ID 25
- Find room "Aula" in event "AOPA"
- Update metadata with room assignment
- Verify the fix

### 🔧 Alternative: Management Command

```bash
# First, list all rooms in the AOPA event to get the room UUID
python manage.py shell
>>> from events.models import Room, Event
>>> event = Event.objects.get(name="AOPA")
>>> for room in Room.objects.filter(event=event):
...     print(f"{room.name}: {room.id}")
>>> exit()

# Then assign the room (replace ROOM_UUID with actual UUID)
python manage.py fix_room_assignments \
    --assignment-id "25" \
    --room-id "ROOM_UUID"
```

### 📝 Alternative: Django Admin

1. Go to: https://makeplus-django-5.onrender.com/admin/
2. Navigate to: **Events** → **User Event Assignments**
3. Find assignment ID 25 (aopagest1@gmail.com in AOPA event)
4. Edit the **Metadata** field to:
   ```json
   {"assigned_room_id": "YOUR_ROOM_UUID"}
   ```
5. Click **Save**

### 💻 Alternative: Django Shell Manual Fix

```bash
python manage.py shell
```

```python
from events.models import UserEventAssignment, Room, Event

# Find the assignment
assignment = UserEventAssignment.objects.get(id="25")
print(f"User: {assignment.user.email}")
print(f"Event: {assignment.event.name}")
print(f"Role: {assignment.role}")

# Find the room (Aula)
room = Room.objects.get(event=assignment.event, name="Aula")
print(f"Room: {room.name} (ID: {room.id})")

# Assign the room
assignment.metadata = {"assigned_room_id": str(room.id)}
assignment.save()

print("✅ FIXED! Room assigned.")

# Verify
assignment.refresh_from_db()
print(f"Metadata: {assignment.metadata}")
```

## After Fix: Verify

Test the API endpoint to confirm:

```bash
curl -X GET "https://makeplus-django-5.onrender.com/api/events/bb04f29e-f282-44c1-a5b7-dd198c752e85/users/" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

Look for assignment ID 25 - the `metadata` field should now contain:
```json
{
  "metadata": {
    "assigned_room_id": "room-uuid-here"
  }
}
```

## Prevention: All New Users Will Have Room Assignments

The recent backend updates ensure:
- ✅ Step 4 of event creation now includes room selection
- ✅ User creation form includes room selection
- ✅ Room assignment is saved to metadata automatically
- ✅ Room is displayed in user detail page

**Only existing users** created before these updates need manual fixing.

## Files Created

1. **fix_assignment_25.py** - Quick fix script for this specific case
2. **fix_room_assignments.py** - Management command for bulk fixes
3. **BACKEND_DOCUMENTATION.md** - Updated with room assignment section

## Questions?

Check the updated section in BACKEND_DOCUMENTATION.md:
- "🚪 Room Assignment System for Organisateurs, Gestionnaires & Contrôleurs"
