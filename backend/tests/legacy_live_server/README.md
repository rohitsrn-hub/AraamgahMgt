# Retired tests (kept for reference)

These 15 files were written against a LIVE deployed backend over HTTP
(`requests` to `REACT_APP_BACKEND_URL`), before login was enforced and before
the billing rules changed (extra beds at check-out, late check-outs, early
arrival, one pricing engine). They send no login token and assert behaviour
that has since been deliberately changed, so they cannot pass against today's
app — and several mention old field names (`guest_rank`, `def_civ_*`) that are
banned in new code. They are excluded from `pytest tests/` by `tests/conftest.py`.

The tests that count are the in-process ones, which need no server or database:
`test_report_calc.py`, `test_manual_occupancy_excel.py`, `test_audit_*.py`
(see `tests/inprocess.py`). Delete this folder whenever you like; git history keeps it.
