# SARAI — Running Work History

Read at session start. Append a dated 2–3 line entry after every completed
feature or fix (newest first). Product terms, not code terms.

---

## 2026-07-06 — Quality audit + fixes (branch: claude/qa-audit-fixes)
Full codebase audit; fixed ~20 issues across 5 commits. Safety: broken daily
backups, confidential archive now admin-only, setup-wizard re-run guarded.
Money: check-in billing routed through the shared rate engine (was legacy
fields + could zero the bill), monthly report colour table (was always blank),
refund capped at advance, no duplicate refund/checkout payments. Integrity:
availability checks added to mix-&-match bookings, date-only amendments, room
swaps, and stay-extension confirm; IST timezone for dates and the cancellation
slab; lowercase usernames; migration re-run made safe. NOT done: full backend
login enforcement (#1, deferred for discussion) and a few low-severity items.

## 2026-07-06 — Standing-instructions rewrite
Rewrote project CLAUDE.md as pure standing instructions (was a mixed session
log), created this history file, and added a copy of the computer-level
CLAUDE.md at docs/computer-level-CLAUDE.md for local-machine hand-off.

## 2026-07-04 — Manual Excel: mobile number column
Replaced the always-empty Aadhaar column with Mobile Number in the manual
Excel export — the app never had an Aadhaar input field anywhere, so mobile
(captured on every booking) is the working identifier.

## 2026-07-03 — Manual-format Excel export
New "Manual Excel" tab in Reports downloads an .xlsx matching the paper
"Summary of Room Occupancy" ledger, one row per room per booking. Army No /
Rank / Unit / Bill No left blank (highlighted) for pen fill-in by policy.

## 2026-07-03 — Financial reports reconciliation (major)
All four reports (Allotment, Guest Details, Occupancy, Monthly) now compute
money through one shared engine (backend/utils/report_calc.py); previously
they disagreed by ₹24,850 (May) / ₹13,775 (June). Six root causes fixed:
dropped extra-bed charges, month-boundary exclusions, missing multi-room
listings, nights drift, Monthly self-contradiction, wrong booking counts.
Added /api/reports/reconcile self-check + 15 unit tests.

## 2026-07-02 — Fable 5 debugging prompt
Wrote docs/fable5-prompt-financial-reconciliation.md from the owner's May/June
manual-vs-app reconciliation workbooks; that prompt drove the fix above.

## 2026-05-11 — Checkout receipts hardened
Receipt PDF now auto-downloads on every checkout, and checked-out bookings
show a purple "Receipt" button to re-download missed receipts anytime.

## 2026-05-08 — Toiletry report + watermark removal
Toiletry page: on-screen stock report (opening stock, added, issued, closing
balance) with "Summary Only" / "Full Report" PDF print options. Removed the
"Made with Emergent" badge and scripts from the app shell.

## 2026-05-07/08 — Stay extension + 5 bug fixes
Added Stay Extension for checked-in guests with a room-shuffling solver that
tries combinations of moving other bookings to free the same room (Phase 2.5).
Fixed: zero-payment checkout skipping payment form, PDF opening twice,
checkout date format, toiletry kits issued at check-in with stock deduction.

## 2026-04-23/26 — Report accuracy + polish round
Room occupancy counted only physically occupied nights; monthly report
aligned to occupancy logic; Indian number formatting everywhere; auto-logout
on tab close; Windows 10 setup guide written.

## Earlier (April 2026 and before)
Core system built and sanitized: bookings, check-in/out, refunds, feedback,
monthly reports, backups, auth. Military terminology replaced by Org/Non-Org
+ color classification; confidential service data moved to paper-only forms.
