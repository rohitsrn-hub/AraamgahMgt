"""
Owner-approved clean-up (Nov 2026): Net Revenue = cash received, no cancelling
after check-in, room renames admin-only, real room count in the Monthly
Report, password rule on user edit, login lockout, and the backup-file check.
"""
import asyncio
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from inprocess import api, server  # noqa: F401
from test_audit_endpoints import booking


# ---------------- Net Revenue = cash received - refunds ----------------

def pay(pid, kind, amount, at):
    return {"id": pid, "booking_id": "b1", "booking_number": "BK0001", "amount": amount, "payment_type": kind, "created_at": at}


def funds(api, month=10, year=2026):
    return api.client.get(f"/api/dashboard/funds?month={month}&year={year}").json()


def test_net_revenue_counts_each_rupee_once(api):
    """Rs 1,000 stay: Rs 400 advance + Rs 600 at check-out = Rs 1,000 in. It used to show Rs 1,400."""
    api.seed("payments", [pay("a", "advance", 400, "2026-10-05T10:00:00+00:00"), pay("f", "final", 600, "2026-10-07T10:00:00+00:00")])
    f = funds(api)
    assert (f["advance_booking_amount"], f["completed_stays_amount"], f["cash_received"], f["net_revenue"]) == (400, 600, 1000, 1000)


def test_net_revenue_subtracts_refunds_and_money_handed_back_at_checkout(api):
    api.seed("payments", [pay("a", "advance", 1500, "2026-10-05T10:00:00+00:00"), pay("r", "refund", -200, "2026-10-09T10:00:00+00:00")])
    api.seed("bookings", [booking(status="checked_out", final_payment=-300.0, actual_check_out="2026-10-07T10:00:00+00:00")])
    f = funds(api)
    assert f["refunds_issued"] == 500 and f["net_revenue"] == 1000


def test_net_revenue_months_are_ist_months(api):
    # 19:00 UTC on 31 Oct = 00:30 IST on 1 Nov -> November's money
    api.seed("payments", [pay("late", "advance", 400, "2026-10-31T19:00:00+00:00"), pay("oct", "advance", 100, "2026-10-31T10:00:00+00:00")])
    assert funds(api, 10)["net_revenue"] == 100
    assert funds(api, 11)["net_revenue"] == 400


# ---------------- cancelling after check-in ----------------

def test_a_checked_in_guest_cannot_be_cancelled_and_nothing_changes(api):
    api.seed("bookings", [booking(status="checked_in")])
    res = api.client.post("/api/bookings/cancel", json={"booking_id": "b1"})
    assert res.status_code == 400 and "Check Out" in res.json()["detail"]
    assert api.find_one("bookings", {"id": "b1"})["status"] == "checked_in" and api.find("refunds") == []


# ---------------- room edits ----------------

def test_staff_can_set_room_status_but_not_rename_or_recategorise(api):
    api.as_role("staff")
    assert api.client.put("/api/rooms/r1", json={"status": "maintenance"}).status_code == 200
    for body in ({"room_number": "C9-99"}, {"category": "Cat II"}, {"floor": 3}):
        assert api.client.put("/api/rooms/r1", json=body).status_code == 403, body
    assert api.find_one("rooms", {"id": "r1"})["room_number"] == "C1-01"
    api.as_role("admin")
    assert api.client.put("/api/rooms/r1", json={"room_number": "C1-09"}).status_code == 200


# ---------------- Monthly Report room count ----------------

def test_monthly_report_uses_the_rooms_that_exist_not_the_settings_count(api):
    asyncio.run(api.db.app_settings.update_one({}, {"$set": {"cat_i_rooms_count": 6, "cat_ii_rooms_count": 9}}))
    assert api.client.get("/api/reports/monthly?month=5&year=2026").json()["total_rooms"] == 4     # the harness has 4 rooms


# ---------------- user password ----------------

def test_editing_a_user_cannot_set_a_short_password(api):
    api.seed("users", [{"id": "u1", "email": "x", "name": "Xavier", "role": "staff", "is_active": True,
                        "password_hash": "h", "created_at": "2026-01-01T00:00:00+00:00"}])
    assert api.client.put("/api/users/u1", json={"password": "a"}).status_code == 400
    assert api.client.put("/api/users/u1", json={"password": 12345678}).status_code == 400
    assert api.client.put("/api/users/u1", json={"password": "long-enough-1"}).status_code == 200
    assert api.find_one("users", {"id": "u1"})["password_hash"] != "h"


# ---------------- login lockout ----------------

def login(api, user, password, ip=None):
    headers = {"X-Forwarded-For": ip} if ip else {}
    return api.client.post("/api/auth/login", json={"email": user, "password": password}, headers=headers)


def seed_login_user(api):
    api.seed("users", [{"id": "u1", "email": "owner", "name": "Owner", "role": "admin", "is_active": True,
                        "password_hash": server.hash_password("correct-horse"), "created_at": "2026-01-01T00:00:00+00:00"}])


def test_five_wrong_passwords_lock_that_user_from_that_address_even_for_the_right_password(api):
    seed_login_user(api)
    for _ in range(5):
        assert login(api, "owner", "wrong", "1.1.1.1").status_code == 401
    res = login(api, "owner", "correct-horse", "1.1.1.1")
    assert res.status_code == 429 and "minute" in res.json()["detail"]
    assert login(api, "owner", "correct-horse", "2.2.2.2").status_code == 200, "the real user from elsewhere is not locked out"
    assert login(api, "someone-else", "wrong", "1.1.1.1").status_code == 401, "other usernames from that address are not locked yet"


def test_a_correct_login_clears_the_failures(api):
    seed_login_user(api)
    for _ in range(4):
        login(api, "owner", "wrong", "1.1.1.1")
    assert login(api, "owner", "correct-horse", "1.1.1.1").status_code == 200
    for _ in range(4):
        assert login(api, "owner", "wrong", "1.1.1.1").status_code == 401     # counting starts again from zero
    assert login(api, "owner", "correct-horse", "1.1.1.1").status_code == 200


def test_failures_age_out_after_the_window(api):
    seed_login_user(api)
    for _ in range(5):
        login(api, "owner", "wrong", "1.1.1.1")
    old = (datetime.now(timezone.utc) - timedelta(minutes=16)).isoformat()
    asyncio.run(api.db.login_failures.update_many({}, {"$set": {"at": old}}))
    assert login(api, "owner", "correct-horse", "1.1.1.1").status_code == 200


def test_one_address_guessing_many_usernames_is_stopped(api):
    for i in range(30):
        assert login(api, f"user{i}", "x", "3.3.3.3").status_code == 401
    assert login(api, "user99", "x", "3.3.3.3").status_code == 429
    assert login(api, "user99", "x", "4.4.4.4").status_code == 401


def test_the_address_used_is_the_last_forwarded_one_so_it_cannot_be_faked(api):
    seed_login_user(api)
    for i in range(5):                   # caller varies the fake leading entry; the proxy's (last) entry is constant
        login(api, "owner", "wrong", f"9.9.9.{i}, 5.5.5.5")
    assert login(api, "owner", "correct-horse", "8.8.8.8, 5.5.5.5").status_code == 429


# ---------------- backup files ----------------

def test_audit_check_tells_whether_backup_files_survive_redeploys(api, tmp_path, monkeypatch):
    from services import backup_service
    monkeypatch.setattr(backup_service, "BACKUP_DIR", tmp_path)
    api.seed("bookings", [booking()])
    first = asyncio.run(backup_service.perform_full_backup(api.db))
    second = asyncio.run(backup_service.perform_full_backup(api.db))
    Path(first["file_path"]).unlink()                                   # a redeploy wipes one of them
    state = api.client.get("/api/reports/audit-check").json()["current_state"]["backups"]
    assert (state["successful_total"], state["files_still_on_server"], state["files_missing_from_server"]) == (2, 1, 1)
    assert state["kept_in_database_too"] == 2 and second["file_path"]


# ---------------- found by the first full month check (Oct 2026) ----------------

def test_audit_check_lists_the_bookings_behind_reported_but_not_collected(api, monkeypatch):
    monkeypatch.setattr(server, "ist_today_str", lambda: "2026-06-17")
    api.seed("bookings", [
        booking(status="checked_out", actual_checkout_date="2026-05-12", charged_nights=2, charge_reason="normal",
                total_amount=1000.0, advance_paid=400.0, final_payment=0.0, balance_amount=600.0, payment_mode="cash"),
        booking(id="b2", booking_number="BK0002", status="checked_out", actual_checkout_date="2026-05-12", charged_nights=2,
                charge_reason="normal", total_amount=1000.0, advance_paid=400.0, final_payment=700.0, room_ids=["r2"], room_numbers=["C1-02"]),
        booking(id="b3", booking_number="BK0003", status="checked_out", actual_checkout_date="2026-05-12", charged_nights=2,
                charge_reason="normal", total_amount=1000.0, advance_paid=400.0, final_payment=600.0, room_ids=["r3"], room_numbers=["C2-07"], room_categories=["Cat I"]),
    ])
    data = api.client.get("/api/reports/audit-check").json()
    assert [r["bk"] for r in data["under_collected"]] == ["BK0001"]
    assert data["under_collected"][0]["short_by"] == 600 and data["under_collected"][0]["advance"] == 400
    assert data["under_collected"][0]["balance_on_record"] == 600
    assert [r["bk"] for r in data["over_collected"]] == ["BK0002"] and data["over_collected"][0]["extra"] == 100
    assert data["checked_out_in_month"]["reported_but_not_collected"] == 600


def test_backup_history_says_which_backups_can_really_be_restored(api, tmp_path):
    from services import backup_service
    api.seed("backup_metadata", [
        {"backup_id": "lost", "status": "SUCCESS", "backup_type": "FULL", "timestamp": "2026-10-01T00:00:00+00:00",
         "file_path": str(tmp_path / "gone.json")},
        {"backup_id": "kept", "status": "SUCCESS", "backup_type": "FULL", "timestamp": "2026-11-01T00:00:00+00:00",
         "file_path": None, "stored_in_database": True},
        {"backup_id": "bad", "status": "FAILED", "backup_type": "FULL", "timestamp": "2026-11-02T00:00:00+00:00"},
    ])
    history = {b["backup_id"]: b["restorable"] for b in asyncio.run(backup_service.get_backup_history(api.db))}
    assert history == {"lost": False, "kept": True, "bad": False}


# ---------------- Monthly Report: printed lines must add up ----------------

def test_monthly_report_gives_real_per_category_rent_that_adds_up_to_the_subtotal(api):
    """After a rate revision, days x today's base rate no longer equals what was billed. The report
    must hand the screens the real per-category totals (and billed days, which include an
    uninformed early check-out's penalty nights) so every printed line adds up."""
    asyncio.run(api.db.app_settings.update_one({}, {"$set": {
        "cat_i_room_rent": 470, "cat_i_license_fee": 30, "cat_ii_room_rent": 385, "cat_ii_license_fee": 15,
        "non_org_room_rent": 570, "non_org_license_fee": 30,
        "rate_history": [{"id": "h", "effective_date": "2026-08-16", "cat_i_room_rent": 670, "cat_ii_room_rent": 585,
                          "non_org_room_rent": 770}]}}))
    api.seed("bookings", [
        booking(status="checked_out", check_in_date="2026-10-10", check_out_date="2026-10-12", actual_checkout_date="2026-10-12"),
        booking(id="b2", booking_number="BK0002", status="checked_out", check_in_date="2026-10-10", check_out_date="2026-10-13",
                actual_checkout_date="2026-10-11", charge_reason="early_checkout_not_informed",    # 1 night stayed, 3 billed
                room_ids=["r3"], room_numbers=["C2-07"], room_categories=["Cat II"]),
    ])
    rep = api.client.get("/api/reports/monthly?month=10&year=2026").json()
    cat = rep["room_rent_by_category"]
    assert cat["org_cat_i"] == {"days": 2, "billed_days": 2, "total": 1340.0, "avg_rate": 670.0}
    assert cat["org_cat_ii"] == {"days": 1, "billed_days": 3, "total": 1755.0, "avg_rate": 585.0}
    assert round(sum(c["total"] for c in cat.values()), 2) == rep["room_rent_total"] == 3095.0
    lf = rep["license_fees"]
    assert lf["org_cat_ii"]["billed_days"] * lf["org_cat_ii"]["rate"] == lf["org_cat_ii"]["total"] == 45
    assert rep["grand_total"] == rep["room_rent_total"] + rep["total_license_fee"] + rep["extra_bed_amount"]


# ---------------- overdue check-out reminder ----------------

def test_overdue_checkout_reminder_lists_checked_in_guests_past_their_booked_date(api, monkeypatch):
    monkeypatch.setattr(server, "ist_today_str", lambda: "2026-05-20")
    api.seed("bookings", [
        booking(id="late", booking_number="BKLATE", status="checked_in", check_in_date="2026-05-10", check_out_date="2026-05-12"),
        booking(id="today", booking_number="BKTODAY", status="checked_in", check_in_date="2026-05-18", check_out_date="2026-05-20",
                room_ids=["r2"], room_numbers=["C1-02"]),                    # due today: not overdue yet
        booking(id="conf", booking_number="BKCONF", status="confirmed", check_in_date="2026-05-10", check_out_date="2026-05-12",
                room_ids=["r3"], room_numbers=["C2-07"]),                    # never checked in: the other banner
        booking(id="out", booking_number="BKOUT", status="checked_out", check_in_date="2026-05-10", check_out_date="2026-05-12",
                room_ids=["r4"], room_numbers=["C2-08"]),
    ])
    data = api.client.get("/api/bookings/overdue-checkout").json()
    assert data["count"] == 1
    assert data["bookings"][0]["booking_number"] == "BKLATE" and data["bookings"][0]["days_overdue"] == 8
    assert data["bookings"][0]["rooms"] == ["C1-01"]
    # reminding changes nothing, and it does not block the room (deliberate overstay rule)
    assert api.find_one("bookings", {"id": "late"})["status"] == "checked_in"
    api.as_role("viewer")
    assert api.client.get("/api/bookings/overdue-checkout").status_code == 403
