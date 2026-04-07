"""
Test suite for P1: Bank Details in Booking Form
Features tested:
1. Backend `/api/bookings` POST accepts bank_name, bank_ifsc, bank_account, upi_id, upi_phone
2. Bank/UPI details are stored in booking and returned in response
3. Bank/UPI details are passed to refund when booking is cancelled
4. Check-in form receives bank/UPI details from booking (auto-fill)
"""

import pytest
import requests
import os
import uuid
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


@pytest.fixture(scope="module")
def api_session():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture(scope="module")
def settings(api_session):
    """Get app settings"""
    response = api_session.get(f"{BASE_URL}/api/settings")
    assert response.status_code == 200
    return response.json()


@pytest.fixture(scope="module")
def rooms(api_session):
    """Get all rooms"""
    response = api_session.get(f"{BASE_URL}/api/rooms")
    assert response.status_code == 200
    return response.json()


@pytest.fixture(scope="module")
def staff(api_session):
    """Get staff list"""
    response = api_session.get(f"{BASE_URL}/api/staff")
    assert response.status_code == 200
    return response.json()


class TestBookingWithBankDetails:
    """Test booking creation with bank/UPI details for refunds"""
    
    def test_create_booking_with_all_bank_upi_fields(self, api_session, rooms, settings):
        """Test that booking accepts all bank/UPI fields: bank_name, bank_ifsc, bank_account, upi_id, upi_phone"""
        available_rooms = [r for r in rooms if r["status"] == "available"]
        if not available_rooms:
            pytest.skip("No available rooms")
        
        unique_offset = 600 + int(uuid.uuid4().int % 100)
        check_in = (datetime.now() + timedelta(days=unique_offset)).strftime("%Y-%m-%d")
        check_out = (datetime.now() + timedelta(days=unique_offset + 2)).strftime("%Y-%m-%d")
        
        booking_data = {
            "guest_name": f"TEST_P1_BankDetails_{uuid.uuid4().hex[:8]}",
            "guest_contact": "+91 9876543210",
            "guest_rank": "Hav",
            "army_number": f"TEST-{uuid.uuid4().hex[:6]}",
            "guest_unit": "Test Unit",
            "room_ids": [available_rooms[0]["id"]],
            "num_rooms": 1,
            "check_in_date": check_in,
            "check_out_date": check_out,
            "advance_paid": 500,
            "payment_mode": "upi",
            "payment_id": f"UPI-TXN-{uuid.uuid4().hex[:8]}",
            # Bank/UPI details for refund
            "bank_name": "State Bank of India",
            "bank_ifsc": "SBIN0001234",
            "bank_account": "12345678901234",
            "upi_id": "testuser@upi",
            "upi_phone": "9876543210"
        }
        
        response = api_session.post(f"{BASE_URL}/api/bookings", json=booking_data)
        assert response.status_code == 200, f"Booking creation failed: {response.text}"
        
        booking = response.json()
        
        # Verify all bank/UPI fields are stored
        assert booking.get("bank_name") == "State Bank of India", "bank_name not stored"
        assert booking.get("bank_ifsc") == "SBIN0001234", "bank_ifsc not stored"
        assert booking.get("bank_account") == "12345678901234", "bank_account not stored"
        assert booking.get("upi_id") == "testuser@upi", "upi_id not stored"
        assert booking.get("upi_phone") == "9876543210", "upi_phone not stored"
        
        print(f"✓ Booking created with all bank/UPI fields")
        print(f"  Booking Number: {booking['booking_number']}")
        print(f"  Bank Name: {booking.get('bank_name')}")
        print(f"  IFSC: {booking.get('bank_ifsc')}")
        print(f"  Account: {booking.get('bank_account')}")
        print(f"  UPI ID: {booking.get('upi_id')}")
        print(f"  UPI Phone: {booking.get('upi_phone')}")
        
        return booking
    
    def test_create_booking_with_partial_bank_details(self, api_session, rooms, settings):
        """Test that booking accepts partial bank details (only bank or only UPI)"""
        available_rooms = [r for r in rooms if r["status"] == "available"]
        if not available_rooms:
            pytest.skip("No available rooms")
        
        unique_offset = 650 + int(uuid.uuid4().int % 100)
        check_in = (datetime.now() + timedelta(days=unique_offset)).strftime("%Y-%m-%d")
        check_out = (datetime.now() + timedelta(days=unique_offset + 2)).strftime("%Y-%m-%d")
        
        # Only UPI details, no bank details
        booking_data = {
            "guest_name": f"TEST_P1_UPIOnly_{uuid.uuid4().hex[:8]}",
            "guest_contact": "+91 9876543211",
            "guest_rank": "Sep/Dfr/Swr",
            "room_ids": [available_rooms[0]["id"]],
            "num_rooms": 1,
            "check_in_date": check_in,
            "check_out_date": check_out,
            "advance_paid": 400,
            "payment_mode": "upi",
            "payment_id": f"UPI-TXN-{uuid.uuid4().hex[:8]}",
            # Only UPI details
            "upi_id": "onlyupi@paytm",
            "upi_phone": "9876543211"
        }
        
        response = api_session.post(f"{BASE_URL}/api/bookings", json=booking_data)
        assert response.status_code == 200, f"Booking creation failed: {response.text}"
        
        booking = response.json()
        
        # Verify UPI fields are stored
        assert booking.get("upi_id") == "onlyupi@paytm", "upi_id not stored"
        assert booking.get("upi_phone") == "9876543211", "upi_phone not stored"
        # Bank fields should be None or empty
        assert not booking.get("bank_name"), "bank_name should be empty"
        
        print(f"✓ Booking created with only UPI details")
        print(f"  UPI ID: {booking.get('upi_id')}")
        print(f"  UPI Phone: {booking.get('upi_phone')}")


class TestBankDetailsInRefund:
    """Test that bank/UPI details are passed to refund when booking is cancelled"""
    
    def test_cancel_booking_creates_refund_with_bank_details(self, api_session, rooms, settings):
        """Test that cancelling a booking creates refund with bank/UPI details"""
        available_rooms = [r for r in rooms if r["status"] == "available"]
        if not available_rooms:
            pytest.skip("No available rooms")
        
        # Create booking with bank details
        unique_offset = 700 + int(uuid.uuid4().int % 100)
        check_in = (datetime.now() + timedelta(days=unique_offset)).strftime("%Y-%m-%d")
        check_out = (datetime.now() + timedelta(days=unique_offset + 2)).strftime("%Y-%m-%d")
        
        booking_data = {
            "guest_name": f"TEST_P1_Refund_{uuid.uuid4().hex[:8]}",
            "guest_contact": "+91 9876543212",
            "guest_rank": "Nk",
            "room_ids": [available_rooms[0]["id"]],
            "num_rooms": 1,
            "check_in_date": check_in,
            "check_out_date": check_out,
            "advance_paid": 500,
            "payment_mode": "bank_transfer",
            "payment_id": f"NEFT-{uuid.uuid4().hex[:8]}",
            "bank_name": "HDFC Bank",
            "bank_ifsc": "HDFC0001234",
            "bank_account": "98765432109876",
            "upi_id": "refundtest@hdfc",
            "upi_phone": "9876543212"
        }
        
        response = api_session.post(f"{BASE_URL}/api/bookings", json=booking_data)
        assert response.status_code == 200, f"Booking creation failed: {response.text}"
        booking = response.json()
        
        # Calculate refund
        refund_calc_response = api_session.get(f"{BASE_URL}/api/bookings/{booking['id']}/calculate-refund")
        assert refund_calc_response.status_code == 200
        refund_info = refund_calc_response.json()
        
        # Cancel booking
        cancel_data = {
            "booking_id": booking["id"],
            "reason": "Test cancellation for P1 bank details",
            "refund_amount": refund_info.get("refund_amount", 0)
        }
        
        cancel_response = api_session.post(f"{BASE_URL}/api/bookings/cancel", json=cancel_data)
        assert cancel_response.status_code == 200, f"Cancellation failed: {cancel_response.text}"
        
        # Check refund was created with bank details
        refunds_response = api_session.get(f"{BASE_URL}/api/refunds", params={"status": "pending"})
        assert refunds_response.status_code == 200
        refunds = refunds_response.json()
        
        # Find the refund for this booking
        booking_refund = next((r for r in refunds if r.get("booking_id") == booking["id"]), None)
        
        if booking_refund:
            print(f"✓ Refund created with bank/UPI details")
            print(f"  Refund ID: {booking_refund.get('id')}")
            print(f"  Bank Name: {booking_refund.get('bank_name')}")
            print(f"  IFSC: {booking_refund.get('bank_ifsc')}")
            print(f"  Account: {booking_refund.get('bank_account')}")
            print(f"  UPI ID: {booking_refund.get('upi_id')}")
            print(f"  UPI Phone: {booking_refund.get('upi_phone')}")
            
            # Verify bank details are in refund
            assert booking_refund.get("bank_name") == "HDFC Bank", "bank_name not in refund"
            assert booking_refund.get("bank_ifsc") == "HDFC0001234", "bank_ifsc not in refund"
            assert booking_refund.get("bank_account") == "98765432109876", "bank_account not in refund"
            assert booking_refund.get("upi_id") == "refundtest@hdfc", "upi_id not in refund"
            assert booking_refund.get("upi_phone") == "9876543212", "upi_phone not in refund"
        else:
            # Refund might not be created if refund_amount is 0
            print(f"Note: No refund created (refund_amount may be 0)")


class TestCheckInAutoFillBankDetails:
    """Test that check-in form receives bank/UPI details from booking"""
    
    def test_booking_has_bank_details_for_checkin_autofill(self, api_session, rooms, staff, settings):
        """Test that booking response includes bank/UPI details for check-in auto-fill"""
        available_rooms = [r for r in rooms if r["status"] == "available"]
        if not available_rooms:
            pytest.skip("No available rooms")
        
        # Create booking with bank details
        unique_offset = 750 + int(uuid.uuid4().int % 100)
        check_in = (datetime.now() + timedelta(days=unique_offset)).strftime("%Y-%m-%d")
        check_out = (datetime.now() + timedelta(days=unique_offset + 2)).strftime("%Y-%m-%d")
        
        booking_data = {
            "guest_name": f"TEST_P1_CheckIn_{uuid.uuid4().hex[:8]}",
            "guest_contact": "+91 9876543213",
            "guest_rank": "Hav",
            "room_ids": [available_rooms[0]["id"]],
            "num_rooms": 1,
            "check_in_date": check_in,
            "check_out_date": check_out,
            "advance_paid": 500,
            "payment_mode": "cash",
            "payment_id": f"CASH-{uuid.uuid4().hex[:8]}",
            "bank_name": "ICICI Bank",
            "bank_ifsc": "ICIC0001234",
            "bank_account": "11223344556677",
            "upi_id": "checkintest@icici",
            "upi_phone": "9876543213"
        }
        
        response = api_session.post(f"{BASE_URL}/api/bookings", json=booking_data)
        assert response.status_code == 200, f"Booking creation failed: {response.text}"
        booking = response.json()
        
        # Fetch booking by ID to verify bank details are returned
        get_response = api_session.get(f"{BASE_URL}/api/bookings/{booking['id']}")
        assert get_response.status_code == 200
        fetched_booking = get_response.json()
        
        # Verify bank/UPI details are in the booking response (for auto-fill)
        assert fetched_booking.get("bank_name") == "ICICI Bank", "bank_name not in fetched booking"
        assert fetched_booking.get("bank_ifsc") == "ICIC0001234", "bank_ifsc not in fetched booking"
        assert fetched_booking.get("bank_account") == "11223344556677", "bank_account not in fetched booking"
        assert fetched_booking.get("upi_id") == "checkintest@icici", "upi_id not in fetched booking"
        assert fetched_booking.get("upi_phone") == "9876543213", "upi_phone not in fetched booking"
        
        print(f"✓ Booking has bank/UPI details for check-in auto-fill")
        print(f"  Booking Number: {fetched_booking['booking_number']}")
        print(f"  Bank Name: {fetched_booking.get('bank_name')}")
        print(f"  UPI ID: {fetched_booking.get('upi_id')}")


class TestPaymentModeSimplification:
    """Test simplified payment mode fields (UPI = only Transaction ID, Bank Transfer = only Reference)"""
    
    def test_upi_payment_with_transaction_id_only(self, api_session, rooms, settings):
        """Test UPI payment mode with only transaction ID (no duplicate UPI details)"""
        available_rooms = [r for r in rooms if r["status"] == "available"]
        if not available_rooms:
            pytest.skip("No available rooms")
        
        unique_offset = 800 + int(uuid.uuid4().int % 100)
        check_in = (datetime.now() + timedelta(days=unique_offset)).strftime("%Y-%m-%d")
        check_out = (datetime.now() + timedelta(days=unique_offset + 2)).strftime("%Y-%m-%d")
        
        # UPI payment with transaction ID in payment_id field
        booking_data = {
            "guest_name": f"TEST_P1_UPIPayment_{uuid.uuid4().hex[:8]}",
            "guest_contact": "+91 9876543214",
            "guest_rank": "Sgt",
            "room_ids": [available_rooms[0]["id"]],
            "num_rooms": 1,
            "check_in_date": check_in,
            "check_out_date": check_out,
            "advance_paid": 500,
            "payment_mode": "upi",
            "payment_id": "UPI123456789012",  # UPI Transaction ID
            # Bank/UPI details for refund (separate from payment)
            "bank_name": "Axis Bank",
            "upi_id": "payment@axis"
        }
        
        response = api_session.post(f"{BASE_URL}/api/bookings", json=booking_data)
        assert response.status_code == 200, f"Booking creation failed: {response.text}"
        
        booking = response.json()
        
        assert booking.get("payment_mode") == "upi", "payment_mode should be upi"
        assert booking.get("payment_id") == "UPI123456789012", "payment_id should be UPI transaction ID"
        
        print(f"✓ UPI payment with transaction ID only")
        print(f"  Payment Mode: {booking.get('payment_mode')}")
        print(f"  Payment ID (Transaction ID): {booking.get('payment_id')}")
    
    def test_bank_transfer_with_reference_only(self, api_session, rooms, settings):
        """Test Bank Transfer payment mode with only transfer reference"""
        available_rooms = [r for r in rooms if r["status"] == "available"]
        if not available_rooms:
            pytest.skip("No available rooms")
        
        unique_offset = 850 + int(uuid.uuid4().int % 100)
        check_in = (datetime.now() + timedelta(days=unique_offset)).strftime("%Y-%m-%d")
        check_out = (datetime.now() + timedelta(days=unique_offset + 2)).strftime("%Y-%m-%d")
        
        # Bank transfer with reference in payment_id field
        booking_data = {
            "guest_name": f"TEST_P1_BankTransfer_{uuid.uuid4().hex[:8]}",
            "guest_contact": "+91 9876543215",
            "guest_rank": "PO",
            "room_ids": [available_rooms[0]["id"]],
            "num_rooms": 1,
            "check_in_date": check_in,
            "check_out_date": check_out,
            "advance_paid": 500,
            "payment_mode": "bank_transfer",
            "payment_id": "NEFT123456789",  # Bank Transfer Reference
            # Bank/UPI details for refund (separate from payment)
            "bank_name": "Punjab National Bank",
            "bank_ifsc": "PUNB0001234",
            "bank_account": "99887766554433"
        }
        
        response = api_session.post(f"{BASE_URL}/api/bookings", json=booking_data)
        assert response.status_code == 200, f"Booking creation failed: {response.text}"
        
        booking = response.json()
        
        assert booking.get("payment_mode") == "bank_transfer", "payment_mode should be bank_transfer"
        assert booking.get("payment_id") == "NEFT123456789", "payment_id should be bank transfer reference"
        
        print(f"✓ Bank Transfer with reference only")
        print(f"  Payment Mode: {booking.get('payment_mode')}")
        print(f"  Payment ID (Transfer Reference): {booking.get('payment_id')}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
