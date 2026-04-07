# 📖 E-ARMS User Handbook v2.0
## AraamgahMgt - Complete User Guide with Latest Features

**Version:** 2.0  
**Last Updated:** April 2026  
**For:** Rest House Managers, Duty Staff, and Administrators

---

## 🎯 What's New in Version 2.0

### ✨ Major Feature Updates:

**🏠 Enhanced Check-In Experience**
- Room-wise guest assignment with inline family member addition
- Per-room pricing based on dependent card validation
- Automatic Def Civ rate application when required

**💰 Improved Financial Management**
- Bank/UPI details captured during booking for faster refunds
- Simplified payment fields
- Read-only room rates summary in Settings

**🔧 Operational Flexibility**
- Modify room assignments during check-in
- Conflict detection prevents double-booking
- Migration mode for historical data import

**⚙️ Dynamic Configuration**
- Custom room categories with capacity management
- "Run Setup" option to reconfigure system
- Formation signs with official military insignia

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

The Command Center is your home screen with quick access to common tasks.

### Quick Actions

**📅 New Booking**
- Opens booking form
- For creating new reservations

**✅ Check In**
- Goes to Bookings page with confirmed bookings
- Quick access to check-in process

**✈️ Check Out**
- Goes to Bookings page with checked-in guests
- Quick access to checkout process

**📊 Dashboard**
- View occupancy statistics
- Today's arrivals and departures
- Monthly analytics

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

---

## 5. Making a Booking (NEW)

### Step 1: Guest Details

**Required Information:**
- Guest Name
- Guest Contact (10-digit mobile)
- Rank (select from dropdown)
- Army Number
- Unit

**Tip:** Contact number is auto-formatted as "+91 XXXXXXXXXX"

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
   - Relation (w/o, s/o, d/o, other)
   - Name
   - Age
   - Sex
   - Mobile
3. **Dependent Card Available?** checkbox:
   - ☑ **Checked** - Family member has valid dependent card
     - Dependent ID Ser No field appears
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

### Payment Collection

**Amount to Collect:**
- Displayed clearly
- Can be paid via Cash/UPI/Card/Bank Transfer

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

### Ranks Management

**Add Rank:**
- Click "Add Rank"
- Enter rank name
- Click checkmark

**Remove Rank:**
- Click trash icon next to rank
- Rank removed from dropdown

**Reset to Defaults:**
- Restores standard military ranks
- Confirmation required

**Default Ranks:**
Gen, Lt Gen, Maj Gen, Brig, Col, Lt Col, Maj, Capt, Lt, Sub, JCO, NCO, Def Civ

---

### Default Advance Amount

**Configuration:**
- Set default advance per room
- E.g., ₹400
- Can be overridden during booking

---

### Cancellation Policy

**Text Field:**
- Enter cancellation policy terms
- Displayed to guests
- Editable rich text

**Example:**
"Cancellations must be made 48 hours before check-in. Full refund if cancelled 48+ hours before. 50% refund if cancelled within 48 hours."

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

## 15. Troubleshooting

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
