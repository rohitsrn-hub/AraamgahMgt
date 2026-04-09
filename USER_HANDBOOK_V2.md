# 📖 E-ARMS User Handbook v2.0
## AraamgahMgt - Complete User Guide with Latest Features

**Version:** 2.0  
**Last Updated:** April 2026  
**For:** Rest House Managers, Duty Staff, and Administrators

---

## 🎯 What's New in Version 2.0

### ✨ Major Feature Updates:

**🗑️ Booking Management**
- **NEW:** Hard Delete button for permanently removing wrong entries
- Complete removal from database, analytics, and planner
- Confirmation dialog with detailed warnings
- Available for all booking statuses

**🏠 Enhanced Check-In Experience**
- Room-wise guest assignment with inline family member addition
- Per-room pricing based on dependent card validation
- Automatic Def Civ rate application when required
- **NEW:** Expanded family relations (Father, Mother, Brother, Sister)
- **NEW:** Dynamic rank dropdown automatically updates from Settings

**💰 Improved Financial Management**
- Bank/UPI details captured during booking for faster refunds
- Comprehensive payment details at check-out (transaction IDs, card details, bank references)
- Auto-population of payment details from booking data
- **NEW:** Hours-based cancellation policy (96h/48h thresholds)
- Simplified payment fields

**📋 Enhanced Booking Information**
- **NEW:** Total members field with individual age capture
- Better party composition tracking
- Automatic age-based categorization

**🔧 Operational Flexibility**
- **NEW:** Context-aware check-in/check-out from Dashboard and Command Center
- **NEW:** Booking selection modal for streamlined operations
- Modify room assignments during check-in
- Conflict detection prevents double-booking
- Migration mode for historical data import

**📅 Enhanced Planning & Navigation**
- **NEW:** Month/year navigation in Room Planner
- **NEW:** Visual gradient indicators for check-in/check-out dates
- **NEW:** Same-day availability visualization
- Previous/Next month buttons for quick browsing
- Dropdown selectors for any month/year
- Visual calendar with occupancy tracking
- Color-coded status (Blue=Confirmed, Amber=Checked-In, Grey=Checked-Out)

**⚙️ Dynamic Configuration**
- Custom room categories with capacity management
- **NEW:** Hours-based cancellation policy configuration
- "Run Setup" option to reconfigure system
- Formation signs with official military insignia

**🔐 Data Validation & Consistency**
- Uniform mobile number validation across all forms
- Auto-uppercase for Service/Defence/Dependent IDs
- **NEW:** Auto-uppercase for Identity Card numbers
- IFSC code validation (11-character format)
- Real-time validation feedback

---

## 📑 Table of Contents

1. [Introduction](#1-introduction)
2. [Getting Started](#2-getting-started)
3. [Command Center](#3-command-center)
4. [Dashboard](#4-dashboard)
5. [Making a Booking (NEW)](#5-making-a-booking-new)
6. [Check-In Process (REDESIGNED)](#6-check-in-process-redesigned)
7. [Check-Out Process](#7-check-out-process)
8. [Managing Bookings](#8-managing-bookings)
9. [Room Modification (NEW)](#9-room-modification-new)
10. [Rooms Management](#10-rooms-management)
11. [Feedback System](#11-feedback-system)
12. [Reports](#12-reports)
13. [Settings & Configuration (ENHANCED)](#13-settings--configuration-enhanced)
14. [Migration Mode (NEW)](#14-migration-mode-new)
15. [Troubleshooting](#15-troubleshooting)

---

## 1. Introduction

### What is E-ARMS?

E-ARMS (AraamgahMgt - Automated Room Management System) is a comprehensive military resthouse management application designed for Eastern Command and 101 Area facilities.

**Core Capabilities:**
- Guest booking and room assignment
- Per-room pricing with dependent card validation
- Bank/UPI details capture for refunds
- Dynamic check-in with room modification
- Staff and occupancy management
- PDF bill generation
- Analytics and reporting
- Flexible room category configuration

### Who Should Use This Handbook?

- **Duty Staff** - Daily booking and check-in operations
- **Administrators** - System configuration and management
- **Accounts Personnel** - Financial reporting and refunds
- **Management** - Analytics and decision-making

---

## 2. Getting Started

### System Access

1. Open your web browser
2. Navigate to the E-ARMS application URL
3. You'll see the **Command Center** splash screen
4. Click any action button to begin

### Main Navigation

**Command Center Actions:**
- **New Booking** - Create a reservation
- **Check In** - Process guest arrival
- **Check Out** - Process guest departure
- **View Dashboard** - See occupancy & analytics

**Sidebar Menu:**
- Dashboard
- Bookings
- Rooms
- Staff
- Feedback
- Reports
- Settings

---

## 3. Command Center

### Overview

The **Command Center** is your central hub for quick actions. It features a military-inspired interface with large, color-coded buttons for instant access to core functions.

### Available Actions

#### 🟢 New Booking
- **Action:** Creates a new booking
- **Navigation:** Opens Bookings page with new booking form
- **Use Case:** Guest calls to reserve a room

#### 🔵 Check In
- **Action:** Opens booking selection modal
- **Process:**
  1. Click "Check In" button
  2. System shows all **confirmed** bookings
  3. Select the booking from dropdown
  4. Click "Proceed"
  5. Full check-in form opens with guest details pre-populated
- **Use Case:** Guest arrives at facility

**NEW Feature:** Context-aware booking selection ensures you check in the right guest.

#### 🟠 Check Out
- **Action:** Opens booking selection modal
- **Process:**
  1. Click "Check Out" button
  2. System shows all **checked-in** bookings
  3. Select the booking from dropdown
  4. Click "Proceed"
  5. Full check-out form opens with payment details
- **Use Case:** Guest departs from facility

**NEW Feature:** Payment details auto-populate from booking data for faster processing.

#### 🔴 Cancel
- **Action:** Opens booking cancellation flow
- **Navigation:** Opens Dashboard with cancel dialog
- **Use Case:** Booking needs to be cancelled

#### 🟣 Dashboard
- **Action:** Opens main dashboard
- **Features:** Occupancy stats, analytics, room planner
- **Use Case:** View current facility status

### Best Practices

✅ **Use Command Center for:**
- Quick check-in/check-out during busy hours
- Fast access to booking form
- Visual navigation for new users

✅ **Booking Selection Tips:**
- Use dropdown search to find specific guest by name
- Booking info shows: Guest Name, Booking #, Room, Dates
- Selected booking preview appears before proceeding

❌ **Avoid:**
- Skipping booking selection - always verify correct guest
- Proceeding without reviewing booking summary

---

## 4. Dashboard

### Overview Cards

**Occupancy Summary:**
- Total rooms available
- Currently occupied rooms
- Occupancy percentage
- Available rooms

**Today's Activity:**
- Expected arrivals (confirmed bookings for today)
- Expected departures (checkouts due today)

**Monthly Statistics:**
- Total bookings this month
- Total revenue
- Average occupancy rate

### Charts & Graphs

- **Occupancy Trend** - Daily occupancy over time
- **Revenue Analysis** - Monthly revenue breakdown
- **Category Distribution** - Bookings by room category

### Room Planner (NEW ENHANCED 📅)

**Purpose:** Visual calendar showing room occupancy by date with gradient indicators for same-day availability

**NEW Navigation Features:**
- **Month Dropdown:** Select any month (January - December)
- **Year Dropdown:** Select year (2024-2027)
- **Previous Month Button (◀):** Go back one month
- **Next Month Button (▶):** Go forward one month
- **Show/Hide Toggle:** Collapse planner to save screen space

**How to Navigate:**

1. **Quick Navigation:**
   - Click ◀ to go to previous month
   - Click ▶ to go to next month
   - Year automatically adjusts (Dec → Jan increments year)

2. **Direct Selection:**
   - Click month dropdown → Select any month
   - Click year dropdown → Select any year
   - Planner updates immediately

**Calendar Display:**

**Status Colors:**
- **Blue:** Confirmed bookings
- **Amber:** Checked-in guests
- **Grey:** Checked-out (historical)
- **Green:** Available rooms

**NEW: Gradient Indicators** 🎨
- **Check-in dates:** Show gradient (light → dark blue/amber)
  - Indicates guest checks in at 13:00
- **Check-out dates:** Show gradient (light → dark blue/amber)
  - Indicates room available from 09:00 same day
- **Middle dates:** Solid color (fully occupied)

**Visual Example:**
```
Room C1-01:  [▓▓▓▓▓] [████] [████] [░░░▓]
             Check-in  Full   Full  Check-out
             13:00     Day    Day   09:00
```

Each day shows:
- Date number
- Booking status (color + gradient)
- Hover: Guest name, booking number

**Use Cases:**
- Check availability for future dates
- Review past occupancy patterns
- Identify same-day availability (gradient cells)
- Plan maintenance during low occupancy periods
- Identify peak booking periods

**Same-Day Turnaround:**
- Check-out at 08:00 + Cleaning (1 hour) = Available 09:00
- New check-in at 13:00 (4-hour gap)
- Gradient visualization shows this availability

**Tips:**
✅ Use month navigation to check seasonal trends
✅ Gradient cells indicate same-day booking opportunities
✅ Show planner during guest calls to confirm availability
✅ Hide planner when not needed to reduce clutter

### Quick Action Buttons (NEW ✨)

The Dashboard now includes quick access buttons:

**Check In Button:**
1. Click "Check In"
2. Booking selection modal opens
3. Shows only **confirmed** bookings
4. Select guest from dropdown
5. Click "Proceed" → Full check-in form opens

**Check Out Button:**
1. Click "Check Out"  
2. Booking selection modal opens
3. Shows only **checked-in** bookings
4. Select guest from dropdown
5. Click "Proceed" → Full check-out form opens

**Benefits:**
- Context-aware booking selection
- No wrong guest selection
- Faster operations during busy times

---

## 5. Making a Booking (NEW)

### Step 1: Guest Details

**Required Information:**
- Guest Name
- Guest Contact (10-digit mobile, auto-formatted: XXXXX XXXXX)
- Rank (select from dropdown)
- Army/Service Number (auto-converts to UPPERCASE)
- Unit Name

**NEW: Party Composition** 👥

1. **Total Members (including self):** Enter total people (1-20), includes primary guest
2. **Ages of All Members:** Auto-generates age fields - M1=Member 1 (guest), M2=Member 2, etc.

**Example:** Total: 4 → Ages: M1=45, M2=42, M3=15, M4=12

**Tip:** Mobile numbers auto-format as "XXXXX XXXXX"

---

### Step 2: Room Selection

**Choose Rooms:**
1. Select number of rooms needed
2. Pick check-in date (calendar)
3. Pick check-out date (calendar)
4. Select specific rooms from available options

**Available Rooms Display:**
- Green = Available
- Red = Occupied
- Shows room number and category

**Migration Mode Note:**
If Migration Mode is enabled in Settings, you can select past dates for historical data entry.

---

### Step 3: Bank/UPI Details (NEW ✨)

**Purpose:** For refund processing if booking is cancelled

**Required Fields:**
- Bank Name (e.g., State Bank of India)
- IFSC Code (e.g., SBIN0001234)
- Account Number
- UPI ID (e.g., name@upi)
- UPI Phone (10-digit mobile)

**Why Now?**
Capturing these details during booking speeds up refund processing in case of cancellation. All fields are optional but recommended.

---

### Step 4: Payment Details

**Advance Amount:**
- Default: ₹400 per room
- Can be customized

**Payment Mode:**
Select one of:
- **Cash** - Receipt number required
- **UPI** - Transaction ID required
- **Bank Transfer** - Transfer reference required
- **Card** - Transaction reference required

**Simplified Payment Fields:**
Since bank details are already captured above:
- **Cash:** Only Receipt Number
- **UPI:** Only Transaction ID (not UPI details again)
- **Bank Transfer:** Only Transfer Reference (not bank details again)
- **Card:** Only Transaction Reference

---

### Step 5: Review & Confirm

**Bill Preview:**
- Room charges (nights × rate per room)
- Advance paid
- Balance due at checkout

**Confirmation:**
- Click "Create Booking"
- Booking number generated (e.g., BK-2026-0001)
- Status: **CONFIRMED**

---

## 6. Check-In Process (REDESIGNED)

The check-in process has been completely redesigned for better UX and accurate per-room pricing.

### Opening Check-In Dialog

1. Go to **Bookings** page
2. Find confirmed booking
3. Click **"Check In"** button
4. Check-in dialog opens with auto-filled data

**Auto-Filled Fields:**
- Guest contact (from booking)
- Bank details (from booking)
- UPI details (from booking)

---

### Section 1: Personal Details

**Staff Member ID:** Enter duty staff ID

**Guest Details:**
- Guest Age (optional)
- Guest Sex (M/F)
- Guest Address
- Identity Card Number (required for Def Civ validation)

**Service Details:**
- Guest Service Status (required)
  - Serving
  - Retired
- Service Type (if serving)
  - Regular
  - Territorial Army
  - Ex-Serviceman
- Command/HQ

---

### Section 2: Room Assignments (NEW ⚠️)

**Current Room Display:**
Shows rooms assigned during booking (e.g., Room C2-08, Room C2-09)

**Modify Rooms Button:**
- Click to change room assignments
- Only shows available rooms for booking dates
- Visual indicator for changed rooms (green background + "Changed" label)
- "Apply Room Changes" button to save

**When to Modify:**
- Guest preference for different room
- Maintenance issue with assigned room
- Upgrade/downgrade request

**Conflict Detection:**
System prevents assigning already occupied rooms.

---

### Section 3: Room-Wise Guest Assignment (NEW ✨)

This is the **most important new feature** for accurate pricing.

**How It Works:**

For each booked room, you'll see a card like this:

```
┌─────────────────────────────────────────┐
│ Room C2-08 (Cat II)                     │
│ Charging at: Cat II                     │
│ 1 Guest                                  │
├─────────────────────────────────────────┤
│ ☑ Ram Kumar (Self)                      │
│                                         │
│ [Add Family Member to Room C2-08]       │
└─────────────────────────────────────────┘
```

**Assigning Self:**
- Check the box next to "Ram Kumar (Self)" to assign the guest to this room
- Self can only be in ONE room (radio button behavior)

**Adding Family Members:**

1. Click **"Add Family Member to Room C2-08"**
2. Fill in details:
   - **Relation:** Wife (w/o), Son (s/o), Daughter (d/o), Father, Mother, Brother, Sister, Other
   - **Name:** Full name
   - **Age:** Required
   - **Sex:** M/F/Other
   - **Mobile:** Optional (10-digit, auto-formatted)
3. **Dependent Card Available?** checkbox:
   - ☑ **Checked** - Family member has valid dependent card
     - Dependent ID Ser No field appears (auto-converts to UPPERCASE)
     - Enter ID serial number
   - ☐ **Unchecked** - No dependent card
     - Room will be charged at **Def Civ rate**

**Pricing Logic:**

| Room Occupants | Charge Rate |
|----------------|-------------|
| All have valid Defense/Dependent IDs | Cat I/Cat II (standard rate) |
| ANY person lacks valid ID | Def Civ rate (₹600/night) |

**Example:**

**Room C2-08:**
- Ram Kumar (Self) - Identity Card: ✅
- Wife - Dependent Card: ✅ (ID: DEP12345)
→ **Charged at Cat II rate (₹400/night)**

**Room C2-09:**
- Son - Dependent Card: ❌ (No card)
→ **Charged at Def Civ rate (₹600/night)**

---

### Section 4: Bill Summary

**Updated Per-Room Breakdown:**

```
Per-Room Charges (2 nights):
  Room C2-08 (Cat II): ₹400 × 2 = ₹800
  Room C2-09 (Cat II → Def Civ): ₹600 × 2 = ₹1200

Total Room Charges: ₹2000
Extra Beds: ₹0
Advance Paid: ₹500
Balance Due: ₹1500
```

**Real-Time Updates:**
Bill updates automatically as you check/uncheck "Dependent Card Available"

---

### Section 5: Bank/UPI Details

**Auto-Filled from Booking:**
- Bank Name
- IFSC Code
- Account Number
- UPI ID
- UPI Phone

**Editable:**
You can update these if guest provides new information.

---

### Section 6: Extra Beds & Notes

**Extra Beds:**
- Number of extra beds (₹75 per bed)
- Added to final bill

**Notes:**
- Any special requests
- Maintenance issues
- Guest preferences

---

### Completing Check-In

**Validation:**
- Staff ID required
- Service status required
- At least one guest must be assigned to a room

**Confirm Check-In Button:**
- Creates bill with per-room charges
- Marks rooms as OCCUPIED
- Status changes to **CHECKED_IN**
- Bill preview can be printed

---

## 7. Check-Out Process

### Opening Check-Out Dialog

1. Go to **Bookings** page
2. Filter: "Checked In"
3. Click **"Check Out"** button

### Extra Bed Charges at Checkout

**If Extra Beds Used:**
- Enter number of extra beds used
- Enter number of days used
- Auto-calculates: beds × days × ₹75

**Example:**
- 2 extra beds
- Used for 3 days
- Charge: 2 × 3 × ₹75 = ₹450

### Final Bill Calculation

```
Room Charges: ₹2000 (per-room pricing from check-in)
Extra Bed Charges: ₹450
Total: ₹2450
Advance Paid: ₹500
Balance Due: ₹1950
```

### Payment Collection (NEW ENHANCED 💳)

**Payment Mode Selection:**
Choose from:
- Cash
- UPI
- Card
- Bank Transfer

**Based on Payment Mode, Required Details:**

#### Cash Payment
- **Cash Receipt Number** (required)
  - Enter voucher/receipt number

#### Card Payment
- **Card Transaction Reference** (required)
  - Approval/transaction ID
- **Last 4 Digits of Card** (optional)
- **Card Type** (optional): Visa, Mastercard, RuPay, Amex

#### UPI Payment
- **UPI Transaction ID** (required)
  - ⚠️ Unique for each transaction - must enter fresh ID
- **UPI ID** (optional)
  - Auto-filled from booking data
  - Can be updated if needed
- **UPI Phone** (optional)
  - Auto-filled from booking data
  - Format: XXXXX XXXXX

#### Bank Transfer
- **Bank Transfer Reference** (required)
  - NEFT/IMPS/RTGS reference number
- **Bank Name** (optional)
  - Auto-filled from booking data
- **IFSC Code** (optional)
  - Auto-filled from booking data
  - 11-character format: ABCD0123456
- **Account Number** (optional)
  - Auto-filled from booking data

**Auto-Population Feature:**
✅ Fields auto-fill from booking/check-in data when available
✅ Green checkmark (✓) indicates auto-filled fields
✅ Light background highlights pre-filled fields
✅ All fields remain editable

**Validation:**
- Payment mode selected → Transaction ID/Reference required
- System prevents checkout without payment details
- Clear error messages guide data entry

**Amount to Collect:**
- Displayed clearly
- Balance Due + Extra Bed Charges = Final Payment

**Checkout Confirmation:**
- Generates final PDF bill
- Marks rooms as AVAILABLE
- Status changes to **CHECKED_OUT**
- Guest feedback form link provided

---

## 8. Managing Bookings

### Booking Status Flow

**CONFIRMED** → **CHECKED_IN** → **CHECKED_OUT**

**Or:**

**CONFIRMED** → **CANCELLED** (with refund)

### Viewing Bookings

**Filter Options:**
- All
- Confirmed (awaiting check-in)
- Checked In (currently staying)
- Checked Out (completed)
- Cancelled

**Search:**
- By booking number
- By guest name
- By contact number

### Booking Details Card

**Information Displayed:**
- Booking Number
- Guest Name, Rank, Contact
- Check-in / Check-out dates
- Room numbers
- Payment details
- Status badge

### Booking Actions

**For Confirmed Bookings:**
- **Check In** - Opens check-in dialog (available from check-in date)
- **Cancel** - Opens cancellation dialog with refund calculation
- **Delete** 🗑️ - Permanently remove wrong entry (see Hard Delete section below)

**For Checked-In Bookings:**
- **Check Out** - Complete check-out process
- **Print Bill** - Generate checkout receipt PDF
- **Cancel** - Cancel booking with refund calculation
- **Delete** 🗑️ - Permanently remove wrong entry

**For All Other Statuses:**
- **Delete** 🗑️ - Permanently remove entry from system

---

### Hard Delete Feature (NEW 🗑️)

**Purpose:** Completely remove wrong, duplicate, or test bookings from the system.

**⚠️ IMPORTANT DIFFERENCE:**
- **Cancel** = Normal booking cancellation with refund processing (guest cancelled their booking)
- **Delete** = Permanent removal for administrative errors (wrong data entry, duplicate, test data)

**When to Use Delete:**
✅ Wrong guest name entered by mistake
✅ Duplicate booking created accidentally
✅ Test booking that needs complete removal
✅ Data entry error requiring complete removal

**When NOT to Use Delete:**
❌ Guest wants to cancel → Use "Cancel" button instead
❌ Routine booking management → Use normal status changes

**How It Works:**

1. **Click Delete Button** (🗑️ trash icon) in Actions column
2. **Confirmation Dialog Shows:**
   - Booking details (number, guest, rooms, dates)
   - Warning: "This action cannot be undone!"
   - What will be deleted:
     * Booking removed from database
     * Rooms freed for future bookings
     * Removed from analytics and planner
3. **Choose Action:**
   - "Cancel" - Abort deletion
   - "Delete Permanently" - Proceed with deletion
4. **Result:**
   - Booking disappears immediately
   - Rooms become available
   - Cannot be undone

---

## 9. Room Modification (NEW)

### When to Use

- Guest wants different room after booking confirmed
- Maintenance issue with assigned room
- Upgrade/downgrade request
- Room availability changes

### How to Modify Rooms During Check-In

**Step 1: Open Check-In Dialog**

**Step 2: Find "Room Assignments" Section**
- Shows current rooms (e.g., Room C2-08, C2-09)

**Step 3: Click "Modify Rooms" Button**
- Interface changes to room selection dropdowns
- Only available rooms shown (for booking dates)

**Step 4: Select New Rooms**
- Dropdown per room
- Shows: "Room XX (Cat I/II) - ✓ Available" or "Currently Assigned"
- Changed rooms highlighted in green with "(Changed)" label

**Step 5: Apply Changes**
- Click "Apply Room Changes"
- Booking updated with new room assignments
- Room-guest mapping automatically updates

**Step 6: Continue Check-In**
- Assign guests to rooms as usual
- Pricing automatically adjusts if category changed

### Conflict Prevention

**System Checks:**
- Room must be available for booking dates
- Cannot assign already occupied room
- Must select same number of rooms as original booking

---

## 10. Rooms Management

### Viewing Rooms

**Grid View:**
- Shows all rooms
- Color-coded status:
  - Green = Available
  - Red = Occupied
- Displays: Room number, category, status

### Room Information

**Details:**
- Room Number (e.g., C1-01, C2-09)
- Category (e.g., Cat I, Cat II, VIP)
- Capacity (persons)
- Status (Available, Occupied, Under Maintenance)

### Room Categories (Dynamic)

Room categories are now fully configurable in Settings.

**Default Categories:**
- Cat I - Standard Rate: ₹500, Def Civ: ₹600, Capacity: 2
- Cat II - Standard Rate: ₹400, Def Civ: ₹600, Capacity: 2

**Custom Categories:**
Administrators can add categories like VIP Suite, Standard, Economy, etc.

---

## 11. Feedback System

### Guest Feedback Collection

**After Checkout:**
- Guest receives feedback form link
- Can be accessed via QR code or URL

**Feedback Form Fields:**
- Overall experience rating (1-5 stars)
- Room cleanliness
- Staff behavior
- Food quality
- Facilities
- Comments/suggestions

### Viewing Feedback

**Feedback Page:**
- Lists all submitted feedback
- Filter by rating
- Search by guest name
- Export to PDF

**Print Feedback:**
- Individual feedback can be printed
- Useful for management review

---

## 12. Reports

### Available Reports

**Occupancy Report:**
- Date range selection
- Room-wise occupancy
- Category-wise breakdown
- Occupancy percentage

**Revenue Report:**
- Date range selection
- Total revenue
- Payment mode breakdown
- Per-category revenue

**Guest Report:**
- List of guests for date range
- Rank-wise distribution
- Unit-wise analysis

**Monthly Summary:**
- Total bookings
- Total revenue
- Average occupancy
- Peak days

### Exporting Reports

- PDF format
- Excel format (if available)
- Print directly

---

## 13. Settings & Configuration (ENHANCED)

### System Actions (NEW)

**Run Setup:**
- Reconfigure rooms and rates
- Shows setup wizard again
- Confirmation required before reset

**Migration Mode:**
- Enable to allow past-dated bookings
- Used for importing historical data
- Shows warning when enabled
- Remember to disable after migration

---

### Formation Signs

**Official Insignia:**
- Formation Sign 1: Eastern Command, Indian Army
- Formation Sign 2: 101 Area, Indian Army

**"Reset to Official Signs" Button:**
- One-click restore to official insignia
- Custom URLs can be entered if needed

---

### Room Categories (NEW ✨)

**Most Important Configuration Section**

**Add Category Button:**
Creates new room category with fields:

1. **Category Name** (required)
   - E.g., "Cat I", "VIP Suite", "Standard"

2. **Prefix** (required, max 3 chars, auto-uppercase)
   - Used for room numbers
   - E.g., "C1" creates C1-01, C1-02, etc.
   - "VIP" creates VIP-01, VIP-02, etc.

3. **Standard Rate** (₹/night, required, > 0)
   - For defense personnel with valid ID
   - E.g., ₹500

4. **Def Civ Rate** (₹/night, required, > 0)
   - For defense civilians or invalid dependent cards
   - E.g., ₹600

5. **Room Capacity** (persons, required, > 0)
   - Maximum occupancy per room
   - E.g., 2 persons

6. **Number of Rooms** (required, ≥ 0)
   - Total rooms in this category
   - E.g., 6 rooms
   - Shows preview: "Will create rooms: C1-01 to C1-06"

**Managing Categories:**
- Edit any field
- Delete category (trash icon) - minimum 1 required
- Save Categories button
- Cancel button to discard changes

**Example Configuration:**

**Cat I:**
- Name: Cat I
- Prefix: C1
- Standard Rate: ₹500
- Def Civ Rate: ₹600
- Capacity: 2 persons
- Room Count: 6
→ Creates C1-01 to C1-06

**VIP Suite:**
- Name: VIP Suite
- Prefix: VIP
- Standard Rate: ₹1000
- Def Civ Rate: ₹1200
- Capacity: 4 persons
- Room Count: 3
→ Creates VIP-01 to VIP-03

**Validation:**
- All fields required
- Rates must be > 0
- Capacity must be > 0
- At least 1 category required

---

### Room Rates Summary (Read-Only)

**Purpose:** Quick reference view of all category rates

**Displays:**
- Category name (large, bold)
- Prefix, room count, capacity (subtitle)
- Standard Rate (blue box)
- Def Civ Rate (orange box)

**Note:** "edit in Room Categories section above"

**Not Editable:**
This is a summary view only. To change rates, edit in Room Categories section.

---

### License Fee Breakdown

**Purpose:** Monthly financial reporting to maintaining agency

**Editable Fields:**

**Cat I (JCO):**
- Room Rent (₹)
- License Fee (₹)
- Auto-calculated Total

**Cat II (OR):**
- Room Rent (₹)
- License Fee (₹)
- Auto-calculated Total

**Def Civ:**
- Room Rent (₹)
- License Fee (₹)
- Auto-calculated Total

**Formula:** Total Rate = Room Rent + License Fee

**Use Case:**
These values are used in monthly financial reports to calculate the license fee payable to the maintaining agency.

**Note:** This is separate from room category rates and serves a different accounting purpose.

---

### Ranks Management (ENHANCED ✨)

**Purpose:** Manage military ranks that appear in booking forms

**Dynamic Rank Dropdown:**
- Ranks configured here automatically appear in New Booking form
- No manual updates needed
- Changes reflect immediately after saving

**Add Rank:**
1. Enter rank name in text field
2. Click "Add Rank" button or press Enter
3. Rank appears in list below
4. **NEW:** Rank immediately available in New Booking form dropdown

**Remove Rank:**
1. Click trash icon (🗑️) next to rank name
2. Rank removed from list
3. Removed from booking form dropdown after save

**Reset to Defaults:**
- Click "Reset to Default Ranks"
- Restores standard military ranks
- Confirmation required before reset

**Default Ranks:**
Sep/Dfr/Swr, Nk, Hav, Sgt, PO, Nb Sub, JWO, CPO, Sub, WO, CA, SM, MCPO, Hony Lt or Eqvt, Hony Capt or Eqvt, Def Civ

**How Dynamic Update Works:**
1. Add/remove ranks in Settings page
2. Click "Save Settings" button at bottom
3. Navigate to Bookings → New Booking
4. New ranks appear in "Rank" dropdown
5. Removed ranks disappear from dropdown

**Important Notes:**
- Ranks saved in Settings persist across sessions
- Changes take effect immediately after save
- No restart or manual refresh needed
- Existing bookings with old ranks remain unchanged

---

### Default Advance Amount

**Configuration:**
- Set default advance per room
- E.g., ₹400
- Can be overridden during booking

---

### Cancellation Policy (UPDATED - Hours-Based ⏰)

**NEW: Hours-Based System**

The cancellation policy now uses **hours before check-in** for precise refund calculations.

**Default Policy:**

| Notice Period | Charge | Refund |
|---------------|--------|--------|
| >96 hours (4+ days) | 0% | 100% ✅ |
| 48-96 hours (2-4 days) | 50% | 50% ⚠️ |
| <48 hours (<2 days) | 100% | 0% ❌ |

**Configuration:**
- Add/edit policy slabs in Settings
- Set hours_before thresholds (96h, 48h, 0h)
- Set charge percentages (0%, 50%, 100%)
- Real-time preview shows refund amounts

**How It Works:**
System calculates exact hours until check-in (13:00) and applies matching policy slab.

**Examples:**
- Cancel 120 hours before → 100% refund
- Cancel 72 hours before → 50% refund
- Cancel 24 hours before → 0% refund

---

### Save Settings

**Save Button:**
- Click to save all changes
- Confirmation message
- Settings applied immediately

---

## 14. Migration Mode (NEW)

### What is Migration Mode?

A special mode that allows entering bookings with past dates, useful for importing historical data from legacy systems.

### When to Use

- Initial system setup with existing guest records
- Data migration from old register
- Backdated entry corrections
- Historical data import

### Enabling Migration Mode

**Location:** Settings → System Actions → Migration Mode

**Steps:**
1. Click "Enable" button
2. Warning appears: "⚠️ You can now create bookings and check-ins with past dates for data migration."
3. Status changes to "Enabled"
4. Date restrictions removed

### Using Migration Mode

**With Migration Mode ON:**
- Booking form allows past check-in dates
- Date validation bypassed
- Can select any date from calendar

**Example:**
- Today: April 7, 2026
- Can create booking for March 1, 2026 (past date)
- Useful for importing March bookings

### Disabling Migration Mode

**Important:** Always disable after migration complete

**Steps:**
1. Go to Settings → Migration Mode
2. Click "Disable" button
3. Status changes to "Disabled"
4. Normal date validation restored

**Security:**
Migration mode is stored in browser localStorage and persists across sessions until manually disabled.

---

## 15. Data Validation & Consistency (NEW 🔐)

### Uniform Mobile Number Validation

**All mobile number fields use consistent validation:**

**Format:** XXXXX XXXXX (10 digits with space)
**Rules:**
- Must start with 6, 7, 8, or 9
- Exactly 10 digits
- Auto-formatted as you type

**Fields Validated:**
- Guest Contact (Booking)
- Guest Contact (Check-in)
- Family Member Mobile
- UPI Phone (Booking)
- UPI Phone (Check-out)
- Guest History Search

**Visual Feedback:**
- ✅ Valid number: Normal border
- ❌ Invalid number: Red border + error message
- Message: "Enter a valid 10-digit Indian mobile number"

---

### Auto-Uppercase for IDs

**All ID fields automatically convert to UPPERCASE as you type:**

**Fields Affected:**
- Army/Service Number
- Defence ID
- Dependent ID Serial Number

**Benefits:**
- Consistent data format
- Easier searching
- Prevents duplicate entries due to case differences

**Example:**
- You type: `abc123def`
- System shows: `ABC123DEF`
- Real-time conversion - no need to retype

---

### IFSC Code Validation

**Format:** ABCD0123456 (11 characters)

**Rules:**
- First 4 characters: Letters (bank code)
- 5th character: Must be `0`
- Last 6 characters: Alphanumeric (branch code)
- Auto-converts to uppercase

**Visual Feedback:**
- ❌ Invalid format: Red border
- Error message: "Invalid IFSC format (e.g., SBIN0001234)"

**Fields Validated:**
- Bank IFSC (Booking)
- Bank IFSC (Check-in)
- Bank IFSC (Check-out)

---

### Backend Safety Checks

**Even if frontend validation is bypassed, backend ensures:**
- All IDs stored in uppercase
- Mobile numbers match 10-digit format
- IFSC codes follow standard format
- Invalid data rejected with clear error messages

---

## 16. Troubleshooting

### Common Issues

**Issue:** Cannot create booking with today's date
**Solution:** Check if Migration Mode is disabled (normal operation)

**Issue:** Room shows as occupied but should be available
**Solution:** Check for bookings that haven't been checked out. Complete checkout process.

**Issue:** Dependent Card checkbox not showing
**Solution:** Make sure you've added the family member to the room first

**Issue:** Room modification not showing available rooms
**Solution:** Check booking dates - rooms may be occupied for those dates

**Issue:** Bill total seems incorrect
**Solution:** Check if any rooms have Def Civ charges applied due to missing dependent cards

**Issue:** Cannot delete last room category
**Solution:** System requires at least 1 category. Add a new one first, then delete.

**Issue:** Formation signs not showing
**Solution:** Click "Reset to Official Signs" button in Settings → Formation Signs

### Getting Help

**Contact Information:**
- System Administrator
- IT Support Team
- Rest House Manager

**Error Reporting:**
When reporting errors, provide:
- What you were trying to do
- Error message (if any)
- Screenshot of the screen
- Booking number (if applicable)

---

## 17. Latest Features Summary (v2.0) ✨

### 🎯 Quick Reference: What's New

**Faster Operations:**
1. **Booking Selection Modals**
   - Check-in/check-out from Dashboard/Command Center
   - Context-aware - only shows eligible bookings
   - No more wrong guest selection

2. **Enhanced Payment Tracking**
   - Comprehensive payment details at check-out
   - Auto-population from booking data
   - Transaction IDs, card details, bank references

3. **Improved Navigation**
   - Month/year dropdown in Room Planner
   - Previous/Next month buttons
   - Browse any month/year quickly

**Better Data Quality:**
4. **Uniform Validation**
   - All mobile numbers validated consistently
   - Auto-uppercase for Service/Defence/Dependent IDs
   - IFSC code format validation

5. **Scrollable Check-Out Form**
   - No more cut-off fields
   - Smooth scrolling for all content

**Production-Ready Architecture:**
- Zero code duplication (single source of truth)
- Context-aware workflows
- Backend safety validations
- Real-time error feedback

---

## Quick Reference Card

### Booking Status Flow
```
CONFIRMED → CHECKED_IN → CHECKED_OUT
         ↓
    CANCELLED
```

### Pricing Logic
```
All guests have valid IDs → Standard Rate (Cat I/II)
Any guest lacks valid ID → Def Civ Rate (₹600)
```

### Room Categories
```
Name + Prefix + Rate + Def Civ Rate + Capacity + Count
Example: Cat I + C1 + ₹500 + ₹600 + 2 persons + 6 rooms
```

### Payment Modes
```
Cash → Receipt Number
UPI → Transaction ID
Bank Transfer → Transfer Reference
Card → Transaction Reference
```

### Navigation Shortcuts
```
Dashboard → Occupancy overview
Bookings → All reservations
Check In → Click "Check In" button on booking
Check Out → Click "Check Out" button on checked-in booking
Settings → Room Categories = Main configuration
```

---

## Appendix: Keyboard Shortcuts

- `Tab` - Move to next field
- `Shift + Tab` - Move to previous field
- `Enter` - Confirm in most dialogs
- `Esc` - Close dialogs/modals

---

## Version History

**v2.0 (April 2026)**
- ✨ **NEW:** Booking selection modals for context-aware check-in/check-out
- ✨ **NEW:** Enhanced payment details at check-out with auto-population
- ✨ **NEW:** Month/year navigation in Room Planner (dropdown + prev/next buttons)
- ✨ **NEW:** Gradient visualization for check-in/check-out dates (same-day availability indicator)
- ✨ **NEW:** Uniform validation rules (mobile, IFSC, IDs)
- ✨ **NEW:** Auto-uppercase for Service/Defence/Dependent/Identity Card IDs
- ✨ **NEW:** Scrollable check-out form
- ✨ **NEW:** Total members field with individual age capture in booking form
- ✨ **NEW:** Expanded family relations (Father, Mother, Brother, Sister added)
- ✨ **NEW:** Hours-based cancellation policy (96h/48h thresholds instead of days)
- ✨ **FIXED:** Room ID mismatch issue - planner now shows all bookings
- Added room-wise pricing with dependent card validation
- Inline family member addition per room
- Bank/UPI details capture during booking
- Room modification during check-in
- Dynamic room categories with capacity
- Migration mode for historical data
- Formation signs with official insignia
- Room rates summary (read-only)

**v1.0 (December 2024)**
- Initial release
- Basic booking and check-in/out
- Room management
- Reports and feedback

---

**End of Handbook**

For additional support or feature requests, please contact your system administrator.
