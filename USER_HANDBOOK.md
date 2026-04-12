# 📖 SARAI User Handbook - Complete Guide
## Shillong Aramgah Room Automation Interface

**Version**: 2.1 (Authentication Enabled)  
**Last Updated**: April 2026

---

## 📑 Table of Contents

1. [Getting Started](#getting-started)
2. [User Roles & Permissions](#user-roles--permissions)
3. [Authentication & Login](#authentication--login)
4. [Command Center (Staff Landing)](#command-center)
5. [Dashboard](#dashboard)
6. [Bookings Management](#bookings-management)
7. [Check-In Process](#check-in-process)
8. [Check-Out Process](#check-out-process)
9. [Amendments & Cancellations](#amendments--cancellations)
10. [Rooms Management](#rooms-management)
11. [Staff Management](#staff-management)
12. [Reports](#reports)
13. [Feedback System](#feedback-system)
14. [Backup & Restore](#backup--restore)
15. [User Management (Admin Only)](#user-management)
16. [Settings (Admin Only)](#settings)
17. [Tips & Best Practices](#tips--best-practices)
18. [Troubleshooting](#troubleshooting)

---

## 🚀 Getting Started

### System Requirements
- **Modern web browser** (Chrome, Firefox, Safari, Edge)
- **Internet connection**
- **Login credentials** (provided by administrator)

### Accessing SARAI
1. Open your web browser
2. Navigate to your SARAI application URL
3. You'll be directed to the login page
4. Enter your username/email and password
5. Click "Sign In"

---

## 👥 User Roles & Permissions

SARAI has three user roles with different access levels:

### 🔴 **Admin** (Full Access)
**Can access:**
- ✅ All features and pages
- ✅ Create, edit, and delete users
- ✅ Modify system settings
- ✅ Access all reports and analytics
- ✅ Manage backups and restore data
- ✅ Complete booking lifecycle management

**Landing Page**: Dashboard

---

### 🟡 **Staff** (Operational Access)
**Can access:**
- ✅ Command Center (quick actions)
- ✅ Create and manage bookings
- ✅ Check-in and check-out guests
- ✅ Manage rooms and staff
- ✅ View reports
- ✅ Manage feedback
- ✅ Create and restore backups

**Cannot access:**
- ❌ User Management
- ❌ Settings page

**Landing Page**: Command Center (Splash Screen)

---

### 🟢 **Viewer** (Read-Only Access)
**Can access:**
- ✅ View all data (bookings, reports, analytics)
- ✅ View room and staff information
- ✅ View feedback
- ✅ Print PDFs and receipts

**Cannot do:**
- ❌ Create new bookings
- ❌ Check-in or check-out guests
- ❌ Modify or cancel bookings
- ❌ Edit rooms or staff
- ❌ Access backups
- ❌ Access user management or settings

**Visual Indicator**: All action buttons are grayed out with tooltips explaining restrictions

**Landing Page**: Dashboard

---

## 🔐 Authentication & Login

### Logging In

1. **Enter Username or Email**:
   - You can use either your username (e.g., `rohit`) 
   - OR your email (e.g., `rohit@sarai.local`)
   - Both work interchangeably

2. **Enter Password**:
   - Type your password
   - Click the **eye icon** to show/hide password as you type

3. **Click "Sign In"**

4. **Automatic Redirect**:
   - **Admin** → Dashboard
   - **Staff** → Command Center
   - **Viewer** → Dashboard

### Logging Out

Click the **"Logout"** button in the top-right corner (next to your name).

### Forgot Password?

Contact your system administrator to reset your password.

---

## 🎯 Command Center

**Available to**: Admin, Staff

The Command Center is the quick-access hub for daily operations.

### Quick Actions

**📅 New Booking**
- Creates a new room reservation
- Redirects to Bookings page with new booking form open

**✅ Check In**
- Shows list of today's confirmed bookings
- Select booking and complete check-in
- Generates physical form PDF

**🔄 Check Out**
- Shows list of currently checked-in guests
- Select booking and complete checkout
- Calculates final payment
- Generates bill/receipt

**❌ Cancel**
- Shows list of active bookings
- Select booking to cancel
- Calculates refund/cancellation charge

**⭐ Feedback**
- View feedback analysis and ratings
- Navigate to full feedback page

**📊 Reports**
- Quick access to reports dashboard

**📚 Toiletry**
- Manage toiletry supplies and stock

**📦 Backup**
- Create manual backup
- View backup status

---

## 📊 Dashboard

**Available to**: All roles

The Dashboard provides real-time overview of operations.

### Statistics Cards

1. **Occupied Rooms**
   - Current occupied vs total rooms
   - Visual breakdown by room category

2. **Today's Check-Ins**
   - Number of guests checking in today
   - List of pending check-ins

3. **Today's Check-Outs**
   - Number of guests checking out today
   - List of pending checkouts

4. **Current Funds**
   - Total advance received
   - Pending refunds
   - Net balance

### Quick Action Buttons

**Admin & Staff can:**
- Create new bookings
- Quick check-in
- Quick check-out
- Cancel bookings
- View feedback
- Access reports
- View calendar

**Viewers see:**
- Same buttons, but **disabled** (grayed out)
- Hover to see tooltip: "Viewers cannot perform this action"
- Can still view all data cards and analytics

### Today's Activity

Lists all bookings with activity today:
- **Confirmed**: Awaiting check-in
- **Checked In**: Currently occupying rooms
- **Checked Out**: Completed today

Each booking shows:
- Guest name and contact
- Room details
- Party size
- Status badge
- Action buttons (disabled for viewers)

---

## 📅 Bookings Management

**Available to**: Admin, Staff (Create/Edit), Viewer (View Only)

### Creating a New Booking

1. **Click "New Booking"** (Dashboard or Bookings page)

2. **Guest Information**:
   - Name (required)
   - Phone (10-digit Indian mobile)
   - Email (optional)
   - Accompanying persons count

3. **Date Selection**:
   - Check-in date
   - Check-out date
   - System shows available rooms for selected dates

4. **Room Selection** (Mix & Match):
   - Select one or more rooms
   - Different categories allowed
   - Different date ranges per room segment allowed
   - System shows: Room number, category, dates, nights, rate, amount

5. **Payment**:
   - Enter advance amount (₹)
   - Select payment mode (Cash/UPI/Card/Bank Transfer)
   - Enter transaction details if applicable

6. **Review & Confirm**:
   - Check all details
   - Click "Confirm Booking"
   - Booking receives unique ID
   - Status: **Confirmed**

### Same-Day Bookings

For check-in today:
- **No advance required**
- Payment mode automatically set to "Cash"
- Full payment collected at check-in

### Understanding Booking Status

- **🟡 Confirmed**: Booking made, awaiting check-in
- **🟢 Checked In**: Guest currently occupying room(s)
- **🔵 Checked Out**: Guest has checked out
- **🔴 Cancelled**: Booking cancelled
- **⚪ No Show**: Guest didn't arrive on check-in date

---

## ✅ Check-In Process

**Available to**: Admin, Staff

### When to Check In

**Option 1: On Check-In Date**
- Can check in from 12:00 PM (noon) on check-in date

**Option 2: Same-Day Walk-In**
- Create booking and check in immediately

### Check-In Steps

1. **Select Booking**:
   - Dashboard → Quick Check-In
   - OR Bookings page → Find booking → Click "Check In"

2. **Verify Guest Details**:
   - Name, phone, dates are shown
   - Room allocation displayed

3. **Guest Information Form**:
   - Guest fills physical form (generated PDF)
   - Staff member name (auto-selected or choose)
   - Actual check-in time (auto-filled with current time)

4. **Extra Beds** (if needed):
   - Select number of extra beds
   - System calculates charges

5. **Advance Payment** (if not paid during booking):
   - Enter amount received
   - Select payment mode
   - Enter transaction ID if applicable

6. **Generate Physical Form**:
   - System generates "Org Data Form" PDF
   - Contains: Guest details, room info, dates, payment info
   - Print for guest to fill and sign

7. **Confirm Check-In**:
   - Status changes to **Checked In**
   - Rooms marked as occupied

---

## 🔄 Check-Out Process

**Available to**: Admin, Staff

### When to Check Out

Anytime after guest has checked in, typically:
- On check-out date at 11:00 AM
- Or earlier if guest leaves early

### Check-Out Steps

1. **Select Booking**:
   - Dashboard → Quick Check-Out
   - OR Bookings page → Find booking → Click "Check Out"

2. **Review Stay Details**:
   - Rooms occupied
   - Actual nights stayed
   - Extra beds used (if any)

3. **Calculate Final Payment**:

   **System automatically calculates**:
   ```
   Total Room Charges (actual nights × rate)
   + Extra Bed Charges (if any)
   - Advance Already Paid
   - Refund Due (from amendments, if any)
   = Amount Due at Checkout
   ```

4. **Confirm Amount**:
   - Review calculated total
   - Click **"Confirm Amount"** to auto-fill
   - OR click **"Amend Amount"** to edit manually

5. **Special Case: Zero Amount Due**:
   - If total = ₹0 (fully paid in advance)
   - Click "Confirm Amount"
   - System auto-sets payment mode to "Cash"
   - **"Proceed to Feedback" button enables immediately**
   - Skip payment details, go straight to feedback

6. **Payment Collection** (if amount due > 0):
   - Select payment mode
   - Enter transaction ID (if UPI/Card/Bank Transfer)
   - Cash mode: Enter receipt number

7. **Feedback Form**:
   - Guest rates their experience (1-5 stars):
     - Room Quality
     - Cleanliness
     - Staff Behavior
     - Amenities
     - Overall Experience
   - Optional comments

8. **Complete Checkout**:
   - Click "Submit Feedback & Complete"
   - Status changes to **Checked Out**
   - Rooms marked as available
   - Bill/receipt generated (auto-download PDF)

### Checkout Receipt

The generated PDF includes:
- Guest and booking details
- Room charges breakdown
- Extra bed charges (if any)
- Advance paid
- Final payment collected
- Refund due (if any)
- Feedback rating
- Departure date and time

---

## ✏️ Amendments & Cancellations

**Available to**: Admin, Staff

### Amending a Booking

**What can be amended**:
- Check-in/check-out dates
- Room allocation (add, remove, or change rooms)
- Party size

**When you can amend**:
- Booking status: **Confirmed** only
- Cannot amend after check-in (use checkout process instead)

**How to amend**:

1. Bookings page → Find booking → Click **"Amend"**

2. **Modify Details**:
   - Change dates
   - Add/remove room segments
   - Modify party size

3. **Review Changes**:
   - System shows old vs new charges
   - Calculates: Additional payment OR Refund due

4. **Collect/Refund Payment**:
   - If **additional charge**: Collect payment
   - If **refund due**: Record refund transaction

5. **Confirm Amendment**:
   - Changes saved
   - Booking updated
   - Refund/payment recorded

---

### Cancelling a Booking

**When you can cancel**:
- Status: **Confirmed** or **Checked In**

**Cancellation Policy**:

**If cancelled BEFORE check-in date:**
- **Refund**: Advance - ₹100 cancellation charge
- Example: Advance ₹500 → Refund ₹400

**If cancelled AFTER check-in (guest already checked in):**
- Treated as checkout
- Charges calculated for nights stayed
- Refund = Advance - Room charges - Cancellation charge

**How to cancel**:

1. Select booking → Click **"Cancel"** (X button)

2. **Review Cancellation Details**:
   - System shows advance paid
   - Calculates refund due
   - Shows cancellation charge

3. **Confirm Cancellation**:
   - Status changes to **Cancelled**
   - Refund recorded
   - Rooms released

4. **Process Refund**:
   - Record refund transaction
   - Enter transaction ID
   - Select refund mode (same as original payment mode)

---

## 🛏️ Rooms Management

**Available to**: Admin, Staff (Edit), Viewer (View Only)

### Room Categories

SARAI typically has multiple room categories:
- Standard Room
- Deluxe Room
- Suite
- Family Room
- etc.

Each category has:
- **Base rate** (per night)
- **Number of rooms** in that category
- **Room numbers** assigned

### Adding a New Room

1. Rooms page → Click **"Add Room"**

2. **Enter Details**:
   - Room Number (unique)
   - Category (select from dropdown)
   - Rate (₹ per night)
   - Status (Active/Inactive)

3. **Save**

### Editing Room Details

1. Find room → Click **"Edit"** (pencil icon)
2. Modify details
3. Click **"Save"**

### Room Availability

**Dashboard shows**:
- Total rooms by category
- Occupied rooms (current)
- Available rooms

**Bookings page shows**:
- Real-time availability for selected dates
- Prevents double-booking

---

## 👨‍💼 Staff Management

**Available to**: Admin, Staff (Edit), Viewer (View Only)

### Staff Types

- **Front Desk**
- **Housekeeping**
- **Manager**
- **Maintenance**
- etc.

### Adding Staff Member

1. Staff page → Click **"Add Staff"**

2. **Enter Details**:
   - Name
   - Staff Type
   - Contact (optional)
   - Status (Active/Inactive)

3. **Save**

### Staff in Check-In/Check-Out

When checking in or checking out guests:
- Select staff member handling the transaction
- Recorded for accountability
- Appears on physical forms and receipts

---

## 📈 Reports

**Available to**: All roles (View), Admin (Full Access)

### Monthly Financial Report

**Select Month & Year** → Click **"Generate Report"**

**Includes**:

1. **Financial Summary**:
   - Total room revenue
   - Total extra bed charges
   - Total advance received
   - Total refunds issued
   - Net revenue

2. **Room Utilization**:
   - Total room-nights occupied
   - Category-wise breakdown
   - Occupancy percentage

3. **Booking Statistics**:
   - Total bookings created
   - Total check-ins
   - Total check-outs
   - Total cancellations
   - No-shows

4. **Guest Analytics**:
   - Average party size
   - Average stay duration
   - Booking sources (if tracked)

**Export Options**:
- Print report
- Download PDF
- View on screen

### Additional Reports (if configured)

- Daily revenue report
- Room-wise occupancy
- Staff performance
- Payment mode breakdown

---

## ⭐ Feedback System

**Available to**: Admin, Staff (View/Manage), Viewer (View Only)

### Feedback Collection

Collected during checkout process (automatic):
- Room Quality (1-5 stars)
- Cleanliness (1-5 stars)
- Staff Behavior (1-5 stars)
- Amenities (1-5 stars)
- Overall Experience (1-5 stars)
- Comments (optional text)

### Feedback Dashboard

**Shows**:
- **Average score** across all categories
- **Total feedback count**
- **Emoji indicator**: 
  - 😊 Happy (4+ stars)
  - 😐 Neutral (2.5-4 stars)
  - 😢 Needs Improvement (< 2.5 stars)

**Individual Feedback**:
- Guest name
- Checkout date
- Ratings breakdown
- Comments
- Overall score

**Analytics**:
- Trend over time
- Category-wise performance
- Identify areas for improvement

---

## 💾 Backup & Restore

**Available to**: Admin, Staff

### Why Backup?

- Protects against data loss
- Allows recovery from mistakes
- Enables data migration
- Required for compliance

### Automatic Backups

**Daily automatic backup** scheduled at:
- **2:00 AM IST** (default)
- Runs in background
- No user action needed

**Backup Retention**:
- Keeps last 30 backups
- Older backups auto-deleted

### Manual Backup

**When to create manual backup**:
- Before major changes
- After bulk data entry
- Before system updates
- End of month/quarter

**How to create**:

1. Backup & Restore page

2. **Full Backup** (Recommended):
   - Backs up ALL collections:
     - Bookings
     - Rooms
     - Staff
     - Guests
     - Payments
     - Feedback
     - Settings
   - Click **"Full Backup"**
   - Wait 10-30 seconds
   - Success notification shown

3. **Incremental Backup** (Advanced):
   - Backs up only changed data since last backup
   - Faster, smaller size
   - Click **"Incremental Backup"**

### Backup Status

**Last Backup Card** shows:
- Type (Full/Incremental)
- Date and time
- Number of records
- File size

**Total Backups Card** shows:
- Total backup count
- Storage used

**Next Scheduled Backup**:
- Shows next automatic backup time
- Status: Active/Paused

### Backup Warning

**Orange banner** appears if:
- Last backup > 24 hours ago
- Warns: "Backup Required: Last backup was X hours ago"
- Click **"Go to Backup Page"** to create backup

**Banner disappears** when:
- Fresh backup created
- System confirms backup < 24 hours old

### Restoring from Backup

**⚠️ Use with Caution**: Restore replaces current data with backup data.

**When to restore**:
- Accidental deletion
- Data corruption
- System migration
- Rollback after errors

**How to restore**:

1. Backup & Restore page → **Backup History**

2. **Select Backup**:
   - Click on backup from list
   - Shows: Date, time, type, records count

3. **Review Backup Contents**:
   - See what data will be restored

4. **Confirm Restore**:
   - System asks for confirmation
   - Warning: "This will replace current data"
   - Click **"Confirm Restore"**

5. **Wait for Completion**:
   - Takes 30-60 seconds
   - Success notification
   - Page reloads with restored data

---

## 👥 User Management

**Available to**: Admin Only

### Viewing Users

User Management page shows:
- Username
- Name
- Email
- Role (Admin/Staff/Viewer)
- Status (Active/Inactive)
- Created date
- Last login

### Creating a New User

1. Click **"Create User"**

2. **Enter Details**:
   - **Username**: Unique identifier (e.g., `rohit`)
   - **Email**: User's email address
   - **Name**: Full name (e.g., `Rohit Sharma`)
   - **Role**: Select Admin, Staff, or Viewer
   - **Password**: Minimum 8 characters
     - Click eye icon to show/hide password

3. **Click "Create"**

4. **Important**: 
   - Copy the username and password
   - Share securely with the user
   - Passwords cannot be retrieved later!

### Resetting User Password

**When user forgets password**:

1. Find user in list → Click **"Reset"** button

2. **Reset Password Dialog**:
   - Enter new password manually
   - OR click **"Generate Random Password"** (12 characters)
   - Click eye icon to show/hide

3. **Copy Password**:
   - Click copy icon to copy to clipboard
   - Share securely with user

4. **Click "Reset Password"**

**⚠️ Important**:
- Password shown only once
- User cannot retrieve it later
- Must share immediately with user

### Deactivating a User

**Instead of deleting**:
1. Find user → Click **"Deactivate"**
2. User cannot login
3. User data preserved
4. Can reactivate anytime

### Deleting a User

**Permanently removes user**:
1. Find user → Click trash icon
2. Confirm deletion
3. Cannot be undone!

**Note**: Cannot delete your own account (logged-in admin).

---

## ⚙️ Settings

**Available to**: Admin Only

### Configurable Settings

1. **Room Rates**:
   - Update rates for each room category
   - Seasonal pricing (if applicable)

2. **Extra Bed Charges**:
   - Per-day rate for extra beds

3. **Payment Modes**:
   - Enable/disable payment methods
   - Add new payment modes

4. **Cancellation Policy**:
   - Cancellation charge amount
   - Refund calculation rules

5. **Organizational Details**:
   - Organization name
   - Address
   - Contact information
   - Logo (if applicable)

6. **Backup Schedule**:
   - Automatic backup time
   - Retention period
   - Enable/disable automatic backups

7. **Email Notifications** (if configured):
   - Booking confirmations
   - Check-in reminders
   - Checkout receipts

### Updating Settings

1. Settings page
2. Modify desired values
3. Click **"Save Settings"**
4. Changes apply immediately

---

## 💡 Tips & Best Practices

### For All Users

**✅ Do's**:
- ✅ Logout when done (top-right logout button)
- ✅ Keep your password secure
- ✅ Double-check guest details before confirming
- ✅ Review calculations before final submission
- ✅ Print receipts for records
- ✅ Verify payment mode and transaction IDs

**❌ Don'ts**:
- ❌ Share your login credentials
- ❌ Leave your session unattended
- ❌ Skip backup creation before month-end
- ❌ Ignore backup warnings
- ❌ Rush through checkout calculations

---

### For Admins

**User Management**:
- Create individual accounts (don't share credentials)
- Deactivate users instead of deleting (preserves audit trail)
- Change default admin password immediately after setup
- Review user activity monthly

**Backups**:
- Create manual backup before month-end reports
- Test restore process quarterly
- Monitor backup storage space
- Keep backup schedule active

**Data Integrity**:
- Review reports monthly for anomalies
- Audit cancellations and refunds
- Check payment mode distribution
- Verify room utilization percentages

---

### For Staff

**Booking Process**:
- Verify phone numbers (10 digits, starts with 6-9)
- Confirm check-in/check-out dates with guest
- Explain cancellation policy during booking
- Collect advance for confirmed bookings

**Check-In**:
- Print physical form for guest signature
- Verify guest identity
- Explain checkout time and policies
- Note any special requests

**Check-Out**:
- Calculate final payment carefully
- Click "Confirm Amount" to auto-fill (avoid manual errors)
- Collect feedback while guest is present
- Print receipt and hand to guest
- Thank guest and invite future visits

**Room Management**:
- Mark rooms as inactive if under maintenance
- Update rates seasonally if applicable
- Report room issues in feedback/comments

---

## 🛠️ Troubleshooting

### Login Issues

**Problem**: "Invalid username or password"

**Solutions**:
- Check username/email spelling (case-sensitive)
- Verify password (use eye icon to view)
- Try using email instead of username (or vice versa)
- Contact admin to reset your password

---

**Problem**: Login page doesn't load

**Solutions**:
- Check internet connection
- Clear browser cache (`Ctrl+Shift+Del`)
- Try different browser
- Try incognito/private mode

---

### Booking Issues

**Problem**: "Room not available" for selected dates

**Solutions**:
- Check existing bookings for those dates
- Verify room is active (not maintenance)
- Try different room category
- Split booking across multiple rooms if needed

---

**Problem**: Cannot create same-day booking

**Solution**:
- Same-day bookings allowed
- No advance required for today's check-ins
- Full payment at check-in

---

### Check-In Issues

**Problem**: "Check-in button disabled"

**Reasons**:
- Check-in date is in the future (can only check in on/after check-in date)
- Booking already checked in
- Booking cancelled

**Solution**:
- Verify check-in date
- Check booking status
- Contact admin if issue persists

---

**Problem**: Physical form PDF not generating

**Solutions**:
- Check browser pop-up blocker
- Allow downloads from SARAI site
- Try different browser
- Check internet connection

---

### Check-Out Issues

**Problem**: "Proceed to Feedback" button disabled

**Reasons**:
- Amount not confirmed (click "Confirm Amount")
- Payment mode not selected
- Transaction ID missing (for UPI/Card/Bank Transfer)

**Solution**:
- Click "Confirm Amount" button
- If zero amount due: Button enables immediately
- If payment due: Fill payment details first

---

**Problem**: Calculated amount seems wrong

**Solutions**:
- Review booking details (dates, rooms, rates)
- Check for amendments (refunds applied)
- Verify extra bed charges
- Use "Amend Amount" to correct if needed
- Consult admin for complex cases

---

### Backup Issues

**Problem**: Backup warning won't disappear

**Solutions**:
- Create a fresh manual backup
- Wait 1-2 minutes for system to refresh
- Hard refresh page (`Ctrl+Shift+R`)
- Check backup history - verify recent backup exists

---

**Problem**: "Last backup was X hours ago" showing wrong time

**Solution**:
- This was a known issue, now fixed
- Update to latest version
- If persists, contact admin

---

### General Issues

**Problem**: Page not loading / blank screen

**Solutions**:
- Hard refresh: `Ctrl+Shift+R` (Windows/Linux) or `Cmd+Shift+R` (Mac)
- Clear browser cache
- Check internet connection
- Try incognito/private mode
- Contact admin if persists

---

**Problem**: Changes not saving

**Solutions**:
- Check for error messages (red notifications)
- Verify all required fields filled
- Check internet connection
- Try again after refreshing page

---

**Problem**: Logged out unexpectedly

**Reasons**:
- Session timeout (after 24 hours inactivity)
- Token expired
- Multiple logins from different devices

**Solution**:
- Login again
- Your work is auto-saved
- Continue from where you left off

---

## 📞 Support & Contact

For technical issues or questions:
- Contact your system administrator
- Refer to this handbook first
- Note error messages if any
- Provide screenshots for visual issues

---

## 🎓 Training Resources

**For New Users**:
1. Read relevant sections of this handbook
2. Shadow experienced staff member
3. Practice on test bookings (if available)
4. Start with simple tasks
5. Gradually take on complex operations

**For Admins**:
- Read entire handbook thoroughly
- Understand all roles and permissions
- Test backup and restore process
- Configure settings appropriately
- Train staff members on their specific roles

---

## 📝 Appendix

### Keyboard Shortcuts

- `Tab` - Move to next field
- `Enter` - Submit form (when applicable)
- `Esc` - Close dialog/modal
- `Ctrl+Shift+R` - Hard refresh page

### Date Format

All dates displayed in: `DD MMM YYYY, HH:MM IST`  
Example: `12 Apr 2026, 18:37 IST`

### Currency

All amounts in Indian Rupees (₹)

### Phone Numbers

Format: 10-digit Indian mobile (starts with 6-9)  
Example: `9876543210`

---

## 🔄 Version History

**v2.1** (April 2026)
- Added JWT Authentication system
- Role-Based Access Control (Admin/Staff/Viewer)
- User Management features
- Password reset and generation
- Login with username OR email
- Fixed backup warning accuracy
- Zero-amount checkout quick flow
- Security improvements

**v2.0** (April 2026)
- Sanitized defense-related data
- Rebranded to SARAI
- Physical form workflow
- Mix and match room bookings
- Booking amendments
- Same-day booking support

**v1.0** (March 2026)
- Initial release
- Basic booking management
- Check-in/Check-out
- Reports
- Backup system

---

## 📄 License & Credits

**SARAI** - Shillong Aramgah Room Automation Interface  
**Developed by**: Emergent AI  
**For**: Shillong Aramgah Administration

**All Rights Reserved** © 2026

---

**End of Handbook**

For the latest updates and digital version, contact your administrator.
