# SARAI — Running Work History

Read at session start. Append a dated 2–3 line entry after every completed
feature or fix (newest first). Product terms, not code terms.

---

## 2026-09-26 — August 2026 reconciliation, continued: stale-confirmed-booking pattern found and fixed (branch: claude/qa-audit-fixes)
Root-caused the room-overlap issue flagged in the entry below. BK0943 was
never a code bug: it was entered into the app (via Migration Mode) 27 days
after its own check-in date and left at status "confirmed" forever, since
no one ever ran it through the real Check-In/Check-Out flow. A confirmed
booking counts as occupying its room in every report using its original
planned dates no matter how stale it gets, so when a different, real guest
was later placed in the same room, both were counted at once — that's what
inflated C1-04's occupancy to 106%+ for August (BK0943 alone overlapped 5
separate real guests across one week). A scan for the same pattern found 7
such bookings dating back to April 2026, of which 3 (BK0112, BK0356,
BK0943) actually caused this same room-overlap; the other 4 haven't yet
collided with anyone but remain latent risks. Only 2 of the 7 were
backdated entries — the rest were entered on time and simply never
followed up on, so "backdated data entry" was the wrong thing to fix in
isolation. Shipped a permanent fix: a "needs attention" banner on the
Bookings page listing every confirmed booking whose checkout date has
passed with no check-in ever recorded, a one-tap "Mark departed" action to
close one out with its real departure date (money is untouched — reports
already compute money from status + actual_checkout_date, never from the
stored total, so fixing those two fields alone fixes every report), and a
toast reminder right when a Migration-Mode entry is saved for an
already-over stay. The early-checkout-penalty revenue gap (Rs 9,675 across
4 August bookings) and the month-boundary revenue-split question both
remain parked for the owner's accountant, unchanged from below. The
temporary admin-only diagnostic endpoints/buttons from this investigation
(Debug button, Aug 2026 Diagnostics button, /reports/early-checkout-gap,
/reports/stale-confirmed-bookings) are still in place for now — remove
once the owner confirms no further use is needed.

## 2026-09-26 — August 2026 reconciliation: Monthly Report money bug found and fixed (branch: claude/qa-audit-fixes)
Owner's manual register didn't match the app's August 2026 numbers. Traced
it by comparing all four reports against each other and the register
photos: Monthly Report's grand total (Rs 1,76,900) disagreed with Room
Occupancy and Guest Details (both correctly Rs 2,07,700) by exactly
Rs 30,800 — Monthly Report was computing room rent as total-nights x
whatever the settings document holds right now, ignoring rate_history
entirely, instead of summing each booking's actual resolved charge like
the other two reports do. Fixed: now sums real booking_financials()
amounts per category, same as everywhere else. Also found two other real
issues, not yet resolved: (1) Room Occupancy correctly flags rooms C1-03
(187%) and C1-04 (106%) occupancy for August — a genuine sign that a
long-stay booking's date window overlaps with other, separately-registered
guests in the same room (confirmed one case, BK0943/C1-04, against the
register); (2) at least one legitimate month-crossover booking (BK0630,
2 real August nights) is silently missing from every report entirely —
under investigation, cause not yet confirmed. Also surfaced a genuine
policy question (deferred to the owner's accountant): a booking spanning
two months currently splits its revenue per-night across both months'
reports, which will never match a manual register that attributes the
whole stay to the check-in month — this was a deliberate earlier fix for
month-boundary undercounting, not an accident. Added a temporary
admin-only "Debug" button on the Bookings page (shows a booking's raw
record for phone-friendly diagnosis without dev tools) — remove once this
investigation concludes.

## 2026-08-14 — Date-versioned room rates for the 16 Aug rate revision (branch: claude/qa-audit-fixes)
Administration is revising room rates effective 16 Aug 2026. Rates weren't
date-aware at all before this — a single "current rate," applied to every
booking past and future the instant Settings was saved. Built a proper
rate-history engine instead: a booking bills entirely at whichever rate was
in effect on its own check-in date, locked in at check-in (a spanning stay
never splits per-night; an Extend keeps the original rate). New "Rate
Schedule" section on Settings lets the admin enter the new rate now with
16 Aug as the effective date — nothing changes today, existing/current
bookings are unaffected, only check-ins from 16 Aug onward pick it up
automatically. While wiring every money path onto the shared rate function
(the only way a rate change is guaranteed to apply everywhere at once),
found and fixed a real, previously-unknown bug: booking amendments were
silently using stale legacy rate fields with leftover debug prints in the
code — likely wrong ever since the rate-split migration. Also retired a
second, parallel rate-lookup helper that had been drifting from the
report engine.

## 2026-07-08 — Deferred audit items cleared (branch: claude/qa-audit-fixes)
Worked through everything deferred from the login-enforcement work: extension
pricing now reads the same rate settings as reports (was legacy fields, could
drift after a rate change); confirm-extension recomputes the charge and room
categories server-side instead of trusting the client's numbers; room status
now updates correctly on an immediate room move; fixed the exact datetime bug
that crashed backups, at its source. Also: booking numbers are now allocated
atomically (two simultaneous bookings could get the same number before);
rooms can't be deleted out from under an active booking or created/renamed
into a duplicate room number; a guest-history stats bug that silently
undercounted nights now logs instead of hiding it. Two items intentionally
left as open policy questions for the owner (overstay handling, early
check-in) rather than silently decided.

## 2026-07-06 — Server-side login enforcement (branch: claude/qa-audit-fixes)
Closed audit item #1: the server now actually checks who's logged in on every
one of its 79 actions (previously only the browser enforced login — anyone
who found the backend address could act with no password). Four tiers: open
(login/health only), any logged-in user (viewing), staff+admin (day-to-day
actions), admin-only (settings, users, staff records, backups/restore,
destructive deletes). Feedback submission now requires login. Fixed two
"Extend stay" requests that were silently missing their login token. Added
matching disabled-button+tooltip states on Rooms/Staff/Toiletry/Backup pages
so blocked actions look disabled instead of failing with a surprise error.
Owner confirmed Render's JWT_SECRET_KEY is set to a real value (2026-07-06) —
the one blocking safety gate is clear. Ready for owner to test all three
roles on the preview site and merge when satisfied.

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
