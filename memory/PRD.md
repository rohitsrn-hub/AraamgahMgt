# E-ARMS — Araamgah Management System PRD

## Original Problem Statement
Building an app to automate room booking at a rest house. Corrections and enhancements to existing codebase cloned from https://github.com/rohitsrn-hub/AraamgahMgt.git

## Architecture
- **Frontend**: React (CRA + CRACO) → /app/frontend/src
- **Backend**: FastAPI → /app/backend/server.py
- **Database**: MongoDB
- **App URL**: https://rest-house-manager.preview.emergentagent.com

## User Personas
- Rest house manager (admin)
- Duty staff (check-ins/check-outs)
- Military/Def Civ guests

## Core Requirements (Static)
1. Room booking system for rest house
2. Check-in/Check-out management
3. Cancellation with refund tracking
4. Staff management
5. Toiletry inventory tracking
6. Settings configuration

## What's Been Implemented

### Session 5 (Feb 2026) — Payment Details in Booking + Cancellation Fix
- **Booking form**: Added Payment Mode (Cash/UPI/Bank Transfer/Card) with conditional fields; submit blocked until payment details filled
- **Cancellation flow**: `openCancelDialog()` now auto-calculates refund (days until checkin, charge %, refund amount); works from both Bookings page and Dashboard
- **Cancel dialog**: Shows full refund breakdown, Confirm button disabled until calculation loads
- **Pending Refunds modal**: Added "Mark as Paid" green button per refund — marks as completed, removes from list, refreshes dashboard
- **Check-in dialog**: Added Bill Summary section showing Room Charges, Advance Paid (deducted), Extra Beds, Balance Due at Checkout
- **Print Bill button**: Purple "Bill" button on every checked-in booking row — generates PDF receipt immediately
- **Booking form**: stripped to 10 minimum fields (Rank, Name, Army No, Aadhaar, Unit, Num Rooms, Dates, Advance)
- **Check-in form expanded** with all detailed data: Phone (+91), Age, Sex, Address, Identity Card, Service Status, Type of Service, Command HQ (conditional on Army), Family Members (Add/Remove with all sub-fields), Bank/UPI details
- **Backend**: `CheckInRequest` extended with all personal fields; saved to booking doc at check-in

### Session 2 (April 2026) — Extra Beds, Feedback, Rates Update

1. **Extra Beds field in Check-In** — Quantity input (0–5) at ₹75/bed; charge automatically added to balance at check-in
2. **Updated Room Rates** — Cat I: ₹500, Cat II: ₹400, Def Civ both categories: ₹600, Default advance: ₹400/room
3. **Bilingual Feedback Form** — Appears automatically when checkout button is clicked (must be filled before checkout completes); English + Hindi (Devanagari) labels for all 7 rating categories + 3 open-ended questions + recommendation
4. **Feedback required at checkout** — Checkout only completes after feedback form is submitted (cannot skip)
5. **Feedback Analysis Page** (/feedback) — Shows overall average score, 7 category score bars, recommendation rate, recent feedback list
6. **Dashboard Feedback Button** — Dynamic color+emoji: Green+😊 (≥4), Orange+😐 (2.5–3.9), Red+😢 (<2.5)
7. **Sidebar Feedback Nav Link** — Dynamic emoji in nav reflects current average score

### Backend Changes (server.py) — Session 2
- `CheckInRequest`: added `extra_beds: int = 0`
- `Booking`: added `extra_beds`, `extra_bed_charge`
- `check_in` endpoint: computes `extra_bed_charge = extra_beds * 75`, updates `balance_amount`
- `FeedbackCreate` model + `Feedback` document schema
- POST `/feedback` — saves feedback linked to booking
- GET `/feedback` — list feedbacks
- GET `/feedback/analysis` — aggregated scores, category averages, recommendation rate
All corrections and new features applied to cloned codebase:

1. **Calendar auto-close fix** — Popovers for date pickers now close on date selection using controlled open state
2. **onFocus select-all** — All input fields with default values highlight content on focus for quick editing
3. **Indian phone number format** — +91 prefix shown, 10-digit validation (must start 6-9), formatted as XXXXX XXXXX
4. **Rank dropdown** — Replaced text input with Select dropdown, populated from Settings ranks list
5. **Service Status field** — Serving/Retired field added to booking form (record-keeping only, no pricing impact)
6. **Bank details in booking form** — Bank Name, IFSC Code, Account Number, UPI ID, UPI Phone captured at booking time (for refund purposes)
7. **Pending Refunds feature** — "Pending Refunds" button on Bookings page shows cancelled bookings with pending refunds, displays bank/UPI details, allows marking refunds as completed with transaction reference
8. **Def Civ room rates** — Separate rates for Def Civ guests (both Cat I and Cat II) in Settings. Applied automatically when guest rank is "Def Civ"
9. **Ranks Management in Settings** — Add/remove ranks from Settings page. Default 16 ranks: Sep/Dfr/Swr, Nk, Hav, Sgt, PO, Nb Sub, JWO, CPO, Sub, WO, CA, SM, MCPO, Hony Lt or Eqvt, Hony Capt or Eqvt, Def Civ

### Backend Changes (server.py)
- AppSettings: added `def_civ_cat_i_rate`, `def_civ_cat_ii_rate`, `ranks`
- AppSettingsUpdate, SetupRequest: updated with new fields
- Booking, BookingCreate: added `guest_service_status`, `bank_name`, `bank_ifsc`, `bank_account`, `upi_id`, `upi_phone`
- Refund: added structured bank fields + `transaction_ref`, `refund_date`
- RefundUpdate: added `transaction_ref`, `refund_date`
- `get_room_rate()`: applies Def Civ rates based on guest rank
- `cancel_booking`: copies all bank details from booking to refund record

## Test Status
- Backend: 100% (12/12 tests pass)
- Frontend: 100% (all flows verified end-to-end)

## Prioritized Backlog

### P0 (Critical — done)
- All 9 features listed above

### P1 (Next priorities)
- Print/export booking confirmation slip
- Monthly report generation (PDF/Excel)
- Guest history lookup by phone number

### P2 (Future)
- SMS/WhatsApp notification on booking confirmation
- Bulk check-out for group bookings
- Occupancy analytics dashboard with charts

## Next Tasks
1. Test with real data to verify Def Civ pricing calculation
2. Consider making advance payment field editable (currently auto-calculated, readOnly)
3. Add accessibility improvements (aria-describedby for dialogs)
