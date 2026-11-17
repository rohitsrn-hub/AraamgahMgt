"""
Owner-approved corrections to specific LIVE records (Nov 2026), done safely.

Why this exists as an in-app action: the live database cannot be reached from
a development session, and a live-data change needs a record of the original
values and a way back. So the change is:

  * limited to the bookings named below (nothing is found by pattern);
  * previewed first, changing nothing;
  * guarded: a record is changed only if it still holds the values the audit
    saw, and the shared money engine (utils/report_calc) still gives the
    amount the owner approved — otherwise it is skipped and says why;
  * preceded by a full backup;
  * logged: every original value is kept in the `data_corrections` collection
    and an entry is added to the booking's own amendment log;
  * undoable: Undo restores the original values (and refuses, field by field,
    if the record has been changed since).

Reports are NOT affected by any of these corrections: every report computes
money from booking_financials(), never from the stored bill. These fix the
stored bill (what the booking list and receipts show) and a stale field.
"""
import logging
import uuid
from datetime import date, datetime, timezone
from typing import Dict, List

from utils.report_calc import booking_financials, build_room_maps
from services import backup_service

logger = logging.getLogger(__name__)

# booking_number -> the total the shared engine must give for the correction to be applied.
# (From the 18 Nov 2026 October audit: the engine, reports and cash agree on these amounts;
# the stored bill is the odd one out.)
APPROVED_BILL_CORRECTIONS = {
    "BK1284": 1200.0,   # billed at a Cat I rate for a Cat II room: stored 1400, reports and cash 1200
    "BK1032": 2325.0,   # late check-out billed under the pre-ruling rule: stored 1625, reports and cash 2325
}

# booking_number -> the stale "refund due" value the audit saw. Correct value is
# max(0, advance paid - total), which is 0 for every one of these.
APPROVED_REFUND_DUE_RESETS = {
    "BK1294": 1100.0, "BK1327": 300.0, "BK1347": 300.0, "BK1348": 300.0, "BK1359": 2200.0,
    "BK1365": 200.0, "BK1370": 500.0, "BK1372": 600.0, "BK1443": 800.0, "BK1447": 600.0,
}

WIDE = (date(2000, 1, 1), date(2100, 1, 1))
BILL_FIELDS = ("total_amount", "balance_amount", "room_rent_total", "license_fee_total", "charged_nights", "charge_reason")
REFUND_FIELDS = ("refund_due", "refund_reason")


def _num(v) -> float:
    return round(float(v or 0), 2)


async def plan_corrections(db) -> List[Dict]:
    """What would change, without changing anything."""
    settings = await db.app_settings.find_one({}, {"_id": 0}) or {}
    room_maps = build_room_maps(await db.rooms.find({}, {"_id": 0}).to_list(500))
    plan = []

    for number, expected in APPROVED_BILL_CORRECTIONS.items():
        bk = await db.bookings.find_one({"booking_number": number}, {"_id": 0})
        item = {"booking_number": number, "kind": "bill", "status": "skipped", "reason": None, "before": {}, "after": {}}
        plan.append(item)
        if not bk:
            item["reason"] = "booking not found"
            continue
        if bk.get("status") != "checked_out":
            item["reason"] = f"booking is {bk.get('status')}, not checked out"
            continue
        fin = booking_financials(bk, settings, *WIDE, room_maps)
        if _num(fin["total_amount"]) != _num(expected):
            item["reason"] = f"the money engine now gives {fin['total_amount']}, not the approved {expected} — not applied"
            continue
        if _num(bk.get("total_amount")) == _num(expected):
            item["reason"] = "stored bill already correct"
            continue
        collected = _num(bk.get("advance_paid")) + _num(bk.get("final_payment"))
        after = {
            "total_amount": _num(fin["total_amount"]),
            "balance_amount": round(_num(fin["total_amount"]) - collected, 2),
            "room_rent_total": _num(fin["room_rent"]),
            "license_fee_total": _num(fin["license_fee"]),
        }
        actual_out, booked_out = bk.get("actual_checkout_date") or "", bk.get("check_out_date") or ""
        if actual_out > booked_out:     # a late check-out: record it the way check-out now does
            after["charged_nights"] = (date.fromisoformat(actual_out) - date.fromisoformat(bk["check_in_date"][:10])).days
            after["charge_reason"] = "late_checkout"
        item.update(status="ready", booking_id=bk["id"],
                    before={k: bk.get(k) for k in after}, after=after)

    for number, seen in APPROVED_REFUND_DUE_RESETS.items():
        bk = await db.bookings.find_one({"booking_number": number}, {"_id": 0})
        item = {"booking_number": number, "kind": "refund_due", "status": "skipped", "reason": None, "before": {}, "after": {}}
        plan.append(item)
        if not bk:
            item["reason"] = "booking not found"
            continue
        if bk.get("status") not in ("confirmed", "checked_in"):
            item["reason"] = f"booking is {bk.get('status')} now"
            continue
        if _num(bk.get("refund_due")) != _num(seen):
            item["reason"] = f"stored refund due is {bk.get('refund_due')} now, not the {seen} the audit saw — not applied"
            continue
        if max(0.0, _num(bk.get("advance_paid")) - _num(bk.get("total_amount"))) != 0:
            item["reason"] = "the advance now exceeds the total, so a refund really is due — not applied"
            continue
        after = {"refund_due": 0.0, "refund_reason": None}
        item.update(status="ready", booking_id=bk["id"], before={k: bk.get(k) for k in after}, after=after)
    return plan


async def apply_corrections(db, user: str) -> Dict:
    plan = await plan_corrections(db)
    ready = [p for p in plan if p["status"] == "ready"]
    if not ready:
        return {"batch_id": None, "applied": 0, "plan": plan, "message": "Nothing to apply."}

    # Safety copy first. If it fails, change nothing.
    backup = await backup_service.perform_full_backup(db)
    batch_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    applied = 0
    for p in ready:
        guard = {"id": p["booking_id"], **{k: v for k, v in p["before"].items()}}
        entry = {"amended_at": now, "source": "data_correction", "batch_id": batch_id,
                 "reason": "Owner-approved correction (Nov 2026)",
                 "changes": [f"{k}: {p['before'][k]} -> {p['after'][k]}" for k in p["after"]]}
        res = await db.bookings.update_one(guard, {"$set": {**p["after"], "updated_at": now}, "$push": {"amendment_log": entry}})
        if res.matched_count == 0:
            p["status"], p["reason"] = "skipped", "record changed while applying — not applied"
            continue
        applied += 1
        p["status"] = "applied"
        await db.data_corrections.insert_one({
            "id": str(uuid.uuid4()), "batch_id": batch_id, "applied_at": now, "applied_by": user,
            "collection": "bookings", "record_id": p["booking_id"], "booking_number": p["booking_number"],
            "kind": p["kind"], "original": p["before"], "new": p["after"], "reverted_at": None,
            "backup_id_before": backup["backup_id"],
        })
    logger.info(f"Data corrections applied: batch {batch_id}, {applied} record(s), by {user}")
    return {"batch_id": batch_id, "applied": applied, "backup_id_before": backup["backup_id"], "plan": plan}


async def undo_batch(db, batch_id: str, user: str) -> Dict:
    rows = await db.data_corrections.find({"batch_id": batch_id, "reverted_at": None}, {"_id": 0}).to_list(500)
    if not rows:
        return {"batch_id": batch_id, "restored": 0, "results": [], "message": "Nothing to undo for this batch."}
    now = datetime.now(timezone.utc).isoformat()
    results, restored = [], 0
    for r in rows:
        # Only if the record still holds exactly what the correction set.
        res = await db.bookings.update_one(
            {"id": r["record_id"], **r["new"]},
            {"$set": {**r["original"], "updated_at": now}, "$pull": {"amendment_log": {"batch_id": batch_id}}},
        )
        if res.matched_count == 0:
            results.append({"booking_number": r["booking_number"], "status": "skipped",
                            "reason": "record has been changed since the correction — not restored"})
            continue
        restored += 1
        await db.data_corrections.update_one({"id": r["id"]}, {"$set": {"reverted_at": now, "reverted_by": user}})
        results.append({"booking_number": r["booking_number"], "status": "restored", "original": r["original"]})
    return {"batch_id": batch_id, "restored": restored, "results": results}


async def list_batches(db) -> List[Dict]:
    rows = await db.data_corrections.find({}, {"_id": 0}).to_list(2000)
    batches: Dict[str, Dict] = {}
    for r in rows:
        b = batches.setdefault(r["batch_id"], {"batch_id": r["batch_id"], "applied_at": r["applied_at"], "applied_by": r["applied_by"],
                                               "backup_id_before": r.get("backup_id_before"), "records": []})
        b["records"].append({"booking_number": r["booking_number"], "kind": r["kind"], "original": r["original"],
                             "new": r["new"], "reverted_at": r.get("reverted_at")})
    return sorted(batches.values(), key=lambda b: b["applied_at"], reverse=True)
