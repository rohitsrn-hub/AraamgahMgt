# SARAI — Running Work History

Read at session start. Append a dated 2–3 line entry after every completed
feature or fix (newest first). Product terms, not code terms.

---

## 2026-11-20 — October fully reconciled; root causes fixed (branch: claude/qa-audit-fixes)
October = ₹2,42,275 in all reports; register ₹2,42,650; the ₹375 is ₹450 of beds on
1-Nov check-outs (counted in November by ruling) less BK1031's ₹75 that the register's
amount column omits. Payment fields now match the register (owner confirmed BK1286
₹4,200, BK1159 ₹1,200, BK1279 ₹1,200). Built: payments-log sync correction (+800, +500,
−400, dated to the original month; Net Revenue changes), Audit check `cash_log_differs`,
check-out refuses a payment differing from the bill without a reason, Room Occupancy
shows money actually paid. Root causes in docs/october-2026-root-causes.md. Open:
Non-Org rule at check-in; beds on month-crossing stays.

## 2026-11-19 — October vs paper register: ₹242,275 vs ₹242,650; payments follow the register (branch: claude/qa-audit-fixes)
After the second Apply the four reports agree at ₹2,42,275 (358 room-days, 133
bookings; BK1293 cancelled). The register's amount column totals ₹2,42,650. The
₹375 gap is exactly four extra-bed top-ups not yet applied (BK1267 150, BK1320
150, BK1324 75, BK1325 75 = 450) less BK1031's ₹75 bed, which the register
left out of its amount column but included in its balance (app is right).
Register shows every October guest fully paid (advance + balance); the app's
payment fields were off for BK1286 (₹800 missing), BK1159 (₹500 missing) and
BK1279 (₹400 extra). Corrections now set those to the register's figures (the
dashboard cash log, a separate collection, is untouched). BK1170 is a September
stay and is not in the October register. Pending: owner's Apply.

## 2026-11-19 — Corrections applied (14 of 20); BK1293 and 5 extra beds fixed up for a second Apply (branch: claude/qa-audit-fixes)
Owner pressed Apply at 00:52 on 19 Nov (explains the one-off report mismatch
that run). Applied: both penalties waived, 9 Org-rate fixes, extra beds on
BK1280/BK1151, advances on BK1159/BK1279. Skipped: BK1293 (its stored bill is
₹21,000 for 35 nights, my guard expected the October part, ₹10,800 — now
corrected) and 5 extra beds (BK1267, 1320, 1324, 1204, 1325) which already had
a smaller bed charge — now a "top up to the register's amount" action. Nothing
further changes until Apply is pressed again.

## 2026-11-19 — October re-check after corrections: reports agree at ₹2,53,000; some items open (branch: claude/qa-audit-fixes)
Second run the same day: all four reports agree (₹2,53,000, 376 room-days, 134
bookings); the earlier disagreement did not repeat and was most likely the
corrections being applied while the check ran. Reported = billed for all 133
October check-outs (₹2,47,950). Uninformed early check-outs now 0 and the Org-rate
differences are gone. Still open: BK1293 still counted (134 bookings, so not
cancelled — reason unknown), BK1204's extra bed apparently not applied,
₹1,500 not collected (BK1286 800, BK1159 500, BK1170 200), ₹475 over-collected
(BK1279 400, BK1204 75). Register grand total not yet compared with ₹2,53,000.

## 2026-11-19 — October audit re-run: four reports disagree; Audit check now says which bookings (branch: claude/qa-audit-fixes)
Re-run on 19 Nov: room-days agree (376) but revenue differs by report
(allotment ₹2,54,625, guest details ₹2,53,825, monthly ₹2,53,000, occupancy
₹2,52,725). Corrections were NOT yet applied (same short/over-collected lists as
before). BK1293 as a checked-out late stay (18 nights, ₹10,800 in October) was
tested and keeps all four reports equal, so it is not the cause by itself. The
Audit check now adds a "disagreements" block when the reports differ: per-booking
and per-room amounts against a direct calculation, plus whether the totals
changed between two runs (edits in progress). Cause still open.

## 2026-11-18 — Administrator "waive penalty" at check-out; Non-Org confirmation at check-in (branch: claude/qa-audit-fixes)
Owner chose to keep the early-departure rule (full booked stay billed when the
guest did not announce leaving early at check-in) but let an administrator
waive it case by case: a checkbox on the check-out screen (admin only, shows
the rupees waived, saved on the booking with who did it; staff get a refusal).
Check-in now asks staff to confirm each time a room will be billed at the
Non-Org rate and says why, to cut wrong Non-Org marks (the cause of ₹4,600
in October).

## 2026-11-18 — October register reconciled; corrections, overdue reminder and late check-out guard built (branch: claude/qa-audit-fixes)
Owner's paper register for October was compared line by line with the app.
The app was ₹16,500 higher: BK1293 (₹10,800, not in the register, so the guest
did not stay), Non-Org rates billed where the register used Org (₹4,600),
uninformed-early-departure penalties (₹2,000), less 7 extra beds the register
had but the app did not (₹900). Owner ruled the register correct and the
penalties waived. Built (nothing in live data changes until the owner presses
Apply on the Reports page): Preview/Apply/Undo for 20 named bookings (cancel
BK1293, 9 Org-rate fixes, waive BK1138/BK1184 penalty, 7 extra beds, 3 advance
splits with the cash unchanged); each is skipped unless the money engine then
gives exactly the register's amount. Also: Monthly Report room-rent lines now
use real per-category totals (they used stale base rates and did not add up);
a red "still checked in past the planned check-out date" reminder on Bookings
(Check out opens at the booked date; Extend alongside); a check-out dated 2+
nights after the booked date now needs a confirmation showing the extra
rupees (BK1293 was billed 31 extra nights by a default of today's date).
Open for the owner: BK1226, BK1293's ₹400 advance, general Non-Org check-in rule,
penalty policy going forward.

## 2026-11-18 — Approved live-data corrections built, with originals saved and an undo (branch: claude/qa-audit-fixes)
Owner approved correcting what the October check found, provided the original
values are kept until the manual register is reconciled. Built as an admin
action on the Reports page (Preview / Apply / Undo last): it fixes the stored
bill of two bookings (BK1284 ₹1,400 → ₹1,200; BK1032 ₹1,625 → ₹2,325) and
resets a stale "refund due" on 10 active bookings. Each record is changed only
if it still holds what the audit saw, a full backup is taken first, every
original value is saved in the data_corrections collection and on the booking's
own log, and Undo restores them. Nothing has been changed yet — it happens
when the owner presses Apply. Reports are unaffected. The other older
bookings whose stored bill differs (pre-ruling late check-outs and extra beds)
are deliberately left alone until the register is reconciled.

## 2026-11-18 — October 2026 month check: reconciles; ₹7,900 not collected still to be traced (branch: claude/qa-audit-fixes)
First full month check (run on 18 Nov, covers 1-31 Oct). October revenue is
₹2,50,625 across 134 bookings and 362 room-days, identical in all four
reports. It was ₹2,52,350 before the extra-bed ruling; the ₹1,725 drop is
exactly 23 bed-nights at ₹75, as expected. Of 133 stays that checked out in
October, 2 differ from their stored bill: BK1032 (late check-out, stored bill
₹700 low, cash matches the reports) and BK1284 (stored ₹1,400 vs ₹1,200: its
check-in record said Cat I for a Cat II room; the guest paid ₹1,200; new code
ignores that stale field). ₹7,900 of reported October value has no matching
payment and ₹850 was collected beyond it — the audit check now lists the
bookings behind both so they can be chased. Backups: 18 of 20 backup files
were already gone from the server (redeploys wipe them) and only 2 backups
had been taken in 30 days (a sleeping server never ran the 2 am job), so
until today there was effectively no usable backup; no copy has been
downloaded to a computer yet. The backup list now marks which backups can
really be restored. Stored refund-due values on 10 active bookings are still
wrong but nothing displays or uses them any more.

## 2026-11-18 — Net Revenue fixed and the small clean-up items done (branch: claude/qa-audit-fixes)
Owner chose "cash received" for the Dashboard's Net Revenue: advances were
being counted twice (a ₹1,000 stay showed ₹1,400); it is now advances plus
check-out payments minus refunds, once each, by IST month. Also done at the
owner's request: a guest who has checked in can no longer be cancelled (use
Check Out); only administrators can rename a room or change its category; the
Monthly Report counts the rooms that really exist; editing a user needs an
8+ character password; login locks out after repeated wrong passwords from
one address; dead second check-in/check-out forms removed from the Dashboard;
old rank/unit/service-status references removed from feedback screens, the
booking message and PDFs (printed blank columns kept for pen entry); the 15
old live-server tests retired so the default test run is green (141 pass);
the audit check now also shows whether backup files survive redeploys. Left
alone: renaming the stored def_civ_* setting keys (needs a data migration) and
the service-data files in the repository (pending).

## 2026-11-18 — Backups that survive, a download button, and early check-in allowed (branch: claude/qa-audit-fixes)
Owner asked for a backup saved on the computer that clicks a button, and for
the automatic backup to run in the daytime if the 2 am one can't. Done: an
admin "Download backup" button on the Backup page saves a complete file (no
login passwords) and the month-end check now reminds to do it; every backup
is also kept inside the database, so Restore still works after a deploy wipes
the server's files; the daily backup moved to 14:00 IST and one is also taken
in the background whenever someone is using the app and the last is over 20
hours old (a sleeping free server can't run a 2 am job — to be confirmed in
the Render dashboard, the provider's docs could not be reached from here);
the backup time set on the screen now survives a restart; a downloaded file is
restored with backend/scripts/restore_from_backup_file.py. Early check-in
(option a): the screen no longer blocks it; check-in moves to today, bills the
extra night(s), and refuses with the clashing booking's number if the room is
taken. Service-data files in the repository: left pending at the owner's
request.

## 2026-11-18 — Owner's rulings applied: extra beds at check-out only, late check-outs billed for nights stayed (branch: claude/qa-audit-fixes)
Owner ruled: (1) extra beds are charged at check-out for the exact beds and
days used — a bed noted at check-in is not a charge; (2) late check-outs are
billed for nights actually stayed; (3) the Audit check covers only the
previous closed month. Done: reports no longer count check-in extra beds (past
months' reported revenue drops by that amount — about ₹40,600 over Apr-Nov, so
the baseline totals in the entry below are now the OLD figures); check-out
now bills late nights and extra beds through one calculation, and the
check-out screen shows that same figure instead of its own (which could be a
night off); the screen's date default no longer lags a day in the early
morning; confirming a stay extension no longer shows a false "Network
error"; the receipt prints the stored bill; and the Audit check now audits
only last month, with a new month-by-month baseline to be recorded at the
next run. Bookings checked out before today keep their old stored bills.

## 2026-11-18 — First live month-end audit check: all months reconcile; two more defects fixed (branch: claude/qa-audit-fixes)
Owner ran the Audit check against the live database. The four reports agree
with each other in every month — baseline totals recorded here for next
month's comparison: Apr ₹1,47,750, May ₹2,08,175, Jun ₹1,98,375, Jul
₹2,01,625, Aug ₹2,29,900 (unchanged from the register-verified figure),
Sep ₹2,56,825, Oct ₹2,52,350, Nov so far ₹1,91,900. Against what guests were
billed, 176 checked-out bookings differ by ₹93,750 in total: about ₹53,500 is
late check-outs (the cash collected matches the reports in most of the listed
cases) and about ₹40,600 is extra beds taken at check-in, which the listed
cases show were reported as revenue but not collected — both still waiting on
the owner's ruling. Five bookings (-₹1,000) were unexplained and could not be
identified because the check only listed the largest 40; the check now lists
every unexplained booking and splits everything by month. Fixed: saving the
Settings page after the 16 Aug rate change re-priced every earlier booking
(reproduced, not yet triggered live); and the "last backup" shown was the
wrong record (it read 11 April), so whether backups have run since May is
still unknown until the next check shows the corrected figure.

## 2026-11-16 — Audit check button made permanent; month-end procedure written (branch: claude/qa-audit-fixes)
The admin-only "Audit check" button on the Reports page is no longer
temporary — owner's decision. It is the data source for a monthly routine:
it shows, for every month, whether the four reports agree, which checked-out
bookings are reported at a different amount than they were billed (and why),
and unpaid balances. The written procedure for a Claude session to run that
check at each month end is docs/month-end-reconciliation-agent.md. (The
entry below still calls the button TEMP — that is superseded by this one.)

## 2026-11-16 — Full-codebase audit: 15 fixes, 9 questions for the owner (branch: claude/qa-audit-fixes)
First systematic read of the whole app rather than one symptom's path. Fixed,
each with a test that failed before: mix & match bookings were mis-reported
(ignored early departure, penalty and Non-Org override) and over-billed at
check-in (every room x every night); a Non-Org booking's unassigned room
billed at the Org rate; stay extensions mispriced or missing from reports;
a shortened booking recorded a bogus "refund due" that the check-out screen
then took off the bill; a cancel could queue no refund (or two); the Excel
export still dropped penalty-only bookings; receipts printed today's rate;
backups left out payments/guests/users and a successful restore said
"failed"; the "backup overdue" warning could never show. Check-in, check-out,
extend and amend now all price rooms through one function in report_calc.py.
Every route on every prefix checked for the ordering bug (none) and for login
and role enforcement, as permanent tests; endpoint tests now run with no
database (backend/tests/inprocess.py). NOT decided, waiting on the owner
(docs/audit-2026-11-findings.md, section B): the check-out screen's own
"amount due" formula, late check-outs counted as unbilled nights, check-in
extra-bed pricing, early check-in blocked on screen, and service-data files
sitting in the repository. A TEMP admin-only "Audit check" button is on the
Reports page for the owner to run against live data — remove it and
/reports/temp-audit-2026-11 once the result is back.

## 2026-11-16 — Temp diagnostic tooling removed, reconciliation cleanup complete (branch: claude/qa-audit-fixes)
With the Aug 2026 investigation fully closed, removed the one-off tools it
needed along the way: the per-row "Debug" button, the "Aug 2026
Diagnostics" button, the "Cancel 7 Flagged Bookings" batch action, and the
two admin-only temp report endpoints behind them. Kept the lasting
results: the permanent "needs attention" banner + "Mark departed" action
on the Bookings page, and the pre-existing /reports/reconcile check.

## 2026-11-16 — Aug 2026 reconciliation saga fully closed out (branch: claude/qa-audit-fixes)
All 7 stale-confirmed bookings from the earlier scan are gone: owner
cross-checked each against the physical register ("DETAILS OF ECSAG
QUERY") — every one was a staff double-entry or a no-show no one ever
cancelled, none a real unclosed stay — then cancelled all 7 through the
fixed bulk-cancel action (one, BK0601, had already been done by hand).
Confirmed clean end state: reconcile still consistent across all four
reports at ₹2,29,900 (down from the ₹2,33,500 peak while those phantom
bookings were still counted, and up from the original, badly broken
₹1,76,900 this whole investigation started from), ₹0 early-checkout gap,
0 stale-confirmed bookings, 0 room-overlaps. This closes the reconciliation
that began with the Monthly Report flat-rate bug: every money and
room-overlap issue found along the way is now fixed and verified against
real production data, not just unit tests. Found along the way, also
during this cleanup: the real deployed backend is `earms-backend` on
Render — a separate, same-named-sounding `sarai-auth-test` service had
been mistaken for it once already; worth remembering which one is real
next time a fix doesn't seem to take effect.

## 2026-11-16 — Stale-booking cleanup: "needs attention" banner and bulk-cancel were silently broken (branch: claude/qa-audit-fixes)
Owner tried the "Cancel 7 Flagged Bookings" cleanup action (after confirming
against the physical register that all 7 were mistakes/no-shows) and got
"Booking not found" immediately. Root cause: GET /bookings/stale-confirmed
was registered AFTER GET /bookings/{booking_id} — FastAPI matches routes in
registration order, and {booking_id} matches any single path segment
including the literal word "stale-confirmed", so every call was actually
hitting get_booking("stale-confirmed") and 404ing. This had been broken
since both were added in September: the Bookings page's "needs attention"
banner has never actually shown (it fails open, no error toast), and the
one booking (BK0601) that did get cancelled was evidently done by hand,
not through this feature. Fixed by moving the route above the generic
{booking_id} one; audited every other /bookings/* route for the same
conflict (none found). Owner can now re-run the bulk-cancel for the
remaining 6 (BK0112, BK0331, BK0453, BK0356, BK0943, BK0929).

## 2026-09-27 — August 2026 reconciliation: verified fixed end to end (branch: claude/qa-audit-fixes)
Owner re-ran the Aug 2026 Diagnostics button after all fixes deployed:
reconcile still consistent across all four reports (₹2,33,500, up from the
original ₹1,76,900), and the early-checkout-gap scan now returns ₹0 across
0 bookings (was ₹9,675). The full multi-week reconciliation — Monthly
Report's flat-rate bug, the accountant's early-checkout-penalty ruling, the
per-room Non-Org override bug, and the checkout-extra-bed bug — is
confirmed resolved with real production numbers, not just unit tests. Also
fixed the "Aug 2026 Diagnostics" popup itself, which was silently
truncating its own text once the stale-bookings list grew (window.prompt()
has a length limit on some mobile browsers) — now copies the full text to
the clipboard instead. Remaining: 7 stale-confirmed bookings from the
earlier scan are a data-entry backlog, not a code bug — owner is clearing
them via the new banner/Mark-departed UI directly, using the register to
tell a real unclosed stay (Mark departed) from a duplicate entry (Cancel —
flagged BK0453/BK0454 as likely the same guest's stay entered twice).

## 2026-09-27 — August 2026 reconciliation, truly concluded: two more revenue gaps found and fixed (branch: claude/qa-audit-fixes)
After the early-checkout-penalty fix recovered ₹7,800 of the ₹9,675 gap,
₹1,875 still didn't reconcile on BK0754/BK0689/BK0630. Pulled their raw
records and found two more real, pre-existing bugs — neither related to
early checkout, both silently affecting every report for any booking that
ever used them, not just these three: (1) a per-room "Non-Org" billing
override (room_guest_mapping's charge_category) was honored when actually
charging a guest at check-in/check-out, but no report ever read it — every
report always billed every room at the booking's overall Org/Non-Org status
instead. BK0754 (Org booking, one room deliberately billed Non-Org) showed
₹1,000 less revenue than was actually collected. (2) An extra bed added at
CHECKOUT time (separate from one set at booking time) was real, collected
money that no report ever counted — BK0630's ₹75 was exactly one such
bed-night. Both fixed in report_calc.py, the shared engine every report
must use; also had to fix the Monthly Report's extra-bed money, which
computed itself independently and would have quietly stopped matching the
other three reports the moment a booking had a checkout-added bed. 17 new
unit tests added this round (26 total for the week's reconciliation work).
All three flagged bookings now compute their exact real billed amount.

## 2026-09-26 — August 2026 reconciliation, concluded: accountant's ruling implemented (branch: claude/qa-audit-fixes)
Owner got a ruling from the accountant on the two questions parked earlier.
(1) Month-boundary split — a stay crossing months splits its revenue
per-night between them (e.g. 29 Jul -> 2 Aug bills 3 nights to July, 1 to
August). Checked this against the existing code and it already does exactly
this via nights_in_period() — no change needed, just confirmed. (2) An
early checkout the guest didn't inform staff about must still be billed for
its full originally-booked nights as a penalty, but the room must show
vacant from the real departure onward. This DID need a fix: occupancy and
money had always come from the same "nights" number, so correctly freeing
the room early was also silently shrinking the penalty to match — this was
the ₹9,675 gap found earlier. Worse, for a month-crossing booking (BK0630)
whose penalty nights land in a month it has zero physical nights left in,
the booking was dropped from that month's report entirely rather than
undercounted. Fixed in report_calc.py by giving every booking two
independent night counts: physical nights (unchanged, drives vacancy) and
billed nights (money basis, uses the original planned checkout for this one
penalty case, split at month boundaries the same as a normal stay). Updated
all four reports' inclusion check so a booking can appear in a month solely
for its billed nights even with zero physical nights there. Extra-bed
charges are untouched (no ruling covers them). Added 8 unit tests. Next
time the Aug 2026 Diagnostics button is run, the early-checkout-gap section
should show ~₹0 vanished (it previously showed ₹9,675) and reconcile's
total revenue should be about ₹9,675 higher than before, still consistent
across all four reports.

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
