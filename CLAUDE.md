# SARAI (AramgahMgt) — Development Context

**Branch:** `claude/debug-rates-setup-flicker-Vnopx`  
**Last Updated:** 2026-07-02

---

## Session 1 Summary

### Setup & Codebase Overview
- **Stack:** FastAPI backend (Python async, MongoDB), React 18 frontend (yarn, Vite)
- **Database:** MongoDB (no migration scripts yet)
- **API:** All frontend calls use `${API}` env var from `REACT_APP_BACKEND_URL` (not relative `/api/`)
- **Auth:** Permission-based (isViewer, isEditor flags)

### Branch Context: Sanitization Inconsistencies
System was sanitized to replace military terminology:
- Old: `guest_rank` (string enum: "Sep", "Hav", "Def Civ", etc.)
- New: `is_org` (boolean) + `org_color` (string for Org guests)
- Old rate fields: `def_civ_room_rent`, `def_civ_license_fee`, `def_civ_cat_i_rate`, `def_civ_cat_ii_rate`
- New rate fields: `non_org_room_rent`, `non_org_license_fee` (flat, not per-category)
- Old monthly report keys: `jco`, `or`, `def_civ`
- New monthly report keys: `org_cat_i`, `org_cat_ii`, `non_org`

### Known Issues (6 Critical/High Bugs in Plan File)
See `/root/.claude/plans/you-are-a-senior-rippling-lemur.md` for detailed analysis. Summary:
1. **CRITICAL:** Check-in amendment rate handler uses old `"Def Civ"` string; frontend sends `"Non-Org"` → wrong rate
2. **CRITICAL:** `non_org_*` rate fields never stored in DB (Pydantic models not updated)
3. **HIGH:** `MonthlyReport.jsx` reads old API keys (`jco`/`or`/`def_civ`); backend returns new keys → all zeros
4. **MEDIUM:** AppSettings still contains orphaned `def_civ_*` fields (dead code)
5. **MEDIUM:** `RoomSegmentSelector.jsx` reads old per-category `def_civ_*` fields
6. **MEDIUM:** Setup wizard flicker (onComplete not awaited; catch block doesn't set settings)

---

## Session 2 Work Completed

### 1. Toiletry Report Enhancement ✅
**Files:** `Toiletry.jsx`, `pdfUtils.js`

Updated `generateToiletryReportPDF` signature from `(transactions, fromDate, toDate)` to `(transactions, items, fromDate, toDate, summaryOnly = false)`.

**New PDF structure:**
- Header (title + date range)
- Totals strip (Stock Added | Kits Issued | Current Balance)
- Per-item summary table: Opening Stock | Stock Added | Kits Issued | Closing Balance
- Note about opening stock calculation (computed as: current - (in - out) within range)
- If `summaryOnly=false`: full transaction detail table

**Toiletry.jsx on-screen report:**
- Two print buttons: "Summary Only" + "Full Report"
- Expandable transaction details toggle
- `computeItemSummary()` calculates opening stock, inflows, consumption, final balance per item

### 2. Removed Emergent Watermark ✅
**File:** `frontend/public/index.html`

Deleted:
- `<meta name="description" content="A product of emergent.sh">`
- `<script src="https://assets.emergent.sh/scripts/emergent-main.js">`
- Fixed bottom-right badge anchor (`#emergent-badge`) with "Made with Emergent" text
- Updated meta description to SARAI

### 3. Auto-Download Checkout Receipts + Missed Receipt Button ✅
**File:** `Bookings.jsx`

**Changes:**
- Added `triggerPDFDownload(blobUrl, filename)` helper that does `link.click()` for browser file save
- `showPDFNotification()` gains `autoDownload` param; when `true`, triggers download before showing toast
- Checkout handler passes `autoDownload=true` → receipt auto-downloads to Downloads folder on successful checkout
- Added "Receipt" button (FilePdf icon) for `checked_out` status bookings in main table
  - Allows re-downloading any missed receipts at any time
  - Button shows purple, labeled "Receipt", next to delete button

---

## Critical File Locations

| File | Purpose |
|------|---------|
| `frontend/src/pages/Bookings.jsx` | Main bookings page; check-in/check-out/extend/amend dialogs |
| `frontend/src/pages/Toiletry.jsx` | Toiletry stock management + on-screen report with PDF export |
| `frontend/src/utils/pdfUtils.js` | PDF generators (receipts, reports, slips, etc.) |
| `frontend/src/App.js` | Main app wrapper; settings init + loading state |
| `frontend/public/index.html` | HTML template; meta tags, script includes |
| `backend/server.py` | FastAPI main; all endpoints (1500+ lines) |
| `backend/utils/helpers.py` | Rate calculation helpers (get_room_rate, etc.) |
| `backend/models/` | Pydantic models (Booking, AppSettings, etc.) |

---

## API Endpoints (Key Ones)

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/bookings/check-in` | Record check-in; update booking status to `checked_in` |
| POST | `/bookings/check-out` | Record check-out; final payment; update status to `checked_out` |
| PUT | `/bookings/{id}/amend` | Extend/amend stay; handle room reassignment via CSP solver |
| POST | `/bookings/{id}/plan-extension` | Phase 2.5 CSP backtracking for extension planning |
| POST | `/bookings/{id}/confirm-extension` | Confirm extension + room assignments |
| POST | `/toiletry/consumption` | Log toiletry kit consumption at check-in |
| GET | `/toiletry/items` | Fetch all toiletry item types |
| GET | `/toiletry/transactions?from=YYYY-MM-DD&to=YYYY-MM-DD` | Fetch transactions in date range |
| GET | `/api/settings` | Fetch app config (rates, room list, etc.) |
| PUT | `/api/settings` | Update settings (rates, room categories, etc.) |

---

## Next Tasks (Prioritized)

### Blocking (Rating system broken for Non-Org guests)
- [ ] **Bug #1:** Fix check-in amendment handler — change `"Def Civ"` to `"Non-Org"` at `server.py:1576`
- [ ] **Bug #2:** Add `non_org_room_rent` / `non_org_license_fee` to Pydantic models (AppSettings, AppSettingsUpdate, SetupRequest)
- [ ] **Bug #3:** Update MonthlyReport.jsx to read new API keys (org_cat_i/ii, non_org instead of jco/or/def_civ)

### High Priority (UI consistency)
- [ ] **Bug #5:** Fix RoomSegmentSelector.jsx rate display — use non_org_room_rent + non_org_license_fee, not old per-category fields
- [ ] **Bug #6:** Fix setup wizard flicker — await onComplete(); handle settings=null in error path

### Tech Debt (Post-migration cleanup)
- [ ] **Bug #4:** Remove orphaned `def_civ_*` fields from AppSettings model + DB documents
- [ ] Remove per-category `def_civ_rate` from room_categories array (conflicts with flat non_org model)

---

## Dev Environment Notes

- **Yarn:** Primary package manager (package.json scripts use yarn)
- **Dev server:** `yarn start` (Vite, probably port 5173)
- **Backend:** `python server.py` (FastAPI, port 8000)
- **Git branch:** All work goes to `claude/debug-rates-setup-flicker-Vnopx`; do NOT push to main/master
- **Commits:** Normal English prose (not caveman mode) for git log readability

---

## Useful Patterns

### Rate Calculation (Correct Pattern)
```javascript
// In Bookings.jsx and other files (CORRECT):
const ratePerNight = isNonOrg
  ? ((settings?.non_org_room_rent || 570) + (settings?.non_org_license_fee || 30))
  : (category === "Cat I"
      ? ((settings?.cat_i_room_rent || 470) + (settings?.cat_i_license_fee || 30))
      : ((settings?.cat_ii_room_rent || 385) + (settings?.cat_ii_license_fee || 15)));
```

### PDF Download Helper
```javascript
const triggerPDFDownload = (blobUrl, filename) => {
  const link = document.createElement('a');
  link.href = blobUrl;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};
```

### Toast Notification for PDFs
```javascript
const showPDFNotification = (result, title = "PDF Generated", autoDownload = false) => {
  if (autoDownload) triggerPDFDownload(result.blobUrl, result.filename);
  // ... rest of toast UI
};
```
