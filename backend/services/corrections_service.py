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

The bill and refund-due corrections do not move any report (every report computes
money from booking_financials(), never the stored bill). The October-register ones (cancel, Org rate, penalty waiver, extra beds, advances) DO change October reports on purpose. The bill ones fix the
stored bill (what the booking list and receipts show) and a stale field.
"""
import logging
import uuid
import copy
from datetime import date, datetime, timezone
from typing import Dict, List

from utils.report_calc import EXTRA_BED_RATE, booking_financials, build_room_maps, resolve_rooms
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

# October 2026 register reconciliation (owner rulings, 18 Nov 2026: "the register is correct";
# a booking not in the register means the guest did not stay; early-departure penalty waived).
# booking_number -> what to change. `total` is the register's amount for the booking: the money
# engine must give exactly that once the change is made, otherwise the booking is skipped.
#   org_rate      bill every room at the Org rate (the register did; the app had Non-Org)
#   waive_penalty bill the nights actually stayed instead of the full booked stay
#   extra_bed     (beds, days) used, charged at check-out (the register had it; the app did not)
#   extra_bed_top_up  the booking already has a bed charge but the register has more: raise the
#                 bed days so the bill equals the register's amount
#   set_payments  ((advance, final) in the app now, (advance, final) in the register): the booking's
#                 payment fields are set to the register's figures (the dashboard's cash log is separate)
#   advance       (as the app has it, as the register has it): the cash is unchanged, so the
#                 difference moves between "advance" and "final payment"
#   cancel_total  the booking was never in the register: cancel it (guard: its stored total)
APPROVED_RECONCILIATIONS = {
    "BK1293": {"cancel_total": 21000.0},   # stored bill (35 nights to its 18 Nov check-out); October reports carry 10,800 of it
    "BK1184": {"org_rate": True, "waive_penalty": True, "total": 2700.0},
    "BK1138": {"waive_penalty": True, "total": 675.0},
    "BK1122": {"org_rate": True, "total": 4800.0},
    "BK0999": {"org_rate": True, "total": 2700.0},
    "BK0995": {"org_rate": True, "total": 2400.0},
    "BK1152": {"org_rate": True, "total": 1350.0},
    "BK1161": {"org_rate": True, "total": 2400.0},
    "BK1228": {"org_rate": True, "total": 1200.0},
    # Org rate/advance split already applied 19 Nov 00:52. The register shows the advance AND the
    # full balance paid at check-out (it records every guest as fully paid), so the payments are
    # set to the register's figures: (advance, final payment) as the app has them -> as the register has them.
    "BK1286": {"set_payments": ((800.0, 2600.0), (800.0, 3400.0))},
    "BK1258": {"org_rate": True, "total": 700.0},
    "BK1280": {"extra_bed": (1, 3), "total": 2625.0},
    "BK1267": {"extra_bed_top_up": True, "total": 1550.0},
    "BK1151": {"extra_bed": (1, 2), "total": 1350.0},
    "BK1320": {"extra_bed_top_up": True, "total": 1750.0},
    "BK1324": {"extra_bed_top_up": True, "total": 1675.0},
    "BK1204": {"extra_bed_top_up": True, "total": 1450.0},
    "BK1325": {"extra_bed_top_up": True, "total": 875.0},
    "BK1159": {"set_payments": ((500.0, 200.0), (500.0, 700.0))},
    "BK1279": {"set_payments": ((400.0, 1200.0), (400.0, 800.0))},
}

# The dashboard's Net Revenue counts the PAYMENTS LOG (db.payments), not the booking's advance /
# final-payment fields. The October payment-field corrections (BK1286, BK1159, BK1279) changed the
# booking fields only, so the log is brought into line with them: booking_number -> the difference
# (advance, final payment) between the booking fields and the log that the audit expects to find.
# An adjustment row is added in the month the original money was recorded (the booking's own
# advance row, else the date the booking was made), so each month's Net Revenue is right.
APPROVED_CASH_LOG_SYNC = {
    "BK1286": (800.0, 0.0),     # ₹800 advance taken (register serials 111-112) but never entered
    "BK1159": (500.0, 0.0),     # ₹500 advance taken (register serial 125) but never entered
    "BK1279": (-400.0, 0.0),    # advance entered as ₹800; register serial 129 shows ₹400
}

WIDE = (date(2000, 1, 1), date(2100, 1, 1))
BILL_FIELDS = ("total_amount", "balance_amount", "room_rent_total", "license_fee_total", "charged_nights", "charge_reason")
REFUND_FIELDS = ("refund_due", "refund_reason")


def _num(v) -> float:
    return round(float(v or 0), 2)


def _describe(spec: Dict) -> str:
    parts = []
    if spec.get("cancel_total") is not None:
        parts.append("cancel (guest did not stay; not in the register)")
    if spec.get("org_rate"):
        parts.append("bill at the Org rate")
    if spec.get("waive_penalty"):
        parts.append("waive the early-departure penalty")
    if spec.get("extra_bed"):
        parts.append(f"add extra bed {spec['extra_bed'][0]} x {spec['extra_bed'][1]} day(s)")
    if spec.get("extra_bed_top_up"):
        parts.append("raise the extra-bed charge to the register's amount")
    if spec.get("set_payments"):
        (a0, f0), (a1, f1) = spec["set_payments"]
        parts.append(f"payments: advance {a0:g} + final {f0:g} -> advance {a1:g} + final {f1:g} (as the register)")
    if spec.get("advance"):
        parts.append(f"advance {spec['advance'][0]:g} -> {spec['advance'][1]:g} (cash unchanged)")
    return ", ".join(parts)


def _plan_reconciliation(bk: Dict, spec: Dict, settings: Dict, room_maps: Dict) -> Dict:
    """One October-register correction for one booking. Never changes anything."""
    item = {"booking_number": bk.get("booking_number"), "kind": "reconciliation", "label": "October register",
            "description": _describe(spec), "status": "skipped", "reason": None, "before": {}, "after": {}}
    if spec.get("cancel_total") is not None:
        if bk.get("status") != "checked_out":
            item["reason"] = f"booking is {bk.get('status')}, not checked out — not applied"
            return item
        if _num(bk.get("total_amount")) != _num(spec["cancel_total"]):
            item["reason"] = f"stored total is {bk.get('total_amount')}, not the {spec['cancel_total']} the audit saw — not applied"
            return item
        after = {"status": "cancelled",
                 "notes": f"{bk.get('notes') or ''} | Cancelled: not in the paper register, guest did not stay (owner ruling, Nov 2026)"}
        item.update(status="ready", booking_id=bk["id"], before={k: bk.get(k) for k in after}, after=after,
                    note=f"The advance of {_num(bk.get('advance_paid')):g} is NOT refunded or changed by this; decide that separately.")
        return item

    if bk.get("status") != "checked_out":
        item["reason"] = f"booking is {bk.get('status')}, not checked out — not applied"
        return item

    cand = copy.deepcopy(bk)
    after: Dict = {}
    changes_money = spec.get("total") is not None

    if spec.get("org_rate"):
        mapping = copy.deepcopy(bk.get("room_guest_mapping") or [])
        if bk.get("is_org"):
            for m in mapping:
                if m.get("charge_category") == "Non-Org":
                    m["charge_category"] = "Org"
        else:
            for rn, cat in resolve_rooms(bk, room_maps):
                entry = next((m for m in mapping if m.get("room_number") == rn), None)
                if entry is None:
                    mapping.append({"room_number": rn, "room_category": cat, "charge_category": "Org"})
                else:
                    entry["charge_category"] = "Org"
        if mapping == (bk.get("room_guest_mapping") or []):
            item["reason"] = "no room is billed at the Non-Org rate — nothing to change, not applied"
            return item
        cand["room_guest_mapping"] = mapping
        after["room_guest_mapping"] = mapping

    if spec.get("waive_penalty"):
        if bk.get("charge_reason") != "early_checkout_not_informed":
            item["reason"] = f"charge reason is {bk.get('charge_reason')}, not an uninformed early check-out — not applied"
            return item
        nights = (date.fromisoformat(bk["actual_checkout_date"][:10]) - date.fromisoformat(bk["check_in_date"][:10])).days
        cand["charge_reason"] = "early_checkout_penalty_waived"
        cand["charged_nights"] = nights
        after.update(charge_reason="early_checkout_penalty_waived", charged_nights=nights)

    if spec.get("extra_bed"):
        if _num(bk.get("extra_bed_charge_checkout")) != 0:
            item["reason"] = "an extra-bed charge is already recorded — not applied"
            return item
        beds, days = spec["extra_bed"]
        charge = round(beds * days * EXTRA_BED_RATE, 2)
        cand.update(extra_beds_checkout=beds, extra_bed_days=days, extra_bed_charge_checkout=charge)
        after.update(extra_beds_checkout=beds, extra_bed_days=days, extra_bed_charge_checkout=charge)

    if spec.get("extra_bed_top_up"):
        old = _num(bk.get("extra_bed_charge_checkout"))
        if old <= 0:
            item["reason"] = "no extra-bed charge is recorded, so there is nothing to top up — not applied"
            return item
        now_total = booking_financials(cand, settings, *WIDE, room_maps)["total_amount"]
        new_charge = round(old + (_num(spec["total"]) - _num(now_total)), 2)
        beds = int(bk.get("extra_beds_checkout") or 0)
        if new_charge <= old:
            item["reason"] = "the bill is not below the register's amount — not applied"
            return item
        if beds <= 0 or new_charge % (beds * EXTRA_BED_RATE) != 0:
            beds = 1
        if new_charge % (beds * EXTRA_BED_RATE) != 0:
            item["reason"] = f"an extra-bed charge of {new_charge:g} is not a whole number of bed-days — not applied"
            return item
        days = int(new_charge // (beds * EXTRA_BED_RATE))
        cand.update(extra_beds_checkout=beds, extra_bed_days=days, extra_bed_charge_checkout=new_charge)
        after.update(extra_beds_checkout=beds, extra_bed_days=days, extra_bed_charge_checkout=new_charge)

    if changes_money:
        fin = booking_financials(cand, settings, *WIDE, room_maps)
        if _num(fin["total_amount"]) != _num(spec["total"]):
            item["reason"] = f"the money engine gives {fin['total_amount']} after this change, not the register's {spec['total']} — not applied"
            return item
        after.update(total_amount=_num(fin["total_amount"]), room_rent_total=_num(fin["room_rent"]),
                     license_fee_total=_num(fin["license_fee"]))

    advance, final = _num(bk.get("advance_paid")), _num(bk.get("final_payment"))
    if spec.get("advance"):
        seen, new = spec["advance"]
        if advance != _num(seen):
            item["reason"] = f"stored advance is {advance:g}, not the {seen:g} the audit saw — not applied"
            return item
        new_final = round(final - (new - advance), 2)
        if new_final < 0:
            item["reason"] = "the final payment is too small to move the difference out of — not applied"
            return item
        after.update(advance_paid=_num(new), final_payment=new_final)
        advance, final = _num(new), new_final

    if spec.get("set_payments"):
        (a0, f0), (a1, f1) = spec["set_payments"]
        if (advance, final) != (_num(a0), _num(f0)):
            item["reason"] = f"stored advance/final payment are {advance:g}/{final:g}, not the {a0:g}/{f0:g} the audit saw — not applied"
            return item
        after.update(advance_paid=_num(a1), final_payment=_num(f1))
        advance, final = _num(a1), _num(f1)
        changes_money = True

    total_now = after.get("total_amount", _num(bk.get("total_amount")))
    if changes_money or spec.get("advance"):
        after["balance_amount"] = round(total_now - advance - final, 2)
    # Drop fields that would not change, so the preview shows only real differences.
    after = {k: v for k, v in after.items() if v != bk.get(k) and not (isinstance(v, float) and v == _num(bk.get(k)))}
    if not after:
        item["reason"] = "already matches the register"
        return item
    collected = round(advance + final, 2)
    note = None
    if collected != total_now:
        note = (f"Cash collected is {collected:g} and the corrected bill is {total_now:g}: "
                f"{'over-collected' if collected > total_now else 'still to collect'} by {abs(collected - total_now):g}.")
    item.update(status="ready", booking_id=bk["id"], before={k: bk.get(k) for k in after}, after=after, note=note)
    return item


async def payments_log_totals(db, booking_id: str) -> Dict[str, float]:
    """What the payments log holds for one booking: advance, final and refund sums."""
    rows = await db.payments.find({"booking_id": booking_id}, {"_id": 0}).to_list(500)
    out = {"advance": 0.0, "final": 0.0, "refund": 0.0}
    for r in rows:
        if r.get("payment_type") in out:
            out[r["payment_type"]] = round(out[r["payment_type"]] + float(r.get("amount") or 0), 2)
    return out


async def _plan_cash_log(db, number: str, expected) -> Dict:
    item = {"booking_number": number, "kind": "cash_log", "label": "payments log",
            "description": f"payments log: advance {expected[0]:+g}, final {expected[1]:+g} (to match the booking)",
            "status": "skipped", "reason": None, "before": {}, "after": {}}
    bk = await db.bookings.find_one({"booking_number": number}, {"_id": 0})
    if not bk:
        item["reason"] = "booking not found"
        return item
    log = await payments_log_totals(db, bk["id"])
    diff = (round(_num(bk.get("advance_paid")) - log["advance"], 2),
            round(max(0.0, _num(bk.get("final_payment"))) - log["final"], 2))
    if diff == (0.0, 0.0):
        item["reason"] = "the payments log already matches the booking"
        return item
    if diff != (_num(expected[0]), _num(expected[1])):
        item["reason"] = (f"the log differs from the booking by advance {diff[0]:+g}, final {diff[1]:+g}, "
                          f"not the {expected[0]:+g}, {expected[1]:+g} expected — not applied")
        return item
    first_adv = await db.payments.find({"booking_id": bk["id"], "payment_type": "advance"}, {"_id": 0}).sort("created_at", 1).to_list(1)
    first_fin = await db.payments.find({"booking_id": bk["id"], "payment_type": "final"}, {"_id": 0}).sort("created_at", 1).to_list(1)
    rows = []
    for ptype, amount, anchor in (("advance", diff[0], first_adv[0]["created_at"] if first_adv else bk.get("created_at")),
                                  ("final", diff[1], first_fin[0]["created_at"] if first_fin else bk.get("actual_check_out") or bk.get("created_at"))):
        if amount:
            rows.append({"id": str(uuid.uuid4()), "booking_id": bk["id"], "booking_number": number, "amount": amount,
                         "payment_type": ptype, "payment_mode": bk.get("payment_mode"),
                         "created_at": anchor if isinstance(anchor, str) else (anchor.isoformat() if anchor else datetime.now(timezone.utc).isoformat()),
                         "correction": "Owner-approved: payments log aligned with the paper register (Nov 2026)"})
    item.update(status="ready", booking_id=bk["id"], before={"log": log},
                after={"rows_to_add": rows}, note="Changes the dashboard's Net Revenue for the month of each row.")
    return item


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

    for number, spec in APPROVED_RECONCILIATIONS.items():
        bk = await db.bookings.find_one({"booking_number": number}, {"_id": 0})
        if not bk:
            plan.append({"booking_number": number, "kind": "reconciliation", "label": "October register",
                         "description": _describe(spec), "status": "skipped", "reason": "booking not found",
                         "before": {}, "after": {}})
            continue
        plan.append(_plan_reconciliation(bk, spec, settings, room_maps))
    for number, expected in APPROVED_CASH_LOG_SYNC.items():
        plan.append(await _plan_cash_log(db, number, expected))
    for item in plan:
        item.setdefault("label", "bill" if item["kind"] == "bill" else "refund due")
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
        if p["kind"] == "cash_log":
            rows = p["after"]["rows_to_add"]
            for r in rows:
                await db.payments.insert_one({**r, "correction_batch_id": batch_id})
            applied += 1
            p["status"] = "applied"
            await db.data_corrections.insert_one({
                "id": str(uuid.uuid4()), "batch_id": batch_id, "applied_at": now, "applied_by": user,
                "collection": "payments", "record_id": p["booking_id"], "booking_number": p["booking_number"],
                "kind": "cash_log", "original": p["before"], "new": {"payment_ids": [r["id"] for r in rows]},
                "reverted_at": None, "backup_id_before": backup["backup_id"],
            })
            continue
        guard = {"id": p["booking_id"], **{k: v for k, v in p["before"].items()}}
        entry = {"amended_at": now, "source": "data_correction", "batch_id": batch_id,
                 "reason": "Owner-approved correction (Nov 2026)" + (f": {p['description']}" if p.get("description") else ""),
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
        if r.get("collection") == "payments":
            ids = r["new"]["payment_ids"]
            res = await db.payments.delete_many({"id": {"$in": ids}, "correction_batch_id": batch_id})
            restored += 1
            await db.data_corrections.update_one({"id": r["id"]}, {"$set": {"reverted_at": now, "reverted_by": user}})
            results.append({"booking_number": r["booking_number"], "status": "restored", "removed_log_rows": res.deleted_count})
            continue
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
