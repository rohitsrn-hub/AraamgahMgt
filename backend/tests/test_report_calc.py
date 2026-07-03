"""
Unit tests for utils/report_calc.py — the shared calculation module that all
four financial reports (room-allotment, guest-details, room-occupancy, monthly)
must use.

These tests encode the May/June 2026 reconciliation findings: extra-bed charges
dropped from the occupancy report, month-boundary bookings excluded, multi-room
bookings under-represented, and booking-nights vs room-nights mixed within the
monthly report. Each test would have failed against the old per-report logic.
"""
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.report_calc import (
    EXTRA_BED_RATE,
    booking_financials,
    build_room_maps,
    effective_stay,
    nights_in_period,
    report_booking_query,
    resolve_rooms,
)

MAY_START = date(2026, 5, 1)
MAY_END = date(2026, 5, 31)

ROOMS = [
    {"id": "r1", "room_number": "C1-01", "category": "Cat I"},
    {"id": "r2", "room_number": "C2-08", "category": "Cat II"},
    {"id": "r3", "room_number": "C2-09", "category": "Cat II"},
    {"id": "r4", "room_number": "C2-15", "category": "Cat II"},
]
ROOM_MAPS = build_room_maps(ROOMS)
SETTINGS = {}  # defaults: Cat I 470+30, Cat II 385+15, Non-Org 570+30


def booking(**overrides):
    base = {
        "id": "x", "booking_number": "BKTEST", "status": "checked_out",
        "is_org": True, "check_in_date": "2026-05-10",
        "check_out_date": "2026-05-11",
        "room_numbers": ["C1-01"], "room_categories": ["Cat I"],
        "extra_beds": 0,
    }
    base.update(overrides)
    return base


class TestExtraBeds:
    """Root cause #1 — the ₹75 signature. Occupancy dropped extra-bed money."""

    def test_one_extra_bed_one_night(self):
        # Evidence case BK0146: Occ ₹500 vs Alloc ₹575 — gap exactly 1 x 75
        fin = booking_financials(booking(extra_beds=1), SETTINGS, MAY_START, MAY_END, ROOM_MAPS)
        assert fin["total_amount"] == 575.0
        assert fin["extra_bed_charge"] == 75.0

    def test_extra_beds_multiple_nights(self):
        # Evidence case BK0123 shape: 4 nights Cat I + 4 extra beds -> 2000 + 1200
        fin = booking_financials(
            booking(check_out_date="2026-05-14", extra_beds=4),
            SETTINGS, MAY_START, MAY_END, ROOM_MAPS,
        )
        assert fin["nights"] == 4
        assert fin["room_rent"] + fin["license_fee"] == 2000.0
        assert fin["extra_bed_charge"] == 4 * EXTRA_BED_RATE * 4
        assert fin["total_amount"] == 3200.0

    def test_per_room_revenues_sum_to_total(self):
        # Occupancy credits rooms individually; the sum must equal the booking
        # total so occupancy and allotment can never diverge again.
        fin = booking_financials(
            booking(room_numbers=["C1-01", "C2-08"], room_categories=["Cat I", "Cat II"],
                    extra_beds=2, check_out_date="2026-05-13"),
            SETTINGS, MAY_START, MAY_END, ROOM_MAPS,
        )
        assert round(sum(r["revenue"] for r in fin["rooms"]), 2) == fin["total_amount"]


class TestMonthBoundary:
    """Root cause #2 — bookings overlapping the month were dropped entirely."""

    def test_booking_started_previous_month_is_included(self):
        # Evidence cases BK0090/BK0091/BK0141/BK0147: started 2026-04-28/29
        bk = booking(check_in_date="2026-04-28", check_out_date="2026-05-03")
        assert nights_in_period(bk, MAY_START, MAY_END) == 2  # nights of May 1, 2

    def test_query_includes_confirmed_status(self):
        # June evidence cases missing without month-boundary explanation:
        # occupancy filtered to checked_in/checked_out only, allotment did not.
        q = report_booking_query("2026-06-01", "2026-06-30")
        assert "confirmed" in q["status"]["$in"]

    def test_query_catches_overstay_via_actual_checkout(self):
        # Planned checkout before month start but actual checkout inside it.
        q = report_booking_query("2026-05-01", "2026-05-31")
        assert {"actual_checkout_date": {"$gt": "2026-05-01"}} in q["$or"]

    def test_booking_fully_outside_period_has_zero_nights(self):
        bk = booking(check_in_date="2026-04-01", check_out_date="2026-04-05",
                     actual_checkout_date="2026-04-05")
        assert nights_in_period(bk, MAY_START, MAY_END) == 0


class TestMultiRoom:
    """Root cause #3 — BK0234 appeared under only 2 of its 4 rooms."""

    def test_all_rooms_present(self):
        bk = booking(
            room_numbers=["C2-15", "C2-09", "C1-01", "C2-08"],
            room_categories=["Cat II", "Cat II", "Cat I", "Cat II"],
            check_out_date="2026-05-12",
        )
        fin = booking_financials(bk, SETTINGS, MAY_START, MAY_END, ROOM_MAPS)
        assert [r["room_number"] for r in fin["rooms"]] == ["C2-15", "C2-09", "C1-01", "C2-08"]
        # room-days = 4 rooms x 2 nights
        assert sum(r["nights"] for r in fin["rooms"]) == 8

    def test_mixed_categories_billed_per_room(self):
        # Old allotment bug: "Cat I in cats" billed every room at Cat I rate.
        bk = booking(room_numbers=["C1-01", "C2-08"], room_categories=["Cat I", "Cat II"])
        fin = booking_financials(bk, SETTINGS, MAY_START, MAY_END, ROOM_MAPS)
        assert fin["total_amount"] == (470 + 30) + (385 + 15)

    def test_room_ids_fallback(self):
        bk = booking(room_numbers=[], room_categories=[], room_ids=["r2", "r4"])
        rooms = resolve_rooms(bk, ROOM_MAPS)
        assert rooms == [("C2-08", "Cat II"), ("C2-15", "Cat II")]


class TestNightsConvention:
    """Root cause #4 — reports disagreed on nights for the same booking."""

    def test_actual_checkout_wins_for_checked_out(self):
        # Early departure: planned 6 nights, actually left after 4.
        bk = booking(check_in_date="2026-05-10", check_out_date="2026-05-16",
                     actual_checkout_date="2026-05-14")
        ci, co = effective_stay(bk)
        assert (ci, co) == (date(2026, 5, 10), date(2026, 5, 14))
        assert nights_in_period(bk, MAY_START, MAY_END) == 4

    def test_planned_dates_for_confirmed(self):
        bk = booking(status="confirmed", check_in_date="2026-05-20",
                     check_out_date="2026-05-23")
        assert nights_in_period(bk, MAY_START, MAY_END) == 3

    def test_nights_clipped_to_period_no_double_count(self):
        # A booking spanning May->June contributes each night to exactly one month.
        bk = booking(check_in_date="2026-05-30", check_out_date="2026-06-02")
        may = nights_in_period(bk, MAY_START, MAY_END)
        june = nights_in_period(bk, date(2026, 6, 1), date(2026, 6, 30))
        assert (may, june) == (2, 1)
        assert may + june == 3  # total stay


class TestSegmentedBookings:
    def test_segment_nights_per_room(self):
        bk = booking(
            check_in_date="2026-05-10", check_out_date="2026-05-13",
            room_segments=[
                {"night_date": "2026-05-10", "rooms": [{"room_number": "C1-01", "category": "Cat I"}]},
                {"night_date": "2026-05-11", "rooms": [{"room_number": "C2-08", "category": "Cat II"}]},
                {"night_date": "2026-05-12", "rooms": [{"room_number": "C2-08", "category": "Cat II"}]},
            ],
        )
        fin = booking_financials(bk, SETTINGS, MAY_START, MAY_END, ROOM_MAPS)
        by_room = {r["room_number"]: r["nights"] for r in fin["rooms"]}
        assert by_room == {"C1-01": 1, "C2-08": 2}
        assert fin["total_amount"] == (470 + 30) * 1 + (385 + 15) * 2


class TestNonOrg:
    def test_flat_rate_regardless_of_category(self):
        bk = booking(is_org=False, room_numbers=["C2-08"], room_categories=["Cat II"])
        fin = booking_financials(bk, SETTINGS, MAY_START, MAY_END, ROOM_MAPS)
        assert fin["total_amount"] == 570 + 30
