"""
The approved live-data corrections: previewed, guarded, backed up first, logged
with the original values, and undoable. (The real booking numbers/amounts are
swapped for ones that fit the test harness's rates.)
"""
import asyncio
import copy
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from inprocess import api, server  # noqa: F401
from services import backup_service, corrections_service
from test_audit_endpoints import booking, reported_total


@pytest.fixture(autouse=True)
def approved(tmp_path, monkeypatch):
    monkeypatch.setattr(backup_service, "BACKUP_DIR", tmp_path)
    monkeypatch.setattr(corrections_service, "APPROVED_BILL_CORRECTIONS", {"BKA": 800.0, "BKB": 2150.0})
    monkeypatch.setattr(corrections_service, "APPROVED_REFUND_DUE_RESETS", {"BKC": 300.0})
    monkeypatch.setattr(corrections_service, "APPROVED_CASH_LOG_SYNC", {})
    monkeypatch.setattr(corrections_service, "APPROVED_RECONCILIATIONS", {})


def seed(api):
    api.seed("bookings", [
        # A: Cat II room billed at a Cat I rate (stored 1000, should be 800); guest paid 800
        booking(id="a", booking_number="BKA", status="checked_out", room_ids=["r3"], room_numbers=["C2-07"],
                room_categories=["Cat II"], room_guest_mapping=[{"room_number": "C2-07", "room_category": "Cat I", "charge_category": "Cat I"}],
                actual_checkout_date="2026-05-12", charged_nights=2, charge_reason="normal",
                total_amount=1000.0, room_rent_total=940.0, license_fee_total=60.0, advance_paid=400.0,
                final_payment=400.0, balance_amount=200.0),
        # B: late check-out (booked 10-12, left 14th) + a bed charged at check-out; stored under the old rule
        booking(id="b", booking_number="BKB", status="checked_out", room_ids=["r2"], room_numbers=["C1-02"],
                actual_checkout_date="2026-05-14", charged_nights=2, charge_reason="normal", extra_bed_charge_checkout=150.0,
                total_amount=1150.0, room_rent_total=940.0, license_fee_total=60.0, advance_paid=400.0,
                final_payment=1750.0, balance_amount=-1000.0),
        # C: active booking with a stale refund due
        booking(id="c", booking_number="BKC", status="checked_in", room_ids=["r4"], room_numbers=["C2-08"],
                room_categories=["Cat II"], total_amount=800.0, advance_paid=400.0, refund_due=300.0,
                refund_reason="Booking amended - cost reduced"),
    ])


def docs(api):
    return {b["id"]: b for b in api.find("bookings")}


def test_preview_shows_each_change_and_changes_nothing(api):
    seed(api)
    before = api.find("bookings")
    data = api.client.get("/api/admin/corrections").json()
    ready = {p["booking_number"]: p for p in data["preview"] if p["status"] == "ready"}
    assert set(ready) == {"BKA", "BKB", "BKC"}
    assert ready["BKA"]["before"]["total_amount"] == 1000.0 and ready["BKA"]["after"]["total_amount"] == 800.0
    assert ready["BKA"]["after"]["balance_amount"] == 0.0
    assert ready["BKB"]["after"]["total_amount"] == 2150.0 and ready["BKB"]["after"]["charge_reason"] == "late_checkout"
    assert ready["BKB"]["after"]["charged_nights"] == 4
    assert ready["BKC"]["after"] == {"refund_due": 0.0, "refund_reason": None}
    assert api.find("bookings") == before and api.find("data_corrections") == []


def test_apply_takes_a_backup_first_changes_only_those_fields_and_logs_the_originals(api):
    seed(api)
    original = copy.deepcopy(docs(api))
    res = api.client.post("/api/admin/corrections/apply").json()
    assert res["applied"] == 3 and res["batch_id"] and res["backup_id_before"]
    assert api.find_one("backup_metadata", {"backup_id": res["backup_id_before"]})["status"] == "SUCCESS"
    now = docs(api)
    assert (now["a"]["total_amount"], now["a"]["balance_amount"]) == (800.0, 0.0)
    assert (now["b"]["total_amount"], now["b"]["balance_amount"], now["b"]["charged_nights"], now["b"]["charge_reason"]) == (2150.0, 0.0, 4, "late_checkout")
    assert (now["c"]["refund_due"], now["c"]["refund_reason"]) == (0.0, None)
    for bid in "abc":                                   # nothing else on the record moved
        changed = {k for k in set(original[bid]) | set(now[bid]) if original[bid].get(k) != now[bid].get(k)}
        assert changed <= {"total_amount", "balance_amount", "room_rent_total", "license_fee_total", "charged_nights",
                           "charge_reason", "refund_due", "refund_reason", "updated_at", "amendment_log"}, (bid, changed)
        assert now[bid]["amendment_log"][-1]["source"] == "data_correction"
    log = {r["booking_number"]: r for r in api.find("data_corrections")}
    assert log["BKA"]["original"]["total_amount"] == 1000.0 and log["BKA"]["original"]["balance_amount"] == 200.0
    assert log["BKB"]["original"]["charge_reason"] == "normal" and log["BKC"]["original"]["refund_due"] == 300.0


def test_reports_are_identical_before_and_after_because_they_never_read_the_stored_bill(api):
    seed(api)
    before = {i: reported_total(api, i)["total_amount"] for i in "ab"}
    api.client.post("/api/admin/corrections/apply")
    assert {i: reported_total(api, i)["total_amount"] for i in "ab"} == before == {"a": 800, "b": 2150}


def test_applying_twice_changes_nothing_the_second_time(api):
    seed(api)
    api.client.post("/api/admin/corrections/apply")
    again = api.client.post("/api/admin/corrections/apply").json()
    assert again["applied"] == 0 and again["batch_id"] is None
    assert len(api.find("data_corrections")) == 3


def test_undo_restores_every_original_value_exactly(api):
    seed(api)
    original = copy.deepcopy(docs(api))
    batch = api.client.post("/api/admin/corrections/apply").json()["batch_id"]
    res = api.client.post(f"/api/admin/corrections/undo/{batch}").json()
    assert res["restored"] == 3
    now = docs(api)
    for bid in "abc":
        a, b = dict(original[bid]), dict(now[bid])
        a.pop("updated_at", None); b.pop("updated_at", None)
        assert b.pop("amendment_log") == [] and "amendment_log" not in a   # the entry is removed; an empty list is all that remains
        assert a == b, bid                                                 # every other value is back exactly
    assert all(r["reverted_at"] for r in api.find("data_corrections"))
    assert api.client.post(f"/api/admin/corrections/undo/{batch}").json()["restored"] == 0


def test_undo_will_not_overwrite_a_record_changed_since(api):
    seed(api)
    batch = api.client.post("/api/admin/corrections/apply").json()["batch_id"]
    asyncio.run(api.db.bookings.update_one({"id": "a"}, {"$set": {"total_amount": 777.0}}))   # someone edited it
    res = api.client.post(f"/api/admin/corrections/undo/{batch}").json()
    assert res["restored"] == 2
    assert [r["status"] for r in res["results"] if r["booking_number"] == "BKA"] == ["skipped"]
    assert docs(api)["a"]["total_amount"] == 777.0


def test_a_record_is_skipped_if_it_no_longer_matches_what_the_audit_saw(api):
    seed(api)
    asyncio.run(api.db.bookings.update_one({"id": "c"}, {"$set": {"refund_due": 123.0}}))       # not the audited 300
    asyncio.run(api.db.bookings.update_one({"id": "b"}, {"$set": {"status": "cancelled"}}))
    plan = {p["booking_number"]: p for p in api.client.get("/api/admin/corrections").json()["preview"]}
    assert plan["BKC"]["status"] == "skipped" and "not the 300" in plan["BKC"]["reason"]
    assert plan["BKB"]["status"] == "skipped" and "not checked out" in plan["BKB"]["reason"]
    assert plan["BKA"]["status"] == "ready"


def test_a_changed_rate_that_makes_the_engine_disagree_blocks_the_bill_correction(api, monkeypatch):
    seed(api)
    monkeypatch.setattr(corrections_service, "APPROVED_BILL_CORRECTIONS", {"BKA": 999.0, "BKB": 2150.0})
    plan = {p["booking_number"]: p for p in api.client.get("/api/admin/corrections").json()["preview"]}
    assert plan["BKA"]["status"] == "skipped" and "engine now gives 800" in plan["BKA"]["reason"]


def test_unknown_booking_numbers_are_reported_not_fatal(api):
    plan = api.client.get("/api/admin/corrections").json()["preview"]
    assert all(p["status"] == "skipped" and p["reason"] == "booking not found" for p in plan)
    assert api.client.post("/api/admin/corrections/apply").json()["applied"] == 0
    assert api.find("backup_metadata") == [], "no backup is taken when there is nothing to change"


def test_corrections_are_admin_only(api):
    for role in ("staff", "viewer"):
        api.as_role(role)
        assert api.client.get("/api/admin/corrections").status_code == 403
        assert api.client.post("/api/admin/corrections/apply").status_code == 403
        assert api.client.post("/api/admin/corrections/undo/x").status_code == 403
