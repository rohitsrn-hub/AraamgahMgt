# Handoff — SARAI, for a full financial + quality audit

Written 2026-11-16, at the close of a ~2-month reactive investigation into one
month's (August 2026) reconciliation mismatch. This document is background for
whoever (human or AI) picks this up next. The actual audit instructions are in
the companion prompt, `docs/fable52-prompt-full-audit.md` — read this document
first, then that one.

## What SARAI is

Booking, billing and reporting app for one guesthouse (Araamgah) in Shillong.
**In live daily use** — every push to the working branch deploys straight to
production; staff use it the same day. Backend: FastAPI + MongoDB (async/
motor), almost entirely in one ~4,900-line `backend/server.py`, with shared
financial logic in `backend/utils/report_calc.py`. Frontend: React 18 (CRA +
CRACO), mainly `frontend/src/pages/Bookings.jsx`.

Read `/home/user/AraamgahMgt/CLAUDE.md` in full — it is the project's own
standing instructions (money rules, hard data-privacy rules, deliberate
non-bugs, conventions) and takes precedence over anything below if the two
ever disagree.

## Branch and deployment — the two traps that cost real time this round

1. **Work branch**: `claude/debug-rates-setup-flicker-Vnopx` is what a fresh
   session sometimes defaults to on checkout — it is stale by dozens of
   commits and missing this entire investigation. The real branch, with every
   fix described below, is **`claude/qa-audit-fixes`**. Always
   `git log --oneline -5` right after checkout and confirm you're looking at
   recent, relevant commits before trusting anything else about the repo's
   state — including `memory/HISTORY.md`'s own content, which differs
   completely between the two branches.
2. **Render backend service**: the real one the live Vercel frontend calls is
   **`earms-backend`** (confirmed via the live site's browser console network
   log). A separate, similarly-purposed-sounding service, `sarai-auth-test`,
   exists and was mistaken for production once already — a fix pushed to the
   right branch did nothing visible because the wrong Render service got
   manually redeployed. If a fix doesn't seem to take effect after a push,
   verify which Render service is actually being hit before assuming the code
   is wrong.

## What this investigation covered — and, importantly, what it didn't

This was **reactive**: it started from one specific symptom (the owner's
manual paper register for August 2026 not matching the app's numbers) and
followed that thread wherever it led, fixing each root cause as it was found.
It was not a systematic read of the whole codebase. The bugs below were all
in `backend/utils/report_calc.py` (the shared financial engine every report
is supposed to use) or in `backend/server.py`'s booking/report endpoints —
simply because that's where the symptom pointed. **Nobody has yet
systematically checked the rest of the application** — the booking-creation
flow, the stay-extension/amendment logic, the PDF generators, the frontend's
own price previews, the staff/room/toiletry/backup endpoints, auth, or
anything outside the direct path of these specific bugs — for either
financial correctness or general code quality. That gap is the reason for
the audit this handoff leads into.

## The bugs found and fixed this round (newest-relevant first)

All of these are in `claude/qa-audit-fixes`; see `memory/HISTORY.md` on that
branch for the full dated narrative with real numbers at each step.

1. **Monthly Report flat-rate bug.** It computed room rent as
   `total_nights × current settings rate`, ignoring `rate_history` entirely
   and ignoring each booking's actually-resolved charge — while the other
   three reports already summed real per-booking amounts. Fixed by routing it
   through `booking_financials()` like everything else.
2. **Early-checkout-penalty bug (accountant-ruled).** An early checkout the
   guest didn't inform staff about is billed for its full originally-booked
   nights as a penalty, but the room must still show vacant from the real
   departure onward. Both numbers had always come from one `nights` value, so
   correctly freeing the room early silently shrank the penalty to match.
   Worse: for a booking whose penalty nights land in a month with zero
   physical nights left in it, the booking was dropped from that month's
   report entirely (not just undercounted) by an `if nights == 0: continue`
   gate. Fixed by giving every booking two independent night counts —
   physical (`nights_in_period`, drives occupancy/vacancy, unchanged) and
   billed (`billing_nights_in_period`, drives money, uses the *original*
   planned checkout for this one penalty case) — and updating the inclusion
   gate in all four report endpoints accordingly.
3. **Per-room "Non-Org" billing override ignored by every report.** A room
   can be deliberately billed at the Non-Org rate regardless of the booking's
   overall `is_org` flag (`room_guest_mapping`'s `charge_category`) — honored
   at check-in/check-out when actually charging the guest, but
   `report_calc.py` never read it, so every report billed every room at the
   booking-level `is_org` status instead. Fixed via `_room_charge_categories()`
   in `report_calc.py`; each room in `booking_financials()`'s output now also
   carries its own resolved `is_org` so a caller bucketing money by Org/
   Non-Org (the Monthly Report's category tables) doesn't put an overridden
   room's now-correct money in the wrong bucket.
4. **Extra bed added at checkout never counted anywhere.** Separate from
   `extra_beds` (set at booking time), `extra_beds_checkout` /
   `extra_bed_charge_checkout` (set at checkout) was real, collected money
   that `report_calc.py` never read at all. Fixed by adding it into
   `extra_bed_charge`, attributed to whichever period contains the actual
   checkout date (the one date it's genuinely tied to — it has no stored
   date range of its own). Had to also fix the Monthly Report's separate,
   independent extra-bed total (`extra_beds_total × 75`), which would
   otherwise have silently stopped matching the other three reports.
5. **Stale "confirmed" bookings distorting room-occupancy.** A booking stuck
   at `status: "confirmed"` with `actual_check_in` never set (staff never
   ran it through the real check-in/checkout flow, whether because it was a
   backdated paper-register entry or just a forgotten no-show) still counts
   as occupying its room for its full original planned window in every
   report — and can overlap a different, real guest later placed in the same
   room, inflating that room's occupancy % with no real double-booking. One
   case (BK0943) overlapped **five** different real guests sequentially
   across one week. Shipped a permanent fix: `GET /bookings/stale-confirmed`
   powers a "needs attention" banner on the Bookings page, and
   `POST /bookings/{id}/close-stale` is a one-tap "Mark departed" action.
   Deliberately does NOT recompute money (every report already derives
   money from `status` + `actual_checkout_date`, never the stored total, so
   fixing those two fields alone fixes every report).
6. **A second bug class, found fixing #5: FastAPI route-ordering.** FastAPI/
   Starlette matches routes in registration order, not by specificity.
   `GET /bookings/{booking_id}` was registered *before*
   `GET /bookings/stale-confirmed`, so every call to the latter was actually
   being swallowed by the former — treating the literal string
   "stale-confirmed" as a booking ID, finding nothing, and 404ing. This
   silently broke the "needs attention" banner and a batch-cancel action for
   weeks before anyone noticed, because it fails open (no error surfaced to
   the user) rather than loud. Fixed by moving the specific route above the
   generic one. **Every other `/bookings/*` route was checked for the same
   conflict (none found) — but no other router prefix in the file (`/rooms`,
   `/reports`, `/staff`, `/guests`, `/settings`, etc.) has been checked yet.**
   This is a real, demonstrated bug class in this codebase and should be
   checked for systematically, not just in the one place it happened to bite.

All 7 stale-confirmed bookings this process surfaced were cross-checked by
the owner against the physical register and cancelled (6 were staff
double-entries or forgotten no-shows; one, BK0601, had already been handled
by hand). Final verified state: `GET /api/reports/reconcile?month=8&year=2026`
returns `consistent: true` with all four reports agreeing at ₹2,29,900 (up
from an originally broken ₹1,76,900), the early-checkout gap is ₹0, and 0
stale-confirmed bookings remain.

## Current state of `backend/utils/report_calc.py` (read it — it's short)

This file is the single source every report is supposed to use for money,
nights, and room resolution. Key exports after this round's changes:

- `nights_in_period(bk, start, end)` — **physical** occupancy nights. Drives
  vacancy/occupancy%. Unchanged in meaning from before this round.
- `billing_nights_in_period(bk, start, end)` — **money** nights. Identical to
  the above except for a checked-out booking with
  `charge_reason == "early_checkout_not_informed"`, which uses the original
  planned `check_out_date` instead. New this round.
- `booking_financials(bk, settings, start, end, room_maps)` — the main
  entry point. Returns both `nights` and `billed_nights` at top level, and
  each room in `rooms` carries `nights`, `billed_nights`, and (new) `is_org`
  (resolves `_room_charge_categories()`'s per-room override, falling back to
  the booking-level flag).
- `_room_charge_categories(bk)` — new helper reading `room_guest_mapping`'s
  per-room `charge_category` override.
- `extra_bed_charge` in the returned dict now includes both the booking-time
  `extra_beds` component (physical-nights basis) and the checkout-time
  `extra_bed_charge_checkout` component (attributed to whichever period
  contains the actual checkout date).
- `resolve_rooms`, `rate_components`, `effective_rate_settings`,
  `report_booking_query`, `build_room_maps` — unchanged.

Every one of these is covered by unit tests in
`backend/tests/test_report_calc.py` (44 tests as of this handoff — run
`cd backend && python3 -m pytest tests/test_report_calc.py
tests/test_manual_occupancy_excel.py -q`; these two files are pure Python,
no DB or server needed, per the note in `CLAUDE.md`). **No other test file in
`backend/tests/` has been confirmed to run without a live DB/server in this
environment** — treat them as a starting point to investigate, not as a
currently-green baseline.

## Deliberate design choices — verify the audit does NOT "fix" these

From `CLAUDE.md`, restated here because an audit prompt is exactly the kind
of thing that tends to flag them as bugs:

- **Overstay**: a guest still checked in past their planned checkout date
  does *not* block that room from a new booking. This is intentional — an
  overstay almost always means staff delayed processing the checkout, and
  Extend is the correct path if the guest genuinely stayed longer.
- **Early check-in**: staff can check a guest in before the booked check-in
  date, with no date restriction. Intentional — covers early walk-ins.

## Hard data-privacy rules — also worth an explicit audit pass

- Military rank, Army/service number, unit, or any other service data must
  never be stored or digitized (paper-only by policy). Guests tied to an
  organisation are represented only as `is_org` (bool) + `org_color`.
- Banned field names in new code: `guest_rank`, `def_civ_*`, and the
  `jco`/`or` report keys — a worthwhile `grep` across the whole codebase, not
  just new code, to confirm none have crept back in anywhere (test fixtures,
  old migration scripts, commented-out code).

## Not part of this audit's scope

`claude/n-category-support` is a separate branch with a fully built and
tested (in isolation) N-room-category feature, never merged. It's unrelated
to this investigation and shouldn't be touched by the audit unless the owner
asks for it specifically.
