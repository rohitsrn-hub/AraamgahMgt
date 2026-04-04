"""
Tests for simplified booking form - iteration 5
Verifies booking creation without guest_contact field succeeds
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


def get_available_room():
    """Get first available room for testing"""
    from datetime import datetime, timedelta
    check_in = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    check_out = (datetime.now() + timedelta(days=32)).strftime("%Y-%m-%d")
    res = requests.get(f"{BASE_URL}/api/dashboard/room-availability", params={
        "check_in_date": check_in,
        "check_out_date": check_out
    })
    if res.status_code == 200:
        data = res.json()
        rooms = data.get("available_rooms", [])
        if rooms:
            return rooms[0]["id"], check_in, check_out
    return None, None, None


class TestBookingAPI:
    """Test POST /api/bookings with simplified payload (no guest_contact)"""

    def test_create_booking_without_guest_contact(self):
        """Booking creation should succeed without contact number"""
        room_id, check_in, check_out = get_available_room()
        if not room_id:
            pytest.skip("No available rooms for testing")

        payload = {
            "guest_name": "TEST_SimplifiedBooking",
            "guest_rank": "Hav",
            "army_number": "15814432-F",
            "aadhaar_number": "123456789012",
            "guest_unit": "2 PARA",
            "room_ids": [room_id],
            "num_rooms": 1,
            "check_in_date": check_in,
            "check_out_date": check_out,
            "advance_paid": 400
        }
        # Explicitly no guest_contact field
        assert "guest_contact" not in payload

        res = requests.post(f"{BASE_URL}/api/bookings", json=payload)
        print(f"Status: {res.status_code}, Response: {res.text[:300]}")
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"

        data = res.json()
        assert data["guest_name"] == "TEST_SimplifiedBooking"
        assert data["army_number"] == "15814432-F"
        assert data["aadhaar_number"] == "123456789012"
        # Note: guest_unit is in BookingCreate but NOT stored in Booking model (known gap)
        assert "id" in data
        assert data["status"] == "confirmed"
        print(f"PASS: Booking created with ID {data['id']}, number {data['booking_number']}")

        # Cleanup: cancel the test booking
        cancel_res = requests.post(f"{BASE_URL}/api/bookings/cancel", json={
            "booking_id": data["id"],
            "reason": "TEST cleanup",
            "refund_amount": 0
        })
        print(f"Cleanup cancel status: {cancel_res.status_code}")

    def test_create_booking_minimal_fields_only_name_dates_room(self):
        """Booking with only guest_name, dates, and room - minimum required"""
        room_id, check_in, check_out = get_available_room()
        if not room_id:
            pytest.skip("No available rooms for testing")

        payload = {
            "guest_name": "TEST_MinimalBooking",
            "room_ids": [room_id],
            "check_in_date": check_in,
            "check_out_date": check_out,
        }
        res = requests.post(f"{BASE_URL}/api/bookings", json=payload)
        print(f"Minimal booking status: {res.status_code}, Response: {res.text[:300]}")
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"

        data = res.json()
        assert data["guest_name"] == "TEST_MinimalBooking"
        assert data["status"] == "confirmed"
        print(f"PASS: Minimal booking created with ID {data['id']}")

        # Cleanup
        requests.post(f"{BASE_URL}/api/bookings/cancel", json={
            "booking_id": data["id"],
            "reason": "TEST cleanup",
            "refund_amount": 0
        })

    def test_bookings_list_returns_ok(self):
        """GET /api/bookings returns 200"""
        res = requests.get(f"{BASE_URL}/api/bookings")
        assert res.status_code == 200
        assert isinstance(res.json(), list)
        print(f"PASS: GET /api/bookings returned {len(res.json())} bookings")
