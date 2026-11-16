"""
Manual-format Excel export — regressions found by the Nov 2026 audit.

The four on-screen reports were all updated in Sept 2026 to keep a booking in
a month where it has no physical nights but still owes money there (an
uninformed early checkout's penalty nights, or an extra bed added at
checkout). The Excel export was missed: it still skipped any booking with
zero physical nights in the month, so its Total Amt column came out lower
than the four reports for exactly those months.
"""
import asyncio
import sys
from io import BytesIO
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from openpyxl import load_workbook

from test_manual_occupancy_excel import ROOMS, _FakeDB, _booking
from utils.manual_occupancy_excel import build_manual_occupancy_workbook
from utils.report_calc import booking_financials, build_room_maps
from datetime import date


def _rows(bookings, month, year=2026):
    buf = asyncio.run(build_manual_occupancy_workbook(_FakeDB(bookings, {}, ROOMS), month, year))
    ws = load_workbook(BytesIO(buf.getvalue())).active
    rows = []
    for r in ws.iter_rows(min_row=3, values_only=True):
        if r[0] == "Total":
            break
        rows.append(r)
    return rows


def _penalty_booking():
    # Booked 29 Jul - 3 Aug, left 31 Jul without informing: August has zero
    # physical nights but two billed (penalty) nights.
    return _booking(booking_number="BKPEN", check_in_date="2026-07-29", check_out_date="2026-08-03",
                    actual_checkout_date="2026-07-31", charge_reason="early_checkout_not_informed")


def test_penalty_only_month_is_not_dropped_from_the_excel():
    rows = _rows([_penalty_booking()], month=8)
    assert len(rows) == 1, "booking with only penalty nights in August must still be listed"
    assert rows[0][7] == 0            # Total No of days: physically vacant in August
    assert rows[0][13] == 2 * 500     # Total Amt: two penalty nights at Cat I


def test_excel_total_equals_the_reports_total_for_the_same_month():
    bookings = [_penalty_booking(),
                _booking(booking_number="BKN", check_in_date="2026-08-05", check_out_date="2026-08-07")]
    excel_total = sum(r[13] for r in _rows(bookings, month=8))
    maps = build_room_maps(ROOMS)
    report_total = sum(
        booking_financials(b, {}, date(2026, 8, 1), date(2026, 8, 31), maps)["total_amount"]
        for b in bookings)
    assert excel_total == report_total == 1000 + 1000


def test_advance_is_listed_once_per_booking_not_once_per_room():
    """A two-room booking that paid Rs 400 advance must add Rs 400, not
    Rs 800, to the sheet's Advance Amt total."""
    bk = _booking(room_numbers=["C1-01", "C2-08"], room_categories=["Cat I", "Cat II"], advance_paid=400)
    rows = _rows([bk], month=6)
    assert len(rows) == 2
    assert [r[9] for r in rows] == [400, 0]


def test_room_billed_non_org_is_labelled_non_org():
    bk = _booking(room_numbers=["C1-01", "C2-08"], room_categories=["Cat I", "Cat II"],
                  room_guest_mapping=[{"room_number": "C2-08", "charge_category": "Non-Org"}])
    rows = _rows([bk], month=6)
    assert [r[5] for r in rows] == ["Org", "Non-Org"]
