# 📖 E-ARMS User Handbook
## ECSAG Automated Room Management System - Complete User Guide

**Version:** 1.0  
**Last Updated:** April 2026  
**For:** Rest House Managers, Duty Staff, and Administrators

---

## 📑 Table of Contents

1. [Introduction](#1-introduction)
2. [Getting Started](#2-getting-started)
3. [Command Center (Home Screen)](#3-command-center-home-screen)
4. [Dashboard](#4-dashboard)
5. [Bookings Management](#5-bookings-management)
6. [Check-In Process](#6-check-in-process)
7. [Check-Out Process](#7-check-out-process)
8. [Cancellation & Refunds](#8-cancellation--refunds)
9. [Rooms Management](#9-rooms-management)
10. [Staff Management](#10-staff-management)
11. [Feedback System](#11-feedback-system)
12. [Reports](#12-reports)
13. [Settings](#13-settings)
14. [Troubleshooting](#14-troubleshooting)

---

## 1. Introduction

### What is E-ARMS?

E-ARMS (ECSAG Automated Room Management System) is a comprehensive software application designed to manage all aspects of a military rest house, including:

- Guest bookings and reservations
- Check-in and check-out procedures
- Room availability tracking
- Payment and refund management
- Guest feedback collection
- Staff management
- Analytics and reporting

### Who Should Use This Handbook?

- **New Staff Members** - Learning to operate the system
- **Duty Officers** - Managing daily operations
- **Administrators** - Configuring and maintaining the system
- **Management** - Understanding system capabilities

---

## 2. Getting Started

### Accessing E-ARMS

**URL:** The application URL will be provided by your administrator  
**Example:** `https://earms-frontend.vercel.app`

**No Login Required:** E-ARMS is designed for internal use. Simply open the URL in your browser.

### Recommended Browser

- **Best:** Google Chrome (latest version)
- **Also works:** Microsoft Edge, Firefox, Safari

### Screen Layout

```
┌─────────────────────────────────────────────────────┐
│  [E-ARMS Logo]        E-ARMS                    [≡] │ ← Top Bar
├──────────────┬──────────────────────────────────────┤
│              │                                      │
│  Dashboard   │                                      │
│  Bookings    │        Main Content Area            │
│  Rooms       │      (Changes based on selection)    │
│  Staff       │                                      │
│  Toiletry    │                                      │
│  Feedback    │                                      │
│  Reports     │                                      │
│  Settings    │                                      │
│              │                                      │
└──────────────┴──────────────────────────────────────┘
   Sidebar Menu          Content Area
```

---

## 3. Command Center (Home Screen)

### What You See

The Command Center is your **starting point** when you open E-ARMS. It features a tactical military-themed interface with 5 main action buttons arranged in a pentagon/star pattern.

```
                    ╔═══════════════╗
                    ║  NEW BOOKING  ║  (Green)
                    ╚═══════════════╝
                           ↑
                           │
         ╔═══════════╗     ●     ╔════════════╗
         ║ CHECK IN  ║   E-ARMS  ║ CHECK OUT  ║
         ╚═══════════╝  Command  ╚════════════╝
              ↖        Center       ↗
                 ╲       ●       ╱
                   ╲           ╱
                ╔═══════╗  ╔══════════╗
                ║CANCEL ║  ║DASHBOARD ║
                ╚═══════╝  ╚══════════╝
             (Red)          (Purple)
```

### Button Functions

| Button | Color | Function | When to Use |
|--------|-------|----------|-------------|
| **NEW BOOKING** | Green | Create a new room reservation | Guest calls to book a room |
| **CHECK IN** | Blue | Register guest arrival | Guest arrives at rest house |
| **CHECK OUT** | Orange | Process guest departure | Guest is leaving |
| **CANCEL** | Red | Cancel a booking | Guest cancels their reservation |
| **DASHBOARD** | Purple | View analytics & overview | Check occupancy, revenue, stats |

### How to Use

1. **Hover over any button** - It will grow larger and glow (visual feedback)
2. **Click the button** - Performs the action
3. **All buttons** take you to the appropriate page/form

---

## 4. Dashboard

### Navigation

Click **"Dashboard"** from:
- Command Center (purple button)
- Sidebar menu (house icon)

### Dashboard Sections

```
┌────────────────────────────────────────────────────┐
│  Guest Feedback Analysis                           │
│  ┌──────────────────────────────────────────────┐  │
│  │  😊 4.25/5    📊 Total: 45   👍 92% Recommend│  │
│  └──────────────────────────────────────────────┘  │
├────────────────────────────────────────────────────┤
│  Occupancy Status                                  │
│  ┌─────────────┬─────────────┬─────────────┐     │
│  │  Overall    │   Cat I     │   Cat II    │     │
│  │   65%       │   75%       │   55%       │     │
│  └─────────────┴─────────────┴─────────────┘     │
├────────────────────────────────────────────────────┤
│  Monthly Calendar Planner                          │
│  [Shows room availability for current month]       │
├────────────────────────────────────────────────────┤
│  Analytics Cards                                   │
│  ┌──────┬──────┬──────┬──────┬──────┐            │
│  │Book  │Guest │Revnu │Occup │Staff │            │
│  │ings  │  s   │  e   │ ancy │      │            │
│  └──────┴──────┴──────┴──────┴──────┘            │
└────────────────────────────────────────────────────┘
```

### Key Metrics Explained

1. **Occupancy Status**
   - **Overall:** Percentage of all rooms occupied
   - **Cat I:** Category I room occupancy
   - **Cat II:** Category II room occupancy
   - **Color coding:**
     - Green (>60%) - Good occupancy
     - Yellow (30-60%) - Moderate
     - Red (<30%) - Low occupancy

2. **Fund Generation**
   - **Total Revenue:** All money collected
   - **Pending Refunds:** Money owed to guests (clickable)
   - Click to see refund details

3. **Monthly Calendar**
   - **Green dates:** Rooms available
   - **Red dates:** Fully booked
   - **Yellow dates:** Partially booked

### What to Check Daily

✅ **Morning:**
- Check today's expected check-ins
- Review occupancy for upcoming days
- Check pending refunds

✅ **Evening:**
- Review today's completions
- Check tomorrow's arrivals

---

## 5. Bookings Management

### Accessing Bookings Page

- Click **"Bookings"** in sidebar (calendar icon)
- Or click **"New Booking"** from Command Center

### Bookings Page Layout

```
┌────────────────────────────────────────────────────┐
│  Bookings                                     [+]   │ ← New Booking Button
├────────────────────────────────────────────────────┤
│  Search: [_________________]  Status: [All ▼]      │
├────────────────────────────────────────────────────┤
│  Booking  │ Guest      │ Dates        │ Status  │ Actions
├───────────┼────────────┼──────────────┼─────────┼────────
│  BK0001   │ Nb Sub R.K │ 05-07 Apr    │ Confirmed│ ✓ ✗
│  BK0002   │ Hav M.S    │ 06-08 Apr    │ Checked-in│ 🧾 ✓ ✗
│  BK0003   │ Sep A.K    │ 04-06 Apr    │ Checked-out│ 📄
└────────────────────────────────────────────────────┘

Legend:
✓ = Check In/Out    ✗ = Cancel    🧾 = Bill    📄 = Receipt
```

### Creating a New Booking

**Step-by-Step:**

1. **Click "+ New Booking" button** (top right) or green button from Command Center

2. **New Booking Form Opens:**

```
┌──────────────────────────────────────┐
│   Create New Booking                 │
├──────────────────────────────────────┤
│  Guest Details:                      │
│  Rank:        [Nb Sub ▼]            │
│  Name:        [________________]     │
│  Army No:     [________________]     │
│  Aadhaar:     [________________]     │
│  Unit:        [________________]     │
│  Phone:       [+91__________]        │
│                                      │
│  Booking Details:                    │
│  Check-in:    [📅 Select Date]      │
│  Check-out:   [📅 Select Date]      │
│  Num Rooms:   [1 ▼]                 │
│                                      │
│  Room Selection:                     │
│  Available Rooms for Selected Dates: │
│  [C1-01] [C1-02] [C1-03] [C2-01]   │
│  (Click to select)                   │
│                                      │
│  Payment Details:                    │
│  Mode:        [Cash ▼]              │
│  Amount:      ₹400 (auto-calculated)│
│                                      │
│  [Cancel]          [Create Booking] │
└──────────────────────────────────────┘
```

3. **Fill Required Fields:**

   **MUST fill:**
   - ✅ Rank (select from dropdown)
   - ✅ Name
   - ✅ Army Number
   - ✅ Aadhaar Number
   - ✅ Unit
   - ✅ Number of Rooms
   - ✅ Check-in Date
   - ✅ Check-out Date
   - ✅ Room Selection (must match number of rooms)
   - ✅ Payment Mode

4. **Select Payment Mode:**

   **Cash:**
   - Enter Receipt Number

   **UPI:**
   - Enter UPI ID (e.g., guest@paytm)
   - Enter UPI Phone Number

   **Bank Transfer:**
   - Enter Bank Name
   - Enter IFSC Code
   - Enter Account Number

   **Card:**
   - Enter Authorization Code

5. **Click "Create Booking"**

   **What happens:**
   - Booking number generated (e.g., BK0001)
   - Status: "Confirmed"
   - Rooms marked as booked
   - Appears in bookings table

### Booking Status Types

| Status | Meaning | Available Actions |
|--------|---------|-------------------|
| **Confirmed** | Booking created, awaiting arrival | Check In, Cancel |
| **Checked-in** | Guest has arrived and checked in | Bill Print, Check Out, Cancel |
| **Checked-out** | Guest has departed | Receipt Print |
| **Cancelled** | Booking cancelled | Refund Processing |

---

## 6. Check-In Process

### When to Use

When a guest **arrives** at the rest house with a confirmed booking.

### Starting Check-In

**Method 1:** From Bookings page
1. Find confirmed booking in table
2. Click green **"Check In"** button
3. ⚠️ Note: Button disabled if check-in date hasn't arrived yet

**Method 2:** From Command Center
1. Click blue **"CHECK IN"** button
2. System auto-selects first confirmed booking

### Check-In Form (7 Sections)

```
┌────────────────────────────────────────────┐
│         Check-In Guest                      │
├────────────────────────────────────────────┤
│ Section 1: Booking Summary (Read-only)     │
│  Booking: BK0001                           │
│  Guest: Nb Sub Rohit Kumar                 │
│  Dates: 05 Apr - 07 Apr (2 nights)        │
│  Rooms: C1-01, C1-02                       │
│  Advance Paid: ₹800                        │
├────────────────────────────────────────────┤
│ Section 2: Select Staff Member             │
│  Staff: [Duty Officer ▼]                  │
├────────────────────────────────────────────┤
│ Section 3: Extra Beds                      │
│  Extra Beds: [0 ▼] (₹75 each/night)       │
├────────────────────────────────────────────┤
│ Section 4: Personal Details                │
│  Phone: [+91 9876543210] (auto-filled)    │
│  Age: [__]  Sex: [Male ▼]                 │
│  Address: [_________________________]      │
│  ID Card: [Aadhaar/PAN/Driving License]   │
│  ID Number: [____________________]         │
├────────────────────────────────────────────┤
│ Section 5: Service Details                 │
│  Status: [Serving ▼]                       │
│  Service Type: [Army ▼]                    │
│  Command HQ: [Eastern Command ▼]          │
├────────────────────────────────────────────┤
│ Section 6: Family Members (Optional)       │
│  [+ Add Family Member]                     │
│  Name | Age | Sex | Relation              │
│  ─────┼─────┼─────┼─────────              │
│                                            │
├────────────────────────────────────────────┤
│ Section 7: Bank/UPI Details (auto-filled) │
│  For future refunds:                       │
│  Bank Name: [SBI] (auto-filled)           │
│  IFSC: [SBIN0001234] (auto-filled)        │
│  Account: [1234567890] (auto-filled)      │
│  UPI ID: [guest@paytm] (auto-filled)      │
├────────────────────────────────────────────┤
│ Bill Summary:                              │
│  Room Charges (2 nights): ₹1000           │
│  Extra Bed Charges:       ₹0              │
│  ─────────────────────────────            │
│  Subtotal:               ₹1000            │
│  Advance Paid:          -₹800             │
│  ═════════════════════════════            │
│  Balance Due:            ₹200             │
├────────────────────────────────────────────┤
│  [Cancel]           [Complete Check-In]   │
└────────────────────────────────────────────┘
```

### Step-by-Step Instructions

**Section 1: Booking Summary**
- ℹ️ Read-only, shows booking details
- Verify guest name and dates are correct

**Section 2: Staff Member**
- ✅ **REQUIRED:** Select duty officer handling check-in
- Purpose: Track who processed check-in

**Section 3: Extra Beds**
- Select 0-5 extra beds
- Cost: ₹75 per bed per night
- Auto-added to bill summary

**Section 4: Personal Details**
- Phone: Auto-filled from booking (editable)
- Age: Enter guest's age
- Sex: Male/Female/Other
- Address: Full postal address
- ID Card: Select type (Aadhaar/PAN/Driving License/etc.)
- ID Number: Enter the ID card number

**Section 5: Service Details**
- Status: Serving or Retired
- Service Type: Army/Navy/Air Force/Defense Civilian
- Command HQ: If Army, select command (Eastern/Western/etc.)

**Section 6: Family Members**
- Click "+ Add Family Member" to add each person
- Enter: Name, Age, Sex, Relation to guest
- Can add multiple family members
- Can remove using ✗ button

**Section 7: Bank/UPI Details**
- Auto-filled from booking data
- Editable if guest wants to use different account
- Used for refunds if booking is cancelled

**Bill Summary**
- Auto-calculates based on:
  - Room charges (rate × nights × rooms)
  - Extra bed charges (₹75 × beds × nights)
  - Minus advance already paid
- Shows balance due at checkout

### Completing Check-In

1. **Fill all required fields** (marked with *)
2. **Click "Complete Check-In"**
3. **What happens:**
   - Booking status → "Checked-in"
   - Check-in date/time recorded
   - Balance amount saved
   - Bill Print button now available
   - Check Out button now available

### Validation Rules

⚠️ **Cannot check in if:**
- Check-in date is in the future
- Staff member not selected
- Required personal details missing

---

## 7. Check-Out Process

### When to Use

When a guest is **leaving** the rest house.

### Starting Check-Out

**Method 1:** From Bookings page
1. Find checked-in booking
2. Click orange **"Check Out"** button

**Method 2:** From Command Center
1. Click orange **"CHECK OUT"** button
2. System auto-selects first checked-in booking

### Check-Out Form

```
┌────────────────────────────────────────────┐
│         Check-Out Guest                     │
├────────────────────────────────────────────┤
│ Booking Summary:                           │
│  Guest: Nb Sub Rohit Kumar                 │
│  Checked In: 05 Apr 2026                   │
│  Checking Out: 07 Apr 2026 (Today)        │
│  Actual Stay: 2 Night(s)                   │
├────────────────────────────────────────────┤
│ Final Payment:                             │
│  Balance Due: ₹200                         │
│                                            │
│  Payment Mode: [Cash ▼]                    │
│  Receipt No: [__________]                  │
│                                            │
│ [Cancel]        [Complete Check-Out]       │
└────────────────────────────────────────────┘
```

### Step-by-Step Instructions

1. **Verify Details:**
   - Check guest name
   - Verify actual stay duration
   - Confirm balance amount

2. **Collect Final Payment:**
   - If balance is ₹0, skip payment
   - If balance due, collect payment

3. **Select Payment Mode:**
   - Same options as booking (Cash/UPI/Bank/Card)
   - Enter required details

4. **Click "Complete Check-Out"**

5. **Feedback Form Opens (MANDATORY):**

```
┌────────────────────────────────────────────┐
│    GUEST FEEDBACK FORM                      │
│    अतिथि प्रतिक्रिया प्रपत्र                │
├────────────────────────────────────────────┤
│ 1. Personal Information                     │
│    Rank & Name: Nb Sub Rohit Kumar         │
│    Unit: 21 EME                            │
├────────────────────────────────────────────┤
│ 2. Visit Details                            │
│    Date: 05 Apr to 07 Apr 2026            │
│    Duration: 2 Night(s)                    │
├────────────────────────────────────────────┤
│ 3. Satisfaction Rating (1-5)               │
│    Rate each category:                      │
│                                            │
│    Cleanliness:          [1][2][3][4][5]  │
│    Room Comfort:         [1][2][3][4][5]  │
│    Basic Amenities:      [1][2][3][4][5]  │
│    Check-In Procedure:   [1][2][3][4][5]  │
│    Check-Out Procedure:  [1][2][3][4][5]  │
│    Overall Stay:         [1][2][3][4][5]  │
│    Staff Behaviour:      [1][2][3][4][5]  │
├────────────────────────────────────────────┤
│ 4. Specific Feedback                        │
│    What did you enjoy most?                │
│    [_________________________________]      │
│                                            │
│    Any issues or problems?                 │
│    [_________________________________]      │
│                                            │
│    How can we improve?                     │
│    [_________________________________]      │
├────────────────────────────────────────────┤
│ 5. Additional Comments (Optional)           │
│    [_________________________________]      │
├────────────────────────────────────────────┤
│ 6. Would you recommend us?                 │
│    [✓] Yes / Ha      [ ] No / Nahi        │
├────────────────────────────────────────────┤
│  [Fill Later]  [Submit & Complete Checkout]│
└────────────────────────────────────────────┘
```

6. **Fill Feedback Form:**
   - ✅ MUST rate all 7 categories
   - ✅ MUST select recommendation (Yes/No)
   - Optional: Text responses

7. **Click "Submit Feedback & Complete Checkout"**

8. **PDF Receipt Auto-Downloads:**
   - Contains all booking details
   - Payment summary
   - Guest information
   - A5 landscape format

### What Happens After Check-Out

- Booking status → "Checked-out"
- Rooms become available
- Feedback saved to database
- Receipt generated
- Analytics updated

---

## 8. Cancellation & Refunds

### When to Cancel

- Guest calls to cancel before arrival
- Guest cannot come due to emergency
- Guest wants to cancel during stay

### Cancellation Process

**Step 1: Start Cancellation**

From Bookings page:
1. Find booking (confirmed or checked-in)
2. Click red **✗ Cancel** button

**Step 2: Refund Calculation Dialog**

```
┌────────────────────────────────────────────┐
│         Cancel Booking                      │
├────────────────────────────────────────────┤
│ Booking: BK0001                            │
│ Guest: Nb Sub Rohit Kumar                 │
│ Check-in Date: 10 Apr 2026                │
├────────────────────────────────────────────┤
│ Cancellation Analysis:                     │
│  Days until check-in: 5 days              │
│  Advance Paid: ₹800                        │
│  Cancellation Charge (25%): ₹200          │
│  ══════════════════════════════            │
│  Refund Amount: ₹600                       │
├────────────────────────────────────────────┤
│  [Close]            [Confirm Cancellation] │
└────────────────────────────────────────────┘
```

**Step 3: Confirm Cancellation**
- Review refund amount
- Click "Confirm Cancellation"

### Refund Tiers (Auto-Calculated)

| Days Before Check-In | Cancellation Charge | Refund |
|---------------------|---------------------|--------|
| **15+ days** | 10% | 90% |
| **7-14 days** | 25% | 75% |
| **3-6 days** | 50% | 50% |
| **0-2 days** | 75% | 25% |
| **After check-in** | 100% | 0% |

### Processing Refunds

**Step 1: View Pending Refunds**

From Dashboard:
- Click on "Pending Refund Amount: ₹X" button

OR from Bookings page:
- Click "Pending Refunds" button (top right)

**Step 2: Refunds Dialog**

```
┌────────────────────────────────────────────┐
│         Pending Refunds                     │
├────────────────────────────────────────────┤
│ BK0001 | Nb Sub R.K | ₹600 | [Mark Paid]  │
│ BK0003 | Hav M.S    | ₹400 | [Mark Paid]  │
│                                            │
│ Total Pending: ₹1000                       │
└────────────────────────────────────────────┘
```

**Step 3: Mark as Paid**
1. Click **"Mark as Paid"** button
2. Enter transaction reference number
3. Click "Confirm"
4. Refund status → "Completed"
5. Removed from pending list

---

## 9. Rooms Management

### Accessing Rooms Page

Click **"Rooms"** in sidebar (bed icon)

### Rooms Page Layout

```
┌────────────────────────────────────────────┐
│  Rooms                            [+ Add]   │
├────────────────────────────────────────────┤
│  Category I Rooms (₹500/night)             │
│  ┌────────┬────────┬────────┬────────┐    │
│  │ C1-01  │ C1-02  │ C1-03  │ C1-04  │    │
│  │ Vacant │Occupied│ Vacant │ Vacant │    │
│  │   ✓    │   ✗    │   ✓    │   ✓    │    │
│  └────────┴────────┴────────┴────────┘    │
├────────────────────────────────────────────┤
│  Category II Rooms (₹400/night)            │
│  ┌────────┬────────┬────────┬────────┐    │
│  │ C2-01  │ C2-02  │ C2-03  │ C2-04  │    │
│  │ Vacant │ Vacant │Occupied│ Vacant │    │
│  │   ✓    │   ✓    │   ✗    │   ✓    │    │
│  └────────┴────────┴────────┴────────┘    │
└────────────────────────────────────────────┘
```

### Adding a New Room

1. Click **"+ Add Room"** button
2. Fill details:
   - Room Number (e.g., C1-05)
   - Category (Cat I / Cat II / Def Civ)
3. Click "Add Room"

### Room Status Colors

- **Green background:** Room is vacant (available)
- **Red background:** Room is occupied
- **✓ icon:** Available for booking
- **✗ icon:** Currently occupied

### Deactivating a Room

1. Click on room card
2. Click "Deactivate" button
3. Confirm
4. Room will not show in available rooms list

---

## 10. Staff Management

### Accessing Staff Page

Click **"Staff"** in sidebar (users icon)

### Staff Page Layout

```
┌────────────────────────────────────────────┐
│  Staff                           [+ Add]    │
├────────────────────────────────────────────┤
│  Active Staff Members                      │
│  ┌────────────────────────────────────────┐│
│  │ Name: Duty Officer                     ││
│  │ Type: Army                             ││
│  │ Status: ● Active                       ││
│  │ [Deactivate]                           ││
│  └────────────────────────────────────────┘│
│  ┌────────────────────────────────────────┐│
│  │ Name: Reception Clerk                  ││
│  │ Type: Defense Civilian                 ││
│  │ Status: ● Active                       ││
│  │ [Deactivate]                           ││
│  └────────────────────────────────────────┘│
└────────────────────────────────────────────┘
```

### Adding a Staff Member

1. Click **"+ Add Staff"** button
2. Fill details:
   - Name
   - Type (Army/Navy/Air Force/Defense Civilian)
3. Click "Add Staff"
4. Staff appears in dropdown during check-in

### Deactivating Staff

1. Click **"Deactivate"** on staff card
2. Confirm
3. Staff removed from active list
4. Will not show in check-in dropdown

---

## 11. Feedback System

### Accessing Feedback Page

Click **"Feedback"** in sidebar (star icon)

### Feedback Page Sections

```
┌────────────────────────────────────────────┐
│  Guest Feedback Analysis                   │
├────────────────────────────────────────────┤
│  Overall Score                             │
│  ┌──────────────────────────────────────┐ │
│  │  😊 4.25 / 5                         │ │
│  │  Excellent / Uchcha                  │ │
│  │                                      │ │
│  │  45 Total | 92% Recommend | 😊       │ │
│  └──────────────────────────────────────┘ │
├────────────────────────────────────────────┤
│  Category-wise Scores                      │
│  Cleanliness:        ███████░ 4.5         │
│  Room Comfort:       ██████░░ 4.2         │
│  Basic Amenities:    ███████░ 4.4         │
│  Check-In:           ████████ 4.8         │
│  Check-Out:          ███████░ 4.6         │
│  Overall Stay:       ██████░░ 4.0         │
│  Staff Behaviour:    ████████ 4.9         │
├────────────────────────────────────────────┤
│  Recent Feedbacks                          │
│  ┌────────────────────────────────────┐   │
│  │ Nb Sub Rohit Kumar    4.57/5  [🖨] │   │
│  │ Serving (Army)                     │   │
│  │ 05 Apr - 07 Apr 2026              │   │
│  │ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│  │ Ratings: 5,4,5,5,4,5,5            │   │
│  │ Liked: Excellent cleanliness...    │   │
│  │ Suggestions: More amenities...     │   │
│  └────────────────────────────────────┘   │
└────────────────────────────────────────────┘
```

### Understanding Scores

**Overall Score:**
- **4.0 - 5.0:** 😊 Excellent (Green)
- **2.5 - 3.9:** 😐 Satisfactory (Yellow)
- **0.0 - 2.4:** 😢 Needs Improvement (Red)

**Recommendation Rate:**
- Percentage of guests who would recommend

### Printing Past Feedback

1. Find feedback in "Recent Feedbacks" section
2. Click **🖨 Print** button (top right of feedback card)
3. PDF generates and downloads automatically
4. Filename: `Feedback_GuestName_Date.pdf`

**PDF Contains:**
- Guest details
- Visit dates and duration
- All 7 category ratings
- Average score
- Text feedback responses
- Recommendation status

---

## 12. Reports

### Accessing Reports Page

Click **"Reports"** in sidebar (chart icon)

### Monthly Report Generation

```
┌────────────────────────────────────────────┐
│  Monthly Reports                           │
├────────────────────────────────────────────┤
│  Select Month & Year:                      │
│  Month: [April ▼]  Year: [2026 ▼]        │
│                                            │
│  [Generate PDF Report]                     │
├────────────────────────────────────────────┤
│  Report Preview:                           │
│  • Total Bookings: 45                      │
│  • Total Revenue: ₹67,500                  │
│  • Occupancy Rate: 65%                     │
│  • License Fees: ₹4,500                    │
└────────────────────────────────────────────┘
```

### Generating a Report

**Step 1:** Select Month and Year
- Click month dropdown
- Click year dropdown

**Step 2:** Click "Generate PDF Report"

**Step 3:** PDF Downloads

**Report Contents:**

1. **Command-wise Breakdown**
   - Eastern Command: X bookings, ₹Y revenue
   - Western Command: X bookings, ₹Y revenue
   - etc.

2. **License Fee Calculation**
   - Cat I rooms: nights × rate
   - Cat II rooms: nights × rate
   - Def Civ rooms: nights × rate
   - Total license fees

3. **Financial Summary**
   - Total room revenue
   - Total license fees
   - Grand total
   - Pending refunds

4. **Occupancy Statistics**
   - Total room nights sold
   - Average occupancy %
   - Peak periods

---

## 13. Settings

### Accessing Settings Page

Click **"Settings"** in sidebar (gear icon)

### Settings Sections

```
┌────────────────────────────────────────────┐
│  Settings                                  │
├────────────────────────────────────────────┤
│  Room Rates                                │
│  Category I:  [₹500]                       │
│  Category II: [₹400]                       │
│  Def Civilian:[₹600]                       │
│  [Update Rates]                            │
├────────────────────────────────────────────┤
│  Default Advance                           │
│  Amount per room: [₹400]                   │
│  [Update]                                  │
├────────────────────────────────────────────┤
│  License Fees                              │
│  Cat I:  [₹50/night]                       │
│  Cat II: [₹40/night]                       │
│  Def Civ:[₹60/night]                       │
│  [Update Fees]                             │
├────────────────────────────────────────────┤
│  Ranks                                     │
│  [Nb Sub] [Hav] [Sep] [Naik] [Rfn]       │
│  [+ Add Rank]  [✗ Remove]                 │
├────────────────────────────────────────────┤
│  Cancellation Policy                       │
│  15+ days:    [10%] charge                │
│  7-14 days:   [25%] charge                │
│  3-6 days:    [50%] charge                │
│  0-2 days:    [75%] charge                │
│  [Update Policy]                           │
└────────────────────────────────────────────┘
```

### Updating Room Rates

1. Enter new rates in the boxes
2. Click **"Update Rates"**
3. Confirmation message appears
4. New rates apply to future bookings

⚠️ **Note:** Does NOT change rates for existing bookings

### Managing Ranks

**Add New Rank:**
1. Click **"+ Add Rank"**
2. Enter rank name (e.g., "Maj")
3. Click "Add"
4. Rank appears in booking form dropdown

**Remove Rank:**
1. Click **✗** next to rank name
2. Confirm removal
3. Rank removed from dropdown

### Updating Cancellation Policy

1. Modify percentage values
2. Click **"Update Policy"**
3. New policy applies to future cancellations

---

## 14. Troubleshooting

### Common Issues & Solutions

#### Issue 1: Cannot Create Booking

**Symptoms:**
- "Create Booking" button disabled
- Error message appears

**Solutions:**
✅ Check all required fields are filled
✅ Verify room selection matches number of rooms
✅ Ensure check-out date is after check-in date
✅ Confirm payment details are complete

---

#### Issue 2: Check-In Button Disabled

**Symptoms:**
- Button is grayed out
- Cannot click check-in

**Cause:** Check-in date hasn't arrived yet

**Solution:**
✅ Wait until check-in date
✅ Hover over button to see available date
✅ If guest is early, contact administrator

---

#### Issue 3: Rooms Not Showing as Available

**Symptoms:**
- No rooms in selection grid
- "No available rooms" message

**Solutions:**
✅ Change dates - rooms may be booked for selected period
✅ Check if rooms are deactivated in Rooms page
✅ Verify rooms exist in Settings

---

#### Issue 4: PDF Not Downloading

**Symptoms:**
- Click print/report button but nothing happens

**Solutions:**
✅ Check browser pop-up blocker
✅ Allow downloads in browser settings
✅ Try different browser
✅ Check Downloads folder

---

#### Issue 5: Balance Amount Wrong

**Symptoms:**
- Bill summary shows incorrect amount

**Cause:** Extra beds or rate changes

**Check:**
✅ Verify extra beds selected
✅ Check room rates in Settings
✅ Confirm number of nights
✅ Review advance amount paid

---

### Getting Help

**If issue persists:**

1. **Check Dashboard** - Is system showing correct data?
2. **Refresh Page** - Press F5 or Ctrl+R
3. **Clear Cache** - Ctrl+Shift+Delete → Clear browsing data
4. **Try Different Browser** - Chrome, Edge, Firefox
5. **Contact Administrator** - Provide:
   - What you were trying to do
   - Error message (if any)
   - Screenshot of issue

---

## Appendix A: Keyboard Shortcuts

| Key | Action |
|-----|--------|
| **Esc** | Close dialog/modal |
| **Enter** | Submit form (when button focused) |
| **Tab** | Move to next field |
| **Shift+Tab** | Move to previous field |

---

## Appendix B: Quick Reference

### Daily Checklist

**Morning:**
- [ ] Check Dashboard for today's arrivals
- [ ] Review room availability
- [ ] Check pending refunds

**During Day:**
- [ ] Process check-ins as guests arrive
- [ ] Handle new bookings
- [ ] Print bills for checked-in guests

**Evening:**
- [ ] Process check-outs (collect feedback)
- [ ] Review tomorrow's arrivals
- [ ] Update any changes

**Weekly:**
- [ ] Review feedback scores
- [ ] Process pending refunds
- [ ] Generate monthly report (end of month)

### Important Numbers

**Default Values:**
- Advance per room: ₹400
- Extra bed charge: ₹75/night
- Cat I rate: ₹500/night
- Cat II rate: ₹400/night

**Booking Statuses:**
1. Confirmed
2. Checked-in
3. Checked-out
4. Cancelled

---

## Appendix C: Glossary

| Term | Meaning |
|------|---------|
| **Booking Number** | Unique ID for each reservation (e.g., BK0001) |
| **Cat I** | Category I rooms (higher rate) |
| **Cat II** | Category II rooms (standard rate) |
| **Def Civ** | Defense Civilian (non-military guest) |
| **Advance** | Money paid at booking time |
| **Balance** | Amount due at checkout |
| **Occupancy** | Percentage of rooms occupied |
| **License Fee** | Additional fee per command |
| **Command HQ** | Military command (Eastern, Western, etc.) |

---

## Document Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | April 2026 | Initial release |

---

**END OF USER HANDBOOK**

For additional support, please contact your system administrator.
