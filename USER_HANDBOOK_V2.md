# 📖 E-ARMS User Handbook v2.0
## AraamgahMgt - Complete User Guide with Latest Features

**Version:** 2.0  
**Last Updated:** April 2026  
**For:** Rest House Managers, Duty Staff, and Administrators

---

## 🎯 What's New in Version 2.0

### ✨ Major Feature Updates:

**📊 Advanced Reporting System (NEW)**
- **Tab-based interface** with 4 comprehensive reports
- **Room Occupancy Report** with expandable booking details per room
- **Room Allotment Register** with party composition (Self/Wife/Child/Dependents/Non-Dependents)
- **Guest Details Register** showing ALL party members (main guest + companions)
- **Flexible date filters:** Daily, Monthly, Quarterly, Annual, Custom range
- **Professional PDF export** with formation signs for all reports
- **Real-time data** pulled from live database
- **Color-coded metrics** for easy analysis

**💾 Data Protection & Backup (NEW)**
- **Automatic daily backups** at 02:00 AM IST
- Manual backup options (Full & Incremental)
- Flexible restore with MERGE strategy
- 90-day retention with automatic cleanup
- Backup status dashboard and history
- Warning alerts for missed backups

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

## 12. Reports (REDESIGNED 📊)

E-ARMS now features a **comprehensive tab-based reporting system** that mirrors official military registers. All reports include flexible date filtering and professional PDF export with formation signs.

---

### 🎛️ **Report Navigation**

Access via: **Sidebar → Reports**

**Four Report Tabs:**
1. 📈 **Monthly Summary** - Overall occupancy and financial analysis
2. 🏨 **Room Occupancy** - Room-wise utilization with expandable booking details
3. 📋 **Room Allotment** - Comprehensive booking register
4. 👥 **Guest Details** - Complete party member register

---

### 📈 **Tab 1: Monthly Summary Report**

**Purpose:** Monthly command-wise occupancy and financial summary for administrative reporting

#### **Features:**
- **Month/Year Selection:** Dropdown selectors for any month and year
- **Command-wise Breakdown:** Total guests and occupied days by Command/Service
- **License Fee Calculation:** Automatic calculation for JCO (Cat I), OR (Cat II), and Def Civ
- **Financial Summary:**
  - Room rent totals by category
  - License fee totals
  - Extra bed charges
  - Grand total revenue
  - Advance received/adjusted/balance
  - No-show tracking

#### **Key Metrics:**
- Total rooms and days in month
- Total booked room-days
- Average occupancy percentage
- Total guests served
- Complete financial breakdown

#### **PDF Export:**
- Click **"Print PDF"** button (red)
- A4 portrait format
- Formation signs on top corners
- Professional layout for official records

**Use Case:** Monthly reporting to higher authorities, financial reconciliation

---

### 🏨 **Tab 2: Room Occupancy Report (NEW)**

**Purpose:** Detailed room-wise occupancy analysis with individual booking breakdowns

#### **Date Filters:**
- **Daily:** Today's occupancy
- **Monthly:** Select month and year
- **Quarterly:** Q1/Q2/Q3/Q4 of selected year
- **Annual:** Full year view
- **Custom Range:** Specify start and end dates

#### **Summary Cards Display:**
- Total Rooms (e.g., 15)
- Average Occupancy % (e.g., 1.33%)
- Total Bookings (e.g., 11)

#### **Room-wise Occupancy Table:**

**Main Table Columns:**
- **🔽 Expand Icon** - Click to show booking details
- **Room No** - Room number (e.g., C2-10)
- **Category** - Cat I, Cat II, etc.
- **Occupied Days** - Total days occupied in period
- **Available Days** - Days available
- **Occupancy %** - Utilization percentage (color-coded: Green ≥75%, Amber ≥50%, Grey <50%)
- **Revenue (₹)** - Total revenue generated

#### **Expandable Booking Details:**

Click the **dropdown arrow (▶)** next to any room to view:

**Detailed Booking Information:**
- **Booking No** - Unique booking reference
- **Army No** - Service number
- **Rank** - Guest rank
- **Name** - Main guest name
- **Unit** - Military unit
- **Command** - Command HQ
- **From Date** - Check-in date
- **To Date** - Check-out date
- **Days** - Number of nights
- **Members** - Total party size (highlighted in blue)
- **Rate/Day** - Daily rate charged
- **Revenue** - Days × Rate (highlighted in green)
- **Bill No** - Billing reference
- **Advance Paid** - Advance payment amount
- **Final Amount Paid** - Amount paid at checkout

**Visual Design:**
- Room rows: Light blue background, bold text
- Expanded section: Indigo background with nested table
- Arrows change: ▶ (collapsed) to ▼ (expanded)

#### **PDF Export:**
- Click **"Print PDF"** button (red)
- A4 portrait format with formation signs
- **Includes expanded booking details for ALL rooms**
- Each room shows:
  1. Room summary table with header
  2. Booking details table below (indented) with header
  3. Complete financial breakdown per booking

**Use Case:** Room utilization tracking, maintenance planning, revenue analysis per room

---

### 📋 **Tab 3: Room Allotment Report (ENHANCED)**

**Purpose:** Complete booking register matching the official Room Allotment Register format

#### **Date Filters:**
Same as Room Occupancy (Daily, Monthly, Quarterly, Annual, Custom Range)

#### **Comprehensive Table Columns:**

| Column | Description |
|--------|-------------|
| **S.No** | Serial number |
| **Booking No** | Unique booking reference |
| **Army No** | Service number |
| **Rank** | Guest rank |
| **Name** | Main guest name |
| **Unit** | Military unit |
| **Command** | Command HQ |
| **Self** | Count (always 1 - main guest) |
| **Wife** | Wife count (0 or 1) |
| **Child** | Number of children |
| **Check-in** | Arrival date |
| **Check-out** | Departure date |
| **Nights** | Number of nights |
| **Dependents** | Companions WITH dependent ID (green) |
| **Non-Dep** | Companions WITHOUT dependent ID (orange) |
| **Room(s)** | Allotted room numbers |
| **I Card No** | Identity/Aadhaar number |
| **Mobile No** | Contact number |
| **Amount (₹)** | Total booking amount |

#### **Smart Calculations:**
- **Self, Wife, Child:** Counted from booking party composition
- **Dependents:** Family members with valid `dependent_id` and dependent card
- **Non-Dependents:** Family members without valid dependent credentials
- **Color Coding:**
  - Dependents: Green (valid military dependents)
  - Non-Dependents: Orange (civilians or no ID)

#### **PDF Export:**
- Click **"Print PDF"** button (red)
- A4 landscape format (fits all columns)
- Formation signs on top corners
- Compact font for maximum data visibility
- Color-coded Dependents/Non-Dependents columns

**Use Case:** Official booking register, dependent verification, occupancy tracking

---

### 👥 **Tab 4: Guest Details Report (NEW)**

**Purpose:** Complete party member register showing ALL individuals (main guest + companions)

#### **Date Filters:**
Same as other reports (Daily, Monthly, Quarterly, Annual, Custom Range)

#### **Summary Cards Display:**
- **Total Party Members** (e.g., 23) - Main guests + all companions
- **Total Bookings** (e.g., 13)
- **Total Nights** (e.g., 34)
- **Revenue (₹)** (e.g., ₹29,550.00)

#### **Guest Party Details Table:**

**Complete Information for Each Person:**

| Column | Description |
|--------|-------------|
| **Booking No** | Reference number |
| **Room(s)** | Allotted rooms |
| **Rank** | Rank (for main guest only, "—" for family) |
| **Name** | Individual's name |
| **Age** | Age in years |
| **Sex** | M/F |
| **Unit** | Military unit (main guest only) |
| **Relationship** | Self / W/O / Son / Daughter / Other |
| **Address** | Residential address |
| **Aadhaar No** | Aadhaar number (main guest only) |
| **Mobile No** | Contact number |
| **Check-in** | Arrival date |
| **Check-out** | Departure date |
| **Nights** | Stay duration |
| **Amount (₹)** | Total amount (shown for main guest, "—" for family) |

#### **Visual Highlights:**
- **Main Guest Rows (Self):**
  - Light blue background
  - Bold text
  - Blue "Self" relationship badge
- **Wife Rows:**
  - Pink relationship badge
- **Children/Others:**
  - Green relationship badge

#### **Data Structure:**
- Each booking creates **multiple rows**:
  - 1 row for main guest (Relationship: "Self")
  - 1 row for each family member (Relationship: W/O, Son, Daughter, etc.)
- **Example:** Booking with 1 main guest + wife + 2 children = 4 rows total

#### **PDF Export:**
- Click **"Print PDF"** button (red)
- A4 landscape format
- Formation signs on top corners
- Main guest rows highlighted in light blue
- Compact layout for multiple columns

**Use Case:** Guest register maintenance, demographic analysis, security records, visitor tracking

---

### 🎯 **Common Features Across All Reports**

#### **Date Filter Options:**

1. **Daily**
   - Automatically set to today
   - View current day's data

2. **Monthly**
   - Select Month (dropdown: January - December)
   - Select Year (dropdown: 2024 - current + 1 year)
   - Default: Current month and year

3. **Quarterly**
   - Select Quarter: Q1 (Jan-Mar), Q2 (Apr-Jun), Q3 (Jul-Sep), Q4 (Oct-Dec)
   - Select Year
   - Default: Current quarter based on selected month

4. **Annual**
   - Select Year only
   - Shows full year data (Jan 1 - Dec 31)

5. **Custom Range**
   - Start Date: Date picker
   - End Date: Date picker
   - Click **"Apply"** to fetch data
   - Validation: End date must be ≥ Start date

#### **PDF Generation Features:**

**All PDFs Include:**
- ✅ **Formation Signs:** Eastern Command and 101 Area logos on top corners
- ✅ **Professional Layout:** Optimized for A4 printing
- ✅ **Report Header:** Report name and period label
- ✅ **Color Coding:** Key metrics highlighted (blue, green, orange)
- ✅ **Auto-pagination:** Splits across pages if needed
- ✅ **Footer:** Page numbers and timestamps

**PDF File Naming:**
- `ECSAG_monthly_summary_[Period].pdf`
- `ECSAG_room_occupancy_[Period].pdf`
- `ECSAG_room_allotment_[Period].pdf`
- `ECSAG_guest_details_[Period].pdf`

**Download Location:** Browser's default download folder

---

### 📊 **Report Usage Guide**

#### **Scenario 1: Monthly Administrative Reporting**
1. Go to **Monthly Summary** tab
2. Select month and year
3. Review command-wise breakdown and financials
4. Click **"Print PDF"**
5. Submit PDF to higher authorities

#### **Scenario 2: Room Maintenance Planning**
1. Go to **Room Occupancy** tab
2. Select **"Quarterly"** filter
3. Review occupancy percentages
4. Identify underutilized rooms
5. Click room **dropdown arrows** to see booking patterns
6. Export PDF for maintenance scheduling

#### **Scenario 3: Dependent Verification**
1. Go to **Room Allotment** tab
2. Select desired period
3. Check **Dependents** and **Non-Dep** columns
4. Green numbers = Valid dependent IDs
5. Orange numbers = Need verification
6. Export PDF for admin review

#### **Scenario 4: Guest Register Audit**
1. Go to **Guest Details** tab
2. Select **"Annual"** filter
3. Review all party members for the year
4. Check relationship badges (Self, W/O, Son, Daughter)
5. Verify age, sex, and contact details
6. Export complete register as PDF

---

### 🔧 **Tips & Best Practices**

**Filter Selection:**
- Use **Monthly** for routine monthly reports
- Use **Quarterly** for trend analysis
- Use **Annual** for year-end summaries
- Use **Custom Range** for specific audit periods

**PDF Export:**
- Always review data before exporting
- PDFs are formatted for official records
- Formation signs ensure authenticity
- Keep PDF archives for audit trail

**Data Accuracy:**
- Reports pull real-time data from database
- Ensure bookings have complete information (Army No, Aadhaar, Mobile)
- Validate dependent IDs during check-in for accurate Dependents count
- Update ages and relationships for accurate Guest Details

**Performance:**
- Large date ranges may take longer to load
- Use specific filters for faster results
- Custom range limited to reasonable periods (suggest < 1 year)

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
3. Rank appears in list below as a chip/badge
4. **Green toast notification appears**: "Rank added. Click 'Save Settings' below to persist!"
5. Scroll to bottom and click **"Save Settings"** button to persist the change

**Remove Rank:**
1. Click × button on rank chip/badge
2. **Toast notification appears**: "Rank removed. Click 'Save Settings' to persist!"
3. Scroll to bottom and click **"Save Settings"** button to persist the change

**Reset to Defaults:**
- Click "Reset to Default Ranks"
- Restores standard military ranks
- Confirmation required before reset
- **Must click "Save Settings"** to persist

**Default Ranks:**
Sep/Dfr/Swr, Nk, Hav, Sgt, PO, Nb Sub, JWO, CPO, Sub, WO, CA, SM, MCPO, Hony Lt or Eqvt, Hony Capt or Eqvt, Def Civ

**How Dynamic Update Works:**
1. Add/remove ranks in Settings page (chips appear/disappear immediately)
2. **Scroll to bottom** and click "Save Settings" button (sticky button at bottom)
3. Wait for "Settings saved successfully!" confirmation
4. Navigate to Bookings → New Booking
5. New ranks appear in "Rank" dropdown
6. Removed ranks disappear from dropdown

**⚠️ CRITICAL REMINDER:**
- Ranks are added to **temporary state** when you click "Add"
- They will **disappear** if you leave the page without saving
- **Always click "Save Settings"** button at the bottom after making changes
- Look for the amber warning box: "Remember to click 'Save Settings' button..."
- Toast notifications remind you to save

**Visual Indicators:**
- 🟢 **Green toast**: Shows when rank is added/removed (with save reminder)
- 🟡 **Amber warning box**: Persistent reminder to save changes
- 💾 **Sticky Save Button**: Always visible at bottom with reminder text

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
- ✨ **NEW:** Advanced tab-based reporting system with 4 comprehensive reports
- ✨ **NEW:** Room Occupancy Report with expandable booking details per room
- ✨ **NEW:** Room Allotment Register with party composition tracking (Self/Wife/Child/Dependents/Non-Dependents)
- ✨ **NEW:** Guest Details Register showing ALL party members (main guest + all companions)
- ✨ **NEW:** Flexible date filters (Daily, Monthly, Quarterly, Annual, Custom range) across all reports
- ✨ **NEW:** Professional PDF export with formation signs for all 4 reports
- ✨ **NEW:** Real-time financial breakdown in Room Occupancy (Rate/Day × Days, Advance, Final Payment)
- ✨ **NEW:** Color-coded relationship badges in Guest Details (Self=Blue, Wife=Pink, Children=Green)
- ✨ **NEW:** Smart dependent tracking (Dependents with ID in green, Non-Dependents in orange)
- ✨ **NEW:** Complete party member register with Age, Sex, Address, Aadhaar, Mobile columns
- ✨ **NEW:** Automatic daily backups at 02:00 AM IST with incremental strategy
- ✨ **NEW:** Manual backup options (Full & Incremental) with restore functionality
- ✨ **NEW:** 90-day backup retention with automatic cleanup
- ✨ **NEW:** Backup dashboard with status cards and history
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

## 16. Backup & Restore System (NEW 💾)

### Purpose
Protect your booking data with automated backups and flexible restore options. The system ensures data safety with minimal storage overhead using incremental backups.

---

### 📊 **Backup Dashboard Overview**

Access via: **Sidebar → Backup & Restore**

The dashboard provides:

#### **A. Last Backup Status Card**
- **Type**: FULL or INCREMENTAL
- **Timestamp**: When backup was taken (IST)
- **Records**: Total records backed up
- **Size**: Backup file size in MB
- **Duration**: Time taken to complete

#### **B. Total Backups Card**
- Total number of successful backups
- First backup date
- Complete backup history

#### **C. Next Scheduled Card**
- Next scheduled backup time (IST)
- Scheduler status (Active/Inactive)

---

### 🔄 **Automatic Backup (Scheduled)**

**Default Schedule:** Daily at **02:00 AM IST**

#### **How It Works:**
1. System automatically runs incremental backup every day at 02:00 AM
2. If no prior backup exists, performs full backup
3. Only backs up **new or modified records** since last backup
4. Stores backup in `/app/backups/` directory
5. Saves metadata to database for tracking

#### **What Gets Backed Up:**
- ✅ Bookings (all statuses)
- ✅ Rooms configuration
- ✅ Settings
- ✅ Staff records
- ✅ Refunds
- ✅ App settings

#### **Backup Types:**

**FULL Backup:**
- Backs up **entire dataset**
- Creates baseline backup
- Larger file size
- Use for first backup or after major changes

**INCREMENTAL Backup:**
- Backs up **only new/modified data** since last backup
- Smaller file size (90% less storage)
- Faster backup time
- Default for automatic scheduled backups

#### **Retention Policy:**
- Backups kept for **90 days (3 months)**
- Automatic cleanup runs **every Sunday at 03:00 AM IST**
- Old backups deleted automatically
- No manual cleanup needed

---

### 🖱️ **Manual Backup Options**

Navigate to **Backup & Restore** page → **Manual Backup** section

#### **Trigger Full Backup:**
1. Click **"Full Backup"** button (blue)
2. Wait for backup to complete (progress indicator shown)
3. Success toast notification appears
4. Backup appears in history table

**When to Use:**
- ✅ Before major system changes
- ✅ Before restoring data
- ✅ First backup of the system
- ✅ After bulk data import

#### **Trigger Incremental Backup:**
1. Click **"Incremental Backup"** button (purple)
2. System backs up only new data since last backup
3. Success notification shown
4. Faster than full backup

**When to Use:**
- ✅ Quick daily backups
- ✅ After adding several bookings
- ✅ Routine data protection
- ✅ When automatic backup was missed

---

### 📥 **Restore Functionality**

Navigate to **Backup & Restore** page → **Restore Data** section

#### **Restore Strategy: MERGE**

The system uses **MERGE** strategy for all restores:
- ✅ **Keeps newer existing records** (never overwrites with older data)
- ✅ **Adds missing records** from backup
- ✅ **Skips older records** if newer version exists
- ✅ **Preserves data integrity**

**Example:**
- Backup has booking updated at 10:00 AM
- Current database has same booking updated at 11:00 AM
- **Result:** 11:00 AM version kept (newer), backup version skipped

#### **Three Restore Options:**

**1. Last Backup Restore** 🕐
- Restores most recent successful backup
- Quickest restore option
- Use for recent data recovery

**Steps:**
1. Click **"Last Backup"** button (green)
2. Confirmation dialog appears
3. Review backup details
4. Click **"Restore"**
5. Wait for completion
6. Success notification shown

**2. Select Backup Restore** 📋
- Choose specific backup from history
- Restore particular point in time
- View backup details before restoring

**Steps:**
1. Click **"Select Backup"** button (blue)
2. Dropdown shows backup history
3. Select desired backup by date/time
4. Review backup type and record count
5. Click **"Restore"**
6. Wait for completion

**3. Date Range Restore** 📅
- Restore all backups between two dates
- Useful for recovering specific time period
- Combines multiple backups

**Steps:**
1. Click **"Date Range"** button (purple)
2. Select **Start Date** (date picker)
3. Select **End Date** (date picker)
4. Click **"Restore"**
5. System restores all backups in range chronologically
6. Completion notification shown

#### **⚠️ Important Restore Notes:**
- Restore does **not delete** existing data
- Only **adds or updates** based on MERGE logic
- Safe to run multiple times
- No data loss risk
- Can take several minutes for large datasets

---

### ⏰ **Schedule Configuration**

Navigate to **Backup & Restore** page → **Backup Schedule** section

#### **Modify Backup Time:**
1. **Hour (IST)**: Enter hour (0-23)
   - Example: 2 for 02:00 AM, 14 for 02:00 PM
2. **Minute**: Enter minute (0-59)
   - Example: 30 for :30 minutes
3. Click **"Update Schedule"** button
4. Success confirmation shown
5. New schedule saved to database

#### **Current Schedule Display:**
- Shows active schedule: "Daily at HH:MM IST"
- Next scheduled run time visible in dashboard

#### **Best Practices:**
- ✅ Schedule during **low-usage hours** (night)
- ✅ Avoid peak booking hours
- ✅ Default 02:00 AM IST recommended
- ✅ Ensure system is running at scheduled time

---

### ⚠️ **Failure Handling & Warnings**

#### **Missed Backup Detection:**

If scheduled backup fails or is skipped, system shows:

**1. Warning Modal on Startup** 🚨
- Appears immediately when you open the app
- Shows amber warning icon
- Message: "Scheduled backup was not completed"
- Details: Hours since last backup

**Modal Options:**
- **"Backup Now"** - Triggers immediate incremental backup
- **"Remind Me Later"** - Dismisses modal (banner remains)

**2. Persistent Warning Banner** ⚠️
- **Amber banner** at top of all pages
- Stays visible until backup completed
- Cannot be permanently dismissed
- Shows message: "⚠️ Backup Required: [details]"

**Banner Actions:**
- **"Backup Now"** button - Triggers backup
- **"✕"** button - Temporarily hides banner (reopens on refresh)

#### **Why Backup Is Important:**
- ✅ Protects against data loss
- ✅ Enables recovery from errors
- ✅ Maintains 90-day data retention
- ✅ Ensures business continuity
- ✅ Required for system reliability

---

### 📜 **Backup History**

Located at bottom of **Backup & Restore** page

#### **History Table Columns:**
- **Timestamp**: When backup was taken (DD MMM YYYY, HH:MM)
- **Type**: FULL or INCREMENTAL badge
- **Records**: Total records backed up
- **Size**: File size in MB
- **Duration**: Time taken (seconds)
- **Status**: Success (green) or Failed (red)

#### **Using History:**
- View all past backups
- Identify successful backups for restore
- Monitor backup sizes and durations
- Track backup frequency

---

### 🔧 **Troubleshooting**

#### **Problem: Backup Takes Too Long**
**Solution:**
- Use **Incremental Backup** instead of Full
- Incremental is 90% faster
- Scheduled backups use incremental by default

#### **Problem: Warning Banner Won't Go Away**
**Solution:**
- Click **"Backup Now"** button
- Wait for backup to complete
- Banner disappears after successful backup
- Don't just dismiss - actually run backup

#### **Problem: Restore Didn't Work**
**Check:**
- ✅ Restore completed successfully? (check notification)
- ✅ Using MERGE strategy (doesn't overwrite newer data)
- ✅ Check specific records manually
- ✅ View restore history for details

#### **Problem: Backup Files Taking Too Much Space**
**Solution:**
- Retention is 90 days (automatic cleanup)
- Old backups deleted every Sunday
- Check `/app/backups/` directory
- Cleanup runs at 03:00 AM IST Sundays

#### **Problem: Scheduled Backup Not Running**
**Check:**
- ✅ System must be running at 02:00 AM IST
- ✅ Check scheduler status in dashboard
- ✅ Use manual backup if scheduled missed
- ✅ Verify schedule time is correct

---

### 💡 **Best Practices**

#### **DO:**
- ✅ **Run manual full backup** before major changes
- ✅ **Verify last backup** before modifying data
- ✅ **Test restore** periodically (use date range for old data)
- ✅ **Keep system running** during scheduled time
- ✅ **Monitor backup status** regularly
- ✅ **Respond to warnings** immediately

#### **DON'T:**
- ❌ Ignore backup warning banners
- ❌ Delete files from `/app/backups/` manually
- ❌ Rely only on automatic backups
- ❌ Skip testing restore functionality
- ❌ Change schedule to overlap with peak hours

---

### 📊 **Backup Workflow Example**

**Daily Operation:**
```
02:00 AM IST → Automatic incremental backup runs
02:00:30 AM  → Backup completes (98 records, 0.5 MB)
              → Metadata saved to database
              → Next backup scheduled for tomorrow 02:00 AM
```

**Manual Full Backup:**
```
User clicks "Full Backup"
→ System backs up all 450 records
→ Creates backup_full_20260409_143022.json (2.3 MB)
→ Success toast: "Full backup completed successfully"
→ Backup appears in history table
```

**Restore Last Backup:**
```
User clicks "Last Backup" restore
→ Loads backup_incr_20260409_020015.json
→ Applies MERGE strategy:
  - 95 records added (missing from current DB)
  - 3 records updated (backup newer)
  - 50 records skipped (current DB newer)
→ Success: "Restore completed successfully"
```

---

### 🎯 **Key Takeaways**

1. **Automatic Protection**: Daily backups at 02:00 AM IST
2. **Incremental by Default**: 90% less storage, faster backups
3. **Flexible Restore**: Last backup, specific backup, or date range
4. **MERGE Strategy**: Never lose newer data
5. **90-Day Retention**: Automatic cleanup, no maintenance needed
6. **Warning System**: Modal + banner ensure you never miss backups
7. **Manual Override**: Full control when needed

---

### 📞 **Need Help?**

- Check **Backup History** for past backup status
- Review **Backup Status Dashboard** for current state
- Test **Restore** with old date range (non-destructive)
- Trigger **Manual Backup** if automatic missed
- Monitor **Warning Banners** for alerts

---

**End of Handbook**

For additional support or feature requests, please contact your system administrator.
