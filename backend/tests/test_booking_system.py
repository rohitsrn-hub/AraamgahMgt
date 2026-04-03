"""
Backend tests for Rest House Booking System
Tests: Settings, Rooms, Bookings, Refunds, Pending Refunds
"""
import pytest
import requests
import os
from datetime import date, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestSettings:
    """Settings API tests"""

    def test_get_settings(self):
        res = requests.get(f"{BASE_URL}/api/settings")
        assert res.status_code == 200
        data = res.json()
        assert "cat_i_rate" in data
        assert "cat_ii_rate" in data

    def test_settings_has_def_civ_rates(self):
        res = requests.get(f"{BASE_URL}/api/settings")
        assert res.status_code == 200
        data = res.json()
        assert "def_civ_cat_i_rate" in data, "Missing def_civ_cat_i_rate in settings"
        assert "def_civ_cat_ii_rate" in data, "Missing def_civ_cat_ii_rate in settings"

    def test_settings_has_ranks(self):
        res = requests.get(f"{BASE_URL}/api/settings")
        assert res.status_code == 200
        data = res.json()
        assert "ranks" in data
        ranks = data["ranks"]
        assert len(ranks) >= 1
        # Check Def Civ is present
        assert "Def Civ" in ranks, f"Def Civ not found in ranks: {ranks}"

    def test_update_settings(self):
        res = requests.get(f"{BASE_URL}/api/settings")
        current = res.json()
        payload = {
            "cat_i_rate": current.get("cat_i_rate", 500),
            "cat_ii_rate": current.get("cat_ii_rate", 300),
            "def_civ_cat_i_rate": current.get("def_civ_cat_i_rate", 600),
            "def_civ_cat_ii_rate": current.get("def_civ_cat_ii_rate", 400),
            "default_advance_amount": current.get("default_advance_amount", 500),
            "ranks": current.get("ranks", []),
            "cancellation_policy": current.get("cancellation_policy", []),
            "fmn_sign_1_url": current.get("fmn_sign_1_url", ""),
            "fmn_sign_2_url": current.get("fmn_sign_2_url", ""),
        }
        put_res = requests.put(f"{BASE_URL}/api/settings", json=payload)
        assert put_res.status_code == 200


class TestRooms:
    """Rooms API tests"""

    def test_get_rooms(self):
        res = requests.get(f"{BASE_URL}/api/rooms")
        assert res.status_code == 200
        rooms = res.json()
        assert len(rooms) > 0

    def test_rooms_have_categories(self):
        res = requests.get(f"{BASE_URL}/api/rooms")
        rooms = res.json()
        categories = {r["category"] for r in rooms}
        assert "Cat I" in categories
        assert "Cat II" in categories


class TestBookings:
    """Booking CRUD tests"""

    def get_available_room(self):
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        day_after = (date.today() + timedelta(days=2)).isoformat()
        res = requests.get(f"{BASE_URL}/api/dashboard/room-availability",
                           params={"check_in_date": tomorrow, "check_out_date": day_after})
        if res.status_code == 200:
            rooms = res.json().get("available_rooms", [])
            if rooms:
                return rooms[0]["id"], tomorrow, day_after
        return None, None, None

    def get_staff_id(self):
        res = requests.get(f"{BASE_URL}/api/staff")
        if res.status_code == 200 and res.json():
            return res.json()[0]["id"]
        return None

    def test_get_bookings(self):
        res = requests.get(f"{BASE_URL}/api/bookings")
        assert res.status_code == 200
        assert isinstance(res.json(), list)

    def test_create_booking_with_bank_details(self):
        room_id, checkin, checkout = self.get_available_room()
        if not room_id:
            pytest.skip("No available rooms")

        payload = {
            "guest_name": "TEST_Ramesh Kumar",
            "guest_contact": "+91 98765 43210",
            "guest_rank": "Hav",
            "guest_unit": "2 PARA",
            "guest_service_status": "Serving",
            "room_ids": [room_id],
            "num_guests": 1,
            "num_rooms": 1,
            "check_in_date": checkin,
            "check_out_date": checkout,
            "advance_paid": 500,
            "payment_mode": "cash",
            "payment_id": "RCPT-TEST-001",
            "bank_name": "State Bank of India",
            "bank_ifsc": "SBIN0001234",
            "bank_account": "1234567890",
            "upi_id": "test@upi",
            "upi_phone": "9876543210",
            "notes": "TEST booking"
        }
        res = requests.post(f"{BASE_URL}/api/bookings", json=payload)
        assert res.status_code == 200, f"Booking creation failed: {res.text}"
        data = res.json()
        assert "id" in data
        assert data["guest_name"] == "TEST_Ramesh Kumar"
        assert data.get("bank_name") == "State Bank of India", f"bank_name not persisted: {data}"
        assert data.get("bank_ifsc") == "SBIN0001234", f"bank_ifsc not persisted: {data}"
        assert data.get("upi_id") == "test@upi", f"upi_id not persisted: {data}"
        # Return booking_id for other tests to use
        return data["id"]

    def test_create_and_cancel_booking_creates_refund(self):
        room_id, checkin, checkout = self.get_available_room()
        if not room_id:
            pytest.skip("No available rooms")

        payload = {
            "guest_name": "TEST_Cancel Guest",
            "guest_contact": "+91 87654 32109",
            "guest_rank": "Nk",
            "guest_unit": "3 PARA",
            "guest_service_status": "Retired",
            "room_ids": [room_id],
            "num_guests": 1,
            "num_rooms": 1,
            "check_in_date": checkin,
            "check_out_date": checkout,
            "advance_paid": 500,
            "payment_mode": "upi",
            "payment_id": "UPI-TEST-001",
            "bank_name": "HDFC Bank",
            "bank_ifsc": "HDFC0001234",
            "bank_account": "9876543210",
            "upi_id": "cancel@upi",
            "upi_phone": "8765432109"
        }
        create_res = requests.post(f"{BASE_URL}/api/bookings", json=payload)
        assert create_res.status_code == 200, f"Create failed: {create_res.text}"
        booking_id = create_res.json()["id"]

        # Cancel it
        cancel_res = requests.post(f"{BASE_URL}/api/bookings/cancel", json={
            "booking_id": booking_id,
            "reason": "Test cancellation",
            "refund_amount": 400
        })
        assert cancel_res.status_code == 200, f"Cancel failed: {cancel_res.text}"

        # Check refund was created
        refund_res = requests.get(f"{BASE_URL}/api/refunds", params={"status": "pending"})
        assert refund_res.status_code == 200
        refunds = refund_res.json()
        matching = [r for r in refunds if r["booking_id"] == booking_id]
        assert len(matching) > 0, "No refund created after cancellation"
        refund = matching[0]
        assert refund["amount"] == 400
        # Verify bank details carried over
        assert refund.get("bank_name") == "HDFC Bank", f"bank_name not in refund: {refund}"

        # Mark refund as completed
        refund_id = refund["id"]
        complete_res = requests.put(f"{BASE_URL}/api/refunds/{refund_id}", json={
            "status": "completed",
            "transaction_ref": "UTR-TEST-12345",
            "refund_date": checkin,
            "notes": "Test refund completed"
        })
        assert complete_res.status_code == 200, f"Refund update failed: {complete_res.text}"
        completed = complete_res.json()
        assert completed["status"] == "completed"
        assert completed["transaction_ref"] == "UTR-TEST-12345"


class TestRefunds:
    """Refund endpoint tests"""

    def test_get_pending_refunds(self):
        res = requests.get(f"{BASE_URL}/api/refunds", params={"status": "pending"})
        assert res.status_code == 200
        assert isinstance(res.json(), list)

    def test_get_all_refunds(self):
        res = requests.get(f"{BASE_URL}/api/refunds")
        assert res.status_code == 200
        assert isinstance(res.json(), list)


class TestRoomAvailability:
    """Room availability API tests"""

    def test_room_availability(self):
        tomorrow = (date.today() + timedelta(days=3)).isoformat()
        day_after = (date.today() + timedelta(days=4)).isoformat()
        res = requests.get(f"{BASE_URL}/api/dashboard/room-availability",
                           params={"check_in_date": tomorrow, "check_out_date": day_after})
        assert res.status_code == 200
        data = res.json()
        assert "available_rooms" in data
