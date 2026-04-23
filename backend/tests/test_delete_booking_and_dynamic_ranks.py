"""
Test Suite for Hard Delete Booking and Dynamic Rank Dropdown Features
=====================================================================
Tests:
1. DELETE /api/bookings/{booking_id} - Permanently removes booking and frees rooms
2. Dynamic Rank Dropdown - Adding new rank in Settings makes it appear in New Booking form
"""

import pytest
import requests
import os
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestDeleteBookingAPI:
    """Test DELETE /api/bookings/{booking_id} endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test data"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
    def create_test_booking(self, prefix="TEST_DELETE"):
        """Helper to create a test booking"""
        # Get available rooms
        check_in = (datetime.now() + timedelta(days=10)).strftime("%Y-%m-%d")
        check_out = (datetime.now() + timedelta(days=12)).strftime("%Y-%m-%d")
        
        rooms_response = self.session.get(f"{BASE_URL}/api/rooms/available", params={
            "check_in": check_in,
            "check_out": check_out
        })
        
        if rooms_response.status_code != 200 or not rooms_response.json():
            pytest.skip("No available rooms for testing")
            
        available_rooms = rooms_response.json()
        room_id = available_rooms[0]["id"]
        
        # Create booking
        booking_data = {
            "guest_name": f"{prefix}_Guest",
            "guest_contact": "9876543210",
            "guest_rank": "Hav",
            "room_ids": [room_id],
            "num_rooms": 1,
            "check_in_date": check_in,
            "check_out_date": check_out,
            "advance_paid": 400,
            "payment_mode": "cash",
            "payment_id": "TEST123"
        }
        
        response = self.session.post(f"{BASE_URL}/api/bookings", json=booking_data)
        assert response.status_code == 200, f"Failed to create test booking: {response.text}"
        return response.json()
    
    def test_delete_booking_success(self):
        """Test successful deletion of a booking"""
        # Create a test booking
        booking = self.create_test_booking("TEST_DELETE_SUCCESS")
        booking_id = booking["id"]
        booking_number = booking["booking_number"]
        
        # Verify booking exists
        get_response = self.session.get(f"{BASE_URL}/api/bookings/{booking_id}")
        assert get_response.status_code == 200, "Booking should exist before deletion"
        
        # Delete the booking
        delete_response = self.session.delete(f"{BASE_URL}/api/bookings/{booking_id}")
        assert delete_response.status_code == 200, f"Delete failed: {delete_response.text}"
        
        # Verify response contains expected fields
        delete_data = delete_response.json()
        assert delete_data["message"] == "Booking permanently deleted"
        assert delete_data["booking_id"] == booking_id
        assert delete_data["booking_number"] == booking_number
        
        # Verify booking no longer exists
        get_after_delete = self.session.get(f"{BASE_URL}/api/bookings/{booking_id}")
        assert get_after_delete.status_code == 404, "Booking should not exist after deletion"
        
        print(f"✓ Successfully deleted booking {booking_number}")
    
    def test_delete_booking_frees_rooms(self):
        """Test that deleting a confirmed booking frees up the rooms"""
        # Create a test booking
        booking = self.create_test_booking("TEST_DELETE_ROOMS")
        booking_id = booking["id"]
        room_ids = booking["room_ids"]
        check_in = booking["check_in_date"]
        check_out = booking["check_out_date"]
        
        # Verify rooms are NOT available for same dates (booked)
        rooms_before = self.session.get(f"{BASE_URL}/api/rooms/available", params={
            "check_in": check_in,
            "check_out": check_out
        }).json()
        
        booked_room_ids_before = [r["id"] for r in rooms_before]
        for room_id in room_ids:
            assert room_id not in booked_room_ids_before, "Room should be booked before deletion"
        
        # Delete the booking
        delete_response = self.session.delete(f"{BASE_URL}/api/bookings/{booking_id}")
        assert delete_response.status_code == 200
        
        # Verify rooms ARE now available for same dates
        rooms_after = self.session.get(f"{BASE_URL}/api/rooms/available", params={
            "check_in": check_in,
            "check_out": check_out
        }).json()
        
        available_room_ids_after = [r["id"] for r in rooms_after]
        for room_id in room_ids:
            assert room_id in available_room_ids_after, "Room should be available after deletion"
        
        print(f"✓ Rooms freed after deleting booking")
    
    def test_delete_nonexistent_booking(self):
        """Test deleting a booking that doesn't exist returns 404"""
        fake_id = "nonexistent-booking-id-12345"
        
        delete_response = self.session.delete(f"{BASE_URL}/api/bookings/{fake_id}")
        assert delete_response.status_code == 404, "Should return 404 for nonexistent booking"
        
        print("✓ Correctly returns 404 for nonexistent booking")
    
    def test_delete_already_deleted_booking(self):
        """Test deleting a booking twice returns 404 on second attempt"""
        # Create and delete a booking
        booking = self.create_test_booking("TEST_DELETE_TWICE")
        booking_id = booking["id"]
        
        # First delete - should succeed
        first_delete = self.session.delete(f"{BASE_URL}/api/bookings/{booking_id}")
        assert first_delete.status_code == 200
        
        # Second delete - should fail with 404
        second_delete = self.session.delete(f"{BASE_URL}/api/bookings/{booking_id}")
        assert second_delete.status_code == 404, "Should return 404 for already deleted booking"
        
        print("✓ Correctly returns 404 for already deleted booking")
    
    def test_delete_cancelled_booking(self):
        """Test that cancelled bookings can also be deleted"""
        # Create a booking
        booking = self.create_test_booking("TEST_DELETE_CANCELLED")
        booking_id = booking["id"]
        
        # Cancel the booking first
        cancel_response = self.session.post(f"{BASE_URL}/api/bookings/cancel", json={
            "booking_id": booking_id,
            "reason": "Test cancellation",
            "refund_amount": 0
        })
        assert cancel_response.status_code == 200, "Cancellation should succeed"
        
        # Now delete the cancelled booking
        delete_response = self.session.delete(f"{BASE_URL}/api/bookings/{booking_id}")
        assert delete_response.status_code == 200, "Should be able to delete cancelled booking"
        
        # Verify it's gone
        get_response = self.session.get(f"{BASE_URL}/api/bookings/{booking_id}")
        assert get_response.status_code == 404
        
        print("✓ Successfully deleted cancelled booking")


class TestDynamicRankDropdown:
    """Test that ranks added in Settings appear in booking form dropdown"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test data"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
    def test_get_settings_returns_ranks(self):
        """Test that GET /api/settings returns ranks array"""
        response = self.session.get(f"{BASE_URL}/api/settings")
        assert response.status_code == 200
        
        settings = response.json()
        assert "ranks" in settings, "Settings should contain ranks array"
        assert isinstance(settings["ranks"], list), "Ranks should be a list"
        assert len(settings["ranks"]) > 0, "Ranks list should not be empty"
        
        print(f"✓ Settings contains {len(settings['ranks'])} ranks")
    
    def test_add_new_rank_to_settings(self):
        """Test adding a new rank via PUT /api/settings"""
        # Get current settings
        get_response = self.session.get(f"{BASE_URL}/api/settings")
        assert get_response.status_code == 200
        current_settings = get_response.json()
        current_ranks = current_settings.get("ranks", [])
        
        # Add a new test rank
        test_rank = "TEST_RANK_DYNAMIC"
        if test_rank not in current_ranks:
            new_ranks = current_ranks + [test_rank]
        else:
            new_ranks = current_ranks
        
        # Update settings with new rank
        update_response = self.session.put(f"{BASE_URL}/api/settings", json={
            "ranks": new_ranks
        })
        assert update_response.status_code == 200, f"Failed to update settings: {update_response.text}"
        
        # Verify the rank was added
        updated_settings = update_response.json()
        assert test_rank in updated_settings["ranks"], "New rank should be in settings"
        
        print(f"✓ Successfully added rank '{test_rank}' to settings")
        
        # Cleanup - remove test rank
        cleanup_ranks = [r for r in updated_settings["ranks"] if r != test_rank]
        self.session.put(f"{BASE_URL}/api/settings", json={"ranks": cleanup_ranks})
    
    def test_ranks_persist_after_update(self):
        """Test that ranks persist after settings update"""
        # Get current settings
        get_response = self.session.get(f"{BASE_URL}/api/settings")
        current_settings = get_response.json()
        current_ranks = current_settings.get("ranks", [])
        
        # Add test rank
        test_rank = "TEST_PERSIST_RANK"
        new_ranks = current_ranks + [test_rank] if test_rank not in current_ranks else current_ranks
        
        # Update
        self.session.put(f"{BASE_URL}/api/settings", json={"ranks": new_ranks})
        
        # Fetch again to verify persistence
        verify_response = self.session.get(f"{BASE_URL}/api/settings")
        assert verify_response.status_code == 200
        verified_settings = verify_response.json()
        
        assert test_rank in verified_settings["ranks"], "Rank should persist after update"
        
        print(f"✓ Rank '{test_rank}' persists after settings update")
        
        # Cleanup
        cleanup_ranks = [r for r in verified_settings["ranks"] if r != test_rank]
        self.session.put(f"{BASE_URL}/api/settings", json={"ranks": cleanup_ranks})
    
    def test_booking_with_custom_rank(self):
        """Test creating a booking with a custom rank from settings"""
        # Get settings and add a custom rank
        get_response = self.session.get(f"{BASE_URL}/api/settings")
        current_settings = get_response.json()
        current_ranks = current_settings.get("ranks", [])
        
        test_rank = "TEST_BOOKING_RANK"
        if test_rank not in current_ranks:
            new_ranks = current_ranks + [test_rank]
            self.session.put(f"{BASE_URL}/api/settings", json={"ranks": new_ranks})
        
        # Get available rooms
        check_in = (datetime.now() + timedelta(days=15)).strftime("%Y-%m-%d")
        check_out = (datetime.now() + timedelta(days=17)).strftime("%Y-%m-%d")
        
        rooms_response = self.session.get(f"{BASE_URL}/api/rooms/available", params={
            "check_in": check_in,
            "check_out": check_out
        })
        
        if rooms_response.status_code != 200 or not rooms_response.json():
            pytest.skip("No available rooms for testing")
            
        room_id = rooms_response.json()[0]["id"]
        
        # Create booking with custom rank
        booking_data = {
            "guest_name": "TEST_CUSTOM_RANK_Guest",
            "guest_contact": "9876543210",
            "guest_rank": test_rank,  # Use the custom rank
            "room_ids": [room_id],
            "num_rooms": 1,
            "check_in_date": check_in,
            "check_out_date": check_out,
            "advance_paid": 400,
            "payment_mode": "cash",
            "payment_id": "TEST456"
        }
        
        create_response = self.session.post(f"{BASE_URL}/api/bookings", json=booking_data)
        assert create_response.status_code == 200, f"Failed to create booking: {create_response.text}"
        
        booking = create_response.json()
        assert booking["guest_rank"] == test_rank, "Booking should have custom rank"
        
        print(f"✓ Successfully created booking with custom rank '{test_rank}'")
        
        # Cleanup - delete the test booking
        self.session.delete(f"{BASE_URL}/api/bookings/{booking['id']}")
        
        # Cleanup - remove test rank
        cleanup_response = self.session.get(f"{BASE_URL}/api/settings")
        cleanup_ranks = [r for r in cleanup_response.json()["ranks"] if r != test_rank]
        self.session.put(f"{BASE_URL}/api/settings", json={"ranks": cleanup_ranks})


class TestDeleteBookingAllStatuses:
    """Test delete button works for all booking statuses"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test data"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
    
    def create_booking_with_status(self, status, prefix):
        """Helper to create booking and set to specific status"""
        # Get available rooms
        check_in = (datetime.now() + timedelta(days=20)).strftime("%Y-%m-%d")
        check_out = (datetime.now() + timedelta(days=22)).strftime("%Y-%m-%d")
        
        rooms_response = self.session.get(f"{BASE_URL}/api/rooms/available", params={
            "check_in": check_in,
            "check_out": check_out
        })
        
        if rooms_response.status_code != 200 or not rooms_response.json():
            pytest.skip("No available rooms for testing")
            
        room_id = rooms_response.json()[0]["id"]
        
        # Create booking
        booking_data = {
            "guest_name": f"{prefix}_Guest",
            "guest_contact": "9876543210",
            "guest_rank": "Hav",
            "room_ids": [room_id],
            "num_rooms": 1,
            "check_in_date": check_in,
            "check_out_date": check_out,
            "advance_paid": 400,
            "payment_mode": "cash",
            "payment_id": "TEST789"
        }
        
        response = self.session.post(f"{BASE_URL}/api/bookings", json=booking_data)
        assert response.status_code == 200
        booking = response.json()
        
        # Set to desired status if not confirmed
        if status == "cancelled":
            self.session.post(f"{BASE_URL}/api/bookings/cancel", json={
                "booking_id": booking["id"],
                "reason": "Test",
                "refund_amount": 0
            })
        
        return booking
    
    def test_delete_confirmed_booking(self):
        """Test deleting a confirmed booking"""
        booking = self.create_booking_with_status("confirmed", "TEST_DEL_CONFIRMED")
        
        delete_response = self.session.delete(f"{BASE_URL}/api/bookings/{booking['id']}")
        assert delete_response.status_code == 200
        
        print("✓ Can delete confirmed booking")
    
    def test_delete_cancelled_booking(self):
        """Test deleting a cancelled booking"""
        booking = self.create_booking_with_status("cancelled", "TEST_DEL_CANCELLED")
        
        # Verify it's cancelled
        get_response = self.session.get(f"{BASE_URL}/api/bookings/{booking['id']}")
        assert get_response.json()["status"] == "cancelled"
        
        delete_response = self.session.delete(f"{BASE_URL}/api/bookings/{booking['id']}")
        assert delete_response.status_code == 200
        
        print("✓ Can delete cancelled booking")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
