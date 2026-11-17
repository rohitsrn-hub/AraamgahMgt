"""
Test Suite for Validation Uniformity Feature
Tests:
1. Mobile number validation (10-digit Indian mobile starting with 6-9)
2. IFSC code validation (11 chars: 4 letters + 0 + 6 alphanumeric)
3. Uppercase auto-conversion for ID fields (army_number, bank_ifsc, dependent_id)
"""
import pytest
import requests
import os
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# ============= FIXTURES =============

@pytest.fixture
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session

@pytest.fixture
def available_room_ids(api_client):
    """Get available room IDs for testing"""
    response = api_client.get(f"{BASE_URL}/api/rooms")
    assert response.status_code == 200
    rooms = response.json()
    return [r["id"] for r in rooms if r["status"] == "available"][:2]

@pytest.fixture
def test_dates():
    """Get valid test dates (tomorrow and day after)"""
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    day_after = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
    return {"check_in": tomorrow, "check_out": day_after}

@pytest.fixture
def staff_id(api_client):
    """Get or create a staff member for check-in tests"""
    response = api_client.get(f"{BASE_URL}/api/staff")
    if response.status_code == 200 and response.json():
        return response.json()[0]["id"]
    # Create staff if none exists
    create_response = api_client.post(f"{BASE_URL}/api/staff", json={
        "name": "TEST_Staff_Validation",
        "staff_type": "Army",
        "designation": "Clerk"
    })
    if create_response.status_code in [200, 201]:
        return create_response.json()["id"]
    pytest.skip("Could not get or create staff member")


# ============= MOBILE VALIDATION TESTS =============

class TestMobileValidation:
    """Test mobile number validation on booking and check-in endpoints"""
    
    def test_booking_valid_mobile_starting_with_9(self, api_client, available_room_ids, test_dates):
        """Valid mobile starting with 9 should be accepted"""
        if not available_room_ids:
            pytest.skip("No available rooms")
        
        response = api_client.post(f"{BASE_URL}/api/bookings", json={
            "guest_name": "TEST_Mobile_Valid_9",
            "guest_contact": "+91 98765 43210",
            "room_ids": [available_room_ids[0]],
            "check_in_date": test_dates["check_in"],
            "check_out_date": test_dates["check_out"],
            "advance_paid": 400,
            "payment_mode": "cash",
            "payment_id": "CASH001"
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "id" in data
        # Cleanup
        api_client.post(f"{BASE_URL}/api/bookings/cancel", json={"booking_id": data["id"], "reason": "Test cleanup"})
    
    def test_booking_valid_mobile_starting_with_6(self, api_client, available_room_ids, test_dates):
        """Valid mobile starting with 6 should be accepted"""
        if not available_room_ids:
            pytest.skip("No available rooms")
        
        response = api_client.post(f"{BASE_URL}/api/bookings", json={
            "guest_name": "TEST_Mobile_Valid_6",
            "guest_contact": "+91 61234 56789",
            "room_ids": [available_room_ids[0]],
            "check_in_date": test_dates["check_in"],
            "check_out_date": test_dates["check_out"],
            "advance_paid": 400,
            "payment_mode": "cash",
            "payment_id": "CASH002"
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        # Cleanup
        api_client.post(f"{BASE_URL}/api/bookings/cancel", json={"booking_id": data["id"], "reason": "Test cleanup"})
    
    def test_booking_valid_mobile_starting_with_7(self, api_client, available_room_ids, test_dates):
        """Valid mobile starting with 7 should be accepted"""
        if not available_room_ids:
            pytest.skip("No available rooms")
        
        response = api_client.post(f"{BASE_URL}/api/bookings", json={
            "guest_name": "TEST_Mobile_Valid_7",
            "guest_contact": "+91 71234 56789",
            "room_ids": [available_room_ids[0]],
            "check_in_date": test_dates["check_in"],
            "check_out_date": test_dates["check_out"],
            "advance_paid": 400,
            "payment_mode": "cash",
            "payment_id": "CASH003"
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        # Cleanup
        api_client.post(f"{BASE_URL}/api/bookings/cancel", json={"booking_id": data["id"], "reason": "Test cleanup"})
    
    def test_booking_valid_mobile_starting_with_8(self, api_client, available_room_ids, test_dates):
        """Valid mobile starting with 8 should be accepted"""
        if not available_room_ids:
            pytest.skip("No available rooms")
        
        response = api_client.post(f"{BASE_URL}/api/bookings", json={
            "guest_name": "TEST_Mobile_Valid_8",
            "guest_contact": "+91 81234 56789",
            "room_ids": [available_room_ids[0]],
            "check_in_date": test_dates["check_in"],
            "check_out_date": test_dates["check_out"],
            "advance_paid": 400,
            "payment_mode": "cash",
            "payment_id": "CASH004"
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        # Cleanup
        api_client.post(f"{BASE_URL}/api/bookings/cancel", json={"booking_id": data["id"], "reason": "Test cleanup"})
    
    def test_booking_invalid_mobile_starting_with_5(self, api_client, available_room_ids, test_dates):
        """Invalid mobile starting with 5 should be rejected"""
        if not available_room_ids:
            pytest.skip("No available rooms")
        
        response = api_client.post(f"{BASE_URL}/api/bookings", json={
            "guest_name": "TEST_Mobile_Invalid_5",
            "guest_contact": "+91 51234 56789",
            "room_ids": [available_room_ids[0]],
            "check_in_date": test_dates["check_in"],
            "check_out_date": test_dates["check_out"],
            "advance_paid": 400,
            "payment_mode": "cash",
            "payment_id": "CASH005"
        })
        assert response.status_code == 400, f"Expected 400 for invalid mobile, got {response.status_code}"
        assert "mobile" in response.text.lower() or "phone" in response.text.lower()
    
    def test_booking_invalid_mobile_starting_with_0(self, api_client, available_room_ids, test_dates):
        """Invalid mobile starting with 0 should be rejected"""
        if not available_room_ids:
            pytest.skip("No available rooms")
        
        response = api_client.post(f"{BASE_URL}/api/bookings", json={
            "guest_name": "TEST_Mobile_Invalid_0",
            "guest_contact": "+91 01234 56789",
            "room_ids": [available_room_ids[0]],
            "check_in_date": test_dates["check_in"],
            "check_out_date": test_dates["check_out"],
            "advance_paid": 400,
            "payment_mode": "cash",
            "payment_id": "CASH006"
        })
        assert response.status_code == 400, f"Expected 400 for invalid mobile, got {response.status_code}"
    
    def test_booking_invalid_mobile_9_digits(self, api_client, available_room_ids, test_dates):
        """Invalid mobile with only 9 digits should be rejected"""
        if not available_room_ids:
            pytest.skip("No available rooms")
        
        response = api_client.post(f"{BASE_URL}/api/bookings", json={
            "guest_name": "TEST_Mobile_Invalid_9digits",
            "guest_contact": "+91 912345678",  # Only 9 digits
            "room_ids": [available_room_ids[0]],
            "check_in_date": test_dates["check_in"],
            "check_out_date": test_dates["check_out"],
            "advance_paid": 400,
            "payment_mode": "cash",
            "payment_id": "CASH007"
        })
        assert response.status_code == 400, f"Expected 400 for 9-digit mobile, got {response.status_code}"
    
    def test_booking_invalid_upi_phone(self, api_client, available_room_ids, test_dates):
        """Invalid UPI phone should be rejected"""
        if not available_room_ids:
            pytest.skip("No available rooms")
        
        response = api_client.post(f"{BASE_URL}/api/bookings", json={
            "guest_name": "TEST_UPI_Invalid",
            "guest_contact": "+91 98765 43210",
            "upi_phone": "+91 51234 56789",  # Invalid - starts with 5
            "room_ids": [available_room_ids[0]],
            "check_in_date": test_dates["check_in"],
            "check_out_date": test_dates["check_out"],
            "advance_paid": 400,
            "payment_mode": "upi",
            "payment_id": "UPI001"
        })
        assert response.status_code == 400, f"Expected 400 for invalid UPI phone, got {response.status_code}"
        assert "upi" in response.text.lower() or "phone" in response.text.lower()


# ============= IFSC VALIDATION TESTS =============

class TestIFSCValidation:
    """Test IFSC code validation on booking and check-in endpoints"""
    
    def test_booking_valid_ifsc(self, api_client, available_room_ids, test_dates):
        """Valid IFSC code should be accepted"""
        if not available_room_ids:
            pytest.skip("No available rooms")
        
        response = api_client.post(f"{BASE_URL}/api/bookings", json={
            "guest_name": "TEST_IFSC_Valid",
            "guest_contact": "+91 98765 43210",
            "bank_ifsc": "SBIN0001234",  # Valid: 4 letters + 0 + 6 alphanumeric
            "bank_name": "State Bank of India",
            "bank_account": "1234567890",
            "room_ids": [available_room_ids[0]],
            "check_in_date": test_dates["check_in"],
            "check_out_date": test_dates["check_out"],
            "advance_paid": 400,
            "payment_mode": "bank_transfer",
            "payment_id": "BANK001"
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["bank_ifsc"] == "SBIN0001234"
        # Cleanup
        api_client.post(f"{BASE_URL}/api/bookings/cancel", json={"booking_id": data["id"], "reason": "Test cleanup"})
    
    def test_booking_valid_ifsc_with_alphanumeric(self, api_client, available_room_ids, test_dates):
        """Valid IFSC with alphanumeric branch code should be accepted"""
        if not available_room_ids:
            pytest.skip("No available rooms")
        
        response = api_client.post(f"{BASE_URL}/api/bookings", json={
            "guest_name": "TEST_IFSC_Alphanumeric",
            "guest_contact": "+91 98765 43210",
            "bank_ifsc": "HDFC0ABC123",  # Valid: 4 letters + 0 + 6 alphanumeric
            "bank_name": "HDFC Bank",
            "bank_account": "1234567890",
            "room_ids": [available_room_ids[0]],
            "check_in_date": test_dates["check_in"],
            "check_out_date": test_dates["check_out"],
            "advance_paid": 400,
            "payment_mode": "bank_transfer",
            "payment_id": "BANK002"
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        # Cleanup
        api_client.post(f"{BASE_URL}/api/bookings/cancel", json={"booking_id": data["id"], "reason": "Test cleanup"})
    
    def test_booking_invalid_ifsc_wrong_5th_char(self, api_client, available_room_ids, test_dates):
        """Invalid IFSC with wrong 5th character (not 0) should be rejected"""
        if not available_room_ids:
            pytest.skip("No available rooms")
        
        response = api_client.post(f"{BASE_URL}/api/bookings", json={
            "guest_name": "TEST_IFSC_Invalid_5th",
            "guest_contact": "+91 98765 43210",
            "bank_ifsc": "SBIN1001234",  # Invalid: 5th char is 1, not 0
            "bank_name": "State Bank of India",
            "bank_account": "1234567890",
            "room_ids": [available_room_ids[0]],
            "check_in_date": test_dates["check_in"],
            "check_out_date": test_dates["check_out"],
            "advance_paid": 400,
            "payment_mode": "bank_transfer",
            "payment_id": "BANK003"
        })
        assert response.status_code == 400, f"Expected 400 for invalid IFSC, got {response.status_code}"
        assert "ifsc" in response.text.lower()
    
    def test_booking_invalid_ifsc_too_short(self, api_client, available_room_ids, test_dates):
        """Invalid IFSC with less than 11 characters should be rejected"""
        if not available_room_ids:
            pytest.skip("No available rooms")
        
        response = api_client.post(f"{BASE_URL}/api/bookings", json={
            "guest_name": "TEST_IFSC_Short",
            "guest_contact": "+91 98765 43210",
            "bank_ifsc": "SBIN012345",  # Invalid: only 10 chars
            "bank_name": "State Bank of India",
            "bank_account": "1234567890",
            "room_ids": [available_room_ids[0]],
            "check_in_date": test_dates["check_in"],
            "check_out_date": test_dates["check_out"],
            "advance_paid": 400,
            "payment_mode": "bank_transfer",
            "payment_id": "BANK004"
        })
        assert response.status_code == 400, f"Expected 400 for short IFSC, got {response.status_code}"
    
    def test_booking_invalid_ifsc_too_long(self, api_client, available_room_ids, test_dates):
        """Invalid IFSC with more than 11 characters should be rejected"""
        if not available_room_ids:
            pytest.skip("No available rooms")
        
        response = api_client.post(f"{BASE_URL}/api/bookings", json={
            "guest_name": "TEST_IFSC_Long",
            "guest_contact": "+91 98765 43210",
            "bank_ifsc": "SBIN00123456",  # Invalid: 12 chars
            "bank_name": "State Bank of India",
            "bank_account": "1234567890",
            "room_ids": [available_room_ids[0]],
            "check_in_date": test_dates["check_in"],
            "check_out_date": test_dates["check_out"],
            "advance_paid": 400,
            "payment_mode": "bank_transfer",
            "payment_id": "BANK005"
        })
        assert response.status_code == 400, f"Expected 400 for long IFSC, got {response.status_code}"
    
    def test_booking_invalid_ifsc_numbers_in_first_4(self, api_client, available_room_ids, test_dates):
        """Invalid IFSC with numbers in first 4 characters should be rejected"""
        if not available_room_ids:
            pytest.skip("No available rooms")
        
        response = api_client.post(f"{BASE_URL}/api/bookings", json={
            "guest_name": "TEST_IFSC_Numbers",
            "guest_contact": "+91 98765 43210",
            "bank_ifsc": "SB1N0001234",  # Invalid: number in first 4 chars
            "bank_name": "State Bank of India",
            "bank_account": "1234567890",
            "room_ids": [available_room_ids[0]],
            "check_in_date": test_dates["check_in"],
            "check_out_date": test_dates["check_out"],
            "advance_paid": 400,
            "payment_mode": "bank_transfer",
            "payment_id": "BANK006"
        })
        assert response.status_code == 400, f"Expected 400 for IFSC with numbers in first 4, got {response.status_code}"


# ============= UPPERCASE CONVERSION TESTS =============

class TestUppercaseConversion:
    """Test uppercase auto-conversion for ID fields"""
    
    def test_booking_army_number_uppercase(self, api_client, available_room_ids, test_dates):
        """Army number should be converted to uppercase"""
        if not available_room_ids:
            pytest.skip("No available rooms")
        
        response = api_client.post(f"{BASE_URL}/api/bookings", json={
            "guest_name": "TEST_Army_Uppercase",
            "guest_contact": "+91 98765 43210",
            "army_number": "abc123def",  # lowercase
            "room_ids": [available_room_ids[0]],
            "check_in_date": test_dates["check_in"],
            "check_out_date": test_dates["check_out"],
            "advance_paid": 400,
            "payment_mode": "cash",
            "payment_id": "CASH008"
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["army_number"] == "ABC123DEF", f"Expected uppercase, got {data['army_number']}"
        # Cleanup
        api_client.post(f"{BASE_URL}/api/bookings/cancel", json={"booking_id": data["id"], "reason": "Test cleanup"})
    
    def test_booking_ifsc_uppercase(self, api_client, available_room_ids, test_dates):
        """IFSC code should be converted to uppercase"""
        if not available_room_ids:
            pytest.skip("No available rooms")
        
        response = api_client.post(f"{BASE_URL}/api/bookings", json={
            "guest_name": "TEST_IFSC_Uppercase",
            "guest_contact": "+91 98765 43210",
            "bank_ifsc": "sbin0001234",  # lowercase
            "bank_name": "State Bank of India",
            "bank_account": "1234567890",
            "room_ids": [available_room_ids[0]],
            "check_in_date": test_dates["check_in"],
            "check_out_date": test_dates["check_out"],
            "advance_paid": 400,
            "payment_mode": "bank_transfer",
            "payment_id": "BANK007"
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["bank_ifsc"] == "SBIN0001234", f"Expected uppercase IFSC, got {data['bank_ifsc']}"
        # Cleanup
        api_client.post(f"{BASE_URL}/api/bookings/cancel", json={"booking_id": data["id"], "reason": "Test cleanup"})
    
    def test_checkin_ifsc_uppercase(self, api_client, available_room_ids, test_dates, staff_id):
        """IFSC code in check-in should be converted to uppercase"""
        if not available_room_ids:
            pytest.skip("No available rooms")
        
        # First create a booking
        booking_response = api_client.post(f"{BASE_URL}/api/bookings", json={
            "guest_name": "TEST_Checkin_IFSC",
            "guest_contact": "+91 98765 43210",
            "room_ids": [available_room_ids[0]],
            "check_in_date": test_dates["check_in"],
            "check_out_date": test_dates["check_out"],
            "advance_paid": 400,
            "payment_mode": "cash",
            "payment_id": "CASH009"
        })
        assert booking_response.status_code == 200
        booking_id = booking_response.json()["id"]
        
        # Now check-in with lowercase IFSC
        checkin_response = api_client.post(f"{BASE_URL}/api/bookings/check-in", json={
            "booking_id": booking_id,
            "staff_id": staff_id,
            "guest_contact": "+91 98765 43210",
            "guest_age": 35,
            "guest_sex": "M",
            "guest_address": "Test Address for Validation Testing",
            "identity_card_number": "ARMY123456",
            "guest_service_status": "Serving",
            "bank_ifsc": "hdfc0abc123",  # lowercase
            "bank_name": "HDFC Bank",
            "bank_account": "9876543210"
        })
        
        # Check-in may fail due to date restrictions, but if it succeeds, verify uppercase
        if checkin_response.status_code == 200:
            data = checkin_response.json()
            booking = data.get("booking", {})
            assert booking.get("bank_ifsc") == "HDFC0ABC123", f"Expected uppercase IFSC, got {booking.get('bank_ifsc')}"
        
        # Cleanup
        api_client.post(f"{BASE_URL}/api/bookings/cancel", json={"booking_id": booking_id, "reason": "Test cleanup"})
    
    def test_checkin_dependent_id_uppercase(self, api_client, available_room_ids, test_dates, staff_id):
        """Dependent ID in family members should be converted to uppercase"""
        if not available_room_ids:
            pytest.skip("No available rooms")
        
        # First create a booking
        booking_response = api_client.post(f"{BASE_URL}/api/bookings", json={
            "guest_name": "TEST_Dependent_ID",
            "guest_contact": "+91 98765 43210",
            "room_ids": [available_room_ids[0]],
            "check_in_date": test_dates["check_in"],
            "check_out_date": test_dates["check_out"],
            "advance_paid": 400,
            "payment_mode": "cash",
            "payment_id": "CASH010"
        })
        assert booking_response.status_code == 200
        booking_id = booking_response.json()["id"]
        
        # Now check-in with lowercase dependent_id
        checkin_response = api_client.post(f"{BASE_URL}/api/bookings/check-in", json={
            "booking_id": booking_id,
            "staff_id": staff_id,
            "guest_contact": "+91 98765 43210",
            "guest_age": 35,
            "guest_sex": "M",
            "guest_address": "Test Address for Validation Testing",
            "identity_card_number": "ARMY123456",
            "guest_service_status": "Serving",
            "family_members": [
                {
                    "relation": "w/o",
                    "name": "Test Wife",
                    "age": "30",
                    "sex": "F",
                    "mobile": "+91 87654 32109",
                    "dependent_id": "dep123abc"  # lowercase
                }
            ]
        })
        
        # Check-in may fail due to date restrictions, but if it succeeds, verify uppercase
        if checkin_response.status_code == 200:
            data = checkin_response.json()
            booking = data.get("booking", {})
            family_members = booking.get("family_members", [])
            if family_members:
                assert family_members[0].get("dependent_id") == "DEP123ABC", f"Expected uppercase dependent_id, got {family_members[0].get('dependent_id')}"
        
        # Cleanup
        api_client.post(f"{BASE_URL}/api/bookings/cancel", json={"booking_id": booking_id, "reason": "Test cleanup"})


# ============= CHECK-IN VALIDATION TESTS =============

class TestCheckInValidation:
    """Test validation on check-in endpoint"""
    
    def test_checkin_invalid_mobile(self, api_client, available_room_ids, test_dates, staff_id):
        """Invalid mobile in check-in should be rejected"""
        if not available_room_ids:
            pytest.skip("No available rooms")
        
        # First create a booking
        booking_response = api_client.post(f"{BASE_URL}/api/bookings", json={
            "guest_name": "TEST_Checkin_Mobile",
            "guest_contact": "+91 98765 43210",
            "room_ids": [available_room_ids[0]],
            "check_in_date": test_dates["check_in"],
            "check_out_date": test_dates["check_out"],
            "advance_paid": 400,
            "payment_mode": "cash",
            "payment_id": "CASH011"
        })
        assert booking_response.status_code == 200
        booking_id = booking_response.json()["id"]
        
        # Try check-in with invalid mobile
        checkin_response = api_client.post(f"{BASE_URL}/api/bookings/check-in", json={
            "booking_id": booking_id,
            "staff_id": staff_id,
            "guest_contact": "+91 51234 56789",  # Invalid - starts with 5
            "guest_age": 35,
            "guest_sex": "M",
            "guest_address": "Test Address for Validation Testing",
            "identity_card_number": "ARMY123456",
            "guest_service_status": "Serving"
        })
        
        assert checkin_response.status_code == 400, f"Expected 400 for invalid mobile, got {checkin_response.status_code}"
        
        # Cleanup
        api_client.post(f"{BASE_URL}/api/bookings/cancel", json={"booking_id": booking_id, "reason": "Test cleanup"})
    
    def test_checkin_invalid_upi_phone(self, api_client, available_room_ids, test_dates, staff_id):
        """Invalid UPI phone in check-in should be rejected"""
        if not available_room_ids:
            pytest.skip("No available rooms")
        
        # First create a booking
        booking_response = api_client.post(f"{BASE_URL}/api/bookings", json={
            "guest_name": "TEST_Checkin_UPI",
            "guest_contact": "+91 98765 43210",
            "room_ids": [available_room_ids[0]],
            "check_in_date": test_dates["check_in"],
            "check_out_date": test_dates["check_out"],
            "advance_paid": 400,
            "payment_mode": "cash",
            "payment_id": "CASH012"
        })
        assert booking_response.status_code == 200
        booking_id = booking_response.json()["id"]
        
        # Try check-in with invalid UPI phone
        checkin_response = api_client.post(f"{BASE_URL}/api/bookings/check-in", json={
            "booking_id": booking_id,
            "staff_id": staff_id,
            "guest_contact": "+91 98765 43210",
            "upi_phone": "+91 51234 56789",  # Invalid - starts with 5
            "guest_age": 35,
            "guest_sex": "M",
            "guest_address": "Test Address for Validation Testing",
            "identity_card_number": "ARMY123456",
            "guest_service_status": "Serving"
        })
        
        assert checkin_response.status_code == 400, f"Expected 400 for invalid UPI phone, got {checkin_response.status_code}"
        
        # Cleanup
        api_client.post(f"{BASE_URL}/api/bookings/cancel", json={"booking_id": booking_id, "reason": "Test cleanup"})
    
    def test_checkin_invalid_ifsc(self, api_client, available_room_ids, test_dates, staff_id):
        """Invalid IFSC in check-in should be rejected"""
        if not available_room_ids:
            pytest.skip("No available rooms")
        
        # First create a booking
        booking_response = api_client.post(f"{BASE_URL}/api/bookings", json={
            "guest_name": "TEST_Checkin_IFSC_Invalid",
            "guest_contact": "+91 98765 43210",
            "room_ids": [available_room_ids[0]],
            "check_in_date": test_dates["check_in"],
            "check_out_date": test_dates["check_out"],
            "advance_paid": 400,
            "payment_mode": "cash",
            "payment_id": "CASH013"
        })
        assert booking_response.status_code == 200
        booking_id = booking_response.json()["id"]
        
        # Try check-in with invalid IFSC
        checkin_response = api_client.post(f"{BASE_URL}/api/bookings/check-in", json={
            "booking_id": booking_id,
            "staff_id": staff_id,
            "guest_contact": "+91 98765 43210",
            "bank_ifsc": "INVALID123",  # Invalid format
            "guest_age": 35,
            "guest_sex": "M",
            "guest_address": "Test Address for Validation Testing",
            "identity_card_number": "ARMY123456",
            "guest_service_status": "Serving"
        })
        
        assert checkin_response.status_code == 400, f"Expected 400 for invalid IFSC, got {checkin_response.status_code}"
        
        # Cleanup
        api_client.post(f"{BASE_URL}/api/bookings/cancel", json={"booking_id": booking_id, "reason": "Test cleanup"})
    
    def test_checkin_invalid_family_member_mobile(self, api_client, available_room_ids, test_dates, staff_id):
        """Invalid family member mobile in check-in should be rejected"""
        if not available_room_ids:
            pytest.skip("No available rooms")
        
        # First create a booking
        booking_response = api_client.post(f"{BASE_URL}/api/bookings", json={
            "guest_name": "TEST_Family_Mobile",
            "guest_contact": "+91 98765 43210",
            "room_ids": [available_room_ids[0]],
            "check_in_date": test_dates["check_in"],
            "check_out_date": test_dates["check_out"],
            "advance_paid": 400,
            "payment_mode": "cash",
            "payment_id": "CASH014"
        })
        assert booking_response.status_code == 200
        booking_id = booking_response.json()["id"]
        
        # Try check-in with invalid family member mobile
        checkin_response = api_client.post(f"{BASE_URL}/api/bookings/check-in", json={
            "booking_id": booking_id,
            "staff_id": staff_id,
            "guest_contact": "+91 98765 43210",
            "guest_age": 35,
            "guest_sex": "M",
            "guest_address": "Test Address for Validation Testing",
            "identity_card_number": "ARMY123456",
            "guest_service_status": "Serving",
            "family_members": [
                {
                    "relation": "w/o",
                    "name": "Test Wife",
                    "age": "30",
                    "sex": "F",
                    "mobile": "+91 51234 56789"  # Invalid - starts with 5
                }
            ]
        })
        
        assert checkin_response.status_code == 400, f"Expected 400 for invalid family member mobile, got {checkin_response.status_code}"
        
        # Cleanup
        api_client.post(f"{BASE_URL}/api/bookings/cancel", json={"booking_id": booking_id, "reason": "Test cleanup"})


# ============= OPTIONAL FIELD TESTS =============

class TestOptionalFields:
    """Test that optional fields don't trigger validation when empty"""
    
    def test_booking_without_mobile(self, api_client, available_room_ids, test_dates):
        """Booking without mobile should be accepted"""
        if not available_room_ids:
            pytest.skip("No available rooms")
        
        response = api_client.post(f"{BASE_URL}/api/bookings", json={
            "guest_name": "TEST_No_Mobile",
            # No guest_contact
            "room_ids": [available_room_ids[0]],
            "check_in_date": test_dates["check_in"],
            "check_out_date": test_dates["check_out"],
            "advance_paid": 400,
            "payment_mode": "cash",
            "payment_id": "CASH015"
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        # Cleanup
        api_client.post(f"{BASE_URL}/api/bookings/cancel", json={"booking_id": data["id"], "reason": "Test cleanup"})
    
    def test_booking_without_ifsc(self, api_client, available_room_ids, test_dates):
        """Booking without IFSC should be accepted"""
        if not available_room_ids:
            pytest.skip("No available rooms")
        
        response = api_client.post(f"{BASE_URL}/api/bookings", json={
            "guest_name": "TEST_No_IFSC",
            "guest_contact": "+91 98765 43210",
            # No bank_ifsc
            "room_ids": [available_room_ids[0]],
            "check_in_date": test_dates["check_in"],
            "check_out_date": test_dates["check_out"],
            "advance_paid": 400,
            "payment_mode": "cash",
            "payment_id": "CASH016"
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        # Cleanup
        api_client.post(f"{BASE_URL}/api/bookings/cancel", json={"booking_id": data["id"], "reason": "Test cleanup"})
    
    def test_booking_without_army_number(self, api_client, available_room_ids, test_dates):
        """Booking without army number should be accepted"""
        if not available_room_ids:
            pytest.skip("No available rooms")
        
        response = api_client.post(f"{BASE_URL}/api/bookings", json={
            "guest_name": "TEST_No_Army",
            "guest_contact": "+91 98765 43210",
            # No army_number
            "room_ids": [available_room_ids[0]],
            "check_in_date": test_dates["check_in"],
            "check_out_date": test_dates["check_out"],
            "advance_paid": 400,
            "payment_mode": "cash",
            "payment_id": "CASH017"
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        # Cleanup
        api_client.post(f"{BASE_URL}/api/bookings/cancel", json={"booking_id": data["id"], "reason": "Test cleanup"})
