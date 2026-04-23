# P0 - Check-In Pricing Logic Implementation

## Overview
Implemented new room-wise pricing logic for check-in that charges Defense Civilian (Def Civ) rates for any room where at least one occupant lacks a valid Defense/Dependent ID.

## Implementation Date
April 7, 2026

## Business Requirement
During check-in, defense personnel are charged Cat I/Cat II rates ONLY for rooms occupied entirely by them or bona fide dependents with valid dependent ID cards. If **ANY** member staying in a specific room lacks a valid defense/dependent ID, that **ENTIRE room** must be charged at Defense Civilian (Def Civ) rates.

## Features Implemented

### 1. Frontend Changes (`/app/frontend/src/pages/Bookings.jsx`)

#### A. Dependent ID Field in Family Members
- Added `dependent_id` field (free text) to family member data structure
- Line ~507: Updated `addCheckinFamilyMember()` to include `dependent_id: ""`
- Lines ~1665-1668: Added "Dependent ID Ser No" input field in Family Members UI section

#### B. Room-Wise Guest Assignment Section
- Lines ~150-151: Added `roomGuestMapping` state to track guest-to-room assignments
- Lines ~678-730: Modified `openCheckInDialog()` to initialize room mappings based on booked rooms
- Lines ~520-598: Added helper functions:
  - `addGuestToRoom()` - Assign a guest to a specific room
  - `removeGuestFromRoom()` - Remove guest from room
  - `toggleGuestValidId()` - Toggle ID validation status for a guest
  - `calculateRoomChargeCategory()` - Determine if room should be charged at Def Civ rate
  - `getGuestDisplayName()` - Format guest name for display
  - `isGuestAssignedToRoom()` - Check if guest is already assigned

#### C. Room Assignment UI (Lines ~1702-1798)
New section added between Family Members and Bank Details:
- Displays each booked room with room number and category
- Shows current charge category (Cat I/II or Def Civ) with color coding
- Checkbox to assign "Self" (primary guest) to room
- Checkboxes to assign each family member to rooms
- "Valid ID?" / "Valid Dependent ID?" toggles for each assigned guest
- Real-time calculation of charge category based on ID validation
- Visual warning when any guest lacks valid ID (room turns red with "Def Civ" label)

#### D. Enhanced Bill Preview (Lines ~1833-1910)
- Per-room charges breakdown showing:
  - Room number and category
  - Rate per night (with Def Civ indicator if applicable)
  - Total charge for each room
- Updated total calculation based on room-guest mapping
- Color-coded Def Civ rooms in red

#### E. Check-In Validation & API Call (Lines ~670-702)
- Added validation: At least one guest must be assigned to a room
- Send `room_guest_mapping` to backend during check-in
- Reset `roomGuestMapping` on dialog close/success

### 2. Backend Changes (`/app/backend/server.py`)

#### A. Data Models
- Line ~256: Added `room_guest_mapping` field to `Booking` model
- Line ~319: Added `room_guest_mapping` field to `CheckInRequest` model

#### B. Check-In Endpoint (Lines ~786-893)
Enhanced `/api/bookings/check-in` endpoint:
- Fetch app settings for rate configuration
- Parse `room_guest_mapping` from request
- Calculate nights between check-in and check-out
- For each room in mapping:
  - Check `charge_category` (determined by frontend based on guest IDs)
  - Apply Def Civ rates if charge_category is "Def Civ"
  - Apply regular Cat I/II rates otherwise
- Recalculate `room_rent_total` based on per-room pricing
- Update `total_amount` and `balance_amount`
- Store `room_guest_mapping` in booking document

## Rate Configuration
Default rates (from settings):
- Cat I: ₹500/night
- Cat II: ₹400/night
- Def Civ Cat I: ₹600/night
- Def Civ Cat II: ₹600/night

## Testing Results

### Backend Tests (8/8 Passed) - `/app/backend/tests/test_checkin_pricing_logic.py`
1. ✅ Settings have Def Civ rate configuration
2. ✅ CheckInRequest model accepts room_guest_mapping
3. ✅ Check-in endpoint accepts room_guest_mapping field
4. ✅ All guests with valid IDs → Cat I/II rates applied
5. ✅ Mixed guest IDs → Def Civ rates applied correctly
6. ✅ Room charges recalculated during check-in
7. ✅ room_guest_mapping persisted in booking document
8. ✅ Total amount and balance updated correctly

### Frontend Tests (All Features Verified)
1. ✅ Dependent ID Ser No field visible in Family Members section
2. ✅ Room-Wise Guest Assignment section displays each booked room
3. ✅ Can assign 'Self' to a room via checkbox
4. ✅ 'Valid ID?' checkbox appears when guest is assigned
5. ✅ Family members can be assigned to rooms with 'Valid Dependent ID?' toggle
6. ✅ Room charge category changes to 'Def Civ' when guest lacks valid ID
7. ✅ Bill Summary shows per-room charges with correct rates
8. ✅ Validation prevents check-in without room assignments

### Critical Bug Fixed by Testing Agent
**Issue:** Check-in button in booking list was directly setting `showCheckIn` state instead of calling `openCheckInDialog()`, causing `roomGuestMapping` to not be initialized.

**Fix:** Line ~1135 in Bookings.jsx - Changed onClick handler to `openCheckInDialog(booking)`

## Data Structure

### Room-Guest Mapping Format
```javascript
room_guest_mapping: [
  {
    room_id: "room-uuid",
    room_number: "101",
    room_category: "Cat I",
    guests: [
      { type: "self", index: null, has_valid_id: true },
      { type: "family_member", index: 0, has_valid_id: false }
    ],
    charge_category: "Def Civ"  // Calculated based on guest IDs
  },
  // ... more rooms
]
```

### Family Member with Dependent ID
```javascript
family_members: [
  {
    relation: "w/o",
    name: "...",
    age: "...",
    sex: "F",
    aadhaar: "...",
    mobile: "...",
    dependent_id: "DEP12345"  // NEW FIELD
  }
]
```

## Example Pricing Scenario

**Booking:** 2 rooms (Room 101 - Cat I, Room 102 - Cat II), 2 nights

**Room 101 Assignments:**
- Guest (Self) - Valid ID: ✅
- Wife - Valid Dependent ID: ✅
→ **Charged at Cat I rate:** ₹500 × 2 nights = ₹1000

**Room 102 Assignments:**
- Son - Valid Dependent ID: ❌ (No dependent ID provided)
→ **Charged at Def Civ rate:** ₹600 × 2 nights = ₹1200

**Total Room Charges:** ₹2200
**Extra Beds:** ₹0
**Advance Paid:** ₹500
**Balance Due:** ₹1700

## Files Modified
1. `/app/frontend/src/pages/Bookings.jsx` - Added room assignment UI and logic
2. `/app/backend/server.py` - Updated check-in endpoint with pricing calculation
3. `/app/backend/tests/test_checkin_pricing_logic.py` - Comprehensive test suite (NEW)

## Backward Compatibility
The implementation is backward compatible:
- If `room_guest_mapping` is not provided, the system falls back to original `room_rent_total`
- Existing bookings without room-guest mapping will continue to work
- Old bookings can be checked out normally

## Next Steps (Upcoming Tasks)
- P1: Feature 7 - Bank Details in Booking Form
- P2: Feature 2 - Check-In Flexibility (room number modification)
- P3: Feature 3 - Setup + Migration Support
- P4: Feature 1 - Category & Room Configuration

## Status
✅ **COMPLETED & TESTED** - All features working as expected. Ready for user verification.
