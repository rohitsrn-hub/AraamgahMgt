# 🚀 SARAI V2.0 - REBUILD INSTRUCTION

## TO THE REBUILDING AGENT

You are tasked with building **SARAI** (Shillong Aramgah Room Automation Interface) - a Guest House Management System - **FROM SCRATCH** using the comprehensive specification provided.

---

## 📄 PRIMARY REFERENCE DOCUMENT

**READ THIS FIRST**: `/app/COMPREHENSIVE_REBUILD_PROMPT.md`

This 1000+ line document contains:
- Complete system architecture
- Detailed database schema
- All business logic rules
- Feature specifications
- API endpoint definitions
- Frontend component structure
- Security requirements
- Code quality standards
- Testing requirements

---

## 🎯 YOUR MISSION

**Build a clean, modular, optimized, production-ready Guest House Management System that is:**
- ✅ **Error-free**: Robust validation, comprehensive error handling
- ✅ **Modular**: No file >300 lines, clear separation of concerns
- ✅ **Performant**: Fast queries, optimized renders, <500ms API responses
- ✅ **Secure**: JWT auth, bcrypt passwords, input validation everywhere
- ✅ **Maintainable**: DRY principle, clear naming, well-documented code

---

## 🚫 CRITICAL RULES

### DO NOT:
1. ❌ **Copy-paste from existing codebase** - it's fragmented and buggy
2. ❌ **Hardcode any values** - use env vars and settings
3. ❌ **Skip validation** - validate on both frontend and backend
4. ❌ **Create monolithic files** - keep files small and focused
5. ❌ **Ignore edge cases** - test zero amounts, same-day bookings, early checkout
6. ❌ **Use `_id`** - Always exclude MongoDB `_id`: `.find({}, {"_id": 0})`

### DO:
1. ✅ **Follow the spec** - every detail in COMPREHENSIVE_REBUILD_PROMPT.md
2. ✅ **Extract reusable logic** - services, utilities, components
3. ✅ **Handle errors gracefully** - try/catch, user-friendly messages
4. ✅ **Validate inputs** - phone numbers, IFSC codes, dates, etc.
5. ✅ **Test as you build** - unit tests for services, integration tests for APIs
6. ✅ **Document complex logic** - comments, docstrings
7. ✅ **Think modular** - if a function does >1 thing, split it

---

## 📐 TECH STACK (NON-NEGOTIABLE)

### Backend
- **Framework**: FastAPI (Python 3.11.9 - STRICT for bcrypt compatibility)
- **Database**: MongoDB (Motor async driver)
- **Auth**: JWT + bcrypt
- **Validation**: Pydantic v2
- **PDF**: ReportLab or jsPDF

### Frontend
- **Framework**: React 19
- **Styling**: Tailwind CSS
- **Components**: shadcn/ui (Radix UI)
- **Icons**: Phosphor Icons
- **HTTP**: Axios with interceptors
- **Validation**: React Hook Form + Zod

### Environment
- **Hot Reload**: Enabled (both backend & frontend)
- **Process Manager**: Supervisor
- **Backups**: MongoDB incremental backups

---

## 🗂️ FOLDER STRUCTURE

```
/app/
├── backend/
│   ├── main.py (FastAPI app)
│   ├── config.py (env vars)
│   ├── models/ (Pydantic models)
│   │   ├── booking.py
│   │   ├── user.py
│   │   ├── room.py
│   │   └── settings.py
│   ├── routes/ (API endpoints - one file per resource)
│   │   ├── auth.py
│   │   ├── bookings.py
│   │   ├── rooms.py
│   │   ├── users.py
│   │   ├── reports.py
│   │   └── ...
│   ├── services/ (Business logic)
│   │   ├── booking_service.py
│   │   ├── payment_service.py
│   │   ├── room_service.py
│   │   ├── pdf_service.py
│   │   └── ...
│   ├── utils/ (Helpers)
│   │   ├── validators.py
│   │   ├── date_utils.py
│   │   └── ...
│   └── tests/ (pytest)
│
├── frontend/src/
│   ├── App.js
│   ├── pages/ (Max 300 lines each)
│   │   ├── Dashboard.jsx
│   │   ├── Bookings/ (folder with sub-components)
│   │   ├── Rooms/
│   │   ├── Reports/
│   │   ├── Settings/
│   │   └── ...
│   ├── components/ (Reusable)
│   │   ├── BookingForm.jsx
│   │   ├── CheckInDialog.jsx
│   │   ├── RoomSelector.jsx
│   │   └── ui/ (shadcn)
│   ├── hooks/
│   ├── utils/
│   │   ├── api.js (axios instance)
│   │   ├── validators.js
│   │   └── pdfUtils.js
│   └── context/
│
└── COMPREHENSIVE_REBUILD_PROMPT.md (YOUR BIBLE)
```

---

## 🔑 KEY BUSINESS LOGIC (READ SPEC FOR DETAILS)

### Room Rates
- **Org Cat I**: ₹470 + ₹30 = ₹500/night
- **Org Cat II**: ₹385 + ₹15 = ₹400/night
- **Non-Org (all)**: ₹570 + ₹30 = ₹600/night

### Org Card Logic (CRITICAL)
- Main guest: `has_org_id_card` (Boolean)
- Family members: `has_org_dep_card` (Boolean)
- **Rule**: If ANY family member in ANY room lacks org dep card → That room charged at Non-Org rate (₹600)

### Check-In/Out Times
- **Check-in**: 13:00 (1:00 PM)
- **Check-out**: 08:00 (8:00 AM)
- **Room booking logic**: If room booked till Apr 12 → Next booking can start Apr 12 (guest vacates 08:00, new guest checks in 13:00)

### Cancellation Policy (Configurable)
- >96 hours: 100% refund
- 48-96 hours: 50% refund
- <48 hours: 0% refund

### Extra Beds
- ₹75 per bed per night
- Captured at check-in (estimate), updated at check-out (actual)

---

## 📊 DATABASE SCHEMA HIGHLIGHTS

### Collections
- `app_settings` (singleton): Room categories (dynamic), rates, policies
- `rooms`: room_number (unique), category, status
- `bookings`: Complete booking lifecycle (confirmed → checked_in → checked_out)
- `users`: email/username (unique), password_hash, role (admin/staff/viewer)
- `staff`: Staff records (separate from users)
- `feedback`: Separated from bookings for analytics
- `backups`: Backup metadata

**ALWAYS EXCLUDE `_id`**: `.find({}, {"_id": 0})` in ALL queries

---

## 👥 USER ROLES & PERMISSIONS

| Feature | Admin | Staff | Viewer |
|---------|-------|-------|--------|
| Bookings (view) | ✅ | ✅ | ✅ |
| Bookings (create/edit) | ✅ | ✅ | ❌ |
| Settings | ✅ | ❌ | ❌ |
| User Management | ✅ | ❌ | ❌ |
| Reports (view) | ✅ | ✅ | ✅ |
| Backup/Restore | ✅ | ❌ | ❌ |

---

## 📋 IMPLEMENTATION PHASES

### Phase 1: Foundation
- Project structure
- Auth system (JWT, password hashing)
- User management
- Settings management
- Basic UI layout

### Phase 2: Core Features
- Room management
- Booking creation
- Room availability
- Amendment flow
- Cancellation

### Phase 3: Operations
- Check-in (family members, org card logic)
- Check-out (extra beds, feedback)
- PDF generation

### Phase 4: Reports
- Monthly summary
- Room occupancy
- Room allotment
- Guest details

### Phase 5: Advanced
- Backup/Restore
- Feedback analysis
- Performance optimization
- Security hardening

### Phase 6: Testing & Migration
- Unit tests
- Integration tests
- Data migration scripts
- Production deployment

---

## ✅ VALIDATION REQUIREMENTS

### Phone Number
```javascript
// Format: +91 XXXXXXXXXX
// Regex: /^[6-9]\d{9}$/
validateIndianPhone("+91 9876543210") // true
```

### IFSC Code
```javascript
// Format: ABCD0123456
// Regex: /^[A-Z]{4}0[A-Z0-9]{6}$/
validateIFSC("SBIN0001234") // true
```

### Dates
```javascript
// Check-out MUST be after check-in
// Validate room availability for selected dates
```

---

## 🔒 SECURITY CHECKLIST

- [ ] JWT tokens expire after 12 hours
- [ ] Passwords hashed with bcrypt (Python 3.11.9 required)
- [ ] All endpoints validate JWT (except /api/auth/login)
- [ ] Input validation on EVERY API endpoint (Pydantic)
- [ ] Input validation on EVERY form (Zod + React Hook Form)
- [ ] CORS restricted to frontend URL (not "*")
- [ ] Rate limiting on login endpoint (5/minute)
- [ ] No console.logs in production code
- [ ] No error stack traces sent to frontend (generic messages only)
- [ ] Environment variables for ALL secrets

---

## 📄 PDF GENERATION REQUIREMENTS

### All PDFs Must:
- ✅ **Fit on A4** - no overflow, no cut-off text
- ✅ **Use tables** for structured data (proper borders)
- ✅ **Maximize space** - compact, efficient layout
- ✅ **No overlapping** - validate all text fits within bounds
- ✅ **Consistent branding** - guest house name, logo (if provided)

### PDFs Needed:
1. **Booking Slip** - After booking creation
2. **Org Data Form** - After check-in (Org guests only)
3. **Checkout Receipt** - After checkout
4. **4 Reports** - Monthly summary, room occupancy, room allotment, guest details

---

## 🧪 TESTING REQUIREMENTS

### Backend (pytest)
- Unit tests for all service functions
- Integration tests for all API endpoints
- Test edge cases:
  - Zero balance checkout
  - Same-day booking (advance = 0)
  - Early checkout scenarios
  - Org card logic (mixed family)
  - Cancellation refund calculations

### Frontend (Manual + Playwright)
- Complete booking flow (new → check-in → check-out)
- Amendment (dates, rooms, cost changes)
- Cancellation with refund
- Mix & Match room selection
- PDF generation for all types
- Reports generation and export
- User management flows

---

## 🚨 COMMON PITFALLS TO AVOID

1. **Forgetting to exclude `_id`** from MongoDB queries → Serialization errors
2. **Hardcoding rates** instead of reading from settings → Incorrect calculations
3. **Not handling zero balance** at checkout → Payment validation errors
4. **Mixing org card logic** (checking at booking level vs room level) → Wrong rates
5. **PDF overflow** - text exceeding page boundaries → Unreadable PDFs
6. **Missing phone/IFSC validation** → Invalid data in database
7. **Skipping error handling** → Cryptic errors for users
8. **Creating monolithic files** → Unmaintainable code
9. **Not testing session timeout** → Users stuck with expired tokens
10. **Ignoring role permissions** → Security vulnerabilities

---

## 📞 REFERENCE MATERIALS

1. **COMPREHENSIVE_REBUILD_PROMPT.md** - Primary specification (READ IN FULL)
2. **Existing codebase** - For reference ONLY (don't copy fragmented logic)
3. **Test credentials**: 
   - Email: `admin@sarai.local`
   - Password: `Admin@2026!`

---

## ✨ FINAL INSTRUCTIONS

1. **Read `/app/COMPREHENSIVE_REBUILD_PROMPT.md` in its ENTIRETY** before writing a single line of code
2. **Ask clarifying questions** if ANY part of the spec is unclear (don't assume)
3. **Build incrementally** - complete one phase before moving to next
4. **Test continuously** - don't wait until the end
5. **Document as you go** - comments, docstrings, README
6. **Follow the spec religiously** - it contains all answers
7. **Think production-ready** - this will be deployed and used daily

---

## 🎯 SUCCESS = ZERO BUGS + CLEAN CODE + HAPPY USERS

**You are building a production system that will manage guest house operations daily. Quality over speed. Correctness over cleverness. Simplicity over complexity.**

---

**Ready to build? Start with Phase 1 and work through methodically. Good luck! 🚀**

---

**Document created**: April 15, 2026  
**Author**: E1 Fork Agent (Emergent Labs)  
**For**: SARAI V2.0 Complete Rebuild
