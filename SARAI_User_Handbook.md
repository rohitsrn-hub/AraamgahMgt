# SARAI User Handbook
**Shillong Aramgah Room Automation Interface**

Version 2.0 | April 2026

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Getting Started](#2-getting-started)
3. [Dashboard](#3-dashboard)
4. [Booking Management](#4-booking-management)
5. [Mix & Match Rooms Feature](#5-mix--match-rooms-feature)
6. [Check-In Process](#6-check-in-process)
7. [Check-Out Process](#7-check-out-process)
8. [Amend Booking](#8-amend-booking)
9. [Reports & PDFs](#9-reports--pdfs)
10. [Settings Management](#10-settings-management)
11. [Troubleshooting](#11-troubleshooting)
12. [Appendix](#12-appendix)

---

## 1. System Overview

### 1.1 What is SARAI?

SARAI (Shillong Aramgah Room Automation Interface) is a comprehensive room booking and management system designed to streamline accommodation operations. The system handles:

- Guest bookings and reservations
- Room allocation and availability tracking
- Check-in and check-out processes
- Payment and advance collection
- Automated receipt and form generation
- Occupancy reporting and analytics

### 1.2 Recent Major Changes (Sanitization Update)

The system has been **sanitized** to remove defense-related terminology and implement a more flexible classification system:

**Key Changes:**
- ✅ **Rebranding**: System renamed from "E-ARMS" to "SARAI"
- ✅ **Guest Classification**: Changed from "Defence/Civilian" to **"Organization (Org)" and "Non-Organization (Non-Org)"**
- ✅ **Color System**: Org guests can be assigned color categories (Red, Blue, Green, Yellow, Orange, Purple, Pink, Brown)
- ✅ **Sensitive Data Handling**: Defense-related fields removed from digital forms. Org guests fill an "Org Data Form" PDF manually at check-in
- ✅ **Pricing Structure**: Maintained existing rates (Cat I/Cat II for Org, separate rates for Non-Org)

### 1.3 User Roles

- **Front Desk Staff**: Handle bookings, check-ins, check-outs
- **Manager/Admin**: Access reports, manage settings, configure rates
- **Duty Staff**: Process check-outs, collect payments

---

## 2. Getting Started

### 2.1 Accessing SARAI

1. Open your web browser (Chrome, Firefox, or Edge recommended)
2. Navigate to your SARAI URL: `https://your-sarai-url.com`
3. The system loads directly to the Dashboard (no login required in current version)

### 2.2 Navigation

**Main Menu** (Left Sidebar):
- 🏠 **Dashboard**: Overview and quick actions
- 📅 **Bookings**: View and manage all bookings
- 🏨 **Rooms**: Room status and management
- 👥 **Staff**: Staff information
- 🚽 **Toiletry**: Inventory tracking
- ⭐ **Feedback**: Guest feedback system
- 📊 **Reports**: Analytics and reports
- 💾 **Backup & Restore**: Data management
- ⚙️ **Settings**: System configuration

### 2.3 Quick Actions

Dashboard provides quick access to:
- ➕ **New Booking**: Create a new reservation
- ✅ **Check In**: Process guest arrival
- ✅ **Check Out**: Process guest departure and payment
- ❌ **Cancel**: Cancel a booking
- 📊 **Reports**: Generate occupancy and financial reports

---

## 3. Dashboard

### 3.1 Overall Occupancy

Real-time room status:
- **Total Rooms**: Total available rooms (Cat I + Cat II)
- **Occupied**: Currently checked-in guests
- **Available**: Vacant rooms ready for booking
- **Occupancy %**: Current occupancy percentage

### 3.2 Category-wise Breakdown

- **Cat I Rooms**: Higher-tier rooms with better amenities
- **Cat II Rooms**: Standard rooms

Each category shows:
- Total rooms
- Occupied count
- Available count
- Occupancy rate

### 3.3 Room Planner

Visual calendar showing:
- Current month's bookings
- Room availability by date
- Upcoming reservations

### 3.4 Today's Bookings

List of bookings for current date with:
- Guest name
- Room number(s)
- Booking status (Confirmed, Checked In)

### 3.5 Upcoming Bookings

Next 7 days' reservations for planning purposes

---

## 4. Booking Management

### 4.1 Creating a New Booking

**Step 1: Guest Details**

1. Click **"New Booking"** button
2. Fill in required information:
   - **Guest Name**: Full name of the primary guest
   - **Contact Number**: 10-digit mobile number (must start with 6-9)
   - **Guest Type**: Select **Org** or **Non-Org**
   - **Org Color** (if Org selected): Choose color category
   - **Aadhaar Number**: 12-digit Aadhaar card number
   - **Number of Rooms**: How many rooms needed (1-10)

**Step 2: Date Selection**

3. **Check-in Date**: Select arrival date (today or future)
4. **Check-out Date**: Select departure date (must be after check-in)

📌 **Note**: Same-day bookings (check-in = today) automatically set advance payment to ₹0

**Step 3: Room Selection**

5. System shows available rooms for selected dates
6. Click on room cards to select (turns blue when selected)
7. Select exactly the number of rooms specified earlier

**🆕 Mix & Match Option**: If you need multiple rooms and want to optimize availability, use the **"Mix & Match Rooms"** feature (see Section 5)

**Step 4: Payment Details**

8. **Advance Payment**: Amount to collect now (auto-calculated as ₹400 per room for future bookings, ₹0 for same-day)
9. **Payment Mode**: Select Cash, UPI, or Bank Transfer
10. **Payment Details**: Fill in UPI ID/Phone or Bank details based on mode

**Step 5: Confirm Booking**

11. Review all details
12. Click **"Create Booking"**
13. System generates booking number (BK####)
14. Booking Slip PDF automatically downloads

### 4.2 Viewing Bookings

**Navigate to Bookings Page:**
- Shows all bookings in table format
- Columns: Booking #, Guest Name, Contact, Type, Rooms, Dates, Amount, Status, Actions

**Filter Options:**
- **Status Filter**: All, Confirmed, Checked In, Checked Out, Cancelled
- **Search**: Type guest name, booking number, or contact to search

**Status Indicators:**
- 🔵 **Confirmed**: Booking created, guest hasn't arrived
- 🟢 **Checked In**: Guest currently staying
- ⚪ **Checked Out**: Stay completed, payment settled
- 🔴 **Cancelled**: Booking cancelled

### 4.3 Booking Actions

For each booking, available actions depend on status:

**Confirmed Bookings:**
- ✅ **Check In**: Process guest arrival
- ✏️ **Amend**: Modify dates or rooms
- ❌ **Cancel**: Cancel the reservation

**Checked In Bookings:**
- ✅ **Check Out**: Complete stay and collect payment
- 📄 **Print Bill**: Generate checkout receipt

**All Bookings:**
- 📄 **Print Slip**: Download booking confirmation
- 👁️ **View Details**: See full booking information

---

## 5. Mix & Match Rooms Feature

### 5.1 What is Mix & Match?

**Mix & Match Rooms** is a smart feature that allows guests to book different rooms for different nights when a single room isn't available for the entire duration.

**Example Scenario:**
- Guest needs 2 rooms for 4 nights (April 20-24)
- Room C1-01 available for all 4 nights
- Room C1-02 available for only 2 nights
- Room C1-03 available for the other 2 nights

**Solution**: Mix & Match assigns C1-01 (all 4 nights) + C1-02 (2 nights) + C1-03 (2 nights)

### 5.2 How to Use Mix & Match

**Step 1: Start Normal Booking**
1. Fill guest details, dates, and number of rooms
2. Instead of manually selecting rooms, click **"Mix & Match Rooms"** button

**Step 2: View Optimal Recommendation**
3. System analyzes availability and shows the best combination:
   - Calendar view with per-night room assignments
   - Color-coded rooms (each room gets a unique color)
   - Status badges showing when rooms change
   - Total cost calculation

**Example Display:**
```
Recommended Room Combination
✓ 0 room changes - same rooms for entire stay

Night Date       Assigned Rooms              Status
Apr 20 (Mon)     [C1-01] [C1-02]            ✓ Same
Apr 21 (Tue)     [C1-01] [C1-02]            ✓ Same
Apr 22 (Wed)     [C1-01] [C1-02]            ✓ Same
Apr 23 (Thu)     [C1-01] [C1-02]            ✓ Same

Total Cost: ₹3200 (4 nights × 2 rooms, Org Rate)
```

**Step 3: Accept or Customize**

**Option A: Accept Recommendation**
- Click **"Accept Recommendation"** if satisfied
- Booking proceeds with suggested room assignment

**Option B: Customize Manually**
- Click **"Customize"** button
- For each night, click **"Change"** to select different rooms
- Manual room selector shows all available rooms for that night
- Select required number of rooms
- Click **"Confirm Selection"**
- Repeat for other nights if needed
- Click **"Accept Custom Selection"**

**Step 4: Complete Booking**
- System shows booking summary with room schedule
- Proceed with payment details as normal
- Confirm booking

### 5.3 Room Schedule in PDFs

When a booking has room changes during the stay:

**Booking Slip PDF** shows:
- Room Number field: *"(See room schedule below)"*
- Dedicated "ROOM SCHEDULE" section listing each night's assignment

**Example:**
```
ROOM SCHEDULE (Guest changes rooms during stay):
20 Apr: C1-01, C1-02  |  21 Apr: C1-01, C1-02
22 Apr: C1-01, C1-03  |  23 Apr: C1-01, C1-03
```

**Org Data Form PDF** shows:
- Room(s): C1-01, C1-02, C1-03 (varies)

### 5.4 Mix & Match Benefits

✅ **Maximize Occupancy**: Utilize partial availability instead of rejecting bookings
✅ **Guest Convenience**: One booking covers entire stay even with room changes
✅ **Automatic Optimization**: System minimizes room changes for guest comfort
✅ **Transparent Pricing**: Clear cost breakdown per night and room

---

## 6. Check-In Process

### 6.1 Prerequisites

Before checking in a guest:
- ✅ Booking must be in "Confirmed" status
- ✅ Check-in date should be today (system allows flexibility)

### 6.2 Check-In Steps

**Step 1: Locate Booking**
1. Go to **Bookings** page
2. Find the booking (use search if needed)
3. Click **"Check In"** button

**Step 2: Verify Guest Details**
4. Review displayed information:
   - Guest name, contact
   - Booking number
   - Room assignment
   - Total amount, advance paid, balance due

**Step 3: Guest Information Form**

Fill in additional details:
- **Guest Age**: Primary guest's age
- **Gender**: Male/Female/Other
- **Address**: Full residential address
- **Total Members**: Including primary guest (default = number of rooms × 2)
- **Member Ages**: Age of each family member

**For Org Guests Only:**
- **Org Color**: Verify/update color category
- System will generate **"Org Data Form"** PDF for manual completion

**Step 4: Collect Balance Payment**

If balance amount is due:
- **Amount Due**: Displayed prominently
- **Payment Mode**: Cash, UPI, or Bank Transfer
- **Payment Details**: Fill based on mode selected

**Step 5: Confirm Check-In**
5. Review all information
6. Click **"Confirm Check-In"**
7. Status changes to "Checked In"
8. PDFs auto-download:
   - **Org Data Form** (for Org guests only)
   - **Updated Booking Slip** (if regenerated)

### 6.3 Org Data Form

**Purpose**: Collect sensitive organizational data manually (not stored digitally)

**Instructions for Staff:**
1. PDF downloads automatically at check-in for Org guests
2. Print the form
3. Hand it to the guest to fill manually
4. Guest provides:
   - Service details
   - ID card information
   - Unit/Command information
   - Any other organizational details
5. **Store the physical form securely** (not entered into system)

**Form Contents:**
- Header: SARAI logo and "Organization Personnel Data Form"
- Booking reference: Number, guest name, mobile, room(s), check-in date, color
- Guest section: Fields for organizational details
- Dependents section: Table for family member information
- Signatures: Guest and duty staff

### 6.4 Post Check-In

After successful check-in:
- Guest can access room
- Room status updated to "Occupied"
- Balance payment recorded
- Guest appears in "Today's Bookings" as "Checked In"

---

## 7. Check-Out Process

### 7.1 Prerequisites

- ✅ Booking must be in "Checked In" status
- ✅ Guest ready to vacate room

### 7.2 Check-Out Steps

**Step 1: Initiate Check-Out**
1. Go to **Bookings** page
2. Find the booking
3. Click **"Check Out"** button

**Step 2: Verify Stay Details**
4. System displays:
   - Guest information
   - Room numbers
   - Check-in and check-out dates
   - Number of nights stayed
   - Room categories

**Step 3: Review Charges**

Breakdown shown:
- **Room Rent**: Rate × Nights × Number of rooms
- **License Fee**: Fee × Nights × Number of rooms
- **Extra Beds** (if any): Quantity × ₹75
- **Total Amount**: Sum of all charges
- **Advance Paid**: Amount paid at booking/check-in
- **Balance Collected**: Final amount due/collected

**Step 4: Collect Final Payment**

If balance due:
- Select payment mode
- Fill payment details
- Confirm collection

**Step 5: Confirm Check-Out**
5. Click **"Confirm Check-Out"**
6. Status changes to "Checked Out"
7. Room marked as "Available"
8. **Checkout Receipt (Bill) PDF** auto-downloads

### 7.3 Checkout Receipt (Bill)

**Contents:**
- Header: "CHECKOUT RECEIPT", Booking number
- **Guest Details**: Name, type (Org/Non-Org), color, mobile
- **Stay Details**: Rooms, category, dates, nights
- **Charges Table**: Itemized breakdown with calculations
- **Signature Lines**: Guest signature and Duty Staff signature
- **Footer**: Generated timestamp, SARAI branding

**Staff Instructions:**
1. Print the generated PDF
2. Present to guest for verification
3. Guest signs on designated line
4. Duty staff signs
5. Provide copy to guest, keep one for records

---

## 8. Amend Booking

### 8.1 When to Use Amend

Use the **Amend Booking** feature when a guest needs to:
- Extend their stay (later check-out date)
- Shorten their stay (earlier check-out date)
- Change check-in date
- Add or remove rooms
- Change room assignment

### 8.2 Amendment Process

**Step 1: Open Amendment Dialog**
1. Navigate to **Bookings** page
2. Find the confirmed booking
3. Click **"Amend"** button (three-dot menu)

**Step 2: Modify Details**
4. **New Check-In Date**: Select updated arrival date
5. **New Check-Out Date**: Select updated departure date
6. **Rooms**: Select new rooms from available options
7. **Number of Rooms**: Adjust if needed
8. **Members**: Update total members and ages if changed

**Step 3: Review Cost Analysis**

System automatically calculates:
- **Old Total**: Original booking amount
- **New Total**: Updated amount based on new dates/rooms
- **Difference**: Amount to pay (positive) or refund due (negative)

**Visual Indicators:**
- **Green Text**: Refund due to guest (cost decreased)
  - Message: *"Refund will be processed at check-in"*
  - No additional payment required
  
- **Red Text**: Additional payment required (cost increased)
  - Message: *"Additional advance payment required: ₹X"*
  - Payment section appears

**Step 4: Payment (if cost increased)**

If additional payment needed:
- **Additional Advance**: Auto-populated with difference amount
- **Payment Mode**: Select Cash, UPI, or Bank Transfer
- **Payment Details**: Fill based on mode

**Step 5: Confirm Amendment**
9. Optionally add **Amendment Reason** (notes)
10. Click **"Confirm Amendment"**
11. Booking updated with new details
12. Amendment logged in booking history

### 8.3 Refund Scenario

When amendment results in cost decrease:
- Difference shown in **green** with negative sign (e.g., ₹-800)
- Message: *"Refund will be processed at check-in"*
- **No payment details required**
- Refund amount tracked in system
- Staff processes refund manually at guest check-in

**Example:**
```
Original Booking: 4 nights × 1 room = ₹1600
Amended to: 2 nights × 1 room = ₹800
Difference: ₹-800 (Refund due)
```

### 8.4 Amendment History

Each amendment creates a log entry with:
- Timestamp
- Old values (dates, rooms, amount)
- New values
- Difference calculated
- Payment/refund details
- Reason (if provided)

View amendment history in booking details.

---

## 9. Reports & PDFs

### 9.1 Available Reports

**Navigate to Reports page for:**

**1. Occupancy Reports**
- Daily, weekly, monthly occupancy rates
- Category-wise breakdown (Cat I vs Cat II)
- Graphical visualization

**2. Revenue Reports**
- Total collections by date range
- Advance payments vs balance collected
- Payment mode breakdown

**3. Booking Reports**
- Total bookings by status
- Org vs Non-Org distribution
- Cancellation statistics

**4. Guest Reports**
- Guest history and frequency
- Org color distribution
- Contact directory

### 9.2 Generated PDFs

**9.2.1 Booking Slip**

**When Generated:**
- Automatically after booking creation
- Can be reprinted anytime from booking actions

**Contents:**
- SARAI header with branding
- Booking number and guest details
- Room assignment (or "See room schedule below" for segmented bookings)
- Check-in and check-out dates
- Payment information
- Terms and conditions
- Room schedule section (if applicable)
- Signature lines

**9.2.2 Org Data Form**

**When Generated:**
- Automatically at check-in for Org guests only

**Purpose:**
- Collect sensitive organizational data offline
- Not stored in digital system

**Contents:**
- Booking reference information
- Main guest section with fields for:
  - Service number
  - ID card details
  - Unit/Command
  - Other organizational information
- Dependents table
- Signature sections

**9.2.3 Checkout Receipt (Bill)**

**When Generated:**
- Automatically at check-out
- Can be reprinted from booking actions

**Contents:**
- Checkout receipt header
- Guest details (name, type, color, mobile)
- Stay details (rooms, dates, nights)
- Itemized charges table:
  - Room rent calculation
  - License fee calculation
  - Extra beds (if applicable)
  - Total amount
  - Advance paid
  - Balance collected
- Guest and duty staff signature lines
- Generated timestamp and SARAI footer

**Pricing Display:**
- **Org Guests**: Cat I or Cat II rates
- **Non-Org Guests**: Non-Organization rates (labeled as such)

**9.2.4 Bulk Booking Slips**

**When to Use:**
- Print multiple booking slips at once
- Useful for batch check-ins or record-keeping

**How to Generate:**
1. Go to Bookings page
2. Select multiple bookings (checkboxes)
3. Click **"Print Booking Slips"** button
4. Single PDF with all slips downloads
5. Each booking starts on new page

---

## 10. Settings Management

### 10.1 Accessing Settings

Navigate to **Settings** page (⚙️ icon in sidebar)

### 10.2 Rate Configuration

**10.2.1 Organization Rates**

Configure rates for Org guests:

**Cat I Rooms:**
- **Room Rent**: Base rate per night (e.g., ₹470)
- **License Fee**: Additional fee per night (e.g., ₹30)

**Cat II Rooms:**
- **Room Rent**: Base rate per night (e.g., ₹385)
- **License Fee**: Additional fee per night (e.g., ₹15)

**10.2.2 Non-Organization Rates**

Configure rates for Non-Org guests:

**Cat I Rooms:**
- **Room Rent**: Base rate per night (e.g., ₹570)
- **License Fee**: Additional fee per night (e.g., ₹30)

**Cat II Rooms:**
- **Room Rent**: Base rate per night (e.g., ₹455)
- **License Fee**: Additional fee per night (e.g., ₹15)

**10.2.3 Other Charges**
- **Extra Bed**: Fixed rate (e.g., ₹75 per bed per night)

### 10.3 Advance Payment Rules

**Default Advance:**
- ₹400 per room for future bookings
- Can be overridden during booking

**Same-Day Booking Rule:**
- If check-in date = today, advance automatically set to ₹0
- No advance required for same-day bookings

### 10.4 Color Categories

Configure available color options for Org guests:
- Red
- Blue
- Green
- Yellow
- Orange
- Purple
- Pink
- Brown

### 10.5 System Information

View:
- System name: SARAI
- Full name: Shillong Aramgah Room Automation Interface
- Version number
- Last update date

### 10.6 Saving Changes

1. Modify any settings
2. Click **"Save Settings"** button
3. System confirms update
4. Changes apply immediately to new bookings

---

## 11. Troubleshooting

### 11.1 Common Issues and Solutions

**Issue: Unable to create booking**
- ✅ **Solution**: Ensure all required fields are filled (name, contact, dates, rooms)
- ✅ Check that check-out date is after check-in date
- ✅ Verify mobile number is 10 digits starting with 6-9
- ✅ Ensure correct number of rooms selected

**Issue: No rooms available**
- ✅ **Solution**: Check date range - may be fully booked
- ✅ Try different dates or use **Mix & Match** feature
- ✅ Verify rooms aren't in maintenance status

**Issue: PDF not downloading**
- ✅ **Solution**: Check browser popup blocker settings
- ✅ Allow downloads from SARAI website
- ✅ Try different browser (Chrome recommended)
- ✅ Use "Print Slip" button to regenerate

**Issue: Amendment showing error**
- ✅ **Solution**: Ensure new dates don't conflict with other bookings
- ✅ Check that selected rooms are available for new date range
- ✅ If refund scenario, no payment details needed - remove them

**Issue: Check-in not working**
- ✅ **Solution**: Verify booking is in "Confirmed" status
- ✅ Ensure all guest information fields are filled
- ✅ If balance due, payment details must be provided

**Issue: Org Data Form not generating**
- ✅ **Solution**: Verify guest type is set to "Org" (not "Non-Org")
- ✅ Check that org color is assigned
- ✅ Refresh page and try check-in again

### 11.2 Browser Compatibility

**Recommended Browsers:**
- ✅ Google Chrome (version 90+)
- ✅ Mozilla Firefox (version 88+)
- ✅ Microsoft Edge (version 90+)

**Not Recommended:**
- ❌ Internet Explorer (not supported)
- ⚠️ Safari (may have PDF download issues)

### 11.3 Data Backup

**Regular Backups:**
1. Navigate to **Backup & Restore** page
2. Click **"Create Backup"**
3. JSON file downloads with timestamp
4. Store backup file securely

**Recommended Schedule:**
- Daily backups
- Keep weekly backups for 1 month
- Keep monthly backups for 1 year

**Restore Process:**
1. Go to **Backup & Restore**
2. Click **"Restore from Backup"**
3. Select backup JSON file
4. Confirm restore
5. System reloads with restored data

---

## 12. Appendix

### 12.1 Glossary

**Term** | **Definition**
---------|---------------
**Org** | Organization personnel or affiliated guests
**Non-Org** | Non-organization guests (general public)
**Cat I** | Category I rooms (higher tier)
**Cat II** | Category II rooms (standard tier)
**Advance** | Initial payment collected at booking
**Balance** | Remaining amount collected at check-in/check-out
**Mix & Match** | Feature allowing different rooms for different nights
**Room Segments** | Per-night room assignments in a single booking
**Org Data Form** | PDF form for manual collection of organizational data
**Amendment** | Modification to existing booking dates/rooms
**Sanitization** | Removal of defense-related terminology from system

### 12.2 Rate Structure Summary

**Current Rates (as of April 2026):**

| Room Type | Guest Type | Room Rent | License Fee | Total/Night |
|-----------|------------|-----------|-------------|-------------|
| Cat I | Org | ₹470 | ₹30 | ₹500 |
| Cat I | Non-Org | ₹570 | ₹30 | ₹600 |
| Cat II | Org | ₹385 | ₹15 | ₹400 |
| Cat II | Non-Org | ₹455 | ₹15 | ₹470 |

**Additional Charges:**
- Extra Bed: ₹75 per bed per night

**Note:** Rates are configurable in Settings and may vary by location.

### 12.3 Payment Modes

**Accepted Payment Methods:**

1. **Cash**
   - Direct cash payment
   - No additional details required

2. **UPI**
   - UPI ID (e.g., username@bank)
   - OR UPI Phone number (10 digits)
   - Transaction ID recommended

3. **Bank Transfer**
   - Bank Name
   - Account Number
   - IFSC Code (format: ABCD0123456)
   - Transaction reference recommended

### 12.4 Validation Rules

**Mobile Number:**
- Must be exactly 10 digits
- Must start with 6, 7, 8, or 9
- Example: 9876543210

**Aadhaar Number:**
- Must be exactly 12 digits
- Example: 123456789012

**IFSC Code:**
- Format: 4 letters + 0 + 6 alphanumeric
- Example: SBIN0001234

**Dates:**
- Check-out must be after check-in
- Minimum 1 night stay
- Future bookings: check-in can be today or later
- Migration mode allows past dates (admin only)

### 12.5 Keyboard Shortcuts

**Available Shortcuts:**

| Action | Shortcut |
|--------|----------|
| New Booking | `Alt + N` |
| Search Bookings | `Ctrl + F` (when on Bookings page) |
| Quick Check-In | `Alt + I` |
| Quick Check-Out | `Alt + O` |
| Go to Dashboard | `Alt + D` |
| Go to Reports | `Alt + R` |
| Go to Settings | `Alt + S` |

**Note:** Shortcuts may vary by browser and operating system.

### 12.6 Data Privacy & Security

**Sensitive Data Handling:**

1. **Org Data Form**
   - NOT stored digitally in system
   - Collected manually on paper form
   - Stored securely in physical records
   - Access restricted to authorized staff

2. **Digital Data Storage**
   - Guest name, contact, address stored
   - Aadhaar number stored (masked display)
   - Payment details stored for audit trail
   - No organizational sensitive data stored

3. **Access Control**
   - System accessible only on internal network
   - No external internet access (recommended)
   - Regular backups with encryption
   - User activity logging (when auth enabled)

### 12.7 System Limits

**Current System Limits:**

| Item | Limit |
|------|-------|
| Maximum rooms per booking | 10 |
| Maximum nights per booking | 365 |
| Maximum family members | 20 |
| Maximum simultaneous bookings | No limit |
| Booking number format | BK#### (9999 bookings then resets) |
| Search results per page | 50 |

### 12.8 Future Enhancements

**Planned Features:**

- 🔐 **User Authentication**: Role-based access control (Admin, Staff, Viewer)
- 📧 **Email Notifications**: Automated booking confirmations
- 📱 **SMS Integration**: Check-in reminders and notifications
- 📊 **Advanced Analytics**: Occupancy trends, revenue forecasting
- 🖨️ **Bulk Operations**: Mass check-ins, batch amendments
- 🔄 **Integration APIs**: Connect with other systems
- 🌐 **Guest Portal**: Online booking for approved guests
- 💳 **Payment Gateway**: Online payment collection

### 12.9 Contact & Support

**For Technical Issues:**
- Check troubleshooting section first
- Contact your system administrator
- Refer to this handbook for guidance

**For Rate Changes:**
- Contact management/admin
- Updates applied via Settings page

**For Feature Requests:**
- Submit to system administrator
- Provide detailed use case and benefits

---

## Document Information

**Version:** 2.0  
**Last Updated:** April 2026  
**Author:** SARAI Development Team  
**Reviewed By:** System Administrator  

**Change Log:**

| Version | Date | Changes |
|---------|------|---------|
| 2.0 | April 2026 | Complete rewrite post-sanitization. Added Mix & Match, Amend Booking, updated terminology (Org/Non-Org) |
| 1.5 | March 2026 | Added Org Data Form section |
| 1.0 | February 2026 | Initial handbook (E-ARMS system) |

---

**© 2026 SARAI - Shillong Aramgah Room Automation Interface**

*This handbook is for internal use only. Do not distribute outside authorized personnel.*

---

**END OF HANDBOOK**
