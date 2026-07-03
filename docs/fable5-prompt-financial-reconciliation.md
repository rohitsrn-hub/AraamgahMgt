# Fable 5 Prompt — SARAI Financial Report Reconciliation

Copy everything below the line into a fresh Fable 5 session running in the SARAI project folder, with the four Excel workbooks attached or placed at the listed paths. Recommended effort: `xhigh`.

---

I'm the owner-operator of SARAI, a guesthouse management app (FastAPI + MongoDB backend in `backend/server.py`, React frontend in `frontend/src/`). Real money is reconciled against these reports every month, so correctness matters more than speed. The app's four financial reports disagree with each other, and I've done the forensic analysis for you — your job is to find and fix the underlying bugs, not to re-derive the analysis.

## The problem

SARAI generates four reports from the same booking data: Room Allotment Report, Guest Details Report, Room Occupancy Report, and Monthly Report. For May and June 2026 they produce three different revenue totals for the same month:

| | May 2026 | June 2026 |
|---|---|---|
| Room Allotment + Guest Details (always agree; treat as ground truth) | ₹2,03,450 · 158 bookings · 329 nights | ₹1,82,675 · 145 bookings · 327 nights |
| Room Occupancy Report | ₹1,78,600 · 157 bookings (short ₹24,850) | ₹1,68,900 · 141 bookings (short ₹13,775) |
| Monthly Report grand total | ₹1,93,900 | ₹1,75,150 |

The Room Allotment and Guest Details reports agree to the rupee in both months — their numbers are the reference. The bugs are in how the Room Occupancy Report and Monthly Report derive their totals. The fixed reports must also line up with the manual paper ledger, which is the basis of my real-world accounting.

## Evidence files (already analyzed — read these first)

- `May2026_Reconciliation.xlsx` and `June2026_Reconciliation.xlsx` — sheets: **Summary**, **SARAI Internal Mismatches** (per-booking diffs between reports), **Missing from Occ Report** (bookings absent from Room Occupancy), **Person Case Studies** (worked examples).
- `Room_Occupancy_May_2026.xlsx` and `Room_Occupancy_June_2026.xlsx` — the app's actual Room Occupancy output for both months.

## Start here: the ₹75 signature

34 of 38 mismatched bookings in May and 18 of 20 in June have identical Nights in both reports but Revenue short by an exact multiple of ₹75 — the extra-bed rate. That is the cleanest signature in the data: the Room Occupancy Report almost certainly computes per-booking revenue as `rate_per_day × days` and drops `extra_beds × nights × 75`, while Room Allotment reads the stored final amount. Confirm this first — it explains most of the gap — then move to the messier causes.

Verification cases: May BK0146 (Occ ₹500 vs Alloc ₹575), BK0123 (₹2000 vs ₹3200), BK0145 (₹1500 vs ₹2175), BK0218 (₹2700 vs ₹3675); June BK0463 (₹5000 vs ₹7250, 9-member family), BK0182 and BK0366 (both ₹1200 vs ₹1875).

## The other five confirmed defects

2. **Bookings missing entirely from Room Occupancy.** May: BK0091, BK0090, BK0141, BK0147 all started 2026-04-28/29 and carried into May — a month-boundary filter that tests only the booking's start date instead of night-level overlap. BK0331 is also missing with no cross-month explanation. June: BK0453, BK0356, BK0540, BK0541 are missing but do NOT span a month boundary — same symptom, possibly a different trigger (status flag, cancellation, room reassignment). Find the month-selection query and check whether it filters `start_date BETWEEN month_start AND month_end` rather than date-range overlap.

3. **Multi-room bookings under-represented.** May BK0234 occupies 4 rooms (C2-15, C2-09, C1-01, C2-08) in Room Allotment but appears under only 2 of them (C2-09, C2-15) in Room Occupancy. Check the loop/join over a booking's room list when building each room's booking table.

4. **Same Booking ID, genuinely different Nights between reports.** May: BK0135 (1 night/₹600 vs 3 nights/₹1,800), BK0103 (4 vs 6), BK0342 (4 vs 2). June: BK0235, BK0358, BK0547, BK0404, BK0165, BK0267, BK0548 (full list in the reconciliation workbooks). Trace both report code paths to see whether they read the same record or two sources that drift (e.g. booking document vs a room-assignment/segment structure), and whether post-check-in amendments update one path but not the other. Possible genuine duplicate: May BK0103 and BK0273, both Gulshan Kumar, same room C2-08, overlapping dates — check whether that's an erroneous duplicate booking.

5. **Monthly Report contradicts itself.** Its Command-wise Occupancy table totals 314 days (May) / 310 (June) while its own License Fee Calculation table (Cat I + Cat II + Non-Org) sums to 397 / 376 — gaps of 83 and 66 days inside one report. The two tables are two views of the same day-count and must reconcile; find the two aggregations and the filter difference between them (likely the same month-boundary bug applied inconsistently).

6. **Booking-count header off.** Room Occupancy header says 157 vs 158 (May) and 141 vs 145 (June). June's gap of 4 matches its 4 missing bookings; May's gap of 1 does not match its 5 missing bookings — so the "Total Bookings" header figure may have a second, independent counting bug.

## Constraints

- The booking IDs above are evidence for locating each bug, not the repair list. Fix the underlying causes so every affected booking — listed or not — comes out right. Do not hard-code or special-case any booking ID.
- Do not modify booking data in the database to make reports agree; fix the report logic. If you find genuinely corrupt data (e.g. the possible BK0103/BK0273 duplicate), report it to me with evidence rather than deleting it.
- Backend work happens in the report endpoints in `backend/server.py` and helpers in `backend/utils/`; frontend PDF generators live in `frontend/src/utils/pdfUtils.js`. Note the codebase was recently migrated from old field names (`def_civ_*`, `jco`/`or` keys) to new ones (`non_org_*`, `org_cat_i`/`org_cat_ii`) — stale field reads returning 0 or a fallback default are a plausible contributor, especially in the Monthly Report.
- Work on the current branch. Commit in logical units with clear messages. Do not push to main/master.

## Definition of done

1. One shared calculation function derives per-booking revenue (room rent + license fee + extra beds) and every report consumes it — no report recomputes independently.
2. One shared date-overlap predicate decides month membership: a booking is in month M iff at least one night falls within M.
3. Multi-room bookings appear under every room they occupy, in every report.
4. All four reports produce identical total revenue and total nights/room-days for the same month.
5. A regression check exists — an automated test or a `/reconcile` admin endpoint — that re-derives all four reports' headline numbers from the same source data and fails loudly on divergence, so this cannot silently reappear in July.
6. You demonstrate correctness against the evidence: for each May and June test case above, show the corrected value matching the Room Allotment figure, and show the corrected month totals matching ₹2,03,450 / ₹1,82,675.

## Working style

You are operating autonomously; I am not watching in real time. For reversible code changes that follow from this request, proceed without asking. Pause only for a destructive action, a real scope change, or input only I can provide. Before ending your turn, if your last paragraph is a plan or a promise ("I'll…"), do that work now.

Before reporting progress, audit each claim against a tool result from this session — only report what you can point to evidence for. If a test fails, quote the output. Establish a verification habit: after fixing each root cause, re-run your reconciliation script against the evidence workbooks before moving to the next.

Lead your final summary with the outcome: which of the six defects you confirmed, what each root cause was, and whether the four reports now reconcile — then the supporting detail in complete sentences. Give each file, function, and booking ID its own plain-language clause; no shorthand or arrow chains.
