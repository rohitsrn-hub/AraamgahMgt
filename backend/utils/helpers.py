"""
Helper functions for SARAI application
"""
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import HTTPException


async def generate_booking_number(db):
    """Atomically allocate the next sequential booking number (BK0001, BK0002, ...).

    Uses a dedicated counters collection with MongoDB's atomic $inc, not the
    previous read-latest-then-increment approach: two concurrent bookings
    could both read the same "latest" booking_number and both compute the
    same next value, producing two bookings with an identical booking_number
    (used as the key for refunds, receipts, and the manual ledger). $inc on a
    single document is atomic in MongoDB, so two concurrent calls can never
    receive the same number.

    No schema migration or unique index required — this only adds one
    small counters document the first time it's called, seeded from the
    current highest booking number so numbering continues where it left off.
    """
    # Imported lazily so utils/helpers.py (and everything importing utils/)
    # doesn't need pymongo just to be imported — this module is used by pure
    # unit tests (test_report_calc.py etc.) that run with no DB and no
    # heavy dependencies.
    from pymongo import ReturnDocument

    counter = await db.counters.find_one({"_id": "booking_number"})
    if not counter:
        # One-time bootstrap: seed the counter from the current max existing
        # booking number so this doesn't restart at BK0001 on an existing DB.
        latest_booking = await db.bookings.find_one(
            {}, {"_id": 0, "booking_number": 1}, sort=[("created_at", -1)]
        )
        start = 0
        if latest_booking and latest_booking.get("booking_number"):
            try:
                start = int(latest_booking["booking_number"].replace("BK", ""))
            except ValueError:
                start = await db.bookings.count_documents({})
        else:
            start = await db.bookings.count_documents({})
        # $setOnInsert + upsert is itself atomic: if two requests race here,
        # only the first actually creates the document — the second's upsert
        # matches the just-created doc and does nothing. Either way, every
        # subsequent allocation below is a single atomic increment.
        await db.counters.update_one(
            {"_id": "booking_number"},
            {"$setOnInsert": {"seq": start}},
            upsert=True,
        )

    result = await db.counters.find_one_and_update(
        {"_id": "booking_number"},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )
    return f"BK{result['seq']:04d}"


def serialize_datetime(obj):
    """Convert datetime to ISO string for MongoDB storage"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    return obj


def serialize_doc(doc: dict) -> dict:
    """Serialize document for MongoDB storage"""
    result = {}
    for k, v in doc.items():
        if k == '_id':  # Skip MongoDB ObjectId
            continue
        if isinstance(v, datetime):
            result[k] = v.isoformat()
        else:
            result[k] = v
    return result


def serialize_response(doc: dict) -> dict:
    """Serialize document for API response, excluding _id"""
    if doc is None:
        return None
    result = {}
    for k, v in doc.items():
        if k == '_id':  # Skip MongoDB ObjectId
            continue
        result[k] = v
    return result


def calculate_nights(check_in: str, check_out: str) -> int:
    """Calculate number of nights between dates.

    Never raises: an explicit None (not just a missing/empty string) for
    either date used to raise AttributeError from .replace(), uncaught by
    the original (ValueError, TypeError) — a caller relying on this being
    a safe fallback (e.g. create_feedback) would crash instead of degrading
    to the 1-night default.
    """
    try:
        ci = datetime.fromisoformat(check_in.replace('Z', '+00:00'))
        co = datetime.fromisoformat(check_out.replace('Z', '+00:00'))
        return max(1, (co - ci).days)
    except (ValueError, TypeError, AttributeError):
        return 1


async def get_room_rate(db, category, is_org: bool = True, is_license_fee: bool = False) -> float:
    """
    Get room rate from settings based on Org/Non-Org classification
    
    Args:
        db: MongoDB database instance
        category: Room category (CAT_I or CAT_II)
        is_org: True for Organization personnel, False for Non-Org
        is_license_fee: If True, return license fee instead of room rent
    
    Returns:
        float: Room rent or license fee amount
    """
    settings = await db.app_settings.find_one({}, {"_id": 0})
    
    if settings:
        if is_org:
            # Organization personnel - use Cat I or Cat II rates
            if category == "Cat I" or (hasattr(category, 'value') and category.value == "Cat I"):
                if is_license_fee:
                    return settings.get("cat_i_license_fee", 30.0)
                return settings.get("cat_i_room_rent", 470.0)
            else:  # CAT_II
                if is_license_fee:
                    return settings.get("cat_ii_license_fee", 15.0)
                return settings.get("cat_ii_room_rent", 385.0)
        else:
            # Non-Org - use Non-Org rates
            if is_license_fee:
                return settings.get("non_org_license_fee", 30.0)
            return settings.get("non_org_room_rent", 570.0)
    
    # Fallback defaults if settings not found
    if is_org:
        if category == "Cat I" or (hasattr(category, 'value') and category.value == "Cat I"):
            return 30.0 if is_license_fee else 470.0
        else:
            return 15.0 if is_license_fee else 385.0
    else:
        return 30.0 if is_license_fee else 570.0
