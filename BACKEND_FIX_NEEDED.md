# Backend Fix Needed: `/api/my-room/statistics/` Endpoint

## Problem Summary

The Flutter app is successfully calling the `/api/my-room/statistics/` endpoint with a valid JWT token containing `event_id`, but the backend is returning 404 with error: `"No event context found. Please select an event first."`

---

## Current Request Details

**Endpoint:** `GET https://makeplus-django-5.onrender.com/api/my-room/statistics/`

**HTTP Status:** 404 (should be 200)

**Response Headers Show:** `allow: GET, HEAD, OPTIONS` ✅ (confirms endpoint exists)

**Error Response:**
```json
{"detail":"No event context found. Please select an event first."}
```

**JWT Token Claims (verified in Flutter app):**
```json
{
  "token_type": "access",
  "user_id": 15,
  "event_id": "6442555a-2295-41f7-81ee-0a902a9c4102",
  "role": "controlleur_des_badges"
}
```

**Request Headers:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
Accept: application/json
```

---

## Root Cause Analysis

The endpoint **EXISTS** (confirmed by `allow: GET, HEAD, OPTIONS` header), but the view is returning 404 because it cannot extract the `event_id` from the request context.

### Likely Issues:

1. **Event Context Middleware Not Running**
   - The middleware that extracts `event_id` from JWT and adds it to `request.event` or `request.user.event` might not be configured or is failing silently

2. **Incorrect Event Extraction**
   - The view might be looking for the event in the wrong place:
     - ❌ Checking `request.event` when it should check JWT claims
     - ❌ Checking `request.user.event` when JWT stores `event_id` as a separate claim
     - ❌ Looking for `request.GET['event_id']` instead of JWT
     - ✅ Should read from JWT token claims directly

3. **Token Decoding Issue**
   - The view might not be decoding the JWT properly to access the custom `event_id` claim

---

## What You Need to Check

### 1. Check the View Code (`events/views.py`)

The `MyRoomStatisticsView` should extract event_id like this:

```python
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import AccessToken
from .permissions import IsController
from .models import RoomAssignment, RoomAccess

class MyRoomStatisticsView(APIView):
    permission_classes = [IsAuthenticated, IsController]
    
    def get(self, request):
        # METHOD 1: From JWT token claims directly (RECOMMENDED)
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if not auth_header.startswith('Bearer '):
            return Response(
                {"detail": "Invalid authorization header"}, 
                status=401
            )
        
        token_string = auth_header.split('Bearer ')[1]
        
        try:
            token = AccessToken(token_string)
            event_id = token.get('event_id')
            user_id = token.get('user_id')
            
            if not event_id:
                return Response(
                    {"detail": "No event_id found in JWT token"}, 
                    status=400
                )
            
            # Find controller's assigned room
            assignment = RoomAssignment.objects.filter(
                user_id=user_id,
                event_id=event_id,
                role='controlleur_des_badges',
                is_active=True
            ).first()
            
            if not assignment:
                return Response(
                    {"detail": "No active room assignment found for this controller"},
                    status=404
                )
            
            room = assignment.room
            
            # Calculate statistics
            from django.utils import timezone
            from datetime import datetime, timedelta
            
            today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
            
            # Get all room access records
            all_scans = RoomAccess.objects.filter(room=room)
            today_scans = all_scans.filter(access_time__gte=today_start)
            
            # Get recent scans with participant details
            recent_scans = all_scans.select_related(
                'participant',
                'participant__user',
                'verified_by'
            ).order_by('-access_time')[:20]
            
            recent_scans_data = []
            for scan in recent_scans:
                user = scan.participant.user
                recent_scans_data.append({
                    'id': str(scan.id),
                    'participant': {
                        'id': str(scan.participant.id),
                        'name': f"{user.first_name} {user.last_name}".strip() or user.email,
                        'email': user.email,
                        'badge_id': scan.participant.badge_number,
                    },
                    'session': 'Accès salle',  # You can enhance this with actual session info
                    'status': 'granted',  # All records in RoomAccess are granted
                    'accessed_at': scan.access_time.isoformat(),
                    'verified_by': scan.verified_by.username if scan.verified_by else '',
                })
            
            # Build response
            response_data = {
                'room': {
                    'id': str(room.id),
                    'name': room.name,
                    'capacity': room.capacity,
                },
                'statistics': {
                    'total_scans': all_scans.count(),
                    'today_scans': today_scans.count(),
                    'granted': all_scans.count(),
                    'denied': 0,  # RoomAccess only stores granted access
                    'unique_participants': all_scans.values('participant').distinct().count(),
                    'unique_participants_today': today_scans.values('participant').distinct().count(),
                },
                'recent_scans': recent_scans_data,
            }
            
            return Response(response_data, status=200)
            
        except Exception as e:
            return Response(
                {"detail": f"Error processing request: {str(e)}"}, 
                status=500
            )
```

### 2. Check URL Configuration (`events/urls.py`)

Ensure the endpoint is registered:

```python
from django.urls import path
from .views import MyRoomStatisticsView

urlpatterns = [
    # ... other urls
    path('my-room/statistics/', MyRoomStatisticsView.as_view(), name='my-room-statistics'),
    # ... other urls
]
```

### 3. Check Main URL Configuration (`makeplus_api/urls.py`)

Ensure the events URLs are included:

```python
from django.urls import path, include

urlpatterns = [
    # ... other urls
    path('api/', include('events.urls')),
    # ... other urls
]
```

### 4. Check Middleware (`settings.py`) - OPTIONAL

If you have custom middleware for event context:

```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # Add custom event middleware if you have one
    # 'events.middleware.JWTEventMiddleware',
]
```

### 5. Check Custom JWT Claims (`views.py` or `serializers.py`)

Verify that login response includes `event_id`:

```python
from rest_framework_simplejwt.tokens import RefreshToken

def get_tokens_for_user(user, event, role):
    refresh = RefreshToken.for_user(user)
    
    # Add custom claims
    refresh['event_id'] = str(event.id)
    refresh['role'] = role
    
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }
```

---

## Debugging Steps

### Step 1: Add Debug Logging to the View

```python
def get(self, request):
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"🔍 DEBUG - Request method: {request.method}")
    logger.info(f"🔍 DEBUG - Request path: {request.path}")
    logger.info(f"🔍 DEBUG - Authorization header: {request.META.get('HTTP_AUTHORIZATION', 'MISSING')[:50]}...")
    logger.info(f"🔍 DEBUG - Request user: {request.user}")
    logger.info(f"🔍 DEBUG - User ID: {request.user.id if request.user else 'Anonymous'}")
    
    # Try to get event_id from different sources
    event_from_request = getattr(request, 'event_id', None)
    event_from_user = getattr(request.user, 'event_id', None)
    
    logger.info(f"🔍 DEBUG - Event from request: {event_from_request}")
    logger.info(f"🔍 DEBUG - Event from user: {event_from_user}")
    
    # ... rest of the code
```

### Step 2: Test the Endpoint Directly

```bash
# Replace YOUR_JWT_TOKEN with actual token from Flutter app
curl -X GET https://makeplus-django-5.onrender.com/api/my-room/statistics/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json"
```

### Step 3: Check Room Assignment in Database

```python
# In Django shell: python manage.py shell
from events.models import RoomAssignment
from django.contrib.auth.models import User

user_id = 15
event_id = "6442555a-2295-41f7-81ee-0a902a9c4102"

# Check if user exists
user = User.objects.filter(id=user_id).first()
print(f"User: {user}")

# Check room assignments
assignments = RoomAssignment.objects.filter(
    user_id=user_id,
    event_id=event_id,
    is_active=True
)
print(f"Active assignments: {assignments}")

for assignment in assignments:
    print(f"  - Room: {assignment.room.name}, Role: {assignment.role}")
```

### Step 4: Verify JWT Token Structure

```python
# In Django shell
from rest_framework_simplejwt.tokens import AccessToken

token_string = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."  # Your actual token

try:
    token = AccessToken(token_string)
    print(f"Token payload: {token.payload}")
    print(f"User ID: {token.get('user_id')}")
    print(f"Event ID: {token.get('event_id')}")
    print(f"Role: {token.get('role')}")
except Exception as e:
    print(f"Error decoding token: {e}")
```

---

## Expected Response Structure

Once fixed, the endpoint should return:

```json
{
  "room": {
    "id": "uuid",
    "name": "Salle Principale",
    "capacity": 100
  },
  "statistics": {
    "total_scans": 45,
    "today_scans": 12,
    "granted": 38,
    "denied": 7,
    "unique_participants": 25,
    "unique_participants_today": 8
  },
  "recent_scans": [
    {
      "id": "uuid",
      "participant": {
        "id": "uuid",
        "name": "John Doe",
        "email": "john@example.com",
        "badge_id": "BADGE123"
      },
      "session": "Accès salle",
      "status": "granted",
      "accessed_at": "2025-11-28T14:30:00Z",
      "verified_by": "controller_username"
    }
  ]
}
```

---

## Common Mistakes to Avoid

1. ❌ **Don't** look for `event_id` in `request.GET` or `request.POST`
2. ❌ **Don't** assume `request.event` exists without middleware
3. ❌ **Don't** return 404 if room has no scans yet (return empty statistics instead)
4. ✅ **Do** extract `event_id` directly from JWT token claims
5. ✅ **Do** verify the controller has an active room assignment
6. ✅ **Do** return 200 with empty arrays/zeros if no data exists

---

## Testing Checklist

After implementing the fix, verify:

- [ ] Endpoint returns 200 status code
- [ ] Response includes `room` object with id, name, capacity
- [ ] Response includes `statistics` object with all counts
- [ ] Response includes `recent_scans` array (can be empty)
- [ ] Works with valid JWT token containing `event_id`
- [ ] Returns proper error if controller has no room assignment
- [ ] Returns proper error if token is invalid/expired

---

## Contact

If you need clarification or have questions about this issue, please provide:
1. The debug logs from Step 1
2. The room assignment query results from Step 3
3. The token payload from Step 4
4. Any error traces from the server logs
