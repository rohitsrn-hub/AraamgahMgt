# SARAI — Araamgah (Guesthouse) Management System

Booking, billing and reporting app for ONE guesthouse in Shillong.
**In live daily use. Every push deploys to production** — staff use the
Vercel site the same day. Never push half-done work.

## Session memory
- Running history file: `memory/HISTORY.md`. Read it at session start;
  append a dated 2–3 line entry after every completed feature or fix.

## Stack and layout
- Backend: FastAPI + MongoDB (async/motor). Almost everything lives in one
  big `backend/server.py` (~4,400 lines); shared helpers in `backend/utils/`.
- Frontend: React 18 (CRA + CRACO), Tailwind + Radix (shadcn-style `ui/`),
  phosphor icons, sonner toasts. Package manager is yarn, not npm.
- Main page by far: `frontend/src/pages/Bookings.jsx` (booking → check-in →
  check-out flows). Reports UI: `frontend/src/pages/reports/*`.

## Commands
- Backend tests: `cd backend && python3 -m pytest tests/` (pure unit tests;
  no DB or server needed for test_report_calc / test_manual_occupancy_excel).
- Local run: `./start-local.sh` (or `start-local.bat` on Windows).
- New Python dependency → add to `backend/requirements.txt` in the same
  commit, or the deployed backend crashes on that endpoint.

## Deployment (unusual — read this)
- Vercel (frontend) and Render (backend) deploy from the CURRENT WORKING
  BRANCH (`claude/debug-rates-setup-flicker-Vnopx`), not main. `render.yaml`
  saying `branch: main` is stale; the dashboards hold the real config.
- Push commits as work completes; never merge to main (owner merges via
  GitHub website if ever needed).

## Money rules (the #1 source of past bugs)
- Every rupee in every report must come from `backend/utils/report_calc.py`
  (`booking_financials`, `nights_in_period`, `report_booking_query`).
  Never recompute rates, nights or totals inline — four reports once drifted
  apart exactly this way and broke real-world accounting.
- After changing anything report-related, check
  `GET /api/reports/reconcile?month=&year=` returns `consistent: true`.

## Hard data rules
- NEVER store or digitize: military rank, Army/service number, unit, or any
  service data. These are paper-only by policy (see the Org Data Form PDF).
  Guests are classified only as `is_org` (bool) + `org_color`.
- Old field names are banned in new code: `guest_rank`, `def_civ_*`,
  `jco`/`or` report keys. Use `non_org_*` and `org_cat_i`/`org_cat_ii`.
- Live production DB: any migration or bulk data change needs the owner's
  explicit go-ahead first, plus a stated rollback path.

## Conventions
- Frontend API calls: always `${API}` (imported from `App.js`); a relative
  `/api/...` hits the Vercel domain and returns 405.
- PDF generators in `pdfUtils.js` return `{ blobUrl, filename }` and never
  auto-click downloads; callers decide via
  `showPDFNotification(result, title, autoDownload)`.
- Dates shown to users: dd/MM/yyyy. Amounts: `fmtINR` (Indian digit
  grouping). Guesthouse timezone is IST.
- New documentation goes in `docs/`. The ~30 legacy .md files in the root
  stay where they are (the README links to them).
