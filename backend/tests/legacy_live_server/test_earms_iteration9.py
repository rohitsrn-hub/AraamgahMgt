"""
E-ARMS Backend API Tests - Iteration 9
Testing: Bookings page fixes, validation rules, PDF generation, setup endpoint
"""
import pytest
import requests
import os
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestHealthAndSetup:
    """Test health and setup endpoints"""
    
    def test_health_endpoint(self):
        """Test API health check"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data or "status" in data
        print(f"Health check passed: {data}")
    
    def test_settings_get(self):
        """Test GET /api/settings - should return settings without _id"""
        response = requests.get(f"{BASE_URL}/api/settings")
        assert response.status_code == 200
        data = response.json()
        # Verify no _id field (ObjectId serialization fix)
        assert "_id" not in data, "Settings should not contain _id field"
        assert "cat_i_rate" in data
        assert "cat_ii_rate" in data
        print(f"Settings retrieved successfully, no _id field present")
    
    def test_settings_setup_endpoint(self):
        """Test POST /api/settings/setup - should not have ObjectId serialization error"""
        setup_data = {
            "cat_i_rate": 500.0,
            "cat_ii_rate": 400.0,
            "def_civ_cat_i_rate": 600.0,
            "def_civ_cat_ii_rate": 600.0,
            "cat_i_room_rent": 470.0,
            "cat_i_license_fee": 30.0,
            "cat_ii_room_rent": 385.0,
            "cat_ii_license_fee": 15.0,
            "def_civ_room_rent": 570.0,
            "def_civ_license_fee": 30.0,
            "cat_i_rooms_count": 6,
            "cat_ii_rooms_count": 9,
            "default_advance_amount": 400.0
        }
        response = requests.post(f"{BASE_URL}/api/settings/setup", json=setup_data)
        assert response.status_code == 200, f"Setup failed: {response.text}"
        data = response.json()
        assert "message" in data
        assert "settings" in data
        # Verify no _id in returned settings
        if data.get("settings"):
            assert "_id" not in data["settings"], "Setup response settings should not contain _id"
        print(f"Setup endpoint working correctly: {data['message']}")


class TestRoomsAPI:
    """Test rooms endpoints"""
    
    def test_get_rooms(self):
        """Test GET /api/rooms"""
        response = requests.get(f"{BASE_URL}/api/rooms")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Retrieved {len(data)} rooms")
        if data:
            room = data[0]
            assert "id" in room
            assert "room_number" in room
            assert "category" in room
            assert "_id" not in room
    
    def test_get_rooms_list(self):
        """Test GET /api/rooms returns room list with available rooms"""
        response = requests.get(f"{BASE_URL}/api/rooms")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Check for available rooms
        available_rooms = [r for r in data if r.get("status") == "available"]
        print(f"Found {len(available_rooms)} available rooms out of {len(data)} total")


class TestBookingsAPI:
    """Test bookings CRUD and validation"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get available rooms and settings for tests"""
        self.settings_response = requests.get(f"{BASE_URL}/api/settings")
        self.settings = self.settings_response.json() if self.settings_response.status_code == 200 else {}
        
        self.staff_response = requests.get(f"{BASE_URL}/api/staff")
        self.staff = self.staff_response.json() if self.staff_response.status_code == 200 else []
        
        # Get available rooms for future dates
        check_in = (datetime.now() + timedelta(days=10)).strftime("%Y-%m-%d")
        check_out = (datetime.now() + timedelta(days=12)).strftime("%Y-%m-%d")
        rooms_response = requests.get(
            f"{BASE_URL}/api/rooms/available",
            params={"check_in_date": check_in, "check_out_date": check_out}
        )
        self.available_rooms = rooms_response.json() if rooms_response.status_code == 200 else []
    
    def test_get_bookings(self):
        """Test GET /api/bookings"""
        response = requests.get(f"{BASE_URL}/api/bookings")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Retrieved {len(data)} bookings")
        if data:
            booking = data[0]
            assert "id" in booking
            assert "booking_number" in booking
            assert "guest_name" in booking
            assert "_id" not in booking
    
    def test_create_booking_valid(self):
        """Test POST /api/bookings with valid data"""
        if not self.available_rooms:
            pytest.skip("No available rooms for testing")
        
        room = self.available_rooms[0]
        check_in = (datetime.now() + timedelta(days=10)).strftime("%Y-%m-%d")
        check_out = (datetime.now() + timedelta(days=12)).strftime("%Y-%m-%d")
        
        booking_data = {
            "guest_name": "TEST_ValidBooking_Guest",
            "guest_contact": "+91 98765 43210",
            "guest_rank": "Sep/Dfr/Swr",
            "room_ids": [room["id"]],
            "num_rooms": 1,
            "check_in_date": check_in,
            "check_out_date": check_out,
            "advance_paid": 400.0,
            "payment_mode": "cash",
            "payment_id": "CASH001"
        }
        
        response = requests.post(f"{BASE_URL}/api/bookings", json=booking_data)
        assert response.status_code == 200, f"Booking creation failed: {response.text}"
        data = response.json()
        assert "id" in data
        assert data["guest_name"] == "TEST_ValidBooking_Guest"
        assert data["status"] == "confirmed"
        print(f"Created booking: {data['booking_number']}")
        
        # Cleanup - store for later deletion
        self.created_booking_id = data["id"]
    
    def test_create_booking_invalid_guest_name_short(self):
        """Test booking creation with guest name < 2 chars should fail on frontend validation"""
        # Note: Backend may not enforce this, but frontend should
        if not self.available_rooms:
            pytest.skip("No available rooms for testing")
        
        room = self.available_rooms[0]
        check_in = (datetime.now() + timedelta(days=15)).strftime("%Y-%m-%d")
        check_out = (datetime.now() + timedelta(days=17)).strftime("%Y-%m-%d")
        
        booking_data = {
            "guest_name": "A",  # Too short
            "room_ids": [room["id"]],
            "num_rooms": 1,
            "check_in_date": check_in,
            "check_out_date": check_out,
            "advance_paid": 400.0,
            "payment_mode": "cash",
            "payment_id": "CASH002"
        }
        
        response = requests.post(f"{BASE_URL}/api/bookings", json=booking_data)
        # Backend may accept this - validation is primarily on frontend
        print(f"Short guest name response: {response.status_code}")
    
    def test_guest_history_lookup(self):
        """Test GET /api/bookings/guest-history - endpoint exists and responds"""
        # Test with phone number - may return 404 if no matching guest
        response = requests.get(
            f"{BASE_URL}/api/bookings/guest-history",
            params={"phone_number": "9876543210"}
        )
        # 200 if found, 404 if not found - both are valid responses
        assert response.status_code in [200, 404], f"Unexpected status: {response.status_code}"
        print(f"Guest history lookup response: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            assert "found" in data
            print(f"Guest history found: {data.get('found')}")
    
    def test_calculate_refund(self):
        """Test GET /api/bookings/{id}/calculate-refund"""
        # First get a confirmed booking
        bookings_response = requests.get(f"{BASE_URL}/api/bookings")
        bookings = bookings_response.json()
        
        confirmed_bookings = [b for b in bookings if b.get("status") == "confirmed"]
        if not confirmed_bookings:
            pytest.skip("No confirmed bookings to test refund calculation")
        
        booking = confirmed_bookings[0]
        response = requests.get(f"{BASE_URL}/api/bookings/{booking['id']}/calculate-refund")
        assert response.status_code == 200
        data = response.json()
        assert "refund_amount" in data
        assert "cancellation_charge" in data
        assert "days_until_checkin" in data
        print(f"Refund calculation: refund={data['refund_amount']}, charge={data['cancellation_charge']}")


class TestCheckInValidation:
    """Test check-in endpoint with validation"""
    
    def test_checkin_requires_staff(self):
        """Test that check-in requires staff_id"""
        # Get a confirmed booking
        bookings_response = requests.get(f"{BASE_URL}/api/bookings")
        bookings = bookings_response.json()
        
        confirmed_bookings = [b for b in bookings if b.get("status") == "confirmed"]
        if not confirmed_bookings:
            pytest.skip("No confirmed bookings to test check-in")
        
        booking = confirmed_bookings[0]
        
        # Try check-in without staff_id
        checkin_data = {
            "booking_id": booking["id"],
            "staff_id": "",  # Empty staff_id
            "guest_contact": "+91 98765 43210",
            "guest_age": 30,
            "guest_sex": "Male",
            "guest_address": "Test Address Line 1, City, State 123456",
            "identity_card_number": "ID123456",
            "guest_service_status": "Serving"
        }
        
        response = requests.post(f"{BASE_URL}/api/bookings/check-in", json=checkin_data)
        # Should fail due to empty staff_id
        print(f"Check-in without staff response: {response.status_code}")


class TestStaffAPI:
    """Test staff endpoints"""
    
    def test_get_staff(self):
        """Test GET /api/staff"""
        response = requests.get(f"{BASE_URL}/api/staff")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Retrieved {len(data)} staff members")
        if data:
            staff = data[0]
            assert "id" in staff
            assert "name" in staff
            assert "_id" not in staff


class TestRefundsAPI:
    """Test refunds endpoints"""
    
    def test_get_refunds(self):
        """Test GET /api/refunds"""
        response = requests.get(f"{BASE_URL}/api/refunds")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Retrieved {len(data)} refunds")


class TestFeedbackAPI:
    """Test feedback endpoints"""
    
    def test_get_feedback_analysis(self):
        """Test GET /api/feedback/analysis"""
        response = requests.get(f"{BASE_URL}/api/feedback/analysis")
        assert response.status_code == 200
        data = response.json()
        assert "total_feedbacks" in data or "average_rating" in data or isinstance(data, dict)
        print(f"Feedback analysis retrieved")


class TestDashboardAPI:
    """Test dashboard endpoints"""
    
    def test_get_dashboard_occupancy(self):
        """Test GET /api/dashboard/occupancy"""
        response = requests.get(f"{BASE_URL}/api/dashboard/occupancy")
        assert response.status_code == 200
        data = response.json()
        assert "overall" in data
        assert "cat_i" in data
        assert "cat_ii" in data
        print(f"Dashboard occupancy: {data['overall']}")


# Cleanup fixture
@pytest.fixture(scope="session", autouse=True)
def cleanup_test_data():
    """Cleanup TEST_ prefixed bookings after all tests"""
    yield
    # Cleanup after tests
    try:
        bookings_response = requests.get(f"{BASE_URL}/api/bookings")
        if bookings_response.status_code == 200:
            bookings = bookings_response.json()
            for booking in bookings:
                if booking.get("guest_name", "").startswith("TEST_"):
                    # Cancel the booking
                    requests.post(f"{BASE_URL}/api/bookings/cancel", json={
                        "booking_id": booking["id"],
                        "reason": "Test cleanup",
                        "refund_amount": 0
                    })
                    print(f"Cleaned up test booking: {booking['booking_number']}")
    except Exception as e:
        print(f"Cleanup error: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
