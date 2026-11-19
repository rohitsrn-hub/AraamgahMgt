"""
The October-2026 register reconciliation corrections (owner rulings, 18 Nov 2026): cancel a booking
that is not in the register, bill at the Org rate, waive an early-departure penalty, add extra beds
the register had, and move advance amounts. Previewed, guarded by the money engine, backed up,
logged and undoable. (Booking numbers/amounts are swapped for ones that fit the test rates:
Cat I Org 500/night, Non-Org 600/night, extra bed 75/day.)
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

SPECS = {
    "BKN": {"org_rate": True, "total": 1000.0},                                  # Non-Org guest, register used Org
    "BKM": {"org_rate": True, "total": 1000.0},                                  # Org guest, one room overridden to Non-Org
    "BKZ": {"waive_penalty": True, "total": 500.0},                              # uninformed early departure
    "BKE": {"extra_bed": (1, 2), "total": 1150.0},                               # bed the register had
    "BKA": {"advance": (0.0, 500.0)},                                            # advance recorded differently
    "BKX": {"cancel_total": 1000.0},                                             # not in the register
    "BKT": {"extra_bed_top_up": True, "total": 1300.0},                          # had a 1-day bed, register has 3 days
}


@pytest.fixture(autouse=True)
def approved(tmp_path, monkeypatch):
    monkeypatch.setattr(backup_service, "BACKUP_DIR", tmp_path)
    monkeypatch.setattr(corrections_service, "APPROVED_BILL_CORRECTIONS", {})
    monkeypatch.setattr(corrections_service, "APPROVED_REFUND_DUE_RESETS", {})
    monkeypatch.setattr(corrections_service, "APPROVED_RECONCILIATIONS", SPECS)


def out(**kw):
    base = dict(status="checked_out", actual_checkout_date="2026-05-12", charged_nights=2, charge_reason="normal",
                room_rent_total=940.0, license_fee_total=60.0, advance_paid=400.0)
    base.update(kw)
    return booking(**base)


def seed(api):
    api.seed("bookings", [
        out(id="n", booking_number="BKN", is_org=False, total_amount=1200.0, room_rent_total=1140.0,
            final_payment=800.0, balance_amount=0.0),
        out(id="m", booking_number="BKM", room_guest_mapping=[{"room_number": "C1-01", "charge_category": "Non-Org", "guest": "x"}],
            total_amount=1200.0, room_rent_total=1140.0, final_payment=800.0, balance_amount=0.0),
        out(id="z", booking_number="BKZ", check_out_date="2026-05-14", actual_checkout_date="2026-05-11", charged_nights=4,
            charge_reason="early_checkout_not_informed", total_amount=2000.0, room_rent_total=1880.0, license_fee_total=120.0,
            final_payment=1600.0, balance_amount=0.0),
        out(id="e", booking_number="BKE", total_amount=1000.0, final_payment=600.0, balance_amount=0.0),
        out(id="a", booking_number="BKA", advance_paid=0.0, total_amount=1000.0, final_payment=1000.0, balance_amount=0.0),
        out(id="t", booking_number="BKT", total_amount=1150.0, extra_beds_checkout=1, extra_bed_days=2,
            extra_bed_charge_checkout=150.0, final_payment=750.0, balance_amount=0.0),
        out(id="x", booking_number="BKX", total_amount=1000.0, final_payment=600.0, balance_amount=0.0),
    ])


def docs(api):
    return {b["id"]: b for b in api.find("bookings")}


def test_preview_describes_each_change_and_changes_nothing(api):
    seed(api)
    before = api.find("bookings")
    plan = {p["booking_number"]: p for p in api.client.get("/api/admin/corrections").json()["preview"]}
    assert all(plan[n]["status"] == "ready" for n in SPECS), {n: plan[n]["reason"] for n in SPECS}
    assert plan["BKN"]["after"]["total_amount"] == 1000.0 and plan["BKN"]["after"]["balance_amount"] == -200.0
    assert "over-collected by 200" in plan["BKN"]["note"]
    assert plan["BKZ"]["after"]["charge_reason"] == "early_checkout_penalty_waived" and plan["BKZ"]["after"]["charged_nights"] == 1
    assert plan["BKE"]["after"]["extra_bed_charge_checkout"] == 150.0 and plan["BKE"]["after"]["total_amount"] == 1150.0
    assert plan["BKA"]["after"] == {"advance_paid": 500.0, "final_payment": 500.0}
    assert plan["BKX"]["after"]["status"] == "cancelled" and "NOT refunded" in plan["BKX"]["note"]
    assert api.find("bookings") == before and api.find("data_corrections") == []


def test_apply_makes_the_reports_match_the_register_amounts(api):
    seed(api)
    res = api.client.post("/api/admin/corrections/apply").json()
    assert res["applied"] == 7 and res["backup_id_before"]
    now = docs(api)
    assert {i: reported_total(api, i)["total_amount"] for i in "nmze"} == {"n": 1000, "m": 1000, "z": 500, "e": 1150}
    assert now["z"]["charged_nights"] == 1 and now["z"]["charge_reason"] == "early_checkout_penalty_waived"
    assert (now["e"]["extra_beds_checkout"], now["e"]["extra_bed_days"], now["e"]["extra_bed_charge_checkout"]) == (1, 2, 150.0)
    assert (now["a"]["advance_paid"], now["a"]["final_payment"], now["a"]["total_amount"]) == (500.0, 500.0, 1000.0)
    assert now["a"]["advance_paid"] + now["a"]["final_payment"] == 1000.0, "the cash is unchanged"
    assert now["x"]["status"] == "cancelled"
    assert (now["t"]["extra_beds_checkout"], now["t"]["extra_bed_days"], now["t"]["extra_bed_charge_checkout"], now["t"]["total_amount"]) == (1, 4, 300.0, 1300.0)
    assert now["m"]["room_guest_mapping"][0]["charge_category"] == "Org" and now["m"]["room_guest_mapping"][0]["guest"] == "x"
    assert now["n"]["room_guest_mapping"] == [{"room_number": "C1-01", "room_category": "Cat I", "charge_category": "Org"}]
    assert all(d["amendment_log"][-1]["source"] == "data_correction" for d in now.values())


def test_a_cancelled_booking_leaves_every_report(api):
    seed(api)
    api.client.post("/api/admin/corrections/apply")
    q = {"status": {"$in": ["confirmed", "checked_in", "checked_out"]}}
    assert {b["booking_number"] for b in api.find("bookings", q)} == set(SPECS) - {"BKX"}


def test_undo_puts_every_original_back(api):
    seed(api)
    original = copy.deepcopy(docs(api))
    batch = api.client.post("/api/admin/corrections/apply").json()["batch_id"]
    assert api.client.post(f"/api/admin/corrections/undo/{batch}").json()["restored"] == 7
    now = docs(api)
    for i, o in original.items():
        n = dict(now[i])
        n.pop("updated_at", None); n.pop("amendment_log", None)
        o = {k: v for k, v in o.items() if k != "updated_at"}
        # fields the correction added (absent before) are back to "absent or null"
        for k in set(n) - set(o):
            assert n[k] in (None, [], 0, 0.0), (i, k, n[k])
            n.pop(k)
        assert n == o, i


def test_a_booking_is_skipped_when_the_engine_would_not_match_the_register(api):
    seed(api)
    corrections_service.APPROVED_RECONCILIATIONS["BKN"] = {"org_rate": True, "total": 900.0}
    plan = {p["booking_number"]: p for p in api.client.get("/api/admin/corrections").json()["preview"]}
    assert plan["BKN"]["status"] == "skipped" and "not the register's 900" in plan["BKN"]["reason"]
    assert plan["BKM"]["status"] == "ready"


def test_guards_refuse_changed_records(api):
    seed(api)
    asyncio.run(api.db.bookings.update_one({"id": "a"}, {"$set": {"advance_paid": 100.0}}))      # not the audited 0
    asyncio.run(api.db.bookings.update_one({"id": "z"}, {"$set": {"charge_reason": "normal"}}))   # no longer a penalty
    asyncio.run(api.db.bookings.update_one({"id": "e"}, {"$set": {"extra_bed_charge_checkout": 75.0}}))
    asyncio.run(api.db.bookings.update_one({"id": "x"}, {"$set": {"total_amount": 5.0}}))
    plan = {p["booking_number"]: p for p in api.client.get("/api/admin/corrections").json()["preview"]}
    for n in ("BKA", "BKZ", "BKE", "BKX"):
        assert plan[n]["status"] == "skipped", n
    assert "not the 0 the audit saw" in plan["BKA"]["reason"]


def test_applying_twice_changes_nothing_the_second_time(api):
    seed(api)
    api.client.post("/api/admin/corrections/apply")
    again = api.client.post("/api/admin/corrections/apply").json()
    assert again["applied"] == 0


def test_the_real_approved_list_covers_exactly_the_agreed_bookings():
    # (the fixture patched it; reload the module's own literal for this check)
    import importlib
    real = importlib.reload(corrections_service).APPROVED_RECONCILIATIONS
    assert "BK1293" in real
    assert sum(1 for v in real.values() if v.get("extra_bed")) == 2 and sum(1 for v in real.values() if v.get("extra_bed_top_up")) == 5
    assert real["BK1293"]["cancel_total"] == 21000.0
    assert sum(1 for v in real.values() if v.get("org_rate")) == 9
    assert {n for n, v in real.items() if v.get("waive_penalty")} == {"BK1138", "BK1184"}
    assert {n for n, v in real.items() if v.get("advance")} == {"BK1159", "BK1279", "BK1286"}
    assert "BK1226" not in real and "BK1031" not in real
