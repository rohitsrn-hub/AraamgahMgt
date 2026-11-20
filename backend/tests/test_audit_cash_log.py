"""
The payments log (what the dashboard's Net Revenue counts) must agree with each booking's own
advance / final payment. The audit check lists any booking where they differ, and the approved
correction adds adjustment rows to the log (in the month the original money was recorded),
backed up, logged and undoable.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from inprocess import api, server  # noqa: F401
from services import backup_service, corrections_service
from test_audit_endpoints import booking


@pytest.fixture(autouse=True)
def approved(tmp_path, monkeypatch):
    monkeypatch.setattr(backup_service, "BACKUP_DIR", tmp_path)
    monkeypatch.setattr(corrections_service, "APPROVED_BILL_CORRECTIONS", {})
    monkeypatch.setattr(corrections_service, "APPROVED_REFUND_DUE_RESETS", {})
    monkeypatch.setattr(corrections_service, "APPROVED_RECONCILIATIONS", {})
    monkeypatch.setattr(corrections_service, "APPROVED_CASH_LOG_SYNC", {"BKM": (800.0, 0.0), "BKO": (-400.0, 0.0)})
    monkeypatch.setattr(server, "ist_today_str", lambda: "2026-06-03")


def seed(api):
    out = dict(status="checked_out", actual_checkout_date="2026-05-12", actual_check_out="2026-05-12T05:00:00+00:00",
               charged_nights=2, charge_reason="normal", total_amount=1000.0, created_at="2026-05-01T05:00:00+00:00")
    api.seed("bookings", [
        booking(id="m", booking_number="BKM", advance_paid=800.0, final_payment=200.0, balance_amount=0.0, **out),   # advance never logged
        booking(id="o", booking_number="BKO", advance_paid=400.0, final_payment=600.0, balance_amount=0.0, **out),   # advance logged as 800
        booking(id="k", booking_number="BKK", advance_paid=400.0, final_payment=600.0, balance_amount=0.0, **out),   # all good
    ])
    api.seed("payments", [
        {"id": "p1", "booking_id": "m", "booking_number": "BKM", "amount": 200.0, "payment_type": "final", "created_at": "2026-05-12T05:00:00+00:00"},
        {"id": "p2", "booking_id": "o", "booking_number": "BKO", "amount": 800.0, "payment_type": "advance", "created_at": "2026-04-20T05:00:00+00:00"},
        {"id": "p3", "booking_id": "o", "booking_number": "BKO", "amount": 600.0, "payment_type": "final", "created_at": "2026-05-12T05:00:00+00:00"},
        {"id": "p4", "booking_id": "k", "booking_number": "BKK", "amount": 400.0, "payment_type": "advance", "created_at": "2026-05-01T05:00:00+00:00"},
        {"id": "p5", "booking_id": "k", "booking_number": "BKK", "amount": 600.0, "payment_type": "final", "created_at": "2026-05-12T05:00:00+00:00"},
    ])


def funds(api, month):
    return api.client.get("/api/dashboard/funds", params={"month": month, "year": 2026}).json()


def test_audit_check_lists_bookings_whose_payments_log_differs(api):
    seed(api)
    a = api.client.get("/api/reports/audit-check").json()
    assert {r["bk"]: (r["booking_advance"], r["log_advance"]) for r in a["cash_log_differs"]} == {"BKM": (800, 0), "BKO": (400, 800)}
    assert a["checked_out_in_month"]["cash_log_differs_from_bookings"] == 2


def test_sync_adds_rows_in_the_original_month_and_net_revenue_follows(api):
    seed(api)
    before_apr, before_may = funds(api, 4)["cash_received"], funds(api, 5)["cash_received"]
    plan = {p["booking_number"]: p for p in api.client.get("/api/admin/corrections").json()["preview"]}
    assert plan["BKM"]["status"] == plan["BKO"]["status"] == "ready"
    res = api.client.post("/api/admin/corrections/apply").json()
    assert res["applied"] == 2
    assert funds(api, 5)["cash_received"] == before_may + 800          # BKM's advance: month the booking was made
    assert funds(api, 4)["cash_received"] == before_apr - 400          # BKO: same month as its original advance row
    assert api.client.get("/api/reports/audit-check").json()["cash_log_differs"] == []
    again = {p["booking_number"]: p for p in api.client.get("/api/admin/corrections").json()["preview"]}
    assert again["BKM"]["reason"] == "the payments log already matches the booking"
    # Undo removes exactly the added rows
    assert api.client.post(f"/api/admin/corrections/undo/{res['batch_id']}").json()["restored"] == 2
    assert funds(api, 5)["cash_received"] == before_may and funds(api, 4)["cash_received"] == before_apr
    assert {p["id"] for p in api.find("payments")} == {"p1", "p2", "p3", "p4", "p5"}


def test_sync_is_refused_when_the_log_differs_by_something_else(api):
    seed(api)
    api.seed("payments", [{"id": "p6", "booking_id": "m", "booking_number": "BKM", "amount": 100.0,
                           "payment_type": "advance", "created_at": "2026-05-02T05:00:00+00:00"}])
    plan = {p["booking_number"]: p for p in api.client.get("/api/admin/corrections").json()["preview"]}
    assert plan["BKM"]["status"] == "skipped" and "not the +800" in plan["BKM"]["reason"]
