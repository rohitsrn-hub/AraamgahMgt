# Fable 5.2 Prompt — SARAI Full Financial + Quality Audit

Copy everything below the line into a fresh Fable 5.2 session checked out on
the `claude/qa-audit-fixes` branch of this repo (verify with
`git log --oneline -5` right after checkout — a fresh session sometimes
defaults to a stale, unrelated branch). Recommended effort: `xhigh`.

---

I'm the owner-operator of SARAI, a guesthouse management app in live daily
production use (FastAPI + MongoDB backend in `backend/server.py` and
`backend/utils/`, React frontend in `frontend/src/`). I've just spent about
two months chasing one specific financial mismatch through this codebase and
found six real, previously-unknown bugs along the way (five financial-
calculation bugs and one structural bug — a route-registration-order issue
in FastAPI that silently 404'd an endpoint for weeks). That investigation was
reactive: it only ever looked at the code directly on the path of the symptom
I started with. Nobody has looked at the rest of this application the same
way. I want you to do that now: read the entire codebase on this branch and
find anything else wrong, financial or otherwise, before it becomes a real
discrepancy I have to chase by hand again.

**Read `docs/handoff-2026-11-financial-audit.md` in full before anything
else.** It has the complete narrative of what was already found and fixed,
exactly which files and functions changed, what `backend/utils/report_calc.py`
looks like now and why, and — just as important — a list of things that are
*deliberately* not bugs (an overstay doesn't block rebooking the room; early
check-in has no date restriction) so you don't waste time "fixing" intentional
behavior. Then read `CLAUDE.md` in full; it's this project's own standing
instructions and takes precedence over anything that seems to conflict with
this prompt.

## What I want from this audit

Two kinds of findings, both in scope, in this priority order:

1. **Financial correctness.** Every rupee in every report is supposed to
   come from `backend/utils/report_calc.py`. Verify that invariant holds
   everywhere, not just in the four report endpoints already fixed:
   - Grep the whole backend for anywhere money, rate, or night-count math
     happens *outside* `report_calc.py` — booking creation, check-in,
     check-out, stay extension/amendment, cancellation/refund calculation,
     the manual-occupancy Excel export, any PDF generator. Each one is a
     candidate for exactly the kind of silent drift already found four times
     over. Cross-check each such path against what `report_calc.py` would
     compute for the same booking and settings; where they can legitimately
     differ (e.g. a quoted estimate before a booking exists), confirm that's
     intentional and not a drift risk.
   - Stress-test `report_calc.py` itself beyond the existing 44 unit tests:
     combinations the tests may not cover — a room-category override
     *together with* a checkout-added extra bed *together with* a month-
     crossing early-checkout penalty on a multi-room, segmented (mix-and-
     match) booking; a rate-history change effective mid-stay; a booking
     amended (room swap, date change) after check-in; refund/cancellation
     math.
   - Check the frontend's own price previews (`frontend/src/utils/rateUtils.js`
     and anywhere Bookings.jsx shows a live total before submission) against
     the backend's actual resolved charge for the same inputs — a previous
     fix in this project's history found these drifting from each other
     before (see `memory/HISTORY.md`, further back than this round).
   - Re-verify `GET /api/reports/reconcile?month=&year=` stays `consistent:
     true` for several different real months in the live database (not just
     August 2026, which is now hand-verified) — ask me for which months to
     check if you can't reach the database yourself.

2. **Code quality and structural bugs.** The handoff document describes one
   concrete bug class already found: FastAPI/Starlette matches routes in
   *registration order*, so a specific path registered after a generic
   `{param}` path on the same prefix gets silently swallowed by it. That was
   only checked for the `/bookings/*` prefix. Check every other prefix in
   `backend/server.py` (`/rooms`, `/reports`, `/staff`, `/guests`,
   `/settings`, `/toiletry`, `/backups`, `/auth`, anything else) for the same
   conflict. Beyond that specific class, do a general quality pass: dead
   code, unreachable branches, missing error handling on paths that touch
   real money or real guest data, authorization gaps (every action should
   require the right role per `CLAUDE.md`'s tiers), N+1 or unbounded queries,
   and anything that fails silently the way the route bug did (swallowed
   exceptions, `console.error`-only frontend failures with no user-visible
   signal) — that failure mode let a real bug hide for weeks last time.

3. **Data-privacy rule compliance.** `CLAUDE.md` bans storing military rank,
   service number, or unit anywhere, and bans specific legacy field names.
   Grep the whole codebase (not just recently-touched files) for any of
   those banned names or any code path that could persist the banned data,
   including test fixtures and migration scripts.

## Constraints

- This is a live production app — real guests, real money, staff using it
  today. Read-only investigation can go as deep as you like without asking.
  A code fix that's self-contained and covered by a new or existing test is
  fine to make directly. Do **not** touch live booking/guest data, run a
  bulk migration, or change anything a real staff member is relying on right
  now without stopping to tell me first and getting an explicit go-ahead —
  same rule `CLAUDE.md` already states for any live-DB change.
- You most likely can't reach the live MongoDB or the live Render backend
  directly from your sandbox (this has been true in every session so far —
  `pymongo`/`cryptography` native bindings are broken in at least one
  previous sandbox, and there's no direct network path to the production
  database regardless). Don't assume you can query it. For anything that
  needs real production data to confirm, either reason from the pure-Python
  unit-testable parts of `report_calc.py` (no DB needed) or build the same
  kind of temporary, admin-only diagnostic endpoint-plus-button this
  investigation used repeatedly (see `memory/HISTORY.md` for the pattern:
  phone-friendly, copies results to the clipboard, admin-role-gated, clearly
  marked TEMP) and ask me to run it and paste back the result. Remove any
  such temporary tooling once you're done with it, the same way this round's
  was removed at the end.
- Run `cd backend && python3 -m pytest tests/test_report_calc.py
  tests/test_manual_occupancy_excel.py -q` before and after any change to
  confirm you haven't regressed the 44 existing tests. The other files under
  `backend/tests/` have not been confirmed to run without a live DB/server
  in past sessions — if you get them running, that's a useful bonus finding
  in itself (tell me how), but don't block on it.
- Never push directly to `main`; stay on `claude/qa-audit-fixes` (or branch
  off it if you'd rather keep this audit's commits separate — tell me which
  you chose and why).

## Definition of done

1. A written list of every finding, each one stating: what's wrong, the
   exact file/function, how you confirmed it (a failing test you wrote, a
   concrete input/output pair, a code-reading argument), its real-world
   impact in plain terms (who notices, how much money or what data), and
   your confidence level if you couldn't fully verify it against live data.
2. Every finding that's a straightforward, test-covered code fix: fixed,
   with a new test that would have caught it and does now pass.
3. Every finding that needs my input (ambiguous intent, touches live data,
   a genuine policy question like the ones already resolved this round) —
   flagged clearly and separately, not silently decided either way.
4. Confirmation the existing 44 `report_calc`/`manual_occupancy_excel` tests
   still pass, plus whatever new tests you added.
5. `memory/HISTORY.md` updated the same way every entry in it already is:
   dated, product-terms, 2-3 sentences, newest first.
6. Any temporary diagnostic tooling you built for this audit is either still
   there with a clear TEMP marker (if I might still need it) or already
   removed (if its job is done) — not left half-cleaned-up.

## Working style

Audit first, fix second: don't start patching the moment you spot something
that looks wrong — finish reading the relevant area, understand the actual
blast radius, and check whether it's one of the deliberate non-bugs in the
handoff doc before touching anything.

I am not watching in real time. For a reversible, test-covered code fix that
follows directly from a confirmed finding, proceed without asking. Pause and
ask only when: the fix would touch live data, the intent is genuinely
ambiguous, or it's a policy question only I can answer (the handoff doc shows
two such questions already got resolved by asking my accountant — treat a
new one the same way, don't guess).

Audit each claim in your final report against a tool result from this
session — quote the actual test output or the actual line you're pointing to,
not a paraphrase. Lead your final summary with the outcome: how many findings,
how many fixed outright, how many flagged for me, and whether the four
reports still reconcile — then the supporting detail in complete sentences,
one finding per paragraph, plain language, no shorthand.
