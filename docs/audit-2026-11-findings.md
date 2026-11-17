# Full-codebase audit — findings (16 Nov 2026)

Branch: `claude/qa-audit-fixes`. Companion to `docs/handoff-2026-11-financial-audit.md`.
Every "fixed" item has a test that failed before the fix and passes now.

How to run the tests (no database or server needed):

    cd backend
    pip install -r requirements.txt -r requirements-dev.txt
    python3 -m pytest tests/test_report_calc.py tests/test_manual_occupancy_excel.py tests/test_audit_*.py -q

## A. Fixed in this round

| # | What was wrong | Where | Test |
|---|---|---|---|
| A1 | Mix & match (segmented) bookings ignored the real departure date, the uninformed-early-checkout penalty split and the per-room Non-Org override in every report | `utils/report_calc.py` `_segment_room_nights`, `booking_financials` | `test_audit_report_calc.py` |
| A2 | Manual Excel export still dropped a booking with only penalty nights / a checkout extra bed in a month; repeated the advance on every room row; labelled a Non-Org-billed room "Org" | `utils/manual_occupancy_excel.py` | `test_audit_manual_excel.py` |
| A3 | Check-in re-priced a mix & match booking as every room x every night | `server.py` `check_in`, `Bookings.jsx` `computeCheckInTotals` | `test_mix_and_match_booking_is_not_billed_for_every_room_every_night` |
| A4 | A room left unassigned in a multi-room Non-Org booking was billed at the Org rate | `Bookings.jsx` `openCheckInDialog` / `calculateRoomChargeCategory`, `server.py` `check_in` | `test_non_org_booking_never_gets_an_org_rate_room` |
| A5 | Check-out without a room mapping divided the pre-extension room total by the post-extension nights (extension came out free) | `server.py` `check_out` | `test_extension_is_not_given_away_free_at_checkout_without_a_room_mapping` |
| A6 | Stay extension: ignored the per-room Non-Org override; extension nights of a mix & match stay never reached reports; "other room" extension scrambled the room lists; dropped the check-in extra bed from the balance; marked a not-yet-arrived guest's new room occupied | `server.py` `plan_extension`, `confirm_extension` | five `test_ext*` / `test_moving_*` tests |
| A7 | Amending to a cheaper stay stored "refund due" = whole price drop (not an overpayment) and the check-out screen deducted it from the bill; additional advance never reached the payments ledger; a mix & match booking kept its old night plan | `server.py` `amend_booking`, `Bookings.jsx` check-out dialog | four amendment tests |
| A8 | Cancelling when the refund preview had failed to load queued no refund; a double-submitted cancel queued two | `server.py` `cancel_booking`, `utils/report_calc.cancellation_refund`, `Bookings.jsx` `handleCancel` | five cancellation tests |
| A9 | Backups omitted payments, guests, users, feedback and toiletry data; a successful restore was reported as failed; date-range restore never found a backup; old-backup cleanup never deleted anything | `services/backup_service.py`, `services/restore_service.py`, `server.py` `restore_date_range` | four backup tests |
| A10 | The app-wide "backup overdue" warning could never appear | `App.js` `checkBackupStatus` | code reading |
| A11 | Check-out receipt PDF priced the stay at today's rate, not the booking's check-in-date rate | `utils/pdfUtils.js` `generateCheckoutReceipt` | parity check (84 cases) |
| A12 | Mix & match price preview read the legacy `cat_i_rate`/`cat_ii_rate` fields | `components/RoomSegmentSelector.jsx` | parity check |
| A13 | Failures with no on-screen signal: dashboard load, "needs attention" check, Org Data Form, mix & match availability, refund preview | `Dashboard.jsx`, `Bookings.jsx`, `RoomSegmentSelector.jsx` | code reading |
| A14 | Setup dropped the Non-Org rate it was given; a malformed check-out or extension date crashed with a 500 | `server.py` | `test_setup_*`, `test_checkout_with_a_garbage_date_*` |
| A15 | Route-ordering bug class: all 84 routes on every prefix checked, none shadowed; login/role enforcement checked on all 84 | `tests/test_audit_endpoints.py` | permanent tests |

## B. Needs the owner's decision (nothing changed)

- **B1 Check-out screen "Amount Due" is its own formula.** `Bookings.jsx` check-out dialog counts nights as elapsed time from the actual check-in moment to *now* (ignores the Checkout Date field, the booked nights and the uninformed-early-checkout penalty) and uses the booking-level Org flag (ignores per-room Non-Org). The backend stores a different total. Recommend: the dialog shows the backend's own figure.
- **B2 Late check-out.** Check-out bills booked nights; the reports count nights up to the actual check-out date. A check-out processed a day late adds an unbilled night of revenue and occupancy to every report.
- **B3 Check-in extra bed.** Screen and stored charge: Rs 75 per bed flat. Reports: Rs 75 x bed x night. Check-out bill: not included at all.
- **B4 Early check-in.** `Bookings.jsx` `handleCheckIn` blocks check-in before the booked date, which `CLAUDE.md` says must not be blocked. Separately, nights before the booked date are neither billed nor shown as occupied.
- **B5 Service data in the repository.** `backend/DEFENSE_DATA_ARCHIVE.csv`, `backend/migrations/DEFENSE_DATA_ARCHIVE_20260410_034916.csv` and six `backups/backup_full_20260409_*.json` files are committed and contain rank / service number / unit columns (rows look like test data). `backend/.env` is committed with a JWT secret.
- **B6 Backups live on the app server's own disk** (`backend/backups/`); `render.yaml` says `plan: free`, whose disk is wiped on every deploy.
- **B7 Dashboard "Net Revenue"** adds completed-stay receipts (which include the advance) to advances received — the advance is counted twice.
- **B8 Existing bookings may hold a wrong stored "refund due"** from past amendments (harmless now that the screen ignores it; correcting the stored values is a live-data change).
- **B9 Smaller items:** cancelling a checked-in booking removes its stayed nights from all reports; Monthly Report takes its room count from Settings while Room Occupancy counts actual rooms; staff can rename a room or change its category; `PUT /users/{id}` accepts a password of any length; no login rate limiting; `Dashboard.jsx` carries an unreachable second check-in/check-out form; the backup time set in the UI resets to 02:00 on every restart; legacy `def_civ_*` setting names and display-only `guest_rank`/`guest_unit` references remain; the 15 older API test files need a live server and send no login token.

## B2. Added after the first live audit check (18 Nov 2026)

- **Fixed: saving the Settings page re-priced old bookings.** After a scheduled rate change takes effect, Settings shows today's rate and sends it back on every Save, which overwrote the base rate that every booking dated before the change is priced from. Reproduced: a ₹1,000 July stay became ₹1,200 after an admin changed only the default advance. The live totals were intact at the time of the check (August still ₹2,29,900). Test: `test_saving_settings_after_a_rate_change_does_not_reprice_old_bookings`. Still open for the owner: typing a different rate into those fields (rather than saving unchanged ones) still rewrites the base rate and so past months — rate changes should only go through the Rate Schedule.
- **Fixed: "last backup" was read wrongly.** Backup records exist as real dates (before 11 May) and as text (after); Mongo sorts every date above every text value, so the newest backup came back as 11 April 2026. That also made "Restore last backup" pick the April one and the overdue warning misjudge. Worked out in Python now; tests `test_latest_backup_is_the_newest_*`, `test_backup_status_*`, `test_restore_last_backup_picks_the_newest`. Whether backups have actually been running since May can only be read from the new `exposure.backups` block of the audit check.

## B3. Owner's rulings on B1-B4 (18 Nov 2026) and what changed

- **B3 extra beds:** charged only at check-out for beds x exact days used. Check-in no longer bills or counts them; reports count only the check-out charge. This lowers every past month's reported revenue by the check-in component (about ₹40,600 across April-November in the 18 Nov audit data, much of it double-counted where a bed was also charged at check-out).
- **B2 late check-outs:** billed for nights actually stayed. Check-out now stores that bill (charge reason `late_checkout`); reports already counted those nights.
- **B1 check-out screen:** now shows the server's bill (`/bookings/{id}/checkout-quote`) instead of its own elapsed-time arithmetic.
- Also fixed in the same pass: the check-out screen's default date used UTC (a day behind between 00:00 and 05:30 IST); confirming a stay extension showed "Network error" after succeeding (`fetchBookings` did not exist).
- **B4 early check-in (owner chose option a):** the screen no longer blocks it; check-in moves to today, bills the extra night(s), and is refused with a message naming the booking if the room is taken for those nights.
- **B6 backups (owner chose a download button, plus a daytime/automatic backup):** "Download backup" on the Backup page (admin) saves a complete file to the computer used, without login passwords; each backup is now also kept compressed inside the database (`backup_snapshots`) so Restore works after a redeploy wipes the server's files; the daily backup is a FULL one at 14:00 IST, plus one is taken in the background whenever the app is in use and the last is over 20 hours old. A downloaded file is restored with `backend/scripts/restore_from_backup_file.py` (dry run by default).
- **B7 Net Revenue (owner chose cash received):** now advances + check-out payments − refunds, each payment once, in the IST month.
- **B9 smaller items (owner: "do all"):** cancelling after check-in blocked; room rename/category/floor admin-only (staff keep status); Monthly Report uses the real room count; editing a user needs an 8+ character password; login lockout (5 wrong passwords per username per address, 30 per address, 15-minute window); the dead second check-in/check-out/feedback forms removed from `Dashboard.jsx`; old rank/unit/service-status references removed from feedback screens, the booking message and PDFs (the PDFs keep their blank Army No/Rank/Unit columns for pen fill-in); the 15 old live-server tests retired to `tests/legacy_live_server/`. NOT done, because it needs a data migration and the owner's go-ahead: renaming the stored `def_civ_*` setting keys (including `def_civ_rate` inside `room_categories`).
- **Still open:** B5 service data in the repository (kept pending by the owner).

## C. Audit check (kept permanently)

`GET /api/reports/audit-check` (admin-only, read-only) and the "Audit check" button on the Reports page. Built as temporary tooling for this audit; made permanent on the owner's instruction as the data source for the month-end check in `docs/month-end-reconciliation-agent.md`.
