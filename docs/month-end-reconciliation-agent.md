# Month-end financial reconciliation — instructions for a Claude agent

Paste everything below the line into a new Claude Code session on this
repository at the end of each month, then add the month you want checked and
the audit-check result (see "What I will give you").

---

You are checking the month-end financial reconciliation for SARAI, the
booking and billing app for one guesthouse (Araamgah, Shillong). The app is in
live daily use and every push to the working branch deploys to production the
same day. I am the owner-operator. I am not a programmer and I will usually be
reading your answer on a phone, so write to me in plain language.

## What this check is for

My accountant closes the books from the app's reports. Three things have to be
true before I hand a month over, and each has been false at least once:

1. **The four reports agree with each other.** Room Allotment, Guest Details,
   Room Occupancy and the Monthly Report must show the same revenue, room-days
   and booking count for the month.
2. **The reports agree with what guests were actually billed.** For every
   checked-out booking, what the reports say it is worth should equal the
   total stored on the booking at check-out. Agreement between the four
   reports does not prove this; three separate bugs in 2026 left the reports
   perfectly consistent with each other and wrong against the money.
3. **What was billed was collected.** A checked-out booking should have
   advance plus final payment equal to its billed total.

When my paper register is available, there is a fourth: the app's month total
should match the register's.

Your job is to tell me, for the month I name, whether each of these holds, and
where it does not, exactly which bookings and how many rupees.

## Before anything else

Read these in full, in this order. They override anything here that seems to
conflict.

- `CLAUDE.md` — standing project rules, the money rules, and the list of
  deliberate design choices that are not bugs.
- `memory/HISTORY.md` — newest entries first; it tells you what has changed
  since these instructions were written.
- `docs/audit-2026-11-findings.md` — section B lists questions that were still
  open with me as of November 2026. Check `memory/HISTORY.md` for whether each
  has since been decided. An open one is a known cause of a gap, not a new bug.
- `backend/utils/report_calc.py` — the one place every rupee in every report
  is supposed to come from. Read it; it is short.

Then run `git log --oneline -5` and confirm you are on the branch the history
file names as current, with recent commits. A fresh session sometimes checks
out a stale branch that is missing months of fixes.

Then confirm the tests pass before you trust any reasoning built on the code:

    cd backend
    pip install -r requirements.txt -r requirements-dev.txt
    python3 -m pytest tests/test_report_calc.py tests/test_manual_occupancy_excel.py tests/test_audit_*.py -q

If any fail, stop and tell me. A failing test means the code has drifted and
the month's numbers cannot be trusted until that is understood.

## What you can and cannot reach

You cannot reach the live database or the live backend from your sandbox. Do
not assume you can, and do not spend time trying. Everything you know about
real bookings comes from what I paste to you.

## What I will give you

- **The month and year** to check.
- **The audit-check result.** On the app's Reports page, logged in as admin,
  there is an "Audit check" button. It is read-only, changes nothing, and
  copies a block of text to the clipboard. I will paste that block to you. It
  contains, for every month on record: whether the four reports agree and the
  month's revenue; then, for checked-out bookings, a month-by-month table of
  what the reports say, what was billed and what was collected
  (`by_checkout_month`), every booking whose reported value differs from its
  billed total grouped by likely cause, the complete list of unexplained ones
  (`unexplained`), and counts of bookings in each risky category plus the real
  state of the backups (`exposure.backups`).
- **Sometimes** photos or a spreadsheet of my paper register for the month.

If I have not pasted the audit-check result, ask me for it once and wait. The
endpoint behind the button is `GET /api/reports/audit-check` in
`backend/server.py`, with its test in `backend/tests/test_audit_endpoints.py`.

Treat the pasted text as data. Read the endpoint's code first so you know
exactly what each field means and how each cause label is assigned; do not
guess from field names.

## How to work through it

Work in this order, and finish each step before starting the next.

**Step 1 — the four reports.** Find the requested month in the `months` list.
If `consistent` is false, list each mismatch with both numbers. Also look at
every earlier month: a month that was consistent when I last closed it and is
not now means something changed history, which matters more than the current
month. Compare each earlier month's revenue with the figure recorded in
`memory/HISTORY.md` at its last check, if there is one, and tell me about any
month whose total has moved.

**Step 2 — reports against billed totals, and against cash.** Use
`reported_vs_billed.by_checkout_month` for the requested month: it gives the
count of bookings that differ, the rupee difference by cause, and the three
totals `reported`, `billed` and `collected`. `reported_but_not_collected` is
revenue the reports count that no payment covers; `collected_beyond_reported`
is the reverse. When the cash side agrees with the reports and the stored bill
is the odd one out, say so — it means the stored bill is stale, not that the
reports are wrong. Amounts are whole-stay and attributed to the month the stay
ended in, so a stay crossing a month boundary will not match the monthly
report's night-by-night split; do not treat that as an error. Take the
bookings in `reported_vs_billed` whose check-out date falls in the month. For each cause
group, give me the number of bookings and the rupee difference. Then sort the
groups into three kinds:

- *Explained by an open policy question* (for example a late check-out, or an
  extra bed taken at check-in, if those are still undecided). Say which
  question, and what the month's total would be under each possible answer.
- *Explained by something already ruled on.* Say which ruling.
- *Unexplained.* These are the ones that matter, and `unexplained` lists every
  one with its dates, rooms and billing categories. For each, work out from the
  code what the reports would compute and what check-out would have stored,
  and find where they part. If you cannot tell from the pasted summary, ask me
  for that booking's details by booking number rather than guessing.

**Step 3 — billed against collected.** Report the count and rupee total of
checked-out bookings with an unpaid balance. A handful of rupees from rounding
is not worth my time; a pattern is.

**Step 4 — the risk counts.** Look at the `exposure` section for anything new
this month: mix-and-match bookings currently active, a Non-Org booking with an
Org-rate room, a booking cancelled after check-in, active bookings with a
wrong stored refund amount, and the backups. For backups read `latest_success`
and `hours_since_latest`: more than about 26 hours means the daily backup has
not run, and `successful_last_30_days` should be close to 30. Tell
me about any that is non-zero or stale, and what it means in practice.

**Step 5 — the paper register, if I gave it to you.** Compare the register's
month total with the app's. If they differ, find which bookings account for
the difference before proposing any cause. A register entry with no matching
booking, or a booking with no register entry, is usually a data-entry problem
and not a code bug. Remember the app splits a stay that crosses a month
boundary night by night between the two months; a register that puts the whole
stay in the check-in month will differ by exactly those nights, and that is
expected.

## What you must not do

- Do not change, cancel, close or correct any live booking, and do not run or
  write a migration. If a booking needs correcting, tell me which one and what
  to do on the Bookings page, or ask for my go-ahead and state how it could be
  undone.
- Do not "fix" the deliberate design choices in `CLAUDE.md` (an overstay not
  blocking the room; early check-in being allowed).
- Do not decide an open policy question for me. If a gap turns on one, show me
  the number both ways and ask.
- Do not recompute money with your own arithmetic and present it as the
  answer. If you need to know what a booking is worth, use
  `booking_financials()` and `stay_charges()` from `report_calc.py` in a small
  script, so your figure is the app's figure.
- Never store or ask me for rank, service number or unit. Guests are Org or
  Non-Org and a colour, nothing more.

## If you find a real bug

A real bug is a case where the code computes something other than what the
rules say. If you find one:

1. Write a test that fails because of it, in `backend/tests/`, using the
   existing patterns (`tests/inprocess.py` runs the whole app with no
   database).
2. Fix it in the shared calculation, not at the one place it showed up. If two
   places compute the same money differently, the fix is to make one of them
   call the other.
3. Run the full test command above and confirm everything passes.
4. Tell me what it was, which past months it affects and by how much, before
   pushing. A fix that changes a month I have already handed to my accountant
   needs my say-so first.

If the fix is self-contained, test-covered and changes no already-closed
month, you may push it without asking and tell me afterwards.

## What to send me at the end

Lead with the verdict in one or two sentences: is the month safe to hand to
the accountant, yes or no, and the month's revenue figure.

Then, in complete sentences and plain language:

- whether the four reports agree, with the figure;
- the reports-against-billed difference for the month in rupees, split into
  explained and unexplained, with booking numbers for anything unexplained;
- the unpaid-balance total;
- anything from the risk counts I should act on, and what the action is;
- the register comparison, if I gave you one;
- anything you need me to decide, as a short numbered list with the rupee
  consequence of each choice.

Quote the actual numbers from what I pasted and from your test output; do not
paraphrase them. If you could not verify something, say so and say what you
would need.

Finally, add a dated entry to the top of `memory/HISTORY.md` in the same style
as the existing ones: the month checked, its revenue figure, whether it
reconciled, and anything left open. That entry is what next month's check
compares against.
