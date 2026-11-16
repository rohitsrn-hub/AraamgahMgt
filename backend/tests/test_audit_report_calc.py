"""
Stress tests for utils/report_calc.py added by the Nov 2026 full-codebase audit.

The original 44 tests cover each rule (penalty nights, per-room Non-Org
override, checkout-added extra bed, rate history, segments) one at a time.
These cover the COMBINATIONS, plus the segmented (mix & match) path, which
until this audit ignored three rules the plain path already honoured:

  * the real departure date (a segmented booking that left early kept being
    counted, and billed, for every originally planned night);
  * the uninformed-early-checkout penalty split (occupancy and money are two
    different night counts — the segmented path only had one);
  * the per-room "Non-Org" charge override in room_guest_mapping.

Pure Python — no DB or server needed.
"""
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.report_calc import (
    booking_financials,
    build_room_maps,
    stay_charges,
)

ROOMS = [
    {"id": "r1", "room_number": "C1-01", "category": "Cat I"},
    {"id": "r2", "room_number": "C2-08", "category": "Cat II"},
    {"id": "r3", "room_number": "C2-09", "category": "Cat II"},
]
ROOM_MAPS = build_room_maps(ROOMS)
SETTINGS = {}  # defaults: Cat I 470+30=500, Cat II 385+15=400, Non-Org 570+30=600

C1 = {"id": "r1", "room_number": "C1-01", "category": "Cat I"}
C2A = {"id": "r2", "room_number": "C2-08", "category": "Cat II"}
C2B = {"id": "r3", "room_number": "C2-09", "category": "Cat II"}

MAY = (date(2026, 5, 1), date(2026, 5, 31))
JUL = (date(2026, 7, 1), date(2026, 7, 31))
AUG = (date(2026, 8, 1), date(2026, 8, 31))
WHOLE = (date(2026, 1, 1), date(2026, 12, 31))


def seg(night, *rooms):
    return {"night_date": night, "rooms": list(rooms)}


def segmented_booking(**overrides):
    """Org booking, 10-14 May (4 nights): two nights in C1-01, then two in C2-08."""
    bk = {
        "id": "b1", "status": "confirmed", "is_org": True,
        "check_in_date": "2026-05-10", "check_out_date": "2026-05-14",
        "room_numbers": ["C1-01", "C2-08"], "room_categories": ["Cat I", "Cat II"],
        "room_segments": [
            seg("2026-05-10", C1), seg("2026-05-11", C1),
            seg("2026-05-12", C2A), seg("2026-05-13", C2A),
        ],
    }
    bk.update(overrides)
    return bk


def rooms_by_number(fin):
    return {r["room_number"]: r for r in fin["rooms"]}


# ---------- segmented bookings honour the real departure date ----------

def test_segmented_full_stay_unchanged():
    fin = booking_financials(segmented_booking(), SETTINGS, *MAY, ROOM_MAPS)
    assert fin["total_amount"] == 2 * 500 + 2 * 400
    assert sum(r["nights"] for r in fin["rooms"]) == 4


def test_segmented_informed_early_checkout_stops_at_real_departure():
    """Left on the 12th having told staff at check-in: the two C2-08 nights
    were never stayed and never charged, so they must not be reported."""
    bk = segmented_booking(status="checked_out", actual_checkout_date="2026-05-12",
                           charge_reason="early_checkout_informed")
    fin = booking_financials(bk, SETTINGS, *MAY, ROOM_MAPS)
    assert fin["nights"] == 2
    assert fin["total_amount"] == 2 * 500
    assert sum(r["nights"] for r in fin["rooms"]) == 2
    assert "C2-08" not in rooms_by_number(fin)


def test_segmented_uninformed_early_checkout_bills_all_but_frees_rooms():
    """Same departure, but not informed: full booked term is billed as a
    penalty, while the vacated nights show as vacant — exactly the two-number
    rule the plain (non-segmented) path already follows."""
    bk = segmented_booking(status="checked_out", actual_checkout_date="2026-05-12",
                           charge_reason="early_checkout_not_informed")
    fin = booking_financials(bk, SETTINGS, *MAY, ROOM_MAPS)
    rooms = rooms_by_number(fin)
    assert fin["total_amount"] == 2 * 500 + 2 * 400
    assert rooms["C1-01"]["nights"] == 2 and rooms["C1-01"]["billed_nights"] == 2
    assert rooms["C2-08"]["nights"] == 0 and rooms["C2-08"]["billed_nights"] == 2
    assert sum(r["nights"] for r in fin["rooms"]) == fin["nights"] == 2


def test_segmented_ignores_segments_outside_the_stay_window():
    """Segments left behind from before a date change must not be counted."""
    bk = segmented_booking()
    bk["room_segments"] = bk["room_segments"] + [seg("2026-05-20", C1)]
    fin = booking_financials(bk, SETTINGS, *MAY, ROOM_MAPS)
    assert fin["total_amount"] == 2 * 500 + 2 * 400


# ---------- segmented bookings honour the per-room Non-Org override ----------

def test_segmented_room_non_org_override_is_billed_non_org():
    bk = segmented_booking(room_guest_mapping=[
        {"room_number": "C1-01", "charge_category": "Cat I"},
        {"room_number": "C2-08", "charge_category": "Non-Org"},
    ])
    fin = booking_financials(bk, SETTINGS, *MAY, ROOM_MAPS)
    rooms = rooms_by_number(fin)
    assert rooms["C2-08"]["rate_per_night"] == 600
    assert rooms["C2-08"]["is_org"] is False
    assert rooms["C1-01"]["is_org"] is True
    assert fin["total_amount"] == 2 * 500 + 2 * 600


# ---------- the full combination ----------

def combo_booking():
    """Org booking 29 Jul - 3 Aug (5 nights), two rooms a night, mix & match:
    C1-01 throughout; C2-08 for the first two nights then C2-09.
    C2-08 is billed Non-Org (per-room override). One extra bed from check-in,
    plus Rs 150 of extra bed added at checkout. Guest left on 31 Jul without
    having informed staff -> penalty for the full term."""
    return {
        "id": "combo", "status": "checked_out", "is_org": True,
        "check_in_date": "2026-07-29", "check_out_date": "2026-08-03",
        "actual_checkout_date": "2026-07-31",
        "charge_reason": "early_checkout_not_informed",
        "extra_beds": 1, "extra_bed_charge_checkout": 150,
        "room_numbers": ["C1-01", "C2-08", "C2-09"],
        "room_categories": ["Cat I", "Cat II", "Cat II"],
        "room_guest_mapping": [{"room_number": "C2-08", "charge_category": "Non-Org"}],
        "room_segments": [
            seg("2026-07-29", C1, C2A), seg("2026-07-30", C1, C2A),
            seg("2026-07-31", C1, C2B), seg("2026-08-01", C1, C2B),
            seg("2026-08-02", C1, C2B),
        ],
    }


def test_combination_july_side():
    fin = booking_financials(combo_booking(), SETTINGS, *JUL, ROOM_MAPS)
    rooms = rooms_by_number(fin)
    # Physically present 29 + 30 Jul only.
    assert fin["nights"] == 2
    assert rooms["C1-01"]["nights"] == 2 and rooms["C2-08"]["nights"] == 2
    assert rooms["C2-09"]["nights"] == 0
    # Billed 29, 30, 31 Jul: C1-01 x3 @500, C2-08 x2 @600 (override), C2-09 x1 @400.
    assert fin["room_rent"] + fin["license_fee"] == 3 * 500 + 2 * 600 + 1 * 400
    # Extra beds: 1 bed x Rs 75 x 2 physical nights + Rs 150 added at checkout (31 Jul).
    assert fin["extra_bed_charge"] == 150 + 150
    assert fin["total_amount"] == 3100 + 300
    assert round(sum(r["revenue"] for r in fin["rooms"]), 2) == fin["total_amount"]


def test_combination_august_side_is_penalty_only():
    fin = booking_financials(combo_booking(), SETTINGS, *AUG, ROOM_MAPS)
    rooms = rooms_by_number(fin)
    assert fin["nights"] == 0
    assert fin["rooms"], "penalty-only month must still list the booking"
    assert all(r["nights"] == 0 for r in fin["rooms"])
    assert rooms["C1-01"]["billed_nights"] == 2 and rooms["C2-09"]["billed_nights"] == 2
    assert fin["extra_bed_charge"] == 0
    assert fin["total_amount"] == 2 * 500 + 2 * 400


def test_combination_months_add_up_to_the_whole():
    bk = combo_booking()
    jul = booking_financials(bk, SETTINGS, *JUL, ROOM_MAPS)["total_amount"]
    aug = booking_financials(bk, SETTINGS, *AUG, ROOM_MAPS)["total_amount"]
    whole = booking_financials(bk, SETTINGS, *WHOLE, ROOM_MAPS)["total_amount"]
    assert jul + aug == whole == 5200


def test_no_rupee_lost_or_doubled_across_month_boundaries():
    """For a spread of booking shapes, the twelve monthly totals must add up
    to the single whole-year total — no night dropped or counted twice."""
    import calendar
    shapes = [
        {"status": "checked_out", "actual_checkout_date": "2026-09-02"},
        {"status": "checked_out", "actual_checkout_date": "2026-08-30",
         "charge_reason": "early_checkout_not_informed"},
        {"status": "checked_out", "actual_checkout_date": "2026-08-30",
         "charge_reason": "early_checkout_informed", "extra_bed_charge_checkout": 75},
        {"status": "checked_in", "extra_beds": 2},
        {"status": "confirmed",
         "room_guest_mapping": [{"room_number": "C2-08", "charge_category": "Non-Org"}]},
    ]
    for shape in shapes:
        bk = {"id": "x", "is_org": True, "check_in_date": "2026-08-28",
              "check_out_date": "2026-09-02",
              "room_numbers": ["C1-01", "C2-08"], "room_categories": ["Cat I", "Cat II"]}
        bk.update(shape)
        monthly = 0.0
        for m in range(1, 13):
            last = calendar.monthrange(2026, m)[1]
            monthly += booking_financials(
                bk, SETTINGS, date(2026, m, 1), date(2026, m, last), ROOM_MAPS)["total_amount"]
        whole = booking_financials(bk, SETTINGS, *WHOLE, ROOM_MAPS)["total_amount"]
        assert round(monthly, 2) == whole, shape


# ---------- rate history ----------

RATE_SETTINGS = {
    "cat_i_room_rent": 470, "cat_i_license_fee": 30,
    "rate_history": [{"effective_date": "2026-08-16", "cat_i_room_rent": 570}],
}


def test_rate_change_mid_stay_keeps_check_in_rate_for_every_night():
    bk = {"id": "r", "status": "checked_out", "is_org": True,
          "check_in_date": "2026-08-14", "check_out_date": "2026-08-18",
          "actual_checkout_date": "2026-08-18",
          "room_numbers": ["C1-01"], "room_categories": ["Cat I"]}
    fin = booking_financials(bk, RATE_SETTINGS, *AUG, ROOM_MAPS)
    assert fin["total_amount"] == 4 * 500  # old rate, including 16 and 17 Aug


def test_rate_change_applies_from_its_effective_check_in_date():
    bk = {"id": "r", "status": "confirmed", "is_org": True,
          "check_in_date": "2026-08-16", "check_out_date": "2026-08-18",
          "room_numbers": ["C1-01"], "room_categories": ["Cat I"]}
    fin = booking_financials(bk, RATE_SETTINGS, *AUG, ROOM_MAPS)
    assert fin["total_amount"] == 2 * 600


# ---------- stay_charges: the one price used by check-in / check-out / extend ----------

def plain_booking(**overrides):
    bk = {"id": "p", "status": "confirmed", "is_org": True,
          "check_in_date": "2026-05-10", "check_out_date": "2026-05-13",
          "room_numbers": ["C1-01", "C2-08"], "room_categories": ["Cat I", "Cat II"]}
    bk.update(overrides)
    return bk


def test_stay_charges_matches_the_report_for_a_full_stay():
    bk = plain_booking()
    charges = stay_charges(bk, SETTINGS, ROOM_MAPS)
    fin = booking_financials(bk, SETTINGS, *MAY, ROOM_MAPS)
    assert charges["room_rent"] == fin["room_rent"] == 3 * (470 + 385)
    assert charges["license_fee"] == fin["license_fee"] == 3 * (30 + 15)
    assert charges["total"] == 3 * 900


def test_stay_charges_for_fewer_charged_nights():
    assert stay_charges(plain_booking(), SETTINGS, ROOM_MAPS, charged_nights=1)["total"] == 900
    assert stay_charges(plain_booking(), SETTINGS, ROOM_MAPS, charged_nights=0)["total"] == 0


def test_stay_charges_segmented_bills_each_room_only_for_its_own_nights():
    """A mix & match stay of 4 nights in ONE room a night is 4 room-nights,
    not 'every room the guest ever touched x every night' (8 room-nights)."""
    bk = segmented_booking()
    assert stay_charges(bk, SETTINGS, ROOM_MAPS)["total"] == 2 * 500 + 2 * 400
    assert stay_charges(bk, SETTINGS, ROOM_MAPS, charged_nights=3)["total"] == 2 * 500 + 400


def test_stay_charges_ignores_checkout_state_and_extra_beds():
    """It prices ROOMS for a number of nights; status, the actual departure
    and extra beds are the caller's business."""
    bk = plain_booking(status="checked_out", actual_checkout_date="2026-05-11",
                       charge_reason="early_checkout_not_informed",
                       extra_beds=3, extra_bed_charge_checkout=500)
    assert stay_charges(bk, SETTINGS, ROOM_MAPS)["total"] == 3 * 900


def test_stay_charges_honours_room_override_and_check_in_rate():
    bk = plain_booking(room_guest_mapping=[{"room_number": "C2-08", "charge_category": "Non-Org"}])
    assert stay_charges(bk, SETTINGS, ROOM_MAPS)["total"] == 3 * (500 + 600)
    late = {"id": "r", "status": "confirmed", "is_org": True,
            "check_in_date": "2026-08-14", "check_out_date": "2026-08-20",
            "room_numbers": ["C1-01"], "room_categories": ["Cat I"]}
    assert stay_charges(late, RATE_SETTINGS, ROOM_MAPS)["total"] == 6 * 500
