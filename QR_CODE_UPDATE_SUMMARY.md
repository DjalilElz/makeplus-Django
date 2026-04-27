# QR Code Update Summary

## When QR Code is Updated

The QR code data is automatically regenerated in the following scenarios:

### 1. ✅ Transaction Created (Process Payment)
**File:** `makeplus_api/caisse/views.py` - `process_transaction()`

**When:** After a participant pays for items at caisse

**What happens:**
- Transaction is created with items
- SessionAccess records are created
- QR code is regenerated with new paid items
- Participant's `qr_code_data` field is updated

**Code:**
```python
# Regenerate QR code to include new paid sessions
updated_qr_data = UserProfile.get_qr_for_user(participant.user)
participant.qr_code_data = updated_qr_data
participant.save(update_fields=['qr_code_data'])
```

### 2. ✅ Transaction Cancelled (Revoke Payment)
**File:** `makeplus_api/caisse/views.py` - `cancel_transaction()`

**When:** When a caisse operator cancels a transaction

**What happens:**
- Transaction status changed to 'cancelled'
- QR code is regenerated WITHOUT the cancelled items
- Participant's `qr_code_data` field is updated

**Code:**
```python
# Regenerate QR code to remove cancelled items
updated_qr_data = UserProfile.get_qr_for_user(participant.user)
participant.qr_code_data = updated_qr_data
participant.save(update_fields=['qr_code_data'])
```

### 3. ✅ User Login
**File:** `makeplus_api/events/auth_views.py` - `CustomLoginView`

**When:** User logs in to mobile app

**What happens:**
- QR code is regenerated with latest data
- Returned in login response

### 4. ✅ User Profile Request
**File:** `makeplus_api/events/api_views.py` - `UserProfileAPIView`

**When:** User requests their profile (`GET /api/auth/me/`)

**What happens:**
- QR code is regenerated with latest data
- Returned in profile response

## QR Code Generation Logic

**File:** `makeplus_api/events/models.py` - `UserProfile.get_or_create_qr_code()`

**Data Source:** `CaisseTransaction` table (queries all completed transactions)

**What's included:**
- User info (id, email, name, badge_id)
- Event info (if assigned)
- Participant info (if exists)
- **Paid items from ALL completed transactions:**
  - Sessions (type: "session")
  - Access passes (type: "access")
  - Meals/Dinner (type: "dinner")
  - Other items (type: "other")

**Important:** Only transactions with `status='completed'` are included. Cancelled transactions are automatically excluded.

## Badge ID Behavior

- ✅ **Generated once** when participant is created
- ✅ **Never changes** - same badge_id for life
- ✅ Only the **data inside** the QR code changes
- ✅ Participant keeps the same physical QR code

## Example Flow

### Scenario: Participant pays, then cancels

1. **Initial State:**
```json
{
  "badge_id": "USER-58-37F80526",
  "paid_items": []
}
```

2. **After Payment (Transaction 14):**
```json
{
  "badge_id": "USER-58-37F80526",
  "paid_items": [
    {"title": "Intro to AI", "amount_paid": 6000},
    {"title": "access", "amount_paid": 2000}
  ]
}
```

3. **After Cancellation (Transaction 14 cancelled):**
```json
{
  "badge_id": "USER-58-37F80526",
  "paid_items": []  // Items removed because transaction is cancelled
}
```

4. **After New Payment (Transaction 15):**
```json
{
  "badge_id": "USER-58-37F80526",
  "paid_items": [
    {"title": "Workshop B", "amount_paid": 5000}
  ]
}
```

## Testing

### Test Transaction Cancellation:

1. Create a transaction with 2 items
2. Verify QR code shows 2 items
3. Cancel the transaction
4. Verify QR code shows 0 items (or items from other transactions)

### Test Multiple Transactions:

1. Create Transaction A with Item 1
2. Verify QR code shows Item 1
3. Create Transaction B with Item 2
4. Verify QR code shows Item 1 + Item 2
5. Cancel Transaction A
6. Verify QR code shows only Item 2

## Logging

When transaction is cancelled, logs will show:
```
[CAISSE] Transaction 14 cancelled for user@example.com
[CAISSE] Regenerating QR code to remove cancelled items...
[CAISSE] ✅ QR code updated - cancelled items removed
```

## Database Query

The QR code generation queries:
```python
completed_transactions = CaisseTransaction.objects.filter(
    participant=participant,
    status='completed'  # Only completed transactions
).prefetch_related('items', 'items__session')
```

Cancelled transactions have `status='cancelled'` so they are automatically excluded.

## Mobile App Behavior

After cancellation:
1. ✅ Participant's QR code data is updated in database
2. ✅ Next time participant logs in, they get updated QR code
3. ✅ Controller scanning shows updated items (without cancelled items)
4. ❌ Participant needs to refresh/re-login to see updated QR code in their app

**Note:** If participant doesn't refresh their app, they might still have old QR code data locally. But when controller scans, the backend will fetch fresh data from database (if using scan_participant endpoint).

## Recommendation

For best user experience:
- ✅ Use backend API (`scan_participant`) for real-time data
- ✅ Display QR code data for offline mode
- ✅ Refresh QR code data when app comes to foreground
- ✅ Show "Last updated" timestamp on QR code screen
