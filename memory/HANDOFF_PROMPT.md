# E-ARMS Handoff Prompt for New Agent

---

## STEP 1 — Clone Repository

Clone the GitHub repository and set up the project:

```
GitHub Repository URL: [INSERT YOUR GITHUB REPO URL HERE]
```

This is a **full-stack Rest House Room Booking and Management System** called **E-ARMS (Araamgah Management System)** built for a military rest house. It manages room bookings, check-in/check-out, billing, refunds, feedback, and monthly reports.

---

## STEP 2 — Tech Stack

| Layer     | Technology                             |
|-----------|----------------------------------------|
| Frontend  | React (CRA + CRACO), Tailwind CSS, Shadcn/UI, Phosphor Icons, jsPDF |
| Backend   | FastAPI (Python), Motor (async MongoDB) |
| Database  | MongoDB                                |
| PDF Gen   | jsPDF + jspdf-autotable (frontend only) |

**Service ports:** Backend on `0.0.0.0:8001`, Frontend on `3000`. All backend routes must be prefixed with `/api`.

---

## STEP 3 — Project Summary

The app is built for a military rest house (Araamgah) to manage:
- Room bookings (blocking rooms for dates)
- Guest check-in with detailed personal data capture
- Check-out with billing and PDF receipt
- Cancellations with auto-calculated refund amount
- Pending refunds management (with "Mark as Paid" flow)
- Bilingual (English + Hindi) feedback form at checkout
- Dashboard with analytics, feedback scoring, fund summary
- Monthly PDF report with license fee breakdown
- Settings for room rates, ranks, license fees, staff

---

## STEP 4 — Codebase Architecture

```
/app/
├── backend/
│   ├── server.py              # ALL routes + models (single file, ~1750 lines)
│   ├── requirements.txt
│   └── .env                   # MONGO_URL, DB_NAME (DO NOT CHANGE KEYS)
├── frontend/
│   ├── package.json
│   ├── tailwind.config.js
│   └── src/
│       ├── App.js              # Routes + API constant
│       ├── components/
│       │   ├── Layout.jsx      # Sidebar navigation
│       │   ├── FeedbackForm.jsx  # Bilingual feedback modal
│       │   └── ui/             # Shadcn components
│       ├── pages/
│       │   ├── Dashboard.jsx   # Main dashboard (analytics, fund summary, cancel flow)
│       │   ├── Bookings.jsx    # Booking list + all dialogs (new/checkin/checkout/cancel)
│       │   ├── Settings.jsx    # Room rates, ranks, license fees, staff, rooms
│       │   ├── FeedbackPage.jsx # Feedback analytics
│       │   ├── MonthlyReport.jsx # Monthly report with PDF export
│       │   └── Staff.jsx / Toiletry.jsx
│       └── utils/
│           └── pdfUtils.js     # generateCheckoutReceipt(), generateMonthlyReportPDF(), generateRefundsPDF()
└── memory/
    ├── PRD.md
    └── test_credentials.md
```

---

## STEP 5 — What Has Been Fully Implemented (All Working, 100% Tested)

### Booking Form (New Booking Dialog)
- Minimum fields only: **Rank, Guest Name, Army/Service No, Aadhaar, Unit, Num Rooms, Check-in Date, Check-out Date**
- Room selection grid (auto-loads available rooms based on dates)
- Section 4 — **Advance Payment with Payment Mode**:
  - Payment Mode: Cash / UPI / Bank Transfer / Card
  - **Cash** → Receipt Number field (required)
  - **UPI** → UPI ID + UPI Phone (at least one required)
  - **Bank Transfer** → Bank Name + Account Number (required) + IFSC + Transaction Ref
  - **Card** → Card Transaction Reference (required)
  - Submit button **blocked** until payment mode + details are filled

### Check-In Dialog (Expanded — 7 sections)
1. **Booking Summary** — guest/room/date overview
2. **Staff Member** selection (required)
3. **Extra Beds** — ₹75/bed, adds to final bill
4. **Personal Details** — Phone (+91 validation), Age, Sex, Address, Identity Card No, Service Status (Serving/Retired)
5. **Service Details** — Type of Service (Army/Air Force/Navy/SFC), Command HQ (conditional on Army)
6. **Family Members** — Add/Remove members with Relation, Name, Age, Sex, Aadhaar, Mobile
7. **Bank/UPI Details** — for refund if cancelled (Bank Name, IFSC, Account, UPI ID, UPI Phone)
- Bill Summary shows live breakdown: Room Charges - Advance Paid + Extra Beds = Balance Due

### Check-Out Dialog
- Staff selection, final payment amount + mode
- Mandatory **Bilingual Feedback Form** before checkout completes (7 categories rated 1–5, English + Hindi labels)
- PDF receipt auto-generated on checkout (A5 landscape)

### Cancellation (from ALL screens)
- Cancel button on confirmed + checked-in bookings calls **auto-calculate refund API**
- Dialog shows: Days until check-in, Advance Paid, Cancellation Charge (%), Refund Amount
- Confirm button disabled until calculation loads
- Works from both Bookings page and Dashboard

### Pending Refunds (Dashboard)
- "Pending Refund Amount" button on dashboard is clickable
- Opens modal showing each pending refund: Guest name, booking number, amount, bank/UPI details
- **"Mark as Paid"** green button per refund → marks completed, removes from list, refreshes dashboard amount

### Print Bill
- Purple **"Bill"** button on every checked-in booking row → generates PDF receipt on demand
- PDF receipt also auto-generated on checkout

### Dashboard
- Overview cards: total bookings, checked-in, revenue, occupancy %
- Fund Generation section with pending refund amount button
- Feedback analytics button (color + emoji coded by average score: 😊 green ≥4, 😐 orange 2.5–3.9, 😢 red <2.5)
- Monthly Report button

### Monthly Report
- PDF export with: Command-wise occupancy, License fee calculation, Financial summary
- Configurable in Settings: Cat I license fee, Cat II license fee, Def Civ license fee

### Settings
- Room rate configuration: Cat I, Cat II, Def Civ (separate rates)
- Default advance amount
- License fee per category
- Ranks management (add/remove from dropdown used in bookings)
- Staff management (add/deactivate)
- Room management (add rooms with category)

---

## STEP 6 — Key API Endpoints

```
GET  /api/setup                   # Get all settings
POST /api/setup                   # Update settings

GET  /api/bookings                # List bookings (filter: ?status=confirmed|checked_in|etc)
POST /api/bookings                # Create new booking
POST /api/bookings/check-in       # Check in guest (CheckInRequest with all personal fields)
POST /api/bookings/check-out      # Check out guest
POST /api/bookings/cancel         # Cancel booking
GET  /api/bookings/{id}/calculate-refund  # Auto-calculate refund amount

GET  /api/refunds                 # List refunds (?status=pending|completed)
PUT  /api/refunds/{id}            # Update refund status

POST /api/feedbacks               # Submit feedback
GET  /api/feedbacks/stats         # Feedback analytics

GET  /api/reports/monthly         # Monthly report data (?month=4&year=2026)
GET  /api/dashboard/funds         # Dashboard fund summary (?month=4&year=2026)

GET  /api/rooms                   # List rooms (?available_from=&available_to=)
GET  /api/staff                   # List staff
```

---

## STEP 7 — Key Data Models

### Booking Document (MongoDB)
```python
{
  "id": str,
  "booking_number": str,           # e.g., BK202604011234
  "guest_name": str,
  "guest_rank": Optional[str],     # From settings ranks list
  "guest_unit": Optional[str],
  "army_number": Optional[str],
  "aadhaar_number": Optional[str],
  "guest_contact": Optional[str],  # Captured at CHECK-IN (not booking)
  "guest_age": Optional[int],      # Captured at CHECK-IN
  "guest_sex": Optional[str],      # Captured at CHECK-IN
  "guest_address": Optional[str],  # Captured at CHECK-IN
  "identity_card_number": Optional[str],
  "guest_service_status": Optional[str],  # "Serving" | "Retired"
  "service_type": Optional[str],   # "Army" | "Air Force" | "Navy" | "SFC"
  "command_hq": Optional[str],     # Conditional on Army
  "family_members": List[dict],    # [{relation, name, age, sex, aadhaar, mobile}]
  "bank_name": Optional[str],      # Captured at CHECK-IN
  "bank_ifsc": Optional[str],
  "bank_account": Optional[str],
  "upi_id": Optional[str],
  "upi_phone": Optional[str],
  "payment_mode": Optional[str],   # "cash" | "upi" | "bank_transfer" | "card"
  "payment_id": Optional[str],     # Receipt/transaction ref from BOOKING
  "room_ids": List[str],
  "room_numbers": List[str],
  "room_categories": List[str],    # ["Cat I", "Cat II"]
  "check_in_date": str,            # ISO date "YYYY-MM-DD"
  "check_out_date": str,
  "status": str,                   # "confirmed" | "checked_in" | "checked_out" | "cancelled"
  "total_amount": float,
  "advance_paid": float,
  "balance_amount": float,
  "extra_beds": int,
  "extra_bed_charge": float,
  "license_fee_total": float,
  "room_rent_total": float
}
```

### AppSettings (MongoDB `setup` collection)
```python
{
  "cat_i_rate": float,           # Full rate (rent + license fee) for Cat I
  "cat_ii_rate": float,
  "def_civ_cat_i_rate": float,
  "def_civ_cat_ii_rate": float,
  "cat_i_room_rent": float,
  "cat_ii_room_rent": float,
  "def_civ_room_rent": float,
  "cat_i_license_fee": float,
  "cat_ii_license_fee": float,
  "def_civ_license_fee": float,
  "default_advance_amount": float,
  "ranks": List[str],
  "cancellation_policy": dict    # {days_tiers: [{days, charge_percent}]}
}
```

---

## STEP 8 — Important Coding Rules

1. **Never rewrite `server.py` entirely** — it's ~1750 lines. Use `search_replace` tool for targeted edits
2. **MongoDB `_id` exclusion** — always use `{"_id": 0}` in projections
3. **Frontend uses** `REACT_APP_BACKEND_URL` env var; backend uses `MONGO_URL` from `.env`
4. **Backend routes** must always be prefixed with `/api`
5. **PDF generation** is entirely on the frontend using `jsPDF` (`/app/frontend/src/utils/pdfUtils.js`)
6. **Payment fields at booking** vs **personal details at check-in** — this two-stage design is intentional
7. `guest_contact` in `BookingCreate` is **Optional** (captured at check-in, not booking)
8. For rank "Def Civ" — separate room rates apply (def_civ_cat_i_rate / def_civ_cat_ii_rate)

---

## STEP 9 — Pending / Next Tasks (Prioritized)

### P1 — High Priority
- **Guest history lookup** — Search bookings by phone number or Army No; show past stay history
- **Booking confirmation slip PDF** — Generate a printable confirmation slip when a new booking is created (not just at checkout)

### P2 — Medium Priority
- **Re-print bill for checked-out bookings** — Add "Print Bill" button to checked-out booking rows (currently only checked-in rows have it)
- **Occupancy analytics dashboard** — Charts showing room occupancy trends, peak periods, category-wise breakdown

### P3 — Future / Backlog
- SMS/WhatsApp notification on booking confirmation
- Bulk check-out for group bookings
- Export monthly report to Excel (currently PDF only)
- Refactor `server.py` into separate route files as it grows large

---

## STEP 10 — Test Credentials & Seed Data

Refer to `/app/memory/test_credentials.md` in the repository for any pre-seeded accounts.

The app has **no authentication system** — it's an internal admin tool accessible directly.

To test a full booking flow:
1. Go to Settings → ensure rooms exist (Cat I and Cat II) and ranks are set
2. Go to Bookings → New Booking → fill guest details + dates + select rooms + payment mode
3. Check In the confirmed booking → fill personal details + extra beds
4. Check Out → fill feedback form → PDF receipt auto-downloads
5. Go to Dashboard → Fund Generation section → click "Pending Refund Amount" to manage refunds

---

## STEP 11 — Known Architecture Notes

- `server.py` has grown to ~1750 lines. Consider splitting into `routes/bookings.py`, `routes/reports.py`, `models.py` in a future refactor session
- The feedback form is mandatory at checkout (cannot be skipped). This is by design
- Cancellation charge percent is configured via `cancellation_policy.days_tiers` in settings (tiered by days until check-in)
- License fee = separate from room rent; both stored independently; total = rent + license fee
- The Monthly Report pulls `check_out_date` within the selected month; it uses `service_type` and `command_hq` for command-wise breakdown
