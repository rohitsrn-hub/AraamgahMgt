"""
Validation helper functions for SARAI application
"""
import re


def validate_ifsc(ifsc: str) -> bool:
    """Validate IFSC code format: 4 letters + 0 + 6 alphanumeric"""
    if not ifsc:
        return True  # Optional field
    return bool(re.match(r'^[A-Z]{4}0[A-Z0-9]{6}$', ifsc))


def validate_indian_mobile(mobile: str) -> bool:
    """Validate Indian mobile number (10 digits starting with 6-9)"""
    if not mobile:
        return True  # Optional field
    cleaned = mobile.replace(" ", "").replace("+91", "").replace("-", "")
    return bool(re.match(r'^[6-9]\d{9}$', cleaned))


def normalize_uppercase_fields(data: dict) -> dict:
    """Force uppercase on ID fields (bank_ifsc, org_id for family members)"""
    if "bank_ifsc" in data and data["bank_ifsc"]:
        data["bank_ifsc"] = data["bank_ifsc"].upper()
    # For family members - normalize org_id (formerly dependent_id)
    if "family_members" in data:
        for member in data["family_members"]:
            if "org_id" in member and member["org_id"]:
                member["org_id"] = member["org_id"].upper()
    return data
