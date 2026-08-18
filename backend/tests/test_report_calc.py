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
    effective_category_rate,
    effective_non_org_rate,
    effective_stay,
    get_category,
    migrate_legacy_settings,
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


class TestLegacyMigration:
    """migrate_legacy_settings() upgrades an old flat-field settings document
    to the room_categories[]-based shape, in memory only, without touching
    or deleting anything old — this is what makes it safe to run against a
    document that already has real production data (e.g. an existing
    Aug-2026 rate_history entry saved before N-category support existed)."""

    OLD_SHAPE = {
        "cat_i_room_rent": 470, "cat_i_license_fee": 30, "cat_i_rooms_count": 6,
        "cat_ii_room_rent": 385, "cat_ii_license_fee": 15, "cat_ii_rooms_count": 9,
        "non_org_room_rent": 570, "non_org_license_fee": 30,
        "rate_history": [
            {"id": "abc123", "effective_date": "2026-08-16",
             "cat_i_room_rent": 500, "cat_i_license_fee": 35,
             "cat_ii_room_rent": 420, "cat_ii_license_fee": 20,
             "non_org_room_rent": 600, "non_org_license_fee": 35,
             "note": "Administration rate revision"},
        ],
    }

    def test_builds_room_categories_from_flat_fields(self):
        migrated = migrate_legacy_settings(self.OLD_SHAPE)
        cat_i = get_category(migrated, "Cat I")
        cat_ii = get_category(migrated, "Cat II")
        assert cat_i == {"id": "cat-i", "name": "Cat I", "prefix": "C1", "capacity": 2,
                          "room_count": 6, "room_rent": 470, "license_fee": 30}
        assert cat_ii == {"id": "cat-ii", "name": "Cat II", "prefix": "C2", "capacity": 2,
                           "room_count": 9, "room_rent": 385, "license_fee": 15}

    def test_converts_rate_history_to_category_rates(self):
        migrated = migrate_legacy_settings(self.OLD_SHAPE)
        entry = migrated["rate_history"][0]
        assert entry["category_rates"] == {
            "Cat I": {"room_rent": 500, "license_fee": 35},
            "Cat II": {"room_rent": 420, "license_fee": 20},
        }
        # Non-category fields (id, effective_date, non_org_*, note) survive untouched.
        assert entry["id"] == "abc123"
        assert entry["effective_date"] == "2026-08-16"
        assert entry["non_org_room_rent"] == 600
        assert entry["note"] == "Administration rate revision"
        # Old flat cat_i_room_rent-style keys are gone from the migrated entry
        # (superseded by category_rates), but the ORIGINAL dict is untouched.
        assert "cat_i_room_rent" not in entry
        assert self.OLD_SHAPE["rate_history"][0]["cat_i_room_rent"] == 500

    def test_does_not_mutate_original_dict(self):
        original_copy = {**self.OLD_SHAPE, "rate_history": list(self.OLD_SHAPE["rate_history"])}
        migrate_legacy_settings(self.OLD_SHAPE)
        assert self.OLD_SHAPE == original_copy
        assert "room_categories" not in self.OLD_SHAPE  # migration didn't add it in place

    def test_idempotent_on_already_migrated_settings(self):
        once = migrate_legacy_settings(self.OLD_SHAPE)
        twice = migrate_legacy_settings(once)
        assert once == twice

    def test_rate_components_gives_identical_numbers_old_vs_migrated_shape(self):
        # The whole point: billing must not change for existing Cat I/Cat II
        # bookings just because the storage shape changed underneath them.
        migrated = migrate_legacy_settings(self.OLD_SHAPE)
        for cat in ("Cat I", "Cat II"):
            for ci in (date(2026, 8, 10), date(2026, 8, 16), date(2026, 9, 1)):
                assert rate_components(self.OLD_SHAPE, True, cat, ci) == \
                       rate_components(migrated, True, cat, ci)


class TestNCategorySupport:
    """The actual point of this work: a category beyond the original Cat I/
    Cat II must price correctly, get its own future rate schedule, and never
    fall through to Cat II's rate by accident (the bug found in the old
    `if category == "Cat I": ... else: ...` branches throughout the app)."""

    THREE_CATEGORIES = {
        "room_categories": [
            {"id": "cat-i", "name": "Cat I", "prefix": "C1", "capacity": 2,
             "room_count": 6, "room_rent": 470, "license_fee": 30},
            {"id": "cat-ii", "name": "Cat II", "prefix": "C2", "capacity": 2,
             "room_count": 9, "room_rent": 385, "license_fee": 15},
            {"id": "cat-iii", "name": "Cat III", "prefix": "C3", "capacity": 4,
             "room_count": 24, "room_rent": 650, "license_fee": 40},
        ],
        "non_org_room_rent": 570, "non_org_license_fee": 30,
    }

    def test_third_category_prices_from_its_own_config_not_cat_ii(self):
        assert rate_components(self.THREE_CATEGORIES, True, "Cat III", date(2026, 9, 1)) == (650, 40)

    def test_effective_category_rate_called_directly(self):
        # rate_components() is a thin (is_org, category) router — this checks
        # the underlying per-category resolver itself, dict-shaped.
        assert effective_category_rate(self.THREE_CATEGORIES, "Cat III", date(2026, 9, 1)) == \
            {"room_rent": 650, "license_fee": 40}

    def test_effective_non_org_rate_called_directly(self):
        assert effective_non_org_rate(self.THREE_CATEGORIES, date(2026, 9, 1)) == \
            {"room_rent": 570, "license_fee": 30}

    def test_third_category_gets_its_own_future_rate_change(self):
        settings = {
            **self.THREE_CATEGORIES,
            "rate_history": [
                {"effective_date": "2026-10-01", "category_rates": {
                    "Cat III": {"room_rent": 700, "license_fee": 45},
                }},
            ],
        }
        # Cat III's change doesn't touch Cat I/II...
        assert rate_components(settings, True, "Cat I", date(2026, 10, 15)) == (470, 30)
        assert rate_components(settings, True, "Cat II", date(2026, 10, 15)) == (385, 15)
        # ...and only applies to Cat III from its effective date.
        assert rate_components(settings, True, "Cat III", date(2026, 9, 30)) == (650, 40)
        assert rate_components(settings, True, "Cat III", date(2026, 10, 1)) == (700, 45)

    def test_non_org_stays_flat_regardless_of_which_of_the_three_categories(self):
        for cat in ("Cat I", "Cat II", "Cat III"):
            assert rate_components(self.THREE_CATEGORIES, False, cat, date(2026, 9, 1)) == (570, 30)

    def test_unrecognized_category_does_not_silently_bill_as_cat_ii(self):
        # The old `if category == "Cat I": ... else: (must be Cat II)` branch
        # made ANY unrecognized category name price as Cat II. A typo'd or
        # not-yet-configured category name must not silently match Cat II's
        # rate — it should fall back to the safe default instead.
        assert get_category(self.THREE_CATEGORIES, "Cat IV — Cottage") is None
        rent, fee = rate_components(self.THREE_CATEGORIES, True, "Cat IV — Cottage", date(2026, 9, 1))
        assert (rent, fee) != (385, 15)  # must NOT be Cat II's rate
        assert (rent, fee) == (470, 30)  # safe default, not a crash

    def test_booking_financials_end_to_end_with_third_category(self):
        rooms = ROOMS + [{"id": "r5", "room_number": "C3-01", "category": "Cat III"}]
        room_maps = build_room_maps(rooms)
        bk = booking(
            check_in_date="2026-09-01", check_out_date="2026-09-03",
            room_numbers=["C1-01", "C3-01"], room_categories=["Cat I", "Cat III"],
        )
        fin = booking_financials(bk, self.THREE_CATEGORIES, date(2026, 9, 1), date(2026, 9, 30), room_maps)
        assert fin["nights"] == 2
        by_room = {r["room_number"]: r["rate_per_night"] for r in fin["rooms"]}
        assert by_room == {"C1-01": 470 + 30, "C3-01": 650 + 40}
        assert fin["total_amount"] == (470 + 30) * 2 + (650 + 40) * 2
