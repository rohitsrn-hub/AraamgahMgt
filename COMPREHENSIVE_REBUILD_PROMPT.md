# 🏨 SARAI - Guest House Management System
## COMPREHENSIVE REBUILD SPECIFICATION

**Version**: 2.0 (Complete Rebuild)  
**Date**: April 15, 2026  
**Purpose**: Clean, modular, optimized rebuild from scratch  
**Stack**: React 19 + FastAPI + MongoDB + Tailwind CSS + shadcn/ui

---

## 📋 TABLE OF CONTENTS

1. [Executive Summary](#executive-summary)
2. [System Architecture](#system-architecture)
3. [Database Schema](#database-schema)
4. [Business Logic & Rules](#business-logic--rules)
5. [Feature Specifications](#feature-specifications)
6. [API Endpoints](#api-endpoints)
7. [Frontend Architecture](#frontend-architecture)
8. [User Roles & Permissions](#user-roles--permissions)
9. [PDF Generation](#pdf-generation)
10. [Reports System](#reports-system)
11. [Security & Authentication](#security--authentication)
12. [Code Quality Standards](#code-quality-standards)
13. [Testing Requirements](#testing-requirements)
14. [Migration Strategy](#migration-strategy)

---

## 1. EXECUTIVE SUMMARY

**SARAI** (Shillong Aramgah Room Automation Interface) is a comprehensive guest house management system for managing bookings, check-ins, check-outs, room allocation, payments, and reporting.

### Core Objectives
- ✅ **Clean Architecture**: Modular, maintainable, scalable codebase
- ✅ **Zero Technical Debt**: No fragmented logic, no legacy code
- ✅ **Robust Error Handling**: Comprehensive validation at every layer
- ✅ **Performance**: Fast, efficient, optimized queries
- ✅ **User Experience**: Intuitive, responsive, error-free

### Key Stakeholders
- **Admin**: Full system access (user management, settings, all operations)
- **Staff**: Operational access (bookings, check-in/out, reports - NO settings/user management)
- **Viewer**: Read-only access (view all data, NO action buttons)

---

## 2. SYSTEM ARCHITECTURE

### Technology Stack

**Backend**:
- **Framework**: FastAPI (Python 3.11)
- **Database**: MongoDB (Motor async driver)
- **Authentication**: JWT with bcrypt password hashing
- **PDF Generation**: ReportLab or similar
- **Validation**: Pydantic v2 models
- **Runtime**: Python 3.11.9 (strict - for bcrypt compatibility)

**Frontend**:
- **Framework**: React 19
- **Routing**: React Router v6
- **Styling**: Tailwind CSS 3.x
- **Components**: shadcn/ui (Radix UI primitives)
- **Icons**: Phosphor Icons
- **Forms**: React Hook Form + Zod validation
- **HTTP**: Axios with interceptors
- **State**: React hooks (useState, useEffect, useContext)
- **Notifications**: Sonner (toast)

**DevOps**:
- **Hot Reload**: Enabled for both frontend and backend
- **Process Manager**: Supervisor
- **Environment**: Docker/Kubernetes
- **Backups**: Automated daily + manual incremental

### Architecture Principles

1. **Separation of Concerns**
   - Backend: `/app/backend/` - API, models, services, utils
   - Frontend: `/app/frontend/src/` - pages, components, utils, hooks

2. **Modular Structure**
   ```
   backend/
   ├── main.py (FastAPI app)
   ├── config.py (environment variables)
   ├── models/ (Pydantic models)
   │   ├── booking.py
   │   ├── user.py
   │   ├── room.py
   │   ├── settings.py
   │   └── ...
   ├── routes/ (API endpoints)
   │   ├── auth.py
   │   ├── bookings.py
   │   ├── rooms.py
   │   ├── reports.py
   │   └── ...
   ├── services/ (Business logic)
   │   ├── booking_service.py
   │   ├── payment_service.py
   │   ├── room_service.py
   │   ├── pdf_service.py
   │   └── ...
   ├── utils/ (helpers)
   │   ├── validators.py
   │   ├── date_utils.py
   │   └── ...
   └── tests/ (pytest)
   
   frontend/src/
   ├── App.js
   ├── pages/ (route pages)
   │   ├── Dashboard.jsx
   │   ├── Bookings.jsx (modular, <300 lines)
   │   ├── Rooms.jsx
   │   ├── Reports/ (sub-folder)
   │   └── ...
   ├── components/ (reusable)
   │   ├── BookingForm.jsx
   │   ├── CheckInDialog.jsx
   │   ├── RoomSelector.jsx
   │   ├── ui/ (shadcn components)
   │   └── ...
   ├── hooks/ (custom hooks)
   ├── utils/
   │   ├── api.js (axios instance)
   │   ├── validators.js
   │   ├── formatters.js
   │   └── pdfUtils.js
   └── context/ (global state)
   ```

3. **DRY Principle**: No code duplication - extract into reusable functions/components

4. **Error Boundaries**: Graceful error handling at component and API levels

---

## 3. DATABASE SCHEMA

### Collections

#### `app_settings` (singleton)
```javascript
{
  // Room Categories (dynamic - can add more)
  room_categories: [
    {
      id: "cat_i",
      name: "Cat I",
      capacity: 2,  // Base capacity (adults)
      org_room_rent: 470,
      org_license_fee: 30,
      color: "#3B82F6"  // For visual coding
    },
    {
      id: "cat_ii",
      name: "Cat II",
      capacity: 3,
      org_room_rent: 385,
      org_license_fee: 15,
      color: "#8B5CF6"
    }
  ],
  
  // Non-Org rates (same for all categories)
  non_org_room_rent: 570,
  non_org_license_fee: 30,
  
  // Extra bed pricing
  extra_bed_rate_per_night: 75,
  
  // Booking settings
  default_advance_amount: 400,  // Configurable
  
  // Cancellation policy (configurable)
  cancellation_policy: [
    { hours_before: 96, charge_percent: 0 },    // >96h: 0% charge (100% refund)
    { hours_before: 48, charge_percent: 50 },   // 48-96h: 50% charge
    { hours_before: 0, charge_percent: 100 }    // <48h: 100% charge (0% refund)
  ],
  
  // Check-in/out times
  default_checkin_time: "13:00",   // 1:00 PM
  default_checkout_time: "08:00",  // 8:00 AM
  
  // Guest house info
  guest_house_name: "Shillong Aramgah",
  address: "...",
  contact: "...",
  
  // System
  is_setup_complete: true,
  created_at: ISODate,
  updated_at: ISODate
}
```

#### `rooms`
```javascript
{
  id: "uuid",  // Custom string ID (NOT MongoDB _id)
  room_number: "C1-01",  // Unique
  category: "Cat I",  // References room_categories[].id
  status: "available" | "occupied" | "maintenance",
  floor: 1,
  created_at: ISODate,
  updated_at: ISODate
}
```

**Note**: Always exclude `_id` in all queries: `.find({}, {"_id": 0})`

#### `bookings`
```javascript
{
  id: "uuid",
  booking_number: "BK0001",  // Auto-increment, unique
  
  // Guest info
  guest_name: "John Doe",
  guest_contact: "+91 9876543210",  // Format: +91 XXXXXXXXXX
  guest_age: 35,  // Captured at booking, auto-filled at check-in
  guest_sex: "M" | "F" | "O",  // Auto-filled at check-in (default: M)
  guest_address: "",  // Mandatory at check-in
  guest_type: "org" | "non_org",  // Organization or Non-Organization
  
  // For Org guests only
  has_org_id_card: true | false,  // Main guest's org card availability
  org_color: "RED" | "BLUE" | ...,  // Captured at check-in
  
  // Dates
  check_in_date: "2026-04-15",  // YYYY-MM-DD
  check_out_date: "2026-04-17",
  
  // Actual timestamps (captured at check-in/out)
  actual_checkin_time: ISODate | null,  // Default 13:00 on check-in date
  actual_checkout_time: ISODate | null, // Default 08:00 on check-out date
  
  // Rooms
  room_ids: ["uuid1", "uuid2"],  // Array of room IDs
  room_numbers: ["C1-01", "C1-02"],
  room_categories: ["Cat I", "Cat I"],
  
  // Mix & Match (optional - for complex bookings)
  has_room_changes: false,
  room_segments: [  // Only if has_room_changes = true
    {
      date: "2026-04-15",
      room_id: "uuid1",
      room_number: "C1-01",
      category: "Cat I"
    },
    // ... more segments
  ],
  
  // Family members (captured at check-in)
  family_members: [
    {
      relation: "Spouse" | "Son" | "Daughter" | "Parent" | "Other",
      name: "Jane Doe",
      age: 32,
      sex: "F",
      mobile: "+91 9876543211" | "",  // Optional
      has_org_dep_card: true | false  // Org Dependent Card availability
    }
  ],
  
  // Room-Guest mapping (for check-in)
  room_guest_mapping: [
    {
      room_id: "uuid1",
      room_number: "C1-01",
      room_category: "Cat I",
      has_self: true,  // Main guest in this room?
      family_member_indices: [0, 1],  // Indices from family_members array
      charge_category: "Cat I" | "Non-Org"  // Calculated based on org card logic
    }
  ],
  
  // Payment
  advance_paid: 400,
  payment_mode_advance: "cash" | "card" | "upi" | "bank",
  payment_id_advance: "TXN123",  // Transaction reference
  
  // Bank details (if payment mode = bank)
  bank_name: "",
  bank_ifsc: "",  // Validate format: ABCD0123456
  bank_account: "",
  
  // UPI details (if payment mode = upi)
  upi_id: "user@bank",
  upi_phone: "+91 XXXXXXXXXX",
  
  // Card details (if payment mode = card)
  card_last4: "1234",
  card_type: "Visa" | "Mastercard" | "RuPay",
  
  // Extra beds
  extra_beds_checkin: 0,  // Number of extra beds at check-in
  extra_beds_checkout: 0,  // Actual extra beds at check-out
  extra_bed_days: 0,  // Number of nights extra beds were used
  extra_bed_charge_checkout: 0,  // Calculated: extra_beds_checkout × extra_bed_days × 75
  
  // Charges calculation
  total_room_charges: 1000,  // Calculated based on rates & dates
  final_payment: 600,  // Balance paid at checkout (total - advance + extra bed charges)
  payment_mode_final: "cash" | "card" | "upi" | "bank",
  payment_id_final: "TXN124",
  
  // Status
  status: "confirmed" | "checked_in" | "checked_out" | "cancelled" | "deleted",
  
  // Staff tracking
  booked_by_staff: "staff_uuid",  // Who created the booking
  checkin_by_staff: "staff_uuid" | null,
  checkout_by_staff: "staff_uuid" | null,
  cancelled_by_staff: "staff_uuid" | null,
  
  // Cancellation
  cancellation_reason: "",
  refund_amount: 0,
  cancellation_date: ISODate | null,
  
  // Notes
  booking_notes: "",
  checkin_notes: "",
  checkout_notes: "",
  
  // Feedback (captured at checkout)
  feedback_rating: 1-5 | null,
  feedback_text: "",
  
  // Amendment tracking
  is_amended: false,
  amendment_history: [
    {
      amended_at: ISODate,
      amended_by_staff: "staff_uuid",
      changes: {
        old_dates: { check_in: "2026-04-15", check_out: "2026-04-17" },
        new_dates: { check_in: "2026-04-16", check_out: "2026-04-18" },
        cost_difference: -200,  // Negative = refund
        additional_payment: 0
      }
    }
  ],
  
  // Timestamps
  created_at: ISODate,
  updated_at: ISODate
}
```

#### `users`
```javascript
{
  id: "uuid",
  username: "admin",  // Unique
  email: "admin@sarai.local",  // Unique
  name: "System Administrator",
  password_hash: "$2b$12$...",  // bcrypt
  role: "admin" | "staff" | "viewer",
  is_active: true,
  last_login: ISODate | null,
  created_at: ISODate,
  updated_at: ISODate,
  created_by: "admin_uuid" | null  // Track who created this user
}
```

#### `staff` (for tracking staff details)
```javascript
{
  id: "uuid",
  name: "Staff Name",
  designation: "Front Desk" | "Manager" | ...,
  contact: "+91 XXXXXXXXXX",
  is_active: true,
  created_at: ISODate
}
```

#### `feedback` (separate collection for analytics)
```javascript
{
  id: "uuid",
  booking_id: "booking_uuid",
  guest_name: "John Doe",
  rating: 4,
  feedback_text: "Great stay!",
  created_at: ISODate
}
```

#### `backups` (backup metadata)
```javascript
{
  id: "uuid",
  backup_type: "full" | "incremental",
  timestamp: ISODate,
  status: "completed" | "failed",
  file_path: "/backups/backup_20260415.json",
  records_count: 150,
  size_bytes: 52400,
  created_by: "admin_uuid" | "system"  // Manual or automated
}
```

### Database Indexes

**Critical Indexes** (for performance):
```javascript
// bookings
db.bookings.createIndex({ "booking_number": 1 }, { unique: true })
db.bookings.createIndex({ "status": 1 })
db.bookings.createIndex({ "check_in_date": 1, "check_out_date": 1 })
db.bookings.createIndex({ "guest_contact": 1 })

// rooms
db.rooms.createIndex({ "room_number": 1 }, { unique: true })
db.rooms.createIndex({ "status": 1, "category": 1 })

// users
db.users.createIndex({ "email": 1 }, { unique: true })
db.users.createIndex({ "username": 1 }, { unique: true })
```

---

## 4. BUSINESS LOGIC & RULES

### 4.1 Room Rate Calculation

**Org Guests** (has_org_id_card = true AND all family members have org_dep_card = true):
- **Cat I**: `cat_i_room_rent (470) + cat_i_license_fee (30) = ₹500/night`
- **Cat II**: `cat_ii_room_rent (385) + cat_ii_license_fee (15) = ₹400/night`

**Non-Org Guests** (no org card OR any family member lacks org dep card):
- **All Categories**: `non_org_room_rent (570) + non_org_license_fee (30) = ₹600/night`

**Important Rule**: If ANY family member in ANY room lacks an org dependent card, that specific room is charged at Non-Org rate (₹600/night), NOT the entire booking.

**Example Scenario**:
- Booking: 2 rooms (Cat I)
- Room 1: Self (has org card) + Spouse (has org dep card) → **₹500/night**
- Room 2: Son (no org dep card) → **₹600/night**
- Total: ₹500 + ₹600 = ₹1100/night

### 4.2 Extra Beds
- **Rate**: ₹75 per bed per night (configurable)
- **Capacity**: 
  - Cat I base capacity: 2 adults (can add extra beds)
  - Cat II base capacity: 3 adults (can add extra beds)
- **Capture Points**:
  1. **At Check-in**: Estimate (e.g., 2 extra beds needed)
  2. **At Check-out**: Actual count + number of nights used
- **Calculation**: `extra_beds_checkout × extra_bed_days × 75`

### 4.3 Advance Payment
- **Default**: ₹400 per room (configurable via settings)
- **Same-day Bookings**: If check_in_date = today → advance = ₹0 (auto-set)
- **Requirement**: Booking can ONLY be created if advance is received (no "Pending" status)

### 4.4 Booking Amendments

**Allowed Changes**:
- Check-in date
- Check-out date
- Rooms (add/remove/change category)
- Guest type (Org ↔ Non-Org)

**Process**:
1. Check room availability for new dates
2. Recalculate total cost (new dates × new rooms × rates)
3. Calculate difference: `new_total - original_total`
4. If **difference > 0**: Collect additional payment
5. If **difference < 0**: Mark refund due
6. Recalculate advance: Based on new room count and default advance amount
7. Store amendment in `amendment_history` array

**Restrictions**: None (can amend anytime, even on check-in day)

### 4.5 Cancellation Policy

**Configurable** via settings (default):
- **>96 hours before check-in**: 0% charge → 100% refund of advance
- **48-96 hours before**: 50% charge → 50% refund of advance
- **<48 hours before**: 100% charge → 0% refund

**Calculation Logic**:
```python
def calculate_refund(advance_paid, check_in_date):
    hours_until_checkin = (check_in_date - now()).total_seconds() / 3600
    policy = settings.cancellation_policy  # Sorted by hours_before DESC
    
    for tier in policy:
        if hours_until_checkin >= tier.hours_before:
            charge_percent = tier.charge_percent
            break
    
    refund = advance_paid * (1 - charge_percent / 100)
    return refund
```

**Status**: Cancelled bookings are **soft-deleted** (status = "cancelled", retained in DB for reporting)

**Hard Delete**: Separate button to permanently remove booking (status = "deleted", can be filtered out)

### 4.6 Check-In/Out Time Rules

**Standard Times**:
- **Check-in**: 13:00 (1:00 PM)
- **Check-out**: 08:00 (8:00 AM)

**Room Availability Logic**:
- If room booked until Apr 12 → Next booking can start on Apr 12
- Reason: Guest vacates at 08:00 on Apr 12, new guest checks in at 13:00 same day

**Early/Late Check-In/Out**:

1. **Early Check-In** (before scheduled date):
   - Allowed ONLY if rooms available
   - No extra charges
   - Update `actual_checkin_time`

2. **Late Check-Out** (after scheduled date) - Extension:
   - Allowed ONLY if rooms available
   - No late fees
   - Must amend booking (extends check_out_date)
   - Charged for extended nights

3. **Early Check-Out** (before scheduled date):
   - **Scenario A**: Guest informs at check-in → Amend booking → Charge only actual nights
   - **Scenario B**: Guest did NOT inform at check-in → Charge full booking amount

4. **Late Arrival** (checking in after scheduled date):
   - If NOT amended beforehand → Charge from original check-in date
   - If amended ≥24 hours in advance → No cancellation charge, charge from new date

### 4.7 Family Member & Org Card Logic

**Main Guest**:
- Field: `has_org_id_card` (Boolean)
- If booking type = "org" → Ask if they have Org ID Card
- ID number is NOT captured (only Yes/No)

**Family Members**:
- Field: `has_org_dep_card` (Boolean - Org Dependent Card)
- Each family member asked if they have Org Dependent Card
- If ANY member in ANY room has `has_org_dep_card = false` → That room charged at Non-Org rate

**Auto-Fill Logic**:
- If data captured in earlier form exists → Auto-fill in later forms
- Example: guest_age captured at booking → Auto-fill at check-in

### 4.8 Mix & Match Rooms

**Purpose**: For complex bookings where same rooms not available for entire duration

**Trigger**: Manual option (NOT automatic) - User clicks "Mix & Match" button

**Algorithm**:
- Input: Check-in date, check-out date, number of rooms, category preference
- Output: Optimal room combination minimizing room changes
- Priority: **Fewer room changes** over cost

**Data Structure**:
```javascript
room_segments: [
  { date: "2026-04-15", room_id: "uuid1", room_number: "C1-01", category: "Cat I" },
  { date: "2026-04-16", room_id: "uuid1", room_number: "C1-01", category: "Cat I" },
  { date: "2026-04-17", room_id: "uuid2", room_number: "C1-02", category: "Cat I" }  // Changed room
]
```

**Backward Compatibility**: Also populate `room_ids`, `room_numbers`, `room_categories` with unique rooms

---

## 5. FEATURE SPECIFICATIONS

### 5.1 Authentication & User Management

**Login**:
- Accept **email OR username** in single field
- Password with visibility toggle (eye icon)
- JWT token stored in localStorage
- Session timeout: **12 hours** (token expires, user auto-logged out)
- Axios interceptor handles 401 → Redirect to login

**Password Requirements**:
- Minimum length: 8 characters
- No complexity requirement (letters, numbers, special chars - optional)

**Password Reset**:
- Admin can reset any user's password
- Option to generate random secure password
- User receives new password (display on screen - no email)

**User CRUD** (Admin only):
- Create: Email, username, name, role, password
- Read: List all users with filters
- Update: Change name, role, active status
- Deactivate: Set `is_active = false` (soft delete)
- Role change: Instant effect on next page load

### 5.2 Dashboard

**Layout**: 
- Top action buttons: New Booking, Check In, Check Out, Cancel, Feedback, Reports
- Occupancy cards: Total Rooms, Occupied, Available, Occupancy %
- Category breakdown: Cat I (Total, Occupied, Available), Cat II (same)
- Room Planner: Calendar view showing bookings
- Today's Bookings: List with status badges
- Upcoming Bookings: Next 7 days

**Permissions**:
- **Admin/Staff**: All buttons enabled
- **Viewer**: All buttons disabled, read-only view

### 5.3 Bookings Page

**Features**:
- Search: By booking number, guest name, contact
- Filters: Status, date range, guest type, room category
- Table columns: Booking#, Guest, Contact, Dates, Rooms, Status, Advance, Actions
- Actions: Check-In, Check-Out, Amend, Cancel, Delete, View Details, Print Booking Slip

**New Booking Flow**:
1. **Guest Details**: Name, contact, age (optional initially), guest type (Org/Non-Org)
2. **Dates**: Check-in, check-out (validate availability)
3. **Room Selection**: 
   - Show available rooms with category, rate per night
   - Option: "Mix & Match" for complex bookings (manual)
   - Select rooms
4. **Payment Summary**: 
   - Total nights
   - Room charges breakdown
   - Advance amount (editable, default from settings)
   - Payment mode, payment ID
5. **Confirm**: Create booking → Generate booking slip PDF

**Amendment Flow**:
1. Open booking
2. Modify dates/rooms
3. Cost Analysis: Old total, New total, Difference (± amount)
4. If difference > 0: Collect additional payment
5. If difference < 0: Show refund due message
6. Confirm amendment → Update booking + history

**Check-In Flow**:
1. Select booking (only "confirmed" status allowed)
2. **Guest Details**: 
   - Contact, age (auto-filled), sex (default: M), address (mandatory)
   - If Org guest → Org color
3. **Family Members**: Add relation, name, age, sex, mobile (optional), has org dep card
4. **Room-Guest Assignment**: 
   - For each room: Assign Self (checkbox) + select family members
   - Display charge category based on org card logic
5. **Payment Details** (Bank/UPI - captured for records)
6. **Extra Beds**: Number of extra beds needed (editable later)
7. **Payment Summary**: 
   - Per-room charges (rate × nights)
   - Total room charges
   - Advance paid (subtract)
   - Extra bed estimate
   - Balance due at checkout
8. **Confirm**: Update status → "checked_in", capture timestamp, generate Org Data Form PDF (if Org guest)

**Check-Out Flow**:
1. Select booking (only "checked_in" status allowed)
2. **Extra Beds Actual**: 
   - Auto-fill from check-in
   - Edit if needed
   - Enter number of nights used
3. **Payment Summary**:
   - Room charges (calculated from actual dates if early checkout)
   - Extra bed charges
   - Subtract advance
   - Balance due (can be ₹0)
4. **Payment**: 
   - If balance = 0 → Auto-enable "Proceed to Feedback" (skip payment mode/ID)
   - If balance > 0 → Collect payment mode, payment ID, details
5. **Notes**: Checkout notes
6. **Proceed to Feedback**: Opens feedback dialog
7. **Feedback**: Rating (1-5 stars), text
8. **Confirm**: Update status → "checked_out", generate checkout receipt PDF

**Cancel Flow**:
1. Select booking (only "confirmed" status allowed, NOT "checked_in")
2. Show cancellation policy
3. Calculate refund based on hours until check-in
4. Display refund amount
5. Enter cancellation reason
6. Confirm: Update status → "cancelled", record refund

**Delete Flow** (Hard Delete):
- Separate button (visible to Admin only)
- Confirmation: "This will permanently delete the booking. Continue?"
- On confirm: `db.bookings.delete_one({"id": booking_id})`

### 5.4 Rooms Management

**Features**:
- Add Room: Room number, category, floor, status
- Edit Room: Change category, status, floor
- Delete Room: Soft delete (is_active = false) if no active bookings
- View: List with filters (category, status, floor)
- Bulk Actions: Mark multiple as maintenance/available

**Validation**:
- Room number must be unique
- Cannot delete room with active bookings

### 5.5 Staff Management

**Features**:
- Add Staff: Name, designation, contact
- Edit/Deactivate
- List: With search and filters

**Note**: Staff records are separate from Users. Users are for login, Staff are for tracking who performed operations.

### 5.6 Settings

**Sections**:

1. **Guest House Info**: Name, address, contact
2. **Room Categories** (dynamic):
   - List existing categories
   - Add new category: ID, name, capacity, org_room_rent, org_license_fee, color
   - Edit existing category rates
3. **Non-Org Rates**: Room rent, license fee (same for all categories)
4. **Extra Bed Rate**: Per night charge
5. **Booking Settings**: Default advance amount
6. **Cancellation Policy**: 
   - Editable tiers (hours_before, charge_percent)
   - Add/remove tiers
7. **Check-In/Out Times**: Default times

**Permissions**: Admin only

**Audit Trail** (optional for V2): Track who changed what setting and when

### 5.7 Backup & Restore

**Automated Backup**:
- **Schedule**: Daily at 02:00 AM IST (APScheduler)
- **Type**: Incremental (only new/changed records since last backup)
- **Storage**: MongoDB collection `backups` + file export

**Manual Backup**:
- Button: "Backup Now"
- **Incremental**: Only if new data since last backup
- **Full**: Force full backup option

**Restore**:
- List available backups (sorted by timestamp)
- Select backup to restore
- Options:
  - Restore entire database
  - Restore up to specific date (partial restore)
- Confirmation required
- Background job for large restores

**Backup Warning**:
- Banner shows if >24 hours since last backup
- Dismissible
- Reappears on next login if still not backed up

---

## 6. API ENDPOINTS

### 6.1 Authentication

```
POST   /api/auth/login
Body:  { "email": "admin@sarai.local", "password": "Admin@2026!" }
       OR { "username": "admin", "password": "..." }
Response: { "access_token": "jwt_token", "token_type": "bearer", "user": {...} }

POST   /api/auth/logout (optional - client-side token removal)

GET    /api/auth/me
Header: Authorization: Bearer <token>
Response: { "id": "uuid", "email": "...", "role": "admin", ... }
```

### 6.2 Users

```
GET    /api/users (Admin only)
Response: [{ "id": "uuid", "email": "...", "role": "admin", ... }]

POST   /api/users (Admin only)
Body: { "email": "...", "username": "...", "name": "...", "role": "staff", "password": "..." }

PUT    /api/users/{user_id} (Admin only)
Body: { "name": "...", "role": "viewer", "is_active": true }

PUT    /api/users/{user_id}/reset-password (Admin only)
Body: { "new_password": "..." } OR { "generate_random": true }
Response: { "new_password": "xyz123" }  // If random generated
```

### 6.3 Settings

```
GET    /api/settings
Response: { "room_categories": [...], "non_org_room_rent": 570, ... }

PUT    /api/settings (Admin only)
Body: { "non_org_room_rent": 600, "default_advance_amount": 500, ... }

POST   /api/settings/room-category (Admin only)
Body: { "id": "cat_iii", "name": "Cat III", "capacity": 4, "org_room_rent": 300, ... }

PUT    /api/settings/room-category/{category_id} (Admin only)
```

### 6.4 Rooms

```
GET    /api/rooms
Query: ?status=available&category=Cat I

POST   /api/rooms (Admin/Staff)
Body: { "room_number": "C1-01", "category": "Cat I", "floor": 1 }

PUT    /api/rooms/{room_id}
Body: { "status": "maintenance" }

DELETE /api/rooms/{room_id} (Soft delete)

GET    /api/rooms/available
Query: ?check_in=2026-04-15&check_out=2026-04-17&category=Cat I
Response: [{ "id": "uuid", "room_number": "C1-01", "category": "Cat I" }]
```

### 6.5 Bookings

```
GET    /api/bookings
Query: ?status=confirmed&guest_type=org&search=John

GET    /api/bookings/{booking_id}

POST   /api/bookings
Body: {
  "guest_name": "...", "guest_contact": "...", "guest_type": "org",
  "check_in_date": "2026-04-15", "check_out_date": "2026-04-17",
  "room_ids": ["uuid1"], "advance_paid": 400, "payment_mode_advance": "cash", ...
}

PUT    /api/bookings/{booking_id}/amend
Body: {
  "check_in_date": "2026-04-16", "check_out_date": "2026-04-18",
  "room_ids": ["uuid2"],
  "additional_payment": 200, "payment_mode": "upi", "payment_id": "TXN125"
}

POST   /api/bookings/{booking_id}/check-in
Body: {
  "staff_id": "uuid", "guest_age": 35, "guest_sex": "M", "guest_address": "...",
  "has_org_id_card": true, "org_color": "RED",
  "family_members": [...], "room_guest_mapping": [...],
  "extra_beds_checkin": 1, "bank_name": "...", ...
}

POST   /api/bookings/{booking_id}/check-out
Body: {
  "staff_id": "uuid", "extra_beds_checkout": 1, "extra_bed_days": 2,
  "payment_mode_final": "cash", "payment_id_final": "TXN126", "notes": "..."
}

POST   /api/bookings/{booking_id}/feedback
Body: { "rating": 4, "feedback_text": "Great stay!" }

POST   /api/bookings/{booking_id}/cancel
Body: { "staff_id": "uuid", "reason": "Change of plans" }
Response: { "refund_amount": 200 }

GET    /api/bookings/{booking_id}/calculate-refund
Response: { "refund_amount": 200, "charge_percent": 50, "policy_tier": "48-96 hours" }

DELETE /api/bookings/{booking_id} (Hard delete - Admin only)

POST   /api/rooms/find-optimal-combination (Mix & Match)
Body: { "check_in_date": "...", "check_out_date": "...", "num_rooms": 1, "category": "Cat I" }
Response: { "segments": [...], "total_cost": 1500, "room_changes": 1 }
```

### 6.6 Staff

```
GET    /api/staff
POST   /api/staff
PUT    /api/staff/{staff_id}
DELETE /api/staff/{staff_id}
```

### 6.7 Reports

```
GET    /api/reports/monthly
Query: ?month=4&year=2026
Response: { "month": 4, "year": 2026, "total_revenue": 50000, "occupancy_rate": 75, ... }

GET    /api/reports/room-occupancy
Query: ?start_date=2026-04-01&end_date=2026-04-30

GET    /api/reports/room-allotment
Query: ?start_date=2026-04-01&end_date=2026-04-30

GET    /api/reports/guest-details
Query: ?start_date=2026-04-01&end_date=2026-04-30
```

### 6.8 Dashboard

```
GET    /api/dashboard/occupancy
Response: { "total_rooms": 15, "occupied": 5, "available": 10, "occupancy_percent": 33.3, ... }

GET    /api/dashboard/analytics
Query: ?month=4&year=2026

GET    /api/dashboard/bookings (Today's and upcoming)

GET    /api/dashboard/calendar
Query: ?month=4&year=2026
```

### 6.9 Feedback

```
GET    /api/feedback/analysis
Response: { "average_rating": 4.2, "total_feedbacks": 50, "distribution": {5: 20, 4: 15, ...} }
```

### 6.10 Backups

```
GET    /api/backups/history
Query: ?limit=20

POST   /api/backups/create
Body: { "type": "incremental" | "full" }

POST   /api/backups/restore
Body: { "backup_id": "uuid" } OR { "restore_until_date": "2026-04-15" }

GET    /api/backups/status
Response: { "last_backup": ISODate, "hours_since": 12.5, "missed": false }
```

---

## 7. FRONTEND ARCHITECTURE

### 7.1 Component Structure

**Pages** (Route Components - max 300 lines each):

```
/app/frontend/src/pages/
├── Login.jsx
├── Dashboard.jsx
├── Bookings/
│   ├── BookingsPage.jsx (main page)
│   ├── BookingTable.jsx
│   ├── NewBookingDialog.jsx
│   ├── AmendBookingDialog.jsx
│   ├── CheckInDialog.jsx
│   ├── CheckOutDialog.jsx
│   ├── CancelDialog.jsx
│   └── MixMatchRoomSelector.jsx
├── Rooms/
│   ├── RoomsPage.jsx
│   └── RoomForm.jsx
├── Staff/
│   ├── StaffPage.jsx
│   └── StaffForm.jsx
├── Reports/
│   ├── ReportsPage.jsx (tab container)
│   ├── MonthlySummaryTab.jsx
│   ├── RoomOccupancyTab.jsx
│   ├── RoomAllotmentTab.jsx
│   └── GuestDetailsTab.jsx
├── Settings/
│   ├── SettingsPage.jsx (tab container)
│   ├── GeneralSettingsTab.jsx
│   ├── RoomCategorySettings.jsx
│   ├── PaymentSettings.jsx
│   └── CancellationPolicySettings.jsx
├── UserManagement/
│   ├── UsersPage.jsx
│   └── UserForm.jsx
└── BackupRestore.jsx
```

**Shared Components** (Reusable):

```
/app/frontend/src/components/
├── Layout.jsx (App shell with sidebar, topbar)
├── ProtectedRoute.jsx (Auth guard)
├── RoleGuard.jsx (Permission check)
├── RoomSelector.jsx (Select rooms from available)
├── FamilyMemberForm.jsx (Add/edit family members)
├── RoomGuestMapper.jsx (Assign guests to rooms)
├── PaymentDetailsForm.jsx (Bank/UPI/Card fields)
├── DateRangePicker.jsx
├── SearchBar.jsx
├── FilterPanel.jsx
├── StatusBadge.jsx
├── LoadingSpinner.jsx
├── ErrorBoundary.jsx
└── ui/ (shadcn components)
    ├── button.jsx
    ├── dialog.jsx
    ├── input.jsx
    ├── select.jsx
    ├── table.jsx
    ├── tabs.jsx
    └── ...
```

### 7.2 State Management

**No Redux/Zustand** - Use React hooks:

```jsx
// Global context for auth
export const AuthContext = createContext();

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  
  // Load user from token on mount
  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      // Verify token, load user
    }
  }, []);
  
  return (
    <AuthContext.Provider value={{ user, isAuthenticated, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}
```

**Settings Context**:
```jsx
export const SettingsContext = createContext();

export function SettingsProvider({ children }) {
  const [settings, setSettings] = useState(null);
  
  const fetchSettings = async () => {
    const res = await axios.get(`${API}/settings`);
    setSettings(res.data);
  };
  
  useEffect(() => { fetchSettings(); }, []);
  
  return (
    <SettingsContext.Provider value={{ settings, refreshSettings: fetchSettings }}>
      {children}
    </SettingsContext.Provider>
  );
}
```

### 7.3 Custom Hooks

```jsx
// useBookings.js
export function useBookings(filters = {}) {
  const [bookings, setBookings] = useState([]);
  const [loading, setLoading] = useState(false);
  
  const fetchBookings = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API}/bookings`, { params: filters });
      setBookings(res.data);
    } finally {
      setLoading(false);
    }
  };
  
  useEffect(() => { fetchBookings(); }, [filters]);
  
  return { bookings, loading, refresh: fetchBookings };
}

// usePermissions.js
export function usePermissions() {
  const { user } = useContext(AuthContext);
  
  return {
    canManageUsers: user?.role === 'admin',
    canManageSettings: user?.role === 'admin',
    canCreateBooking: ['admin', 'staff'].includes(user?.role),
    canViewReports: true,  // All roles
    isReadOnly: user?.role === 'viewer'
  };
}
```

### 7.4 Utilities

**Validators** (`utils/validators.js`):
```javascript
export function validateIndianPhone(phone) {
  // Remove spaces, +91
  const cleaned = phone.replace(/\s/g, '').replace(/^\+91/, '');
  return /^[6-9]\d{9}$/.test(cleaned);  // 10 digits, starts with 6-9
}

export function validateIFSC(ifsc) {
  return /^[A-Z]{4}0[A-Z0-9]{6}$/.test(ifsc);  // ABCD0123456
}

export function validateEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}
```

**Formatters** (`utils/formatters.js`):
```javascript
export function formatCurrency(amount) {
  return `₹${amount.toLocaleString('en-IN')}`;
}

export function formatDate(dateStr) {
  return new Date(dateStr).toLocaleDateString('en-IN', {
    day: '2-digit',
    month: 'short',
    year: 'numeric'
  });
}

export function formatPhone(phone) {
  // +91 XXXXXXXXXX
  const cleaned = phone.replace(/\s/g, '').replace(/^\+91/, '');
  return `+91 ${cleaned}`;
}
```

**API Client** (`utils/api.js`):
```javascript
import axios from 'axios';

export const API = process.env.REACT_APP_BACKEND_URL;

const apiClient = axios.create({
  baseURL: API,
  headers: { 'Content-Type': 'application/json' }
});

// Request interceptor - add token
apiClient.interceptors.request.use(config => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor - handle 401
apiClient.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/';
    }
    return Promise.reject(error);
  }
);

export default apiClient;
```

---

## 8. USER ROLES & PERMISSIONS

### Role Matrix

| Feature | Admin | Staff | Viewer |
|---------|-------|-------|--------|
| **Dashboard** | ✅ View | ✅ View | ✅ View |
| **Bookings** |
| - View list | ✅ | ✅ | ✅ |
| - Create new | ✅ | ✅ | ❌ |
| - Check-in | ✅ | ✅ | ❌ |
| - Check-out | ✅ | ✅ | ❌ |
| - Amend | ✅ | ✅ | ❌ |
| - Cancel | ✅ | ✅ | ❌ |
| - Hard delete | ✅ | ❌ | ❌ |
| **Rooms** |
| - View list | ✅ | ✅ | ✅ |
| - Add/Edit | ✅ | ✅ | ❌ |
| - Delete | ✅ | ❌ | ❌ |
| **Staff** |
| - View list | ✅ | ✅ | ✅ |
| - Add/Edit | ✅ | ✅ | ❌ |
| **Reports** | ✅ View All | ✅ View All | ✅ View All |
| **Feedback** | ✅ View | ✅ View | ✅ View |
| **Backup/Restore** |
| - View history | ✅ | ✅ | ✅ |
| - Create backup | ✅ | ❌ | ❌ |
| - Restore | ✅ | ❌ | ❌ |
| **Settings** | ✅ Full Access | ❌ | ❌ |
| **User Management** | ✅ Full Access | ❌ | ❌ |

### Implementation

**Backend** (decorator):
```python
from functools import wraps
from fastapi import HTTPException, Depends

def require_role(*allowed_roles):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, current_user: dict = Depends(get_current_user), **kwargs):
            if current_user['role'] not in allowed_roles:
                raise HTTPException(status_code=403, detail="Insufficient permissions")
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator

# Usage:
@app.post("/api/users")
@require_role("admin")
async def create_user(...):
    ...
```

**Frontend** (component):
```jsx
function BookingActions({ booking }) {
  const { isReadOnly } = usePermissions();
  
  return (
    <div>
      <Button onClick={handleView}>View</Button>
      {!isReadOnly && booking.status === 'confirmed' && (
        <Button onClick={handleCheckIn}>Check In</Button>
      )}
      {/* ... */}
    </div>
  );
}
```

---

## 9. PDF GENERATION

### 9.1 Booking Slip

**Trigger**: After booking creation  
**Content**:
- Header: Guest house name, logo, contact
- Booking number, date of booking
- Guest details: Name, contact, age, guest type
- Dates: Check-in, check-out, total nights
- Room details: 
  - If normal booking: Room numbers, categories
  - If mix & match: Room schedule table (Date | Room Number | Category)
- Payment: Advance paid, payment mode
- Terms: Check-in time, check-out time, cancellation policy
- Signature section: Guest signature, Staff signature

**Format**: A4, portrait, maximize space

### 9.2 Org Data Form

**Trigger**: After check-in (for Org guests only)  
**Content**:
- Guest details
- Family members (name, age, relation)
- Room assignments
- Fields to fill manually: Org ID numbers, signatures
- Note: "Fill this form manually and submit to admin office"

### 9.3 Checkout Receipt (Bill)

**Trigger**: After checkout  
**Content**:
- Header: Guest house name, Bill#, Date
- Guest details
- Booking details
- Charges breakdown:
  - Room charges: Category, Rate, Nights, Amount
  - Extra bed charges: Beds × Days × Rate
  - Subtotal
  - Less: Advance paid
  - Balance paid at checkout
  - **Total Paid**
- Payment mode, payment ID
- Footer: Thank you message

### 9.4 PDF Reports

**Monthly Summary**: Tabular format with totals, percentages  
**Room Occupancy**: Matrix (rooms × dates)  
**Room Allotment**: Date-wise room allocation  
**Guest Details**: Guest list with booking info

**Common Requirements**:
- Header: Report name, date range, generated timestamp
- Footer: Page numbers
- Tables: Proper borders, no overflow, compact
- Maximize A4 space utilization

**Library Recommendation**: Use **jsPDF** (frontend) or **ReportLab** (backend)

---

## 10. REPORTS SYSTEM

### 10.1 Monthly Summary Report

**API**: `GET /api/reports/monthly?month=4&year=2026`

**Calculated Fields**:
```javascript
{
  period: "April 2026",
  total_bookings: 50,
  total_revenue: 125000,  // Sum of all final payments
  total_license_fees: 7500,  // Extracted from room charges
  
  guest_type_breakdown: {
    org: { count: 30, revenue: 75000 },
    non_org: { count: 20, revenue: 50000 }
  },
  
  room_category_breakdown: {
    "Cat I": { bookings: 35, nights: 140, revenue: 70000, occupancy_rate: 77.8 },
    "Cat II": { bookings: 25, nights: 100, revenue: 40000, occupancy_rate: 37.0 }
  },
  
  status_breakdown: {
    confirmed: 10,
    checked_in: 5,
    checked_out: 30,
    cancelled: 5
  },
  
  average_stay_duration: 2.8,  // nights
  average_booking_value: 2500,
  
  occupancy_rate: 62.5  // Overall % for the month
}
```

**Display**: Cards with icons + detailed table

**Export**: PDF with tabular layout

### 10.2 Room Occupancy Report

**API**: `GET /api/reports/room-occupancy?start_date=2026-04-01&end_date=2026-04-30`

**Data Structure**:
```javascript
{
  rooms: [
    {
      room_number: "C1-01",
      category: "Cat I",
      occupancy_by_date: {
        "2026-04-01": { status: "occupied", booking_id: "uuid", guest_name: "John" },
        "2026-04-02": { status: "available" },
        // ...
      },
      total_occupied_days: 20,
      occupancy_percentage: 66.7
    }
  ]
}
```

**Display**: 
- Matrix/Grid: Rows = Rooms, Columns = Dates
- Color coding: Green = available, Blue = occupied, Red = maintenance

**Export**: PDF landscape format

### 10.3 Room Allotment Report

**API**: `GET /api/reports/room-allotment?start_date=2026-04-01&end_date=2026-04-30`

**Data Structure**:
```javascript
{
  allotments: [
    {
      date: "2026-04-15",
      rooms: [
        {
          room_number: "C1-01",
          guest_name: "John Doe",
          booking_number: "BK0001",
          check_in_date: "2026-04-15",
          check_out_date: "2026-04-17",
          guest_type: "Org"
        }
      ]
    }
  ]
}
```

**Display**: Date-wise grouped table

**Export**: PDF with date headers

### 10.4 Guest Details Report

**API**: `GET /api/reports/guest-details?start_date=2026-04-01&end_date=2026-04-30`

**Data Structure**:
```javascript
{
  guests: [
    {
      booking_number: "BK0001",
      guest_name: "John Doe",
      contact: "+91 9876543210",
      guest_type: "Org",
      check_in_date: "2026-04-15",
      check_out_date: "2026-04-17",
      rooms: "C1-01, C1-02",
      total_amount: 1000,
      status: "checked_out"
    }
  ]
}
```

**Display**: Searchable, sortable table

**Export**: PDF with all columns

### Common Report Features

**Date Filters**:
- This Month
- Last Month
- Custom Range (start_date, end_date)
- Financial Year (Apr 1 - Mar 31)

**Export Button**: "Print PDF" - triggers PDF generation and download

---

## 11. SECURITY & AUTHENTICATION

### 11.1 JWT Implementation

**Token Generation** (Backend):
```python
from jose import jwt
from datetime import datetime, timedelta, timezone

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 12

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

**Token Payload**:
```json
{
  "user_id": "uuid",
  "email": "admin@sarai.local",
  "role": "admin",
  "exp": 1776337718,  // 12 hours from creation
  "iat": 1776251318
}
```

### 11.2 Password Security

**Hashing** (bcrypt):
```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
```

**Password Requirements**:
- Minimum 8 characters
- No complexity enforced (optional: letters + numbers)

**Password Reset**:
```python
@app.put("/api/users/{user_id}/reset-password")
@require_role("admin")
async def reset_password(user_id: str, body: dict):
    if body.get("generate_random"):
        new_password = generate_random_password(12)  # abc123XYZ!@#
    else:
        new_password = body["new_password"]
    
    hashed = hash_password(new_password)
    await db.users.update_one({"id": user_id}, {"$set": {"password_hash": hashed}})
    
    return {"new_password": new_password} if body.get("generate_random") else {"message": "Password reset"}
```

### 11.3 API Security

**CORS**:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL")],  # Specific origin, not "*"
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
```

**Rate Limiting** (optional - use slowapi):
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])
app.state.limiter = limiter

@app.post("/api/auth/login")
@limiter.limit("5/minute")  # 5 login attempts per minute
async def login(...):
    ...
```

### 11.4 Input Validation

**Pydantic Models** (Backend):
```python
from pydantic import BaseModel, Field, validator

class BookingCreate(BaseModel):
    guest_name: str = Field(..., min_length=2, max_length=100)
    guest_contact: str
    guest_type: Literal["org", "non_org"]
    check_in_date: str  # YYYY-MM-DD
    check_out_date: str
    room_ids: list[str]
    advance_paid: float = Field(..., ge=0)
    
    @validator('guest_contact')
    def validate_phone(cls, v):
        cleaned = v.replace(' ', '').replace('+91', '')
        if not re.match(r'^[6-9]\d{9}$', cleaned):
            raise ValueError('Invalid Indian phone number')
        return f"+91 {cleaned}"
    
    @validator('check_out_date')
    def checkout_after_checkin(cls, v, values):
        if 'check_in_date' in values and v <= values['check_in_date']:
            raise ValueError('Check-out must be after check-in')
        return v
```

**Frontend Validation** (Zod + React Hook Form):
```jsx
import { z } from 'zod';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';

const bookingSchema = z.object({
  guest_name: z.string().min(2, "Name too short"),
  guest_contact: z.string().regex(/^[6-9]\d{9}$/, "Invalid phone"),
  check_in_date: z.string(),
  check_out_date: z.string()
}).refine(data => data.check_out_date > data.check_in_date, {
  message: "Check-out must be after check-in",
  path: ["check_out_date"]
});

function BookingForm() {
  const { register, handleSubmit, formState: { errors } } = useForm({
    resolver: zodResolver(bookingSchema)
  });
  
  // ...
}
```

### 11.5 Environment Variables

**Backend** (`.env`):
```bash
# Database
MONGO_URL=mongodb://localhost:27017/sarai
DB_NAME=sarai

# Auth
JWT_SECRET_KEY=your-super-secret-key-min-32-chars
JWT_ALGORITHM=HS256
JWT_EXPIRE_HOURS=12

# Python version
PYTHON_VERSION=3.11.9

# CORS
FRONTEND_URL=http://localhost:3000
```

**Frontend** (`.env`):
```bash
REACT_APP_BACKEND_URL=http://localhost:8001
```

**Important**: 
- NEVER hardcode URLs, ports, credentials
- NEVER commit `.env` files to Git
- Use `.env.example` for documentation

---

## 12. CODE QUALITY STANDARDS

### 12.1 Backend Standards

**Structure**:
```
- Max function length: 50 lines
- Max file length: 300 lines
- Use type hints everywhere
- Docstrings for all public functions
```

**Example**:
```python
async def calculate_booking_charges(
    room_ids: list[str],
    check_in_date: str,
    check_out_date: str,
    guest_type: str,
    family_members: list[dict],
    settings: dict
) -> dict:
    """
    Calculate total booking charges based on rooms, dates, and guest type.
    
    Args:
        room_ids: List of room UUIDs
        check_in_date: YYYY-MM-DD format
        check_out_date: YYYY-MM-DD format
        guest_type: "org" or "non_org"
        family_members: List of family member dicts with has_org_dep_card
        settings: App settings dict with rates
        
    Returns:
        {
            "total_charges": float,
            "per_room_breakdown": [...],
            "nights": int
        }
    """
    # Implementation
    ...
```

**Error Handling**:
```python
from fastapi import HTTPException

try:
    result = await db.bookings.find_one({"id": booking_id}, {"_id": 0})
    if not result:
        raise HTTPException(status_code=404, detail=f"Booking {booking_id} not found")
    return result
except Exception as e:
    logger.error(f"Failed to fetch booking: {str(e)}")
    raise HTTPException(status_code=500, detail="Internal server error")
```

**Logging**:
```python
import logging

logger = logging.getLogger(__name__)

@app.post("/api/bookings")
async def create_booking(booking: BookingCreate):
    logger.info(f"Creating booking for {booking.guest_name}")
    try:
        # ...
        logger.info(f"Booking created: {booking_id}")
    except Exception as e:
        logger.error(f"Booking creation failed: {str(e)}")
        raise
```

### 12.2 Frontend Standards

**Component Structure**:
```jsx
// Imports
import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';

// Component (max 200 lines)
export default function BookingForm({ onSubmit, initialData = {} }) {
  // State
  const [formData, setFormData] = useState(initialData);
  const [loading, setLoading] = useState(false);
  
  // Effects
  useEffect(() => {
    // Side effects
  }, []);
  
  // Handlers
  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await onSubmit(formData);
    } catch (err) {
      toast.error(err.message);
    } finally {
      setLoading(false);
    }
  };
  
  // Render
  return (
    <form onSubmit={handleSubmit}>
      {/* JSX */}
    </form>
  );
}
```

**Naming Conventions**:
- Components: PascalCase (`BookingForm.jsx`)
- Functions: camelCase (`handleSubmit`)
- Constants: UPPER_SNAKE_CASE (`API_URL`)
- CSS classes: kebab-case (via Tailwind)

**Props Validation**:
```jsx
import PropTypes from 'prop-types';

BookingForm.propTypes = {
  onSubmit: PropTypes.func.isRequired,
  initialData: PropTypes.object
};
```

**Avoid**:
- Inline styles (use Tailwind classes)
- Magic numbers (use named constants)
- Nested ternaries (use if/else or early returns)
- Deep nesting (max 3 levels)

### 12.3 Testing Standards

**Backend** (pytest):
```python
# /app/backend/tests/test_bookings.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_booking(client: AsyncClient, auth_token: str):
    """Test booking creation with valid data"""
    payload = {
        "guest_name": "Test User",
        "guest_contact": "+91 9876543210",
        "guest_type": "org",
        "check_in_date": "2026-05-01",
        "check_out_date": "2026-05-03",
        "room_ids": ["test-room-id"],
        "advance_paid": 400,
        "payment_mode_advance": "cash"
    }
    
    response = await client.post(
        "/api/bookings",
        json=payload,
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["guest_name"] == "Test User"
    assert "booking_number" in data
```

**Frontend** (React Testing Library - optional):
```jsx
import { render, screen, fireEvent } from '@testing-library/react';
import BookingForm from './BookingForm';

test('submits form with valid data', async () => {
  const handleSubmit = jest.fn();
  render(<BookingForm onSubmit={handleSubmit} />);
  
  fireEvent.change(screen.getByLabelText('Guest Name'), {
    target: { value: 'John Doe' }
  });
  
  fireEvent.click(screen.getByText('Submit'));
  
  expect(handleSubmit).toHaveBeenCalledWith({
    guest_name: 'John Doe',
    // ...
  });
});
```

### 12.4 Git Workflow

**Branch Strategy**:
- `main`: Production-ready code
- `develop`: Integration branch
- `feature/*`: New features
- `bugfix/*`: Bug fixes

**Commit Messages**:
```
feat: Add room category configuration
fix: Correct Non-Org rate calculation in check-in
refactor: Extract payment form into separate component
test: Add booking creation API tests
docs: Update API endpoint documentation
```

**Code Review Checklist**:
- [ ] No console.logs left in production code
- [ ] No hardcoded values (use env vars or settings)
- [ ] Error handling implemented
- [ ] Validation on both frontend and backend
- [ ] No SQL injection / NoSQL injection risks
- [ ] Follows DRY principle
- [ ] Comments for complex logic
- [ ] Responsive design (mobile-friendly)
- [ ] Accessibility (ARIA labels, keyboard navigation)

---

## 13. TESTING REQUIREMENTS

### 13.1 Backend Testing

**Unit Tests**:
- All service functions (business logic)
- Validators, calculators, utilities
- Coverage target: >80%

**Integration Tests**:
- All API endpoints
- Database operations
- Authentication flow

**Test Cases**:

1. **Bookings**:
   - Create booking with valid data
   - Create booking with invalid phone
   - Create booking with past dates (should fail)
   - Check-in with complete family member data
   - Check-out with zero balance (auto-proceed to feedback)
   - Amend booking (cost increase, cost decrease)
   - Cancel booking (different time windows for refund calculation)
   
2. **Room Rate Calculation**:
   - Org guest, all family with cards → Org rate
   - Org guest, one family without card → Non-Org rate for that room
   - Non-Org guest → Non-Org rate

3. **Authentication**:
   - Login with email
   - Login with username
   - Login with wrong password (401)
   - Token expiry (12 hours)
   - Access protected endpoint without token (401)

### 13.2 Frontend Testing

**Manual Testing** (using Playwright or similar):
- Complete booking flow (new booking → check-in → check-out)
- Amendment flow (dates, rooms)
- Cancellation with refund calculation
- Mix & Match room selection
- PDF generation for all types
- Reports generation and export
- User management (create, edit, reset password)
- Settings update

**Browser Compatibility**:
- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

**Responsive Testing**:
- Desktop (1920×1080)
- Tablet (768×1024)
- Mobile (375×667)

### 13.3 Performance Testing

**Metrics**:
- Page load time: <2 seconds
- API response time: <500ms (average)
- Database query time: <100ms

**Load Testing** (optional):
- 100 concurrent users
- 1000 bookings in database
- Reports generation under load

---

## 14. MIGRATION STRATEGY

### 14.1 Data Export from Current System

**Export Collections**:
```bash
# Export all data
mongoexport --uri="mongodb://localhost:27017/sarai" --collection=bookings --out=bookings_old.json
mongoexport --uri="mongodb://localhost:27017/sarai" --collection=rooms --out=rooms_old.json
mongoexport --uri="mongodb://localhost:27017/sarai" --collection=users --out=users_old.json
mongoexport --uri="mongodb://localhost:27017/sarai" --collection=app_settings --out=settings_old.json
```

### 14.2 Schema Mapping

**Old → New**:

```python
# Migration script: migrate_bookings.py

async def migrate_booking(old_booking: dict) -> dict:
    """Transform old booking schema to new schema"""
    
    new_booking = {
        "id": old_booking.get("id"),
        "booking_number": old_booking.get("booking_number"),
        
        # Guest info
        "guest_name": old_booking.get("guest_name"),
        "guest_contact": format_phone(old_booking.get("guest_contact", "")),
        "guest_age": old_booking.get("guest_age"),
        "guest_sex": old_booking.get("guest_sex", "M"),
        "guest_address": old_booking.get("guest_address", ""),
        "guest_type": "org" if old_booking.get("is_org") else "non_org",
        
        # Map old guest_rank to has_org_id_card
        "has_org_id_card": old_booking.get("guest_rank") in ["Off", "JCO", "OR"],
        
        # Dates
        "check_in_date": old_booking.get("check_in_date"),
        "check_out_date": old_booking.get("check_out_date"),
        
        # Timestamps
        "actual_checkin_time": old_booking.get("actual_checkin_time"),
        "actual_checkout_time": old_booking.get("actual_checkout_time"),
        
        # Rooms
        "room_ids": old_booking.get("room_ids", []),
        "room_numbers": old_booking.get("room_numbers", []),
        "room_categories": old_booking.get("room_categories", []),
        
        # Mix & match
        "has_room_changes": old_booking.get("has_room_changes", False),
        "room_segments": old_booking.get("room_segments", []),
        
        # Family members - migrate and add has_org_dep_card field
        "family_members": [
            {
                **member,
                "has_org_dep_card": member.get("has_org_card", False)  # Rename field
            }
            for member in old_booking.get("family_members", [])
        ],
        
        # Room-guest mapping
        "room_guest_mapping": migrate_room_mapping(old_booking.get("room_guest_mapping", [])),
        
        # Payment
        "advance_paid": old_booking.get("advance_paid", 0),
        "payment_mode_advance": old_booking.get("payment_mode", "cash"),
        "final_payment": old_booking.get("final_payment", 0),
        "payment_mode_final": old_booking.get("payment_mode_final", "cash"),
        
        # Status
        "status": old_booking.get("status", "confirmed"),
        
        # ... rest of fields
    }
    
    return new_booking

def migrate_room_mapping(old_mapping: list) -> list:
    """Migrate room-guest mapping, updating charge category logic"""
    new_mapping = []
    for room in old_mapping:
        # Check if any family member lacks org card
        family_without_card = any(
            not room.get("family_members", [])[i].get("has_org_card", True)
            for i in room.get("family_member_indices", [])
        )
        
        new_room = {
            **room,
            "charge_category": "Non-Org" if family_without_card else room.get("room_category")
        }
        new_mapping.append(new_room)
    
    return new_mapping
```

### 14.3 Migration Execution

**Steps**:

1. **Backup Current System**:
   ```bash
   mongodump --uri="mongodb://localhost:27017/sarai" --out=/backups/pre_migration_backup
   ```

2. **Deploy New System** (parallel to old system):
   - New codebase on different port/URL
   - Fresh MongoDB database

3. **Run Migration Scripts**:
   ```bash
   python migrate_bookings.py
   python migrate_users.py
   python migrate_rooms.py
   python migrate_settings.py
   ```

4. **Validation**:
   - Compare record counts
   - Spot-check critical bookings
   - Verify calculations (room rates, refunds)

5. **Parallel Run** (1 week):
   - Use new system for new bookings
   - Old system remains read-only for reference

6. **Cutover**:
   - Archive old system
   - Full production on new system

### 14.4 Rollback Plan

If critical issues found:
1. Switch DNS/routing back to old system
2. Investigate issues in new system
3. Fix and re-migrate
4. Retry cutover

**Rollback Window**: 48 hours after cutover (keep old system running)

---

## 15. IMPLEMENTATION CHECKLIST

### Phase 1: Foundation (Week 1)
- [ ] Setup project structure (backend, frontend)
- [ ] Database schema design and indexes
- [ ] Authentication system (JWT, password hashing)
- [ ] User management (CRUD, roles)
- [ ] Settings management (CRUD, dynamic room categories)
- [ ] Basic UI layout (sidebar, topbar, routing)

### Phase 2: Core Features (Week 2-3)
- [ ] Room management (CRUD)
- [ ] Staff management
- [ ] Booking creation flow
- [ ] Room availability checker
- [ ] Mix & Match room selector (optional, manual)
- [ ] Booking amendment
- [ ] Cancellation with refund calculation

### Phase 3: Operations (Week 3-4)
- [ ] Check-in flow (family members, room-guest mapping, org card logic)
- [ ] Check-out flow (extra beds, payment, feedback)
- [ ] PDF generation (booking slip, org data form, checkout receipt)
- [ ] Dashboard (occupancy, analytics, today's bookings)

### Phase 4: Reports (Week 4-5)
- [ ] Monthly summary report
- [ ] Room occupancy report
- [ ] Room allotment report
- [ ] Guest details report
- [ ] PDF export for all reports

### Phase 5: Advanced (Week 5-6)
- [ ] Backup system (automated, manual, incremental)
- [ ] Restore functionality
- [ ] Feedback analysis
- [ ] Audit trail for settings changes (optional)
- [ ] Performance optimization
- [ ] Security hardening

### Phase 6: Testing & Migration (Week 6-7)
- [ ] Backend unit tests
- [ ] API integration tests
- [ ] Frontend manual testing (all flows)
- [ ] Data migration scripts
- [ ] Migration dry-run
- [ ] Production deployment

### Phase 7: Polish (Week 7-8)
- [ ] Bug fixes from testing
- [ ] UI/UX refinements
- [ ] Documentation (user manual, API docs)
- [ ] Training materials
- [ ] Final production deployment
- [ ] Post-deployment monitoring

---

## 16. SUCCESS CRITERIA

**Technical**:
- ✅ Zero runtime errors in production
- ✅ All calculations mathematically accurate
- ✅ <500ms average API response time
- ✅ 99%+ uptime
- ✅ No data loss (backups working)

**Functional**:
- ✅ All booking flows working end-to-end
- ✅ PDFs generating correctly (no overflow, proper formatting)
- ✅ Reports accurate and exportable
- ✅ Role-based access working (Admin/Staff/Viewer)
- ✅ Multi-user concurrent access without conflicts

**Code Quality**:
- ✅ No code duplication (DRY)
- ✅ Modular structure (files <300 lines)
- ✅ Comprehensive error handling
- ✅ Input validation on all forms
- ✅ Clean, readable code with comments

**User Experience**:
- ✅ Intuitive workflows (minimal training needed)
- ✅ Fast page loads (<2 seconds)
- ✅ Clear error messages
- ✅ Responsive design (works on tablet/mobile)
- ✅ No confusing UI elements

---

## 17. ADDITIONAL NOTES

### Environment Setup

**Backend**:
```bash
cd /app/backend
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

**Frontend**:
```bash
cd /app/frontend
yarn install
yarn start  # Runs on port 3000
```

**MongoDB**:
```bash
# Start MongoDB (Docker)
docker run -d -p 27017:27017 --name sarai-mongo \
  -e MONGO_INITDB_ROOT_USERNAME=admin \
  -e MONGO_INITDB_ROOT_PASSWORD=password \
  mongo:6.0
```

### Deployment

**Backend** (Render/Railway):
- Use `runtime.txt` to specify Python 3.11.9
- Environment variables via platform dashboard
- Auto-deploy from `main` branch

**Frontend** (Vercel/Netlify):
- Build command: `yarn build`
- Publish directory: `build`
- Environment variables: `REACT_APP_BACKEND_URL`

**Database** (MongoDB Atlas):
- M0 free tier or M10 for production
- Enable IP whitelist for backend server
- Connection string in `MONGO_URL` env var

---

## 18. FINAL REMINDERS

1. **Always exclude `_id`** from MongoDB queries: `.find({}, {"_id": 0})`
2. **Never hardcode** URLs, ports, credentials - use env vars
3. **Validate everything** - frontend AND backend
4. **Test edge cases** - zero amounts, same-day bookings, early checkout, etc.
5. **Log errors** - use proper logging, not print statements
6. **Handle failures gracefully** - show user-friendly messages
7. **Optimize queries** - use indexes, limit results, pagination
8. **Security first** - JWT, bcrypt, CORS, rate limiting
9. **Keep components small** - max 300 lines, extract into smaller pieces
10. **Document as you go** - comments, docstrings, README

---

## 19. CONTACT & SUPPORT

**Developer**: E1 Agent (Emergent Labs)  
**Documentation Date**: April 15, 2026  
**Version**: 2.0 (Complete Rebuild Specification)

**For clarifications**, refer to:
- This document (COMPREHENSIVE_REBUILD_PROMPT.md)
- Original app codebase (for reference only)
- User requirements conversation history

**Rebuild Principle**: Clean slate - Do NOT copy-paste from old code. Implement fresh based on this specification.

---

**END OF COMPREHENSIVE REBUILD SPECIFICATION**

🚀 **Ready to build a robust, error-free, production-grade Guest House Management System!**
