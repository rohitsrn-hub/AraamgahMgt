"""
Helper functions for SARAI application
"""
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import HTTPException


async def generate_booking_number(db):
    """Generate sequential booking number starting from BK0001"""
    # Get the latest booking number
    latest_booking = await db.bookings.find_one(
        {},
        {"_id": 0, "booking_number": 1},
        sort=[("created_at", -1)]
    )
    
    if not latest_booking or not latest_booking.get("booking_number"):
        return "BK0001"
    
    try:
        # Extract the number from the booking number (e.g., BK0001 -> 1)
        current_number = int(latest_booking["booking_number"].replace("BK", ""))
        next_number = current_number + 1
        # Format with leading zeros (e.g., 1 -> BK0001)
        return f"BK{next_number:04d}"
    except (ValueError, KeyError):
        # Fallback to counting all bookings if format is unexpected
        count = await db.bookings.count_documents({})
        return f"BK{count + 1:04d}"


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
    """Calculate number of nights between dates"""
    try:
        ci = datetime.fromisoformat(check_in.replace('Z', '+00:00'))
        co = datetime.fromisoformat(check_out.replace('Z', '+00:00'))
        return max(1, (co - ci).days)
    except (ValueError, TypeError):
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
