# Event Edit Form Fix

**Date:** December 21, 2025  
**Issue:** "Number of rooms: This field is required" error when editing events  
**Status:** ✅ Fixed

---

## Problem

When editing an existing event through the dashboard, users encountered the error:
```
Number of rooms: This field is required.
```

## Root Cause

The `EventDetailsForm` was used for both:
1. **Event Creation** - where `number_of_rooms` is needed to determine how many room forms to display
2. **Event Editing** - where `number_of_rooms` should NOT be required (rooms are already created)

The `number_of_rooms` field is NOT a database field in the Event model - it's only a temporary form field used during the multi-step event creation process.

## Solution

Created a separate `EventEditForm` specifically for editing events:

### 1. Created New Form (dashboard/forms.py)

```python
class EventEditForm(forms.ModelForm):
    """Form for editing existing events (without number_of_rooms field)"""
    
    class Meta:
        model = Event
        fields = [
            'name', 'description', 'start_date', 'end_date', 
            'location', 'location_details', 'status',
            'logo', 'banner', 'organizer_contact',
            'programme_file', 'guide_file'
        ]
        # ... widgets configuration
```

**Key Difference:**
- ❌ `EventDetailsForm`: Includes `number_of_rooms` field (for creation)
- ✅ `EventEditForm`: Excludes `number_of_rooms` field (for editing)

### 2. Updated Event Edit View (dashboard/views.py)

```python
@login_required
@user_passes_test(is_staff_user)
def event_edit(request, event_id):
    """Edit event details"""
    
    event = get_object_or_404(Event, id=event_id)
    
    if request.method == 'POST':
        # Use EventEditForm which doesn't include number_of_rooms
        form = EventEditForm(request.POST, request.FILES, instance=event)
        if form.is_valid():
            form.save()
            messages.success(request, f'Event "{event.name}" updated successfully!')
            return redirect('dashboard:event_detail', event_id=event.id)
    else:
        form = EventEditForm(instance=event)
    
    context = {
        'form': form,
        'event': event,
        'is_edit': True
    }
    
    return render(request, 'dashboard/event_edit.html', context)
```

**Changed:**
- Before: `form = EventDetailsForm(request.POST, request.FILES, instance=event)`
- After: `form = EventEditForm(request.POST, request.FILES, instance=event)`

### 3. Updated Imports

```python
from .forms import (
    EventDetailsForm,      # For event creation (Step 1)
    EventEditForm,         # For event editing (new)
    RoomForm, 
    SessionForm, 
    # ... other forms
)
```

---

## Files Modified

1. **dashboard/forms.py**
   - Added `EventEditForm` class (lines ~90-165)
   - Made `number_of_rooms` explicitly `required=True` in `EventDetailsForm`

2. **dashboard/views.py**
   - Updated imports to include `EventEditForm`
   - Changed `event_edit()` view to use `EventEditForm`

---

## Form Usage Clarification

### EventDetailsForm
**Used for:** Event creation (Step 1 of multi-step process)
**Includes:** All event fields + `number_of_rooms`
**Purpose:** `number_of_rooms` determines how many room forms to show in Step 2

### EventEditForm
**Used for:** Event editing
**Includes:** All event fields (NO `number_of_rooms`)
**Purpose:** Update existing event details without recreating rooms

---

## Testing

### Before Fix
```
❌ Edit event → Form validation error
Error: "Number of rooms: This field is required."
```

### After Fix
```
✅ Edit event → Form saves successfully
✅ All event fields update correctly
✅ No "number_of_rooms" field shown in edit form
```

---

## Why This Design?

**Event Creation Process:**
```
Step 1: Event Details + number_of_rooms (e.g., 3)
  ↓
Step 2: Room 1 details
  ↓
Step 2: Room 2 details
  ↓
Step 2: Room 3 details
  ↓
Step 3: Review & Create
```

The `number_of_rooms` field controls how many times Step 2 is repeated.

**Event Editing:**
- Rooms are already created and managed separately
- No need to specify `number_of_rooms` again
- Rooms can be added/edited/deleted through room management pages

---

## Related Documentation

- Event creation workflow: See DASHBOARD_COMPLETION_REPORT.md
- Room management: See BACKEND_DOCUMENTATION.md § Rooms
- Multi-step forms: See ADMIN_DASHBOARD_DOCUMENTATION.md

---

**Status:** All functionality working as expected ✅
