# P2: Check-In Flexibility - Room Modification

## Date
April 7, 2026

## Feature Overview
Allows staff to modify room assignments during the check-in process. This provides flexibility when rooms need to be changed due to guest preferences, maintenance issues, or availability changes.

## Key Features

### 1. Room Assignment Modification UI

**Location:** Check-In Dialog → "Room Assignments" section (amber box)

**Components:**
- Current room display (when not modifying)
- "Modify Rooms" button to toggle modification mode
- Room selection dropdowns (when modifying)
- "Apply Room Changes" button
- Visual feedback for changed rooms (green highlight + "(Changed)" label)

### 2. Smart Room Selection

**Available Rooms Display:**
- Shows only vacant rooms for the booking dates
- Includes currently assigned rooms (to allow no-change scenario)
- Visual indicator: "✓ Available" vs "Currently Assigned"
- Uses `exclude_booking_id` parameter to show current rooms as available

**Conflict Detection:**
- Backend validates room availability for booking dates
- Prevents assigning already occupied rooms
- Ensures selected rooms match original room count

### 3. Real-Time Updates

**When "Apply Room Changes" is clicked:**
1. Calls `PUT /api/bookings/{id}/update-rooms`
2. Updates `booking.room_ids`, `room_numbers`, `room_categories`
3. Refreshes check-in dialog with new room assignments
4. Room-guest mapping automatically updates to reflect new rooms
5. Pricing recalculation happens based on new room categories

## User Flow

### Default View (Not Modifying)
```
┌─────────────────────────────────────────────┐
│ 🔄 Room Assignments      [Modify Rooms]     │
├─────────────────────────────────────────────┤
│ Current room assignments for this booking:  │
│ ┌──────────────┬──────────────┐            │
│ │ Room C2-08   │ Room C2-09   │            │
│ │ (Cat II)     │ (Cat II)     │            │
│ └──────────────┴──────────────┘            │
└─────────────────────────────────────────────┘
```

### Modification Mode
```
┌─────────────────────────────────────────────┐
│ 🔄 Room Assignments    [Cancel Changes]     │
├─────────────────────────────────────────────┤
│ ⚠️  Select new rooms from available options │
│                                              │
│ Room 1 Assignment (Changed)                 │
│ [Room C2-10 (Cat II) - ✓ Available ▼]      │
│                                              │
│ Room 2 Assignment                           │
│ [Room C2-09 (Cat II) - Currently Assigned ▼]│
│                                              │
│ [Apply Room Changes]                        │
└─────────────────────────────────────────────┘
```

## Technical Implementation

### Frontend (`/app/frontend/src/pages/Bookings.jsx`)

**State Management:**
```javascript
const [showRoomModification, setShowRoomModification] = useState(false);
const [availableRoomsForCheckIn, setAvailableRoomsForCheckIn] = useState([]);
const [modifiedRoomIds, setModifiedRoomIds] = useState([]);
```

**Key Functions:**

1. **fetchAvailableRoomsForCheckIn(booking)** (Lines 880-908)
   - Fetches available rooms for booking dates
   - Merges with currently assigned rooms
   - Uses `exclude_booking_id` parameter

2. **toggleRoomModification()** (Lines 910-912)
   - Toggles between view and edit mode

3. **handleRoomChange(oldRoomId, newRoomId)** (Lines 914-932)
   - Updates modified room selection
   - Updates room-guest mapping to reflect new room details
   - Preserves charge category logic (Def Civ status maintained if applicable)

4. **applyRoomChanges()** (Lines 934-951)
   - Calls backend API to update booking
   - Refreshes booking data
   - Exits modification mode

**UI Section** (Lines 1802-1882):
- Amber box distinguishing from blue Room-Wise Guest Assignment section
- Toggle between view and edit modes
- Visual indicators for changed rooms (green background, "(Changed)" label)
- "Apply Room Changes" button disabled if no changes made

### Backend (`/app/backend/server.py`)

**1. GET /api/rooms/available** (Lines 610-645)
```python
@api_router.get("/rooms/available")
async def get_available_rooms(
    check_in: str,
    check_out: str,
    exclude_booking_id: Optional[str] = None
):
    # Returns rooms available for given dates
    # Excludes rooms booked by others for overlapping dates
    # Optionally excludes specific booking (to show its current rooms)
```

**2. PUT /api/bookings/{booking_id}/update-rooms** (Lines 935-974)
```python
@api_router.put("/bookings/{booking_id}/update-rooms")
async def update_booking_rooms(booking_id: str, request: dict):
    # Validates booking status (must be CONFIRMED)
    # Validates room count matches original
    # Fetches new room details
    # Updates booking.room_ids, room_numbers, room_categories
```

**Validation:**
- ✅ Only CONFIRMED bookings can modify rooms (not CHECKED_IN or CHECKED_OUT)
- ✅ Room count must match original booking
- ✅ All new room IDs must exist in database

## Benefits

1. **Flexibility:** Handle last-minute room changes without rebooking
2. **Guest Satisfaction:** Accommodate room preference changes
3. **Operational Efficiency:** Quick room swaps for maintenance or upgrades
4. **Conflict Prevention:** Only shows truly available rooms
5. **Price Transparency:** Automatic recalculation if room category changes
6. **Audit Trail:** Updated room assignments logged with timestamps

## Example Scenarios

### Scenario 1: Guest Requests Different Room
**Original Booking:** Room C2-08 (Cat II)
**Guest Request:** "Can I get Room C2-10 instead? It's quieter."

**Staff Action:**
1. Open check-in dialog
2. Click "Modify Rooms"
3. Select Room C2-10 from dropdown
4. See "(Changed)" indicator
5. Click "Apply Room Changes"
6. ✅ Room updated, proceed with check-in

### Scenario 2: Maintenance Issue
**Original Booking:** Room C1-05 (Cat I)
**Issue:** Air conditioning not working in C1-05

**Staff Action:**
1. Open check-in dialog
2. Click "Modify Rooms"
3. Select available Cat I room (e.g., C1-08)
4. Apply changes
5. ✅ Guest assigned to working room

### Scenario 3: Category Upgrade
**Original Booking:** 2 × Cat II rooms
**Upgrade:** Change one room to Cat I (higher rate)

**Staff Action:**
1. Modify rooms → Select Cat I room
2. Apply changes
3. ✅ Pricing automatically recalculates with Cat I rate for that room

## Testing Results

### Backend Tests (8/8 Passed) ✅
- ✅ GET /api/rooms/available basic functionality
- ✅ Available rooms excludes already booked rooms
- ✅ Available rooms with exclude_booking_id parameter
- ✅ Update rooms for confirmed booking
- ✅ Update rooms blocked for checked-in booking (400 error)
- ✅ Update rooms validates room count
- ✅ Update rooms updates categories correctly
- ✅ Full room modification flow (end-to-end)

### Frontend Tests (All Passed) ✅
- ✅ Room Assignments section visible in check-in dialog
- ✅ "Modify Rooms" button toggles correctly
- ✅ Room dropdown shows available rooms
- ✅ Visual indicator "(Changed)" appears for modified rooms
- ✅ "Apply Room Changes" button enabled/disabled correctly
- ✅ Room assignments updated successfully
- ✅ Integration with room-guest mapping for pricing

### Bugs Fixed by Testing Agent
1. **CRITICAL:** Missing `ArrowsClockwise` icon import → Check-in dialog crash
2. **HIGH:** Missing `/api/rooms/available` endpoint → Room modification not working

**Test Files:**
- `/app/backend/tests/test_p2_room_modification.py`
- `/app/test_reports/iteration_13.json`

## Constraints

1. **Only CONFIRMED bookings:** Cannot modify rooms after check-in
2. **Same room count:** Must select same number of rooms as original booking
3. **Valid rooms only:** All selected rooms must exist in database
4. **Date availability:** Rooms must be available for booking dates

## Integration with Other Features

**With P0 (Room-Wise Pricing):**
- Room-guest mapping automatically updates with new room details
- Charge category (Def Civ vs Cat I/II) recalculates based on new room
- Per-room pricing reflects new room categories

**With Booking System:**
- Booking metadata (room_numbers, room_categories) updated
- Updated timestamp recorded
- No impact on advance payment or balance

## Files Modified

1. `/app/frontend/src/pages/Bookings.jsx`
   - Lines 157-159: P2 state variables
   - Lines 880-951: Room modification functions
   - Lines 1802-1882: Room Assignment Modification UI
   - Line 16: Added `ArrowsClockwise` icon import

2. `/app/backend/server.py`
   - Lines 610-645: GET `/api/rooms/available` endpoint (NEW)
   - Lines 935-974: PUT `/api/bookings/{id}/update-rooms` endpoint (NEW)

---

**Status:** ✅ COMPLETED & TESTED (100% pass rate - 8/8 backend tests)
