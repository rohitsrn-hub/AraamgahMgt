"""
Shared report calculation logic — single source of truth for financial reports.

Every report endpoint (room-allotment, guest-details, room-occupancy, monthly)
must derive booking inclusion, nights, and money from these helpers. The four
reports previously recomputed these independently and drifted apart (extra-bed
charges dropped, month-boundary bookings excluded, booking-nights vs room-nights
mixed within one report). Keeping the logic here makes divergence impossible.

Conventions (applied identically in all reports):
- A booking belongs to period P iff at least one of its nights falls inside P.
- Effective stay = check_in_date .. actual_checkout_date (when checked out and
  recorded) or planned check_out_date otherwise. Actual stay is what was billed.
- Statuses counted: confirmed, checked_in, checked_out. Cancelled never counts.
- Money = per-room (room_rent + license_fee) x nights-in-period
          + extra_beds x EXTRA_BED_RATE x nights-in-period.
  Rates come from the room's own category (a Cat II room in a mixed booking is
  billed at Cat II, not at the booking's "first" category).
- Nights are clipped to the report period, so a booking spanning a month
  boundary contributes each night to exactly one month (no double counting).
"""
from datetime import date, timedelta
from typing import Optional

EXTRA_BED_RATE = 75.0

REPORT_STATUSES = ["confirmed", "checked_in", "checked_out"]


def report_booking_query(start_date: str, end_date: str) -> dict:
    """Mongo filter selecting every booking with >= 1 night overlapping the period.

    Matches on planned dates OR actual checkout so overstays (actual checkout
    after planned) and early departures are both caught; zero-night bookings
    that slip through are dropped later by nights_in_period() == 0.
    """
    return {
        "status": {"$in": REPORT_STATUSES},
        "check_in_date": {"$lte": end_date},
        "$or": [
            {"check_out_date": {"$gt": start_date}},
            {"actual_checkout_date": {"$gt": start_date}},
        ],
    }


def _parse_date(value: str) -> Optional[date]:
    if not value:
        return None
    try:
        return date.fromisoformat(str(value).split("T")[0])
    except (ValueError, TypeError):
        return None


def effective_stay(bk: dict):
    """Return (check_in, check_out) as dates. Uses the recorded actual checkout
    for checked-out bookings (early departures and overstays bill actual nights)."""
    checkin = _parse_date(bk.get("check_in_date"))
    checkout = None
    if bk.get("status") == "checked_out":
        checkout = _parse_date(bk.get("actual_checkout_date"))
    if checkout is None:
        checkout = _parse_date(bk.get("check_out_date"))
    return checkin, checkout


def nights_in_period(bk: dict, period_start: date, period_end: date) -> int:
    """Nights of this booking's effective stay that fall within [start, end]
    (inclusive dates; a 'night' is the night starting on that date)."""
    checkin, checkout = effective_stay(bk)
    if checkin is None or checkout is None:
        return 0
    eff_in = max(checkin, period_start)
    eff_out = min(checkout, period_end + timedelta(days=1))
    return max(0, (eff_out - eff_in).days)


def build_room_maps(all_rooms: list) -> dict:
    """Lookups for resolving a booking's rooms, shared by all reports."""
    return {
        "by_number": {r["room_number"]: r["category"] for r in all_rooms},
        "id_to_number": {r["id"]: r["room_number"] for r in all_rooms},
        "id_to_category": {r["id"]: r["category"] for r in all_rooms},
    }


def resolve_rooms(bk: dict, room_maps: dict) -> list:
    """Return [(room_number, category), ...] for every room in this booking.

    Resolution chain: room_numbers/room_categories -> singular room_number ->
    room_ids looked up against the current rooms collection. Every report uses
    this same chain so a multi-room booking appears under every room it
    occupies in every report.
    """
    by_number = room_maps["by_number"]
    room_nums = list(bk.get("room_numbers", []) or [])
    room_cats = list(bk.get("room_categories", []) or [])

    if not room_nums and bk.get("room_number"):
        room_nums = [bk["room_number"]]
        room_cats = [bk.get("room_category", by_number.get(bk["room_number"], "Cat I"))]

    if not room_nums:
        ids = bk.get("room_ids", []) or []
        if not ids and bk.get("room_id"):
            ids = [bk["room_id"]]
        for rid in ids:
            rn = room_maps["id_to_number"].get(rid)
            if rn:
                room_nums.append(rn)
                room_cats.append(room_maps["id_to_category"].get(rid, by_number.get(rn, "Cat I")))

    if not room_nums:
        return []

    while len(room_cats) < len(room_nums):
        room_cats.append(by_number.get(room_nums[len(room_cats)], "Cat I"))

    return list(zip(room_nums, room_cats[: len(room_nums)]))


# Legacy flat-field names from before room_categories carried its own rates.
# migrate_legacy_settings() reads these once to build the new shape; nothing
# else should read them directly any more.
LEGACY_CATEGORY_DEFAULTS = {
    "Cat I": {"id": "cat-i", "prefix": "C1", "capacity": 2,
              "count_field": "cat_i_rooms_count", "count_default": 6,
              "rent_field": "cat_i_room_rent", "rent_default": 470,
              "fee_field": "cat_i_license_fee", "fee_default": 30},
    "Cat II": {"id": "cat-ii", "prefix": "C2", "capacity": 2,
               "count_field": "cat_ii_rooms_count", "count_default": 9,
               "rent_field": "cat_ii_room_rent", "rent_default": 385,
               "fee_field": "cat_ii_license_fee", "fee_default": 15},
}


def migrate_legacy_settings(settings: dict) -> dict:
    """Upgrade an old-shape settings document to the N-category shape, in
    memory only — this never writes to the database and never deletes or
    overwrites a legacy field, so it's always safe to call and always safe
    to re-run (idempotent). Old fields (cat_i_room_rent, etc.) are left
    exactly as they were: a rollback is just reverting the code, since the
    data those old fields need still exists untouched.

    Before this, a category's rate lived in two disconnected places: the
    flat cat_i_room_rent/cat_ii_room_rent/... fields (what billing actually
    read) and a separate room_categories[] array with its own rate/
    def_civ_rate fields (what the Settings UI showed — write-only, nothing
    read it back). This makes room_categories[] the single real source,
    seeded from whichever flat fields already existed, so the two can never
    drift apart again.
    """
    settings = dict(settings)

    categories = settings.get("room_categories") or []
    needs_upgrade = not categories or any(
        "room_rent" not in c or "license_fee" not in c for c in categories
    )
    if needs_upgrade:
        settings["room_categories"] = [
            {
                "id": info["id"],
                "name": name,
                "prefix": info["prefix"],
                "capacity": info["capacity"],
                "room_count": settings.get(info["count_field"], info["count_default"]),
                "room_rent": settings.get(info["rent_field"], info["rent_default"]),
                "license_fee": settings.get(info["fee_field"], info["fee_default"]),
            }
            for name, info in LEGACY_CATEGORY_DEFAULTS.items()
        ]

    migrated_history = []
    for h in settings.get("rate_history") or []:
        if "category_rates" in h:
            migrated_history.append(h)
            continue
        category_rates = {}
        for name, info in LEGACY_CATEGORY_DEFAULTS.items():
            override = {}
            if h.get(info["rent_field"]) is not None:
                override["room_rent"] = h[info["rent_field"]]
            if h.get(info["fee_field"]) is not None:
                override["license_fee"] = h[info["fee_field"]]
            if override:
                category_rates[name] = override
        migrated_history.append({
            **{k: v for k, v in h.items() if k not in
               ("cat_i_room_rent", "cat_i_license_fee", "cat_ii_room_rent", "cat_ii_license_fee")},
            "category_rates": category_rates,
        })
    settings["rate_history"] = migrated_history

    return settings


def get_category(settings: dict, category_name: str) -> Optional[dict]:
    """The room_categories[] entry matching this category name, or None for
    a category name that doesn't exist in settings (shouldn't normally
    happen — every room/booking category should trace back to a configured
    category — but money code must not crash if it does)."""
    for cat in settings.get("room_categories") or []:
        if cat.get("name") == category_name:
            return cat
    return None


def effective_category_rate(settings: dict, category_name: str, check_in_date) -> dict:
    """Resolve {room_rent, license_fee} for ONE category, by a booking's own
    check-in date — same policy as before: a rate change is locked in at
    check-in, never split per-night across a change (see the module-level
    Aug 2026 policy note previously here, still in force). Call
    migrate_legacy_settings() on `settings` first if it might be old-shape.
    """
    cat = get_category(settings, category_name)
    resolved = {
        "room_rent": cat.get("room_rent") if cat else 470,
        "license_fee": cat.get("license_fee") if cat else 30,
    }
    ci = check_in_date if isinstance(check_in_date, date) else _parse_date(check_in_date)
    if ci is None:
        return resolved

    history = [h for h in (settings.get("rate_history") or []) if _parse_date(h.get("effective_date"))]
    history.sort(key=lambda h: _parse_date(h["effective_date"]))
    for h in history:
        if _parse_date(h["effective_date"]) <= ci:
            override = (h.get("category_rates") or {}).get(category_name)
            if override:
                if override.get("room_rent") is not None:
                    resolved["room_rent"] = override["room_rent"]
                if override.get("license_fee") is not None:
                    resolved["license_fee"] = override["license_fee"]
    return resolved


def effective_non_org_rate(settings: dict, check_in_date) -> dict:
    """Resolve {room_rent, license_fee} for the Non-Org rate — flat, the
    same regardless of room category, by design (owner ruling)."""
    resolved = {
        "room_rent": settings.get("non_org_room_rent", 570),
        "license_fee": settings.get("non_org_license_fee", 30),
    }
    ci = check_in_date if isinstance(check_in_date, date) else _parse_date(check_in_date)
    if ci is None:
        return resolved

    history = [h for h in (settings.get("rate_history") or []) if _parse_date(h.get("effective_date"))]
    history.sort(key=lambda h: _parse_date(h["effective_date"]))
    for h in history:
        if _parse_date(h["effective_date"]) <= ci:
            if h.get("non_org_room_rent") is not None:
                resolved["room_rent"] = h["non_org_room_rent"]
            if h.get("non_org_license_fee") is not None:
                resolved["license_fee"] = h["non_org_license_fee"]
    return resolved


def rate_components(settings: dict, is_org: bool, category: str, check_in_date):
    """(room_rent, license_fee) per night for one room, resolved for the
    booking's own check_in_date (required — no default, so a call site can't
    silently fall back to "today's rate" by omitting it).

    Self-migrating: applies migrate_legacy_settings() internally, so every
    caller gets N-category-safe resolution (any category name, not just
    "Cat I"/"Cat II") automatically, whether or not settings has been
    upgraded to the new room_categories[] shape yet. A caller processing
    many rooms in a loop should migrate once and call effective_category_rate
    directly to avoid repeating the migration per room; this wrapper favors
    safety over that micro-optimization for the many call sites that don't.
    """
    settings = migrate_legacy_settings(settings)
    if not is_org:
        r = effective_non_org_rate(settings, check_in_date)
    else:
        r = effective_category_rate(settings, category, check_in_date)
    return (r["room_rent"], r["license_fee"])


def _segment_room_nights(bk: dict, period_start: date, period_end: date, room_maps: dict) -> dict:
    """For segmented bookings: {room_number: (nights_in_period, category)}."""
    per_room = {}
    for seg in bk.get("room_segments") or []:
        night_dt = _parse_date(seg.get("night_date"))
        if night_dt is None or not (period_start <= night_dt <= period_end):
            continue
        for room_data in seg.get("rooms", []):
            rn = room_data.get("room_number")
            if not rn:
                continue
            cat = room_data.get("category") or room_maps["by_number"].get(rn, "Cat I")
            nights, _ = per_room.get(rn, (0, cat))
            per_room[rn] = (nights + 1, cat)
    return per_room


def booking_financials(bk: dict, settings: dict, period_start: date, period_end: date,
                       room_maps: dict) -> dict:
    """The one calculation every report must use for a booking's money.

    Returns:
        nights            booking-level nights inside the period
        rooms             [{room_number, category, nights, rate_per_night,
                            room_rent, license_fee, revenue}]
                          revenue includes this room's share of money;
                          the extra-bed charge is carried on the first room so
                          per-room revenues always sum to total_amount.
        room_rent         sum of room-rent across rooms
        license_fee       sum of license fees across rooms
        extra_bed_charge  extra_beds x EXTRA_BED_RATE x nights
        total_amount      room_rent + license_fee + extra_bed_charge
    """
    settings = migrate_legacy_settings(settings)
    is_org = bk.get("is_org", False)
    nights = nights_in_period(bk, period_start, period_end)

    rooms_out = []
    room_rent_total = 0.0
    license_total = 0.0

    if bk.get("room_segments"):
        seg_rooms = _segment_room_nights(bk, period_start, period_end, room_maps)
        for rn, (rm_nights, cat) in seg_rooms.items():
            rent, lf = rate_components(settings, is_org, cat, bk.get("check_in_date"))
            rooms_out.append({
                "room_number": rn, "category": cat, "nights": rm_nights,
                "rate_per_night": rent + lf,
                "room_rent": rent * rm_nights, "license_fee": lf * rm_nights,
            })
            room_rent_total += rent * rm_nights
            license_total += lf * rm_nights
    else:
        if nights > 0:
            for rn, cat in resolve_rooms(bk, room_maps):
                rent, lf = rate_components(settings, is_org, cat, bk.get("check_in_date"))
                rooms_out.append({
                    "room_number": rn, "category": cat, "nights": nights,
                    "rate_per_night": rent + lf,
                    "room_rent": rent * nights, "license_fee": lf * nights,
                })
                room_rent_total += rent * nights
                license_total += lf * nights

    extra_bed_charge = (bk.get("extra_beds", 0) or 0) * EXTRA_BED_RATE * nights

    for i, room in enumerate(rooms_out):
        room["revenue"] = round(
            room["room_rent"] + room["license_fee"] + (extra_bed_charge if i == 0 else 0.0), 2
        )

    return {
        "nights": nights,
        "rooms": rooms_out,
        "room_rent": round(room_rent_total, 2),
        "license_fee": round(license_total, 2),
        "extra_bed_charge": round(extra_bed_charge, 2),
        "total_amount": round(room_rent_total + license_total + extra_bed_charge, 2),
    }
