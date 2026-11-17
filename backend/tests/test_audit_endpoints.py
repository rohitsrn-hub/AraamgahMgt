"""
Endpoint-level regression tests from the Nov 2026 full-codebase audit.

These run the REAL FastAPI app in-process against an in-memory database
(see tests/inprocess.py) — no MongoDB, no server, no network.

    cd backend && pip install -r requirements-dev.txt
    python3 -m pytest tests/test_audit_endpoints.py -q
"""
import asyncio
import re
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi import APIRouter

from inprocess import api, server  # noqa: F401  (api is a pytest fixture)
from utils.report_calc import booking_financials, build_room_maps, cancellation_refund

WIDE = (date(2000, 1, 1), date(2100, 1, 1))


def booking(**overrides):
    bk = {
        "id": "b1", "booking_number": "BK0001", "guest_id": "g1", "guest_name": "Test Guest",
        "status": "confirmed", "is_org": True,
        "check_in_date": "2026-05-10", "check_out_date": "2026-05-12",
        "room_ids": ["r1"], "room_numbers": ["C1-01"], "room_categories": ["Cat I"],
        "num_rooms": 1, "total_amount": 1000.0, "advance_paid": 400.0, "balance_amount": 600.0,
        "created_at": "2026-05-01T00:00:00+00:00",
    }
    bk.update(overrides)
    return bk


def reported_total(api, booking_id):
    """What every report says this booking is worth over its whole life."""
    bk = api.find_one("bookings", {"id": booking_id})
    maps = build_room_maps(api.find("rooms"))
    return booking_financials(bk, api.find_one("app_settings", {}), *WIDE, maps)


# ====================================================================
# Route ordering — the bug class that hid /bookings/stale-confirmed
# ====================================================================

def shadowed_routes(router):
    """Every route that can never be reached because an EARLIER-registered
    route with an overlapping HTTP method already matches its path.
    FastAPI/Starlette picks the first match in registration order, so a
    specific path registered after a generic {param} path on the same prefix
    is silently swallowed by it."""
    # Takes the APIRouter itself (routes in registration order, full path
    # including the /api prefix) — works the same on every FastAPI version,
    # unlike app.routes, which newer versions nest.
    routes = [r for r in router.routes if getattr(r, "methods", None) and hasattr(r, "path_regex")]
    problems = []
    for j, later in enumerate(routes):
        sample = re.sub(r"\{[^}]+\}", "sample-value", later.path)
        for earlier in routes[:j]:
            if earlier.methods & later.methods and earlier.path_regex.match(sample):
                problems.append(f"{sorted(later.methods)} {later.path} is shadowed by {earlier.path}")
    return problems


def test_checker_catches_the_original_stale_confirmed_bug():
    router = APIRouter(prefix="/api")

    @router.get("/bookings/{booking_id}")
    async def get_one(booking_id: str):
        return {}

    @router.get("/bookings/stale-confirmed")
    async def stale():
        return {}

    assert shadowed_routes(router) == ["['GET'] /api/bookings/stale-confirmed is shadowed by /api/bookings/{booking_id}"]


def test_no_route_in_the_whole_api_is_shadowed():
    """Every prefix, not just /bookings: /rooms, /reports, /staff, /guests,
    /settings, /toiletry, /backups, /auth, /users, /feedback, /dashboard..."""
    assert len(server.api_router.routes) > 80
    assert shadowed_routes(server.api_router) == []


# ====================================================================
# Authorization tiers
# ====================================================================

OPEN_ROUTES = {"/api/", "/api/health", "/api/auth/login", "/api/auth/logout"}
ADMIN_ONLY_PREFIXES = ("/api/users", "/api/settings", "/api/staff", "/api/backups/restore",
                       "/api/backups/schedule", "/api/migration", "/api/admin")
ADMIN_ONLY_EXTRA = {("DELETE", "/api/bookings/{booking_id}"), ("DELETE", "/api/rooms/{room_id}"),
                    ("POST", "/api/rooms"), ("DELETE", "/api/toiletry/items/{item_id}")}


def api_routes():
    for route in server.api_router.routes:
        if getattr(route, "methods", None) and route.path.startswith("/api"):
            for method in route.methods - {"HEAD", "OPTIONS"}:
                yield method, route.path


def call(api, method, path):
    url = re.sub(r"\{[^}]+\}", "x", path)
    return api.client.request(method, url, json={})


def test_every_non_open_route_rejects_a_request_with_no_login(api):
    server.app.dependency_overrides.clear()
    checked = 0
    for method, path in api_routes():
        if path in OPEN_ROUTES:
            continue
        status = call(api, method, path).status_code
        assert status in (401, 403), f"{method} {path} answered {status} with no token"
        checked += 1
    assert checked >= 80


def test_a_viewer_cannot_change_anything(api):
    api.as_role("viewer")
    for method, path in api_routes():
        if method == "GET" or path in OPEN_ROUTES:
            continue
        status = call(api, method, path).status_code
        assert status == 403, f"viewer was allowed to {method} {path} ({status})"


def test_staff_cannot_use_admin_only_actions(api):
    api.as_role("staff")
    checked = 0
    for method, path in api_routes():
        admin_only = (method, path) in ADMIN_ONLY_EXTRA or (
            path.startswith(ADMIN_ONLY_PREFIXES)
            and not (method == "GET" and path in ("/api/settings", "/api/staff", "/api/staff/{staff_id}",
                                           "/api/backups/restore-history")))
        if not admin_only:
            continue
        checked += 1
        status = call(api, method, path).status_code
        assert status == 403, f"staff was allowed to {method} {path} ({status})"
    assert checked >= 20


# ====================================================================
# Check-in / check-out bill = what the reports say
# ====================================================================

def checkin(api, booking_id="b1", **extra):
    body = {"booking_id": booking_id, "staff_id": "s1"}
    body.update(extra)
    res = api.client.post("/api/bookings/check-in", json=body)
    assert res.status_code == 200, res.text
    return res.json()["booking"]


def checkout(api, booking_id="b1", **extra):
    body = {"booking_id": booking_id, "staff_id": "s1"}
    body.update(extra)
    res = api.client.post("/api/bookings/check-out", json=body)
    assert res.status_code == 200, res.text
    return res.json()["booking"]


def test_checkin_and_checkout_totals_match_the_reports_for_a_plain_booking(api):
    api.seed("bookings", [booking()])
    after_in = checkin(api)
    assert after_in["total_amount"] == 1000 and after_in["room_rent_total"] == 940 and after_in["license_fee_total"] == 60
    after_out = checkout(api, actual_checkout_date="2026-05-12", final_payment=600)
    assert after_out["total_amount"] == 1000
    assert after_out["room_rent_total"] == 940 and after_out["license_fee_total"] == 60
    assert after_out["balance_amount"] == 0
    assert reported_total(api, "b1")["total_amount"] == 1000


MIX = dict(
    room_ids=["r1", "r3"], room_numbers=["C1-01", "C2-07"], room_categories=["Cat I", "Cat II"],
    num_rooms=2, check_in_date="2026-05-10", check_out_date="2026-05-14", total_amount=1800.0,
    has_room_changes=True,
    room_segments=[
        {"night_date": "2026-05-10", "rooms": [{"id": "r1", "room_number": "C1-01", "category": "Cat I"}]},
        {"night_date": "2026-05-11", "rooms": [{"id": "r1", "room_number": "C1-01", "category": "Cat I"}]},
        {"night_date": "2026-05-12", "rooms": [{"id": "r3", "room_number": "C2-07", "category": "Cat II"}]},
        {"night_date": "2026-05-13", "rooms": [{"id": "r3", "room_number": "C2-07", "category": "Cat II"}]},
    ])


def test_mix_and_match_booking_is_not_billed_for_every_room_every_night(api):
    """One room a night for 4 nights (2 in Cat I, then 2 in Cat II) was quoted
    Rs 1,800. Check-in used to re-price it as BOTH rooms x 4 nights = Rs 3,600."""
    api.seed("bookings", [booking(**MIX)])
    mapping = [{"room_id": "r1", "room_number": "C1-01", "room_category": "Cat I", "charge_category": "Cat I"},
               {"room_id": "r3", "room_number": "C2-07", "room_category": "Cat II", "charge_category": "Cat II"}]
    assert checkin(api, room_guest_mapping=mapping)["total_amount"] == 1800
    assert checkout(api, actual_checkout_date="2026-05-14")["total_amount"] == 1800
    assert reported_total(api, "b1")["total_amount"] == 1800


def test_non_org_booking_never_gets_an_org_rate_room(api):
    """Two-room Non-Org booking; staff assign guests to one room only, so the
    other arrives labelled with its plain category. Both must bill Non-Org."""
    api.seed("bookings", [booking(is_org=False, room_ids=["r1", "r3"], room_numbers=["C1-01", "C2-07"],
                                  room_categories=["Cat I", "Cat II"], num_rooms=2, total_amount=2400.0)])
    mapping = [{"room_id": "r1", "room_number": "C1-01", "room_category": "Cat I", "charge_category": "Non-Org"},
               {"room_id": "r3", "room_number": "C2-07", "room_category": "Cat II", "charge_category": "Cat II"}]
    after_in = checkin(api, room_guest_mapping=mapping)
    assert after_in["total_amount"] == 2 * 2 * 600
    assert [m["charge_category"] for m in after_in["room_guest_mapping"]] == ["Non-Org", "Non-Org"]
    assert checkout(api, actual_checkout_date="2026-05-12")["total_amount"] == 2400
    assert reported_total(api, "b1")["total_amount"] == 2400


def test_org_room_charged_non_org_is_billed_non_org_at_checkin_checkout_and_in_reports(api):
    api.seed("bookings", [booking()])
    mapping = [{"room_id": "r1", "room_number": "C1-01", "room_category": "Cat I", "charge_category": "Non-Org"}]
    assert checkin(api, room_guest_mapping=mapping)["total_amount"] == 1200
    assert checkout(api, actual_checkout_date="2026-05-12")["total_amount"] == 1200
    assert reported_total(api, "b1")["total_amount"] == 1200


def test_checkin_refuses_to_store_a_zero_bill_when_rooms_cannot_be_resolved(api):
    api.seed("bookings", [booking(room_ids=["gone"], room_numbers=[], room_categories=[])])
    res = api.client.post("/api/bookings/check-in", json={"booking_id": "b1", "staff_id": "s1"})
    assert res.status_code == 409
    assert api.find_one("bookings", {"id": "b1"})["status"] == "confirmed"


def test_checkout_with_a_garbage_date_is_a_clear_400_not_a_crash(api):
    api.seed("bookings", [booking(status="checked_in")])
    res = api.client.post("/api/bookings/check-out",
                          json={"booking_id": "b1", "staff_id": "s1", "actual_checkout_date": "12/05/2026"})
    assert res.status_code == 400
    assert api.find_one("bookings", {"id": "b1"})["status"] == "checked_in"


def test_uninformed_early_checkout_charges_full_term_and_reports_agree(api):
    api.seed("bookings", [booking(check_out_date="2026-05-14", total_amount=2000.0)])
    checkin(api)
    out = checkout(api, actual_checkout_date="2026-05-12")
    assert out["charge_reason"] == "early_checkout_not_informed" and out["total_amount"] == 2000
    fin = reported_total(api, "b1")
    assert fin["total_amount"] == 2000 and fin["nights"] == 2 and fin["billed_nights"] == 4


# ====================================================================
# Stay extension
# ====================================================================

def extend(api, new_check_out, booking_id="b1"):
    plan = api.client.post(f"/api/bookings/{booking_id}/plan-extension", params={"new_check_out_date": new_check_out})
    assert plan.status_code == 200, plan.text
    plan = plan.json()
    res = api.client.post(f"/api/bookings/{booking_id}/confirm-extension",
                          json={"new_check_out_date": new_check_out, "amendments": plan["proposed_amendments"]})
    assert res.status_code == 200, res.text
    return plan


def test_extension_is_not_given_away_free_at_checkout_without_a_room_mapping(api):
    """2 nights (Rs 1,000) extended to 4 (Rs 2,000). With no room_guest_mapping
    on the booking, check-out used to divide the room total stored at
    check-in (Rs 1,000) by the NEW night count and bill Rs 1,000 for 4 nights."""
    api.seed("bookings", [booking()])
    checkin(api)
    plan = extend(api, "2026-05-14")
    assert plan["status"] == "same_room" and plan["proposed_amendments"][0]["new_total"] == 2000
    stored = api.find_one("bookings", {"id": "b1"})
    assert stored["total_amount"] == 2000 and stored["room_rent_total"] == 4 * 470
    out = checkout(api, actual_checkout_date="2026-05-14")
    assert out["total_amount"] == 2000
    assert reported_total(api, "b1")["total_amount"] == 2000


def test_a_bed_noted_at_checkin_is_not_billed_until_checkout_and_extension_keeps_the_balance(api):
    api.seed("bookings", [booking()])
    after_in = checkin(api, extra_beds=1)
    assert after_in["extra_bed_charge"] == 0 and after_in["balance_amount"] == 1000 - 400
    extend(api, "2026-05-13")
    assert api.find_one("bookings", {"id": "b1"})["balance_amount"] == 1500 - 400


def test_extension_of_a_room_charged_non_org_is_priced_non_org(api):
    api.seed("bookings", [booking()])
    checkin(api, room_guest_mapping=[
        {"room_id": "r1", "room_number": "C1-01", "room_category": "Cat I", "charge_category": "Non-Org"}])
    plan = extend(api, "2026-05-13")
    assert plan["proposed_amendments"][0]["new_total"] == 1200 + 600
    assert checkout(api, actual_checkout_date="2026-05-13")["total_amount"] == 1800
    assert reported_total(api, "b1")["total_amount"] == 1800


def test_extending_a_mix_and_match_stay_extends_only_the_last_room_and_reaches_the_reports(api):
    api.seed("bookings", [booking(**MIX)])
    checkin(api)
    plan = extend(api, "2026-05-15")
    main = plan["proposed_amendments"][0]
    assert main["room_numbers"] == ["C2-07"]          # the room of the last night, not both
    assert main["new_total"] == 1800 + 400
    stored = api.find_one("bookings", {"id": "b1"})
    assert stored["room_segments"][-1]["night_date"] == "2026-05-14"
    assert len(stored["room_segments"]) == 5
    fin = reported_total(api, "b1")
    assert fin["total_amount"] == 2200, "extension night must appear in the reports"
    assert checkout(api, actual_checkout_date="2026-05-15")["total_amount"] == 2200


def test_extension_into_a_different_room_keeps_room_lists_aligned(api):
    """Guest in C1-01 (Cat I); extension only possible in C1-02 (also Cat I)
    because another guest arrives in C1-01. The three parallel room lists
    must stay the same length and order (they used to be built from set()s,
    which collapsed the two 'Cat I' entries into one)."""
    api.seed("bookings", [
        booking(),
        booking(id="b2", booking_number="BK0002", guest_name="Next Guest",
                check_in_date="2026-05-12", check_out_date="2026-05-14",
                room_ids=["r1"], room_numbers=["C1-01"]),
        # every other room except C1-02 is taken for the extension night
        booking(id="b3", booking_number="BK0003", check_in_date="2026-05-12", check_out_date="2026-05-14",
                room_ids=["r3", "r4"], room_numbers=["C2-07", "C2-08"], room_categories=["Cat II", "Cat II"]),
    ])
    checkin(api)
    # make b2 un-movable so the planner must move the extending guest instead
    asyncio.run(api.db.bookings.update_one({"id": "b3"}, {"$set": {"room_ids": ["r3", "r4", "r2x"]}}))
    plan = api.client.post("/api/bookings/b1/plan-extension", params={"new_check_out_date": "2026-05-13"}).json()
    if plan["status"] != "other_room":
        # planner found a shuffle instead; force the other-room amendment directly
        plan = {"proposed_amendments": [{"booking_id": "b1", "change_type": "extension_room_change",
                                         "new_check_out": "2026-05-13", "extension_room_ids": ["r2"]}]}
        asyncio.run(api.db.bookings.delete_many({"id": {"$in": ["b2", "b3"]}}))
    res = api.client.post("/api/bookings/b1/confirm-extension",
                          json={"new_check_out_date": "2026-05-13", "amendments": plan["proposed_amendments"]})
    assert res.status_code == 200, res.text
    stored = api.find_one("bookings", {"id": "b1"})
    assert stored["room_ids"] == ["r1", "r2"]
    assert stored["room_numbers"] == ["C1-01", "C1-02"]
    assert stored["room_categories"] == ["Cat I", "Cat I"]
    assert stored["total_amount"] == 1500
    fin = reported_total(api, "b1")
    assert fin["total_amount"] == 1500
    assert {r["room_number"]: r["nights"] for r in fin["rooms"]} == {"C1-01": 2, "C1-02": 1}


def test_moving_a_not_yet_arrived_booking_does_not_mark_its_new_room_occupied(api):
    api.seed("bookings", [
        booking(),
        booking(id="b2", booking_number="BK0002", guest_name="Next Guest",
                check_in_date="2026-05-12", check_out_date="2026-05-14"),
    ])
    checkin(api)
    plan = extend(api, "2026-05-13")
    assert plan["status"] == "shifted"
    moved = api.find_one("bookings", {"id": "b2"})
    assert moved["status"] == "confirmed" and moved["room_ids"] != ["r1"]
    new_room = api.find_one("rooms", {"id": moved["room_ids"][0]})
    assert new_room["status"] == "available", "nobody is in that room yet"
    assert api.find_one("rooms", {"id": "r1"})["status"] == "occupied"


# ====================================================================
# Amendment
# ====================================================================

def amend(api, **changes):
    body = {"booking_id": "b1", "check_in_date": "2026-05-10", "check_out_date": "2026-05-12", "room_ids": ["r1"]}
    body.update(changes)
    res = api.client.post("/api/bookings/amend", json=body)
    assert res.status_code == 200, res.text
    return res.json()["booking"]


def test_shortening_a_stay_does_not_invent_a_refund_the_guest_never_paid(api):
    """Rs 1,500 booking, Rs 400 advance, shortened to Rs 1,000: nothing is
    owed back (Rs 600 is still to pay). This used to record refund_due 500."""
    api.seed("bookings", [booking(check_out_date="2026-05-13", total_amount=1500.0, balance_amount=1100.0)])
    out = amend(api)
    assert out["total_amount"] == 1000
    assert out["refund_due"] == 0
    assert out["balance_amount"] == 600


def test_a_refund_is_due_only_for_advance_beyond_the_new_total(api):
    api.seed("bookings", [booking(check_out_date="2026-05-13", total_amount=1500.0, advance_paid=1200.0,
                                  balance_amount=300.0)])
    out = amend(api)
    assert out["total_amount"] == 1000 and out["refund_due"] == 200 and out["balance_amount"] == 0


def test_additional_advance_on_amendment_reaches_the_payments_ledger(api):
    api.seed("bookings", [booking()])
    out = amend(api, check_out_date="2026-05-13", additional_advance=500, payment_mode="Cash")
    assert out["total_amount"] == 1500 and out["advance_paid"] == 900 and out["balance_amount"] == 600
    payments = api.find("payments", {"booking_id": "b1"})
    assert [(p["payment_type"], p["amount"]) for p in payments] == [("advance", 500)]


def test_amending_a_mix_and_match_booking_drops_its_stale_night_plan(api):
    api.seed("bookings", [booking(**MIX)])
    res = api.client.post("/api/bookings/amend", json={
        "booking_id": "b1", "check_in_date": "2026-05-20", "check_out_date": "2026-05-22", "room_ids": ["r1", "r3"]})
    assert res.status_code == 200, res.text
    out = res.json()["booking"]
    assert out["room_segments"] is None and out["has_room_changes"] is False
    assert out["total_amount"] == 2 * (500 + 400)
    assert reported_total(api, "b1")["total_amount"] == out["total_amount"]


# ====================================================================
# Cancellation / refund
# ====================================================================

def test_cancellation_refund_slabs():
    assert cancellation_refund(400, 120)["refund_amount"] == 400      # > 96h: full refund
    assert cancellation_refund(400, 96)["refund_amount"] == 400       # boundary is inclusive
    assert cancellation_refund(400, 95.9)["refund_amount"] == 200     # 48-96h: half
    assert cancellation_refund(400, 48)["refund_amount"] == 200
    assert cancellation_refund(400, 47.9)["refund_amount"] == 0       # < 48h: nothing
    assert cancellation_refund(400, -5)["refund_amount"] == 0         # after check-in time
    assert cancellation_refund(0, 500)["refund_amount"] == 0
    assert cancellation_refund(None, 500)["refund_amount"] == 0


def test_cancellation_refund_custom_and_legacy_day_slabs():
    policy = [{"days_before": 7, "charge_percent": 10}, {"hours_before": 0, "charge_percent": 250}]
    assert cancellation_refund(1000, 8 * 24, policy) == {
        "charge_percent": 10.0, "cancellation_charge": 100.0, "refund_amount": 900.0}
    # A nonsense 250% charge can never produce a negative refund.
    assert cancellation_refund(1000, 10, policy)["refund_amount"] == 0


def far_future_booking(**overrides):
    check_in = (datetime.now(timezone.utc) + timedelta(days=30)).date()
    return booking(check_in_date=check_in.isoformat(), check_out_date=(check_in + timedelta(days=2)).isoformat(),
                   **overrides)


def test_cancel_without_an_amount_applies_the_policy_instead_of_refunding_nothing(api):
    api.seed("bookings", [far_future_booking()])
    res = api.client.post("/api/bookings/cancel", json={"booking_id": "b1", "reason": "test"})
    assert res.status_code == 200 and res.json()["refund_amount"] == 400
    refunds = api.find("refunds", {"booking_id": "b1"})
    assert [r["amount"] for r in refunds] == [400]


def test_cancel_preview_and_cancel_agree(api):
    api.seed("bookings", [far_future_booking()])
    preview = api.client.get("/api/bookings/b1/calculate-refund").json()
    done = api.client.post("/api/bookings/cancel", json={"booking_id": "b1"}).json()
    assert preview["refund_amount"] == done["refund_amount"] == 400


def test_cancel_refund_is_capped_at_the_advance_and_second_cancel_is_refused(api):
    api.seed("bookings", [far_future_booking()])
    first = api.client.post("/api/bookings/cancel", json={"booking_id": "b1", "refund_amount": 99999})
    assert first.status_code == 200
    second = api.client.post("/api/bookings/cancel", json={"booking_id": "b1", "refund_amount": 400})
    assert second.status_code == 400
    assert [r["amount"] for r in api.find("refunds", {"booking_id": "b1"})] == [400]


# ====================================================================
# Backup / restore
# ====================================================================

def test_backup_covers_every_collection_that_holds_real_data():
    from services.backup_service import COLLECTIONS_TO_BACKUP
    used = set(re.findall(r"\bdb\.([a-z_]+)\.", Path(server.__file__).read_text()))
    not_business_data = {"backup_metadata", "restore_logs", "migration_status", "counters", "command"}
    assert used - not_business_data <= set(COLLECTIONS_TO_BACKUP), \
        f"collections written by the app but missing from backups: {used - not_business_data - set(COLLECTIONS_TO_BACKUP)}"


def test_backup_then_restore_brings_back_payments_and_reports_success(api, tmp_path, monkeypatch):
    from services import backup_service
    monkeypatch.setattr(backup_service, "BACKUP_DIR", tmp_path)
    api.seed("bookings", [booking()])
    api.seed("payments", [{"id": "p1", "booking_id": "b1", "booking_number": "BK0001", "amount": 400,
                           "payment_type": "advance", "created_at": "2026-05-01T00:00:00+00:00"}])
    made = api.client.post("/api/backups/manual/full")
    assert made.status_code == 200, made.text
    backup_id = made.json()["backup"]["backup_id"]
    assert made.json()["backup"]["record_count"]["payments"] == 1

    asyncio.run(api.db.payments.delete_many({}))
    asyncio.run(api.db.bookings.delete_many({}))
    restored = api.client.post(f"/api/backups/restore/full/{backup_id}")
    assert restored.status_code == 200, "a successful restore must not be reported as a failure: " + restored.text
    assert api.find_one("payments", {"id": "p1"})["amount"] == 400
    assert api.find_one("bookings", {"id": "b1"})["booking_number"] == "BK0001"


def test_restore_by_date_range_finds_backups_taken_on_the_end_date(api, tmp_path, monkeypatch):
    from services import backup_service
    monkeypatch.setattr(backup_service, "BACKUP_DIR", tmp_path)
    api.seed("bookings", [booking()])
    assert api.client.post("/api/backups/manual/full").status_code == 200
    today = datetime.now(timezone.utc).date().isoformat()
    res = api.client.post("/api/backups/restore/range", json={"start_date": today, "end_date": today})
    assert res.status_code == 200, res.text
    assert res.json()["result"]["backups_restored"] == 1


def test_old_backups_are_actually_cleaned_up(api, tmp_path):
    from services import backup_service
    old_file = tmp_path / "old.json"
    old_file.write_text("{}")
    api.seed("backup_metadata", [
        {"backup_id": "old", "status": "SUCCESS", "file_path": str(old_file),
         "timestamp": (datetime.now(timezone.utc) - timedelta(days=200)).isoformat()},
        {"backup_id": "new", "status": "SUCCESS", "file_path": str(tmp_path / "new.json"),
         "timestamp": datetime.now(timezone.utc).isoformat()},
    ])
    deleted = asyncio.run(backup_service.cleanup_old_backups(api.db, retention_days=90))
    assert deleted == 1 and not old_file.exists()
    assert [b["backup_id"] for b in api.find("backup_metadata")] == ["new"]


# ====================================================================
# Setup
# ====================================================================

def test_setup_keeps_the_non_org_rate_it_was_given(api):
    asyncio.run(api.db.app_settings.delete_many({}))
    res = api.client.post("/api/settings/setup", json={"non_org_room_rent": 650, "non_org_license_fee": 50})
    assert res.status_code == 200, res.text
    saved = api.find_one("app_settings", {})
    assert saved["non_org_room_rent"] == 650 and saved["non_org_license_fee"] == 50


# ====================================================================
# Audit check (month-end reconciliation data source)
# ====================================================================

def test_audit_check_is_admin_only_and_read_only(api, monkeypatch):
    monkeypatch.setattr(server, "ist_today_str", lambda: "2026-06-17")
    api.seed("bookings", [booking(status="checked_out", actual_checkout_date="2026-05-12", charged_nights=2,
                                  charge_reason="normal", final_payment=600.0)])
    before = api.find("bookings")
    res = api.client.get("/api/reports/audit-check")
    assert res.status_code == 200, res.text
    assert api.find("bookings") == before, "diagnostic must not change data"
    api.as_role("staff")
    assert api.client.get("/api/reports/audit-check").status_code == 403


def test_audit_check_covers_only_the_previous_closed_month(api, monkeypatch):
    """Run on 17 Nov it audits 1-31 Oct and nothing else; in January it audits December."""
    api.seed("bookings", [
        booking(id="oct", booking_number="BKOCT", status="checked_out", check_in_date="2026-10-10",
                check_out_date="2026-10-12", actual_checkout_date="2026-10-12", charged_nights=2, charge_reason="normal",
                final_payment=600.0),
        booking(id="sep", booking_number="BKSEP", status="checked_out", check_in_date="2026-09-10",
                check_out_date="2026-09-12", actual_checkout_date="2026-09-12", charged_nights=2, charge_reason="normal",
                final_payment=600.0, room_ids=["r2"], room_numbers=["C1-02"]),
        booking(id="nov", booking_number="BKNOV", status="checked_out", check_in_date="2026-11-03",
                check_out_date="2026-11-05", actual_checkout_date="2026-11-05", charged_nights=2, charge_reason="normal",
                final_payment=0.0, room_ids=["r3"], room_numbers=["C2-07"], room_categories=["Cat II"]),
    ])
    monkeypatch.setattr(server, "ist_today_str", lambda: "2026-11-17")
    data = api.client.get("/api/reports/audit-check").json()
    assert data["audited_month"] == "2026-10"
    assert data["period"] == {"from": "2026-10-01", "to": "2026-10-31"}
    assert data["reports"]["consistent"] is True
    assert data["reports"]["totals"]["revenue"]["room_allotment"] == 1000     # October's one stay, not Sept or Nov
    assert data["checked_out_in_month"]["checked_out"] == 1
    assert "months" not in data and "2026-09" not in str(data) and "BKNOV" not in str(data)
    monkeypatch.setattr(server, "ist_today_str", lambda: "2027-01-05")
    assert api.client.get("/api/reports/audit-check").json()["audited_month"] == "2026-12"


# ====================================================================
# Found by the first live audit-check (18 Nov 2026)
# ====================================================================

def test_saving_settings_after_a_rate_change_does_not_reprice_old_bookings(api):
    """The Settings page shows today's in-force rate and sends it back on every
    Save; that used to overwrite the BASE rate and re-price every earlier booking."""
    api.seed("bookings", [booking(status="checked_out", actual_checkout_date="2026-07-12",
                                  check_in_date="2026-07-10", check_out_date="2026-07-12")])
    asyncio.run(api.db.app_settings.update_one({}, {"$set": {
        "cat_i_room_rent": 470, "cat_i_license_fee": 30,
        "rate_history": [{"id": "h", "effective_date": "2026-08-16", "cat_i_room_rent": 570}]}}))
    before = reported_total(api, "b1")["total_amount"]
    shown = api.client.get("/api/settings").json()
    assert shown["cat_i_room_rent"] == 570                      # page shows the new rate
    res = api.client.put("/api/settings", json={
        "cat_i_room_rent": shown["cat_i_room_rent"], "cat_i_license_fee": shown["cat_i_license_fee"],
        "default_advance_amount": 500})                         # admin only changed the advance
    assert res.status_code == 200
    saved = api.find_one("app_settings", {})
    assert saved["cat_i_room_rent"] == 470 and saved["default_advance_amount"] == 500
    assert reported_total(api, "b1")["total_amount"] == before == 1000


def test_a_genuinely_edited_rate_is_still_saved(api):
    assert api.client.put("/api/settings", json={"cat_ii_room_rent": 400}).status_code == 200
    assert api.find_one("app_settings", {})["cat_ii_room_rent"] == 400


def _mixed_backup_records(api):
    new = datetime.now(timezone.utc) - timedelta(days=1)
    old = datetime(2026, 4, 11, 8, 52, 43)               # a real date, as before 11 May 2026
    api.seed("backup_metadata", [
        {"backup_id": "apr", "status": "SUCCESS", "backup_type": "FULL", "timestamp": old},
        {"backup_id": "nov", "status": "SUCCESS", "backup_type": "INCREMENTAL", "timestamp": new.isoformat()},
        {"backup_id": "bad", "status": "FAILED", "backup_type": "FULL", "timestamp": datetime.now(timezone.utc)},
    ])


def test_latest_backup_is_the_newest_not_the_newest_stored_as_a_date(api):
    from services import backup_service
    _mixed_backup_records(api)
    assert asyncio.run(backup_service.get_last_backup_metadata(api.db))["backup_id"] == "nov"
    assert [b["backup_id"] for b in asyncio.run(backup_service.get_backup_history(api.db))][:2] == ["bad", "nov"]
    summary = api.client.get("/api/reports/audit-check").json()["current_state"]["backups"]
    assert summary["successful_total"] == 2 and summary["successful_last_30_days"] == 1
    assert summary["stored_as_dates_not_text"] == 1 and summary["hours_since_latest"] < 30


def test_backup_status_does_not_call_a_recent_backup_overdue(api):
    _mixed_backup_records(api)
    status = api.client.get("/api/backups/status").json()
    assert status["last_backup"]["backup_id"] == "nov"
    assert status["missed_backup_warning"]["missed"] is False


def test_restore_last_backup_picks_the_newest(api, tmp_path):
    from services import restore_service
    _mixed_backup_records(api)
    asyncio.run(api.db.backup_metadata.update_one({"backup_id": "nov"}, {"$set": {"file_path": str(tmp_path / "x.json")}}))
    (tmp_path / "x.json").write_text('{"collections": {}}')
    result = asyncio.run(restore_service.restore_last_backup(api.db))
    assert result["backup_id"] == "nov"


def test_audit_check_lists_every_unexplained_booking_in_the_month(api, monkeypatch):
    monkeypatch.setattr(server, "ist_today_str", lambda: "2026-06-17")
    api.seed("bookings", [
        # billed as Cat I, reported as Cat II: reported is 100 a night lower, no tag explains it
        booking(status="checked_out", actual_checkout_date="2026-05-12", charged_nights=2, charge_reason="normal",
                final_payment=0.0, room_ids=["r3"], room_numbers=["C2-07"], room_categories=["Cat II"],
                total_amount=1000.0, advance_paid=800.0),
        booking(id="b2", booking_number="BK0002", status="checked_out", actual_checkout_date="2026-05-12",
                charged_nights=2, charge_reason="normal", total_amount=1000.0, advance_paid=400.0, final_payment=600.0,
                room_ids=["r2"], room_numbers=["C1-02"]),
    ])
    data = api.client.get("/api/reports/audit-check").json()
    assert [u["bk"] for u in data["unexplained"]] == ["BK0001"]
    summ = data["checked_out_in_month"]
    assert summ["differ_from_billed"] == 1 and summ["reported_minus_billed"] == -200
    assert summ["by_cause"] == {"unexplained": {"bookings": 1, "reported_minus_billed": -200.0}}
    assert summ["reported"] == 1800 and summ["collected"] == 1800 and summ["reported_but_not_collected"] == 0


# ====================================================================
# Owner rulings, Nov 2026: extra beds at check-out only; late check-outs billed for nights stayed
# ====================================================================

def test_late_checkout_is_billed_for_the_nights_actually_stayed(api):
    api.seed("bookings", [booking()])                                  # booked 10-12 May, Rs 500/night
    checkin(api)
    out = checkout(api, actual_checkout_date="2026-05-14", final_payment=1600)
    assert out["charge_reason"] == "late_checkout" and out["charged_nights"] == 4
    assert out["total_amount"] == 2000 and out["room_rent_total"] == 4 * 470
    assert out["balance_amount"] == 0
    assert reported_total(api, "b1")["total_amount"] == 2000, "stored bill and reports must agree"


def test_late_checkout_of_a_mix_and_match_stay_bills_and_reports_the_extra_nights_in_the_last_room(api):
    api.seed("bookings", [booking(**MIX)])
    checkin(api)
    out = checkout(api, actual_checkout_date="2026-05-16")            # booked to the 14th, left the 16th
    assert out["total_amount"] == 1800 + 2 * 400
    assert [seg["night_date"] for seg in out["room_segments"]][-2:] == ["2026-05-14", "2026-05-15"]
    assert reported_total(api, "b1")["total_amount"] == 2600


def test_on_time_and_early_checkouts_are_unchanged_by_the_late_rule(api):
    api.seed("bookings", [booking(check_out_date="2026-05-14", total_amount=2000.0)])
    checkin(api, planned_early_checkout_date="2026-05-12")
    out = checkout(api, actual_checkout_date="2026-05-12")
    assert out["charge_reason"] == "early_checkout_informed" and out["total_amount"] == 1000


def test_extra_bed_is_charged_at_checkout_for_beds_times_days_used(api):
    api.seed("bookings", [booking(check_out_date="2026-05-14", total_amount=2000.0)])
    checkin(api, extra_beds=2)                                         # noted at check-in: not charged
    out = checkout(api, actual_checkout_date="2026-05-14", extra_beds_checkout=1, extra_bed_days=3)
    assert out["extra_bed_charge_checkout"] == 225
    assert out["total_amount"] == 2000 + 225
    assert reported_total(api, "b1")["total_amount"] == 2225
    assert reported_total(api, "b1")["extra_bed_charge"] == 225


def test_a_guest_who_asked_for_a_bed_only_at_checkout_is_charged_for_it(api):
    api.seed("bookings", [booking()])
    checkin(api)                                                        # no extra bed at check-in
    out = checkout(api, actual_checkout_date="2026-05-12", extra_beds_checkout=2, extra_bed_days=1)
    assert out["total_amount"] == 1000 + 150 and reported_total(api, "b1")["total_amount"] == 1150


def test_checkout_quote_equals_the_bill_check_out_stores_and_changes_nothing(api):
    api.seed("bookings", [booking(check_out_date="2026-05-14", total_amount=2000.0)])
    checkin(api)
    before = api.find_one("bookings", {"id": "b1"})
    q = api.client.get("/api/bookings/b1/checkout-quote", params={
        "actual_checkout_date": "2026-05-15", "extra_beds": 1, "extra_bed_days": 2}).json()
    assert api.find_one("bookings", {"id": "b1"}) == before
    assert q["charged_nights"] == 5 and q["room_total"] == 2500 and q["extra_bed_charge"] == 150
    assert q["total_due"] == 2650 and q["amount_due_now"] == 2650 - 400 and q["charge_reason"] == "late_checkout"
    out = checkout(api, actual_checkout_date="2026-05-15", extra_beds_checkout=1, extra_bed_days=2, final_payment=2250)
    assert out["total_amount"] == q["total_due"] and out["balance_amount"] == 0


def test_checkout_quote_shows_an_overpaid_guest_as_negative_and_rejects_bad_input(api):
    api.seed("bookings", [booking(advance_paid=1500.0)])
    checkin(api)
    q = api.client.get("/api/bookings/b1/checkout-quote", params={"actual_checkout_date": "2026-05-12"}).json()
    assert q["amount_due_now"] == -500
    assert api.client.get("/api/bookings/b1/checkout-quote", params={"actual_checkout_date": "tomorrow"}).status_code == 400
    assert api.client.get("/api/bookings/nope/checkout-quote").status_code == 404
