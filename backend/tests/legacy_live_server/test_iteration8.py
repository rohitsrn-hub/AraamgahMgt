"""
Iteration 8 Backend Tests: Payment mode fields in booking, calculate-refund API
"""
import pytest
import requests
import os
from datetime import date, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestCalculateRefund:
    """Tests for GET /api/bookings/{id}/calculate-refund"""

    def get_confirmed_booking_id(self):
        res = requests.get(f"{BASE_URL}/api/bookings")
        assert res.status_code == 200
        bookings = res.json()
        confirmed = [b for b in bookings if b["status"] == "confirmed"]
        if not confirmed:
            pytest.skip("No confirmed bookings available")
        return confirmed[0]["id"], confirmed[0].get("advance_paid", 400)

    def test_calculate_refund_returns_200(self):
        booking_id, _ = self.get_confirmed_booking_id()
        res = requests.get(f"{BASE_URL}/api/bookings/{booking_id}/calculate-refund")
        assert res.status_code == 200

    def test_calculate_refund_response_structure(self):
        booking_id, _ = self.get_confirmed_booking_id()
        res = requests.get(f"{BASE_URL}/api/bookings/{booking_id}/calculate-refund")
        data = res.json()
        assert "days_until_checkin" in data
        assert "charge_percent" in data
        assert "cancellation_charge" in data
        assert "refund_amount" in data
        assert "advance_paid" in data

    def test_calculate_refund_math(self):
        booking_id, _ = self.get_confirmed_booking_id()
        res = requests.get(f"{BASE_URL}/api/bookings/{booking_id}/calculate-refund")
        data = res.json()
        advance = data["advance_paid"]
        charge = data["cancellation_charge"]
        refund = data["refund_amount"]
        # refund + charge should == advance
        assert abs((refund + charge) - advance) < 0.01, f"Math mismatch: {refund} + {charge} != {advance}"

    def test_calculate_refund_invalid_id(self):
        res = requests.get(f"{BASE_URL}/api/bookings/invalid_id_xyz/calculate-refund")
        assert res.status_code == 404

    def test_charge_percent_is_valid(self):
        booking_id, _ = self.get_confirmed_booking_id()
        res = requests.get(f"{BASE_URL}/api/bookings/{booking_id}/calculate-refund")
        data = res.json()
        assert data["charge_percent"] in [0, 25, 50, 100]

    def test_refund_amount_non_negative(self):
        booking_id, _ = self.get_confirmed_booking_id()
        res = requests.get(f"{BASE_URL}/api/bookings/{booking_id}/calculate-refund")
        data = res.json()
        assert data["refund_amount"] >= 0


class TestBookingWithPaymentMode:
    """Test booking creation with payment mode fields"""

    created_booking_id = None

    def get_available_room(self):
        checkin = (date.today() + timedelta(days=30)).isoformat()
        checkout = (date.today() + timedelta(days=32)).isoformat()
        res = requests.get(f"{BASE_URL}/api/dashboard/room-availability",
                           params={"check_in_date": checkin, "check_out_date": checkout})
        assert res.status_code == 200
        rooms = res.json().get("available_rooms", [])
        if not rooms:
            pytest.skip("No available rooms for test dates")
        return rooms[0]["id"], checkin, checkout

    def test_booking_cash_payment_mode(self):
        room_id, checkin, checkout = self.get_available_room()
        payload = {
            "guest_name": "TEST_PaymentMode_Cash",
            "room_ids": [room_id],
            "num_rooms": 1,
            "check_in_date": checkin,
            "check_out_date": checkout,
            "advance_paid": 400,
            "payment_mode": "cash",
            "payment_id": "RCPT-0001"
        }
        res = requests.post(f"{BASE_URL}/api/bookings", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["payment_mode"] == "cash"
        TestBookingWithPaymentMode.created_booking_id = data.get("id")

    def test_booking_upi_payment_mode(self):
        room_id, checkin, checkout = self.get_available_room()
        payload = {
            "guest_name": "TEST_PaymentMode_UPI",
            "room_ids": [room_id],
            "num_rooms": 1,
            "check_in_date": checkin,
            "check_out_date": checkout,
            "advance_paid": 400,
            "payment_mode": "upi",
            "upi_id": "test@upi"
        }
        res = requests.post(f"{BASE_URL}/api/bookings", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["payment_mode"] == "upi"

    def test_booking_bank_transfer_payment_mode(self):
        room_id, checkin, checkout = self.get_available_room()
        payload = {
            "guest_name": "TEST_PaymentMode_Bank",
            "room_ids": [room_id],
            "num_rooms": 1,
            "check_in_date": checkin,
            "check_out_date": checkout,
            "advance_paid": 400,
            "payment_mode": "bank_transfer",
            "bank_name": "State Bank of India",
            "bank_ifsc": "SBIN0001234",
            "bank_account": "12345678901"
        }
        res = requests.post(f"{BASE_URL}/api/bookings", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["payment_mode"] == "bank_transfer"

    def test_booking_card_payment_mode(self):
        room_id, checkin, checkout = self.get_available_room()
        payload = {
            "guest_name": "TEST_PaymentMode_Card",
            "room_ids": [room_id],
            "num_rooms": 1,
            "check_in_date": checkin,
            "check_out_date": checkout,
            "advance_paid": 400,
            "payment_mode": "card",
            "payment_id": "CARD-TXN-9999"
        }
        res = requests.post(f"{BASE_URL}/api/bookings", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["payment_mode"] == "card"
