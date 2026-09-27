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
    billing_nights_in_period,
    booking_financials,
    build_room_maps,
    effective_rate_settings,
    effective_stay,
    nights_in_period,
    rate_components,
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


class TestDateVersionedRates:
    """Aug 2026 rate revision — a booking bills entirely at whichever rate was
    in effect on its own check_in_date, never split per-night across a rate
    change (owner-confirmed policy: rates lock in at check-in, an Extend on
    an old-rate booking stays at the old rate for the whole stay)."""

    RAISED = {
        "rate_history": [
            {"effective_date": "2026-08-16", "cat_i_room_rent": 500, "cat_i_license_fee": 35,
             "cat_ii_room_rent": 420, "cat_ii_license_fee": 20,
             "non_org_room_rent": 600, "non_org_license_fee": 35},
        ]
    }

    def test_no_history_uses_base_settings(self):
        assert effective_rate_settings(SETTINGS, date(2026, 8, 20)) == {}
        assert rate_components(SETTINGS, True, "Cat I", date(2026, 8, 20)) == (470, 30)

    def test_before_effective_date_uses_old_rate(self):
        assert rate_components(self.RAISED, True, "Cat I", date(2026, 8, 15)) == (470, 30)

    def test_on_effective_date_uses_new_rate(self):
        # Boundary is inclusive: the effective date itself already carries the new rate.
        assert rate_components(self.RAISED, True, "Cat I", date(2026, 8, 16)) == (500, 35)

    def test_after_effective_date_uses_new_rate(self):
        assert rate_components(self.RAISED, True, "Cat II", date(2026, 9, 1)) == (420, 20)

    def test_non_org_rate_also_versioned(self):
        assert rate_components(self.RAISED, False, "Cat I", date(2026, 8, 10)) == (570, 30)
        assert rate_components(self.RAISED, False, "Cat I", date(2026, 8, 16)) == (600, 35)

    def test_multiple_future_entries_latest_qualifying_wins(self):
        settings = {
            "rate_history": [
                {"effective_date": "2027-01-01", "cat_i_room_rent": 900, "cat_i_license_fee": 50},
                {"effective_date": "2026-08-16", "cat_i_room_rent": 500, "cat_i_license_fee": 35},
            ]
        }
        # Booking checking in Sep 2026: past the Aug entry, not yet the Jan one.
        assert rate_components(settings, True, "Cat I", date(2026, 9, 1)) == (500, 35)
        # Booking checking in Feb 2027: both entries qualify, the later wins.
        assert rate_components(settings, True, "Cat I", date(2027, 2, 1)) == (900, 50)

    def test_partial_override_falls_back_for_unspecified_fields(self):
        # A history entry only touching Cat I still leaves Cat II on base settings.
        settings = {"rate_history": [{"effective_date": "2026-08-16", "cat_i_room_rent": 500}]}
        assert rate_components(settings, True, "Cat I", date(2026, 8, 20)) == (500, 30)
        assert rate_components(settings, True, "Cat II", date(2026, 8, 20)) == (385, 15)

    def test_missing_or_invalid_check_in_date_falls_back_safely(self):
        assert rate_components(self.RAISED, True, "Cat I", None) == (470, 30)
        assert rate_components(self.RAISED, True, "Cat I", "not-a-date") == (470, 30)

    def test_spanning_stay_bills_entirely_at_check_in_rate_not_split(self):
        # Booked 14 Aug -> 20 Aug, spans the 16 Aug rate change. Whole stay
        # must bill at the OLD rate throughout — no per-night split.
        bk = booking(
            check_in_date="2026-08-14", check_out_date="2026-08-20",
            room_numbers=["C1-01"], room_categories=["Cat I"],
        )
        fin = booking_financials(
            bk, self.RAISED, date(2026, 8, 1), date(2026, 8, 31), ROOM_MAPS
        )
        assert fin["nights"] == 6
        assert fin["total_amount"] == (470 + 30) * 6  # old rate for all 6 nights, not new

    def test_booking_dated_after_effective_date_bills_new_rate_in_full(self):
        # Booked 16 Aug -> 18 Aug: check-in is on the effective date itself.
        bk = booking(
            check_in_date="2026-08-16", check_out_date="2026-08-18",
            room_numbers=["C1-01"], room_categories=["Cat I"],
        )
        fin = booking_financials(
            bk, self.RAISED, date(2026, 8, 1), date(2026, 8, 31), ROOM_MAPS
        )
        assert fin["nights"] == 2
        assert fin["total_amount"] == (500 + 35) * 2  # new rate for all 2 nights


class TestEarlyCheckoutPenalty:
    """2026-09 owner/accountant ruling: an uninformed early checkout is
    billed for its full ORIGINALLY BOOKED nights as a penalty, but the room
    must still be reported vacant from the real (early) departure onward.
    Evidence case BK0630: check-in 31 Jul, planned checkout 3 Aug, actual
    checkout 1 Aug — previously this dropped ₹2,075 of penalty revenue
    because it fell entirely in August, a month the booking had zero
    physical nights left in and was therefore skipped outright."""

    def test_occupancy_uses_actual_departure_not_original_plan(self):
        bk = booking(
            check_in_date="2026-07-31", check_out_date="2026-08-03",
            actual_checkout_date="2026-08-01", charge_reason="early_checkout_not_informed",
        )
        assert nights_in_period(bk, date(2026, 8, 1), date(2026, 8, 31)) == 0

    def test_billing_uses_original_plan_not_actual_departure(self):
        bk = booking(
            check_in_date="2026-07-31", check_out_date="2026-08-03",
            actual_checkout_date="2026-08-01", charge_reason="early_checkout_not_informed",
        )
        assert billing_nights_in_period(bk, date(2026, 8, 1), date(2026, 8, 31)) == 2

    def test_penalty_nights_split_at_month_boundary_like_a_normal_stay(self):
        bk = booking(
            check_in_date="2026-07-31", check_out_date="2026-08-03",
            actual_checkout_date="2026-08-01", charge_reason="early_checkout_not_informed",
        )
        july = billing_nights_in_period(bk, date(2026, 7, 1), date(2026, 7, 31))
        august = billing_nights_in_period(bk, date(2026, 8, 1), date(2026, 8, 31))
        assert (july, august) == (1, 2)
        assert july + august == 3  # the full original 31 Jul -> 3 Aug stay

    def test_booking_appears_in_a_month_it_has_zero_physical_nights_in(self):
        # This is the exact bug: a room-vacant month must not make the
        # booking (and its penalty revenue) disappear from that report.
        bk = booking(
            check_in_date="2026-07-31", check_out_date="2026-08-03",
            actual_checkout_date="2026-08-01", charge_reason="early_checkout_not_informed",
        )
        fin = booking_financials(bk, SETTINGS, date(2026, 8, 1), date(2026, 8, 31), ROOM_MAPS)
        assert fin["nights"] == 0          # room correctly shown vacant in August
        assert fin["billed_nights"] == 2   # penalty revenue still recognized in August
        assert fin["rooms"] != []
        assert fin["total_amount"] == (470 + 30) * 2

    def test_full_penalty_recovered_across_both_months_combined(self):
        bk = booking(
            check_in_date="2026-07-31", check_out_date="2026-08-03",
            actual_checkout_date="2026-08-01", charge_reason="early_checkout_not_informed",
        )
        july = booking_financials(bk, SETTINGS, date(2026, 7, 1), date(2026, 7, 31), ROOM_MAPS)
        august = booking_financials(bk, SETTINGS, date(2026, 8, 1), date(2026, 8, 31), ROOM_MAPS)
        assert july["total_amount"] + august["total_amount"] == (470 + 30) * 3

    def test_informed_early_checkout_is_not_a_penalty(self):
        # Guest informed at check-in -> bills actual nights only, no penalty.
        bk = booking(
            check_in_date="2026-08-05", check_out_date="2026-08-10",
            actual_checkout_date="2026-08-07", charge_reason="early_checkout_informed",
        )
        fin = booking_financials(bk, SETTINGS, date(2026, 8, 1), date(2026, 8, 31), ROOM_MAPS)
        assert fin["nights"] == fin["billed_nights"] == 2

    def test_confirmed_or_checked_in_booking_unaffected(self):
        # charge_reason only ever applies to a checked_out booking; a booking
        # still in progress must never get the penalty treatment.
        bk = booking(status="checked_in", charge_reason="early_checkout_not_informed",
                     check_in_date="2026-08-05", check_out_date="2026-08-10")
        fin = booking_financials(bk, SETTINGS, date(2026, 8, 1), date(2026, 8, 31), ROOM_MAPS)
        assert fin["nights"] == fin["billed_nights"] == 5

    def test_extra_bed_charge_unaffected_by_penalty_basis(self):
        # No ruling covers extra beds for this penalty — they stay on the
        # physical (occupancy) nights, unlike room rent and license fee.
        bk = booking(
            check_in_date="2026-07-31", check_out_date="2026-08-03",
            actual_checkout_date="2026-08-01", charge_reason="early_checkout_not_informed",
            extra_beds=1,
        )
        fin = booking_financials(bk, SETTINGS, date(2026, 8, 1), date(2026, 8, 31), ROOM_MAPS)
        assert fin["extra_bed_charge"] == 0.0  # zero physical nights in August


class TestPerRoomChargeCategoryOverride:
    """2026-09 Aug reconciliation, round 2 — Evidence case BK0754: an Org
    booking (is_org=True) with one room explicitly billed Non-Org via
    room_guest_mapping's charge_category. Every report had always used the
    booking-level is_org for every room, so this room was billed Non-Org in
    reality (₹600/night combined) but reported at the Org Cat II rate
    (₹400/night) — a ₹1,000 gap over 5 nights that had nothing to do with
    early checkout. This must match check_in()/check_out() in server.py,
    which already honor this override when actually charging the guest."""

    def test_non_org_override_on_org_booking(self):
        bk = booking(
            is_org=True, room_numbers=["C2-15"], room_categories=["Cat II"],
            check_out_date="2026-05-15",  # 5 nights
            room_guest_mapping=[
                {"room_number": "C2-15", "room_category": "Cat II", "charge_category": "Non-Org"},
            ],
        )
        fin = booking_financials(bk, SETTINGS, MAY_START, MAY_END, ROOM_MAPS)
        assert fin["total_amount"] == (570 + 30) * 5  # Non-Org rate, not Cat II

    def test_no_mapping_falls_back_to_booking_level_is_org(self):
        # No room_guest_mapping at all — must behave exactly as before.
        bk = booking(is_org=True, room_numbers=["C2-15"], room_categories=["Cat II"],
                     check_out_date="2026-05-15")
        fin = booking_financials(bk, SETTINGS, MAY_START, MAY_END, ROOM_MAPS)
        assert fin["total_amount"] == (385 + 15) * 5  # Org Cat II rate

    def test_mapping_present_without_override_falls_back_too(self):
        # charge_category omitted (or equal to room_category) -> no override.
        bk = booking(
            is_org=True, room_numbers=["C2-15"], room_categories=["Cat II"],
            check_out_date="2026-05-15",
            room_guest_mapping=[{"room_number": "C2-15", "room_category": "Cat II"}],
        )
        fin = booking_financials(bk, SETTINGS, MAY_START, MAY_END, ROOM_MAPS)
        assert fin["total_amount"] == (385 + 15) * 5

    def test_override_applies_only_to_its_own_room_in_multi_room_booking(self):
        bk = booking(
            is_org=True, room_numbers=["C1-01", "C2-08"], room_categories=["Cat I", "Cat II"],
            check_out_date="2026-05-15",  # 5 nights
            room_guest_mapping=[
                {"room_number": "C1-01", "room_category": "Cat I", "charge_category": "Non-Org"},
                {"room_number": "C2-08", "room_category": "Cat II", "charge_category": "Cat II"},
            ],
        )
        fin = booking_financials(bk, SETTINGS, MAY_START, MAY_END, ROOM_MAPS)
        by_room = {r["room_number"]: r for r in fin["rooms"]}
        assert by_room["C1-01"]["room_rent"] + by_room["C1-01"]["license_fee"] == (570 + 30) * 5
        assert by_room["C2-08"]["room_rent"] + by_room["C2-08"]["license_fee"] == (385 + 15) * 5

    def test_room_carries_its_own_resolved_is_org_not_the_booking_level_flag(self):
        # Callers that bucket money by Org/Non-Org (e.g. the monthly category
        # tables) must read this per room, or an overridden room's now-correct
        # money still lands in the wrong bucket.
        bk = booking(
            is_org=True, room_numbers=["C1-01", "C2-08"], room_categories=["Cat I", "Cat II"],
            check_out_date="2026-05-15",
            room_guest_mapping=[
                {"room_number": "C1-01", "room_category": "Cat I", "charge_category": "Non-Org"},
                {"room_number": "C2-08", "room_category": "Cat II", "charge_category": "Cat II"},
            ],
        )
        fin = booking_financials(bk, SETTINGS, MAY_START, MAY_END, ROOM_MAPS)
        by_room = {r["room_number"]: r for r in fin["rooms"]}
        assert by_room["C1-01"]["is_org"] is False
        assert by_room["C2-08"]["is_org"] is True


class TestExtraBedAddedAtCheckout:
    """2026-09 Aug reconciliation, round 2 — Evidence case BK0630: a bed
    added AT CHECKOUT (extra_beds_checkout/extra_bed_days, settled as
    extra_bed_charge_checkout) is real, collected money that report_calc had
    never read at all — separate from extra_beds, which is set at booking
    time. It has no stored date range, so it's counted entirely in whichever
    period contains the actual checkout date."""

    def test_checkout_extra_bed_counted_in_the_checkout_month(self):
        bk = booking(
            check_in_date="2026-07-31", check_out_date="2026-08-03",
            actual_checkout_date="2026-08-01", charge_reason="early_checkout_not_informed",
            room_numbers=["C1-05", "C1-06"], room_categories=["Cat I", "Cat I"],
            extra_bed_charge_checkout=75,
        )
        july = booking_financials(bk, SETTINGS, date(2026, 7, 1), date(2026, 7, 31), ROOM_MAPS)
        august = booking_financials(bk, SETTINGS, date(2026, 8, 1), date(2026, 8, 31), ROOM_MAPS)
        assert july["extra_bed_charge"] == 0.0
        assert august["extra_bed_charge"] == 75.0
        assert july["total_amount"] + august["total_amount"] == (470 + 30) * 2 * 3 + 75

    def test_absent_for_a_booking_still_in_progress(self):
        bk = booking(status="checked_in", check_in_date="2026-05-05", check_out_date="2026-05-10")
        fin = booking_financials(bk, SETTINGS, MAY_START, MAY_END, ROOM_MAPS)
        assert fin["extra_bed_charge"] == 0.0

    def test_adds_to_not_replaces_booking_time_extra_beds(self):
        bk = booking(
            check_in_date="2026-05-10", check_out_date="2026-05-12",
            actual_checkout_date="2026-05-12", extra_beds=1,
            extra_bed_charge_checkout=150,
        )
        fin = booking_financials(bk, SETTINGS, MAY_START, MAY_END, ROOM_MAPS)
        assert fin["extra_bed_charge"] == (1 * 75.0 * 2) + 150

    def test_a_booking_with_zero_nights_here_still_appears_for_its_checkout_extra_bed(self):
        # Guards the fin["rooms"] gate: a checkout-only charge in a period
        # with zero physical/billed nights must not vanish along with it.
        bk = booking(
            check_in_date="2026-04-25", check_out_date="2026-04-30",
            actual_checkout_date="2026-04-30", extra_beds=0,
            extra_bed_charge_checkout=150,
        )
        # actual_checkout_date is in April, so May must see nothing at all —
        # this only guards against the room list going empty while a charge
        # is still expected in the SAME period as the checkout.
        may_fin = booking_financials(bk, SETTINGS, MAY_START, MAY_END, ROOM_MAPS)
        assert may_fin["extra_bed_charge"] == 0.0
        assert may_fin["rooms"] == []

        bk_boundary = booking(
            check_in_date="2026-04-25", check_out_date="2026-04-30",
            actual_checkout_date="2026-05-01", extra_beds=0,
            extra_bed_charge_checkout=150,
        )
        may_boundary_fin = booking_financials(bk_boundary, SETTINGS, MAY_START, MAY_END, ROOM_MAPS)
        assert may_boundary_fin["extra_bed_charge"] == 150.0
        assert may_boundary_fin["rooms"] != []
