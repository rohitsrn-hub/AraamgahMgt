"""
Backups: download to the computer that asked, a copy kept in the database
(files on a free Render server vanish on every deploy), and a backup taken
whenever the app is in use and the last one is old (a sleeping free server
cannot run a 2 am job).
"""
import asyncio
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from inprocess import api, server  # noqa: F401
from services import backup_service, restore_service, scheduler_service
from test_audit_endpoints import booking


@pytest.fixture(autouse=True)
def fresh_state(tmp_path, monkeypatch):
    monkeypatch.setattr(backup_service, "BACKUP_DIR", tmp_path)
    scheduler_service._state.update({"checked_at": None, "failed_at": None, "running": False})
    yield


def seed_world(api):
    api.seed("bookings", [booking()])
    api.seed("payments", [{"id": "p1", "booking_id": "b1", "amount": 400, "payment_type": "advance",
                           "created_at": "2026-05-01T00:00:00+00:00"}])
    api.seed("users", [{"id": "u1", "email": "owner", "name": "Owner", "role": "admin", "is_active": True,
                        "password_hash": "$2b$12$SECRETHASH"}])


# ---------------- download ----------------

def test_download_is_a_complete_file_without_logins_and_is_admin_only(api):
    seed_world(api)
    res = api.client.get("/api/backups/download")
    assert res.status_code == 200
    assert "attachment" in res.headers["content-disposition"] and ".json" in res.headers["content-disposition"]
    assert "SECRETHASH" not in res.text and "password_hash" not in res.text
    data = res.json()
    assert "users" not in data["collections"]
    assert data["users_reference"] == [{"email": "owner", "name": "Owner", "role": "admin", "is_active": True}]
    assert [b["id"] for b in data["collections"]["bookings"]] == ["b1"]
    assert data["collections"]["payments"][0]["amount"] == 400
    note = api.find("backup_downloads")
    assert len(note) == 1 and note[0]["record_count"]["bookings"] == 1
    api.as_role("staff")
    assert api.client.get("/api/backups/download").status_code == 403
    api.as_role("viewer")
    assert api.client.get("/api/backups/download").status_code == 403


def test_audit_check_and_status_show_the_last_download(api, monkeypatch):
    monkeypatch.setattr(server, "ist_today_str", lambda: "2026-12-05")
    seed_world(api)
    assert api.client.get("/api/reports/audit-check").json()["current_state"]["backups"]["last_download_to_a_computer"] is None
    api.client.get("/api/backups/download")
    state = api.client.get("/api/reports/audit-check").json()["current_state"]["backups"]
    assert state["last_download_to_a_computer"]["by"] == "test-admin"
    assert api.client.get("/api/backups/status").json()["last_download"]["by"] == "test-admin"


# ---------------- copy kept in the database ----------------

def test_a_backup_survives_the_server_losing_its_files(api):
    seed_world(api)
    made = api.client.post("/api/backups/manual/full").json()["backup"]
    assert made["stored_in_database"] is True and made["record_count"]["payments"] == 1
    Path(made["file_path"]).unlink()                                   # a redeploy wipes the disk
    asyncio.run(api.db.payments.delete_many({}))
    asyncio.run(api.db.bookings.delete_many({}))
    res = api.client.post(f"/api/backups/restore/full/{made['backup_id']}")
    assert res.status_code == 200, res.text
    assert api.find_one("payments", {"id": "p1"})["amount"] == 400
    assert api.find_one("bookings", {"id": "b1"}) is not None
    assert asyncio.run(backup_service.validate_backup(made["backup_id"], api.db)) is True


def test_backup_still_succeeds_when_the_disk_cannot_be_written(api, monkeypatch):
    seed_world(api)
    monkeypatch.setattr(backup_service, "BACKUP_DIR", Path("/proc/definitely/not/writable"))
    made = asyncio.run(backup_service.perform_full_backup(api.db))
    assert made["status"] == "SUCCESS" and made["file_path"] is None
    assert api.find_one("backup_snapshots", {"backup_id": made["backup_id"]}) is not None


def test_cleanup_removes_the_database_copy_with_the_record(api):
    seed_world(api)
    made = asyncio.run(backup_service.perform_full_backup(api.db))
    asyncio.run(api.db.backup_metadata.update_one(
        {"backup_id": made["backup_id"]}, {"$set": {"timestamp": (datetime.now(timezone.utc) - timedelta(days=200)).isoformat()}}))
    assert asyncio.run(backup_service.cleanup_old_backups(api.db, retention_days=90)) == 1
    assert api.find("backup_snapshots") == [] and api.find("backup_metadata") == []


# ---------------- backup on use / daily ----------------

def full_backup_count(api):
    return len([b for b in api.find("backup_metadata") if b["status"] == "SUCCESS" and b["backup_type"] == "FULL"])


def test_a_backup_is_taken_on_use_only_when_the_last_one_is_old(api):
    seed_world(api)
    assert asyncio.run(scheduler_service.ensure_recent_backup(api.db)) is not None      # none yet -> take one
    assert full_backup_count(api) == 1
    assert asyncio.run(scheduler_service.ensure_recent_backup(api.db)) is None          # fresh -> nothing
    assert full_backup_count(api) == 1
    asyncio.run(api.db.backup_metadata.update_many({}, {"$set": {
        "timestamp": (datetime.now(timezone.utc) - timedelta(hours=21)).isoformat()}}))
    assert asyncio.run(scheduler_service.ensure_recent_backup(api.db)) is not None      # 21h old -> take one
    assert full_backup_count(api) == 2


def test_the_daily_job_always_takes_one(api):
    seed_world(api)
    asyncio.run(scheduler_service.ensure_recent_backup(api.db))
    asyncio.run(scheduler_service.ensure_recent_backup(api.db, max_age_hours=0))
    assert full_backup_count(api) == 2


def test_only_one_backup_runs_at_a_time_and_a_failure_waits_before_retrying(api, monkeypatch):
    seed_world(api)
    calls = []

    async def failing(db):
        calls.append(1)
        raise RuntimeError("disk full")

    monkeypatch.setattr(scheduler_service, "perform_full_backup", failing)

    async def burst():
        return await asyncio.gather(*[scheduler_service.ensure_recent_backup(api.db) for _ in range(5)])

    assert asyncio.run(burst()) == [None] * 5
    assert len(calls) == 1, "five simultaneous requests must start one backup"
    assert asyncio.run(scheduler_service.ensure_recent_backup(api.db)) is None
    assert len(calls) == 1, "must not retry within the hour after a failure"
    scheduler_service._state["failed_at"] -= 4000
    asyncio.run(scheduler_service.ensure_recent_backup(api.db))
    assert len(calls) == 2


def test_using_the_app_triggers_a_backup_but_checks_only_every_ten_minutes(api):
    seed_world(api)

    async def use_the_app():
        scheduler_service.maybe_trigger_backup(api.db)
        scheduler_service.maybe_trigger_backup(api.db)       # throttled: ignored
        await asyncio.gather(*list(scheduler_service._tasks))

    asyncio.run(use_the_app())
    assert full_backup_count(api) == 1
    assert scheduler_service._state["checked_at"] is not None


def test_the_saved_backup_time_is_used_at_startup(api, monkeypatch):
    seen = {}

    async def no_migrations(db):
        return {"status": "already_completed"}

    async def not_missed(db):
        return {"missed": False}

    monkeypatch.setattr(server, "run_startup_migrations", no_migrations)
    monkeypatch.setattr(scheduler_service, "init_scheduler", lambda db, hour, minute: seen.update(hour=hour, minute=minute))
    monkeypatch.setattr(scheduler_service, "check_missed_backups", not_missed)
    asyncio.run(server.startup_event())
    assert (seen["hour"], seen["minute"]) == (14, 0)                       # default: the working day
    asyncio.run(api.db.app_settings.update_one({}, {"$set": {"backup_schedule": {"hour": 9, "minute": 30}}}))
    asyncio.run(server.startup_event())
    assert (seen["hour"], seen["minute"]) == (9, 30)


# ---------------- restore from a downloaded file ----------------

def test_restore_from_a_downloaded_file_adds_missing_keeps_newer_and_dry_run_changes_nothing(api):
    seed_world(api)
    data = api.client.get("/api/backups/download").json()
    asyncio.run(api.db.bookings.delete_many({}))
    live = api.find_one("payments", {"id": "p1"})
    asyncio.run(api.db.payments.update_one({"id": "p1"}, {"$set": {"amount": 999, "updated_at": "2030-01-01T00:00:00+00:00"}}))
    dry = asyncio.run(restore_service.merge_backup_data(data, api.db, dry_run=True))
    assert dry["bookings"]["added"] == 1 and api.find("bookings") == []
    assert dry["payments"]["kept_live_version"] == 1
    asyncio.run(restore_service.merge_backup_data(data, api.db))
    assert api.find_one("bookings", {"id": "b1"})["booking_number"] == "BK0001"
    assert api.find_one("payments", {"id": "p1"})["amount"] == 999, "a newer live record is never overwritten"
    assert live is not None
