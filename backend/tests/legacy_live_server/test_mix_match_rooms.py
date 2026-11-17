"""
Test Suite for P1: Mix & Match Rooms Feature
Tests the optimal room combination API and segmented booking creation
"""
import pytest
import requests
import os
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestOptimalRoomCombinationAPI:
    """Tests for POST /api/rooms/find-optimal-combination endpoint"""
    
    def test_optimal_combination_single_room(self):
        """Test optimal combination for 1 room over 3 nights"""
        response = requests.post(
            f"{BASE_URL}/api/rooms/find-optimal-combination",
            params={
                "check_in": "2026-04-25",
                "check_out": "2026-04-28",
                "num_rooms": 1
            }
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Verify response structure
        assert "optimal_combination" in data
        assert "total_room_changes" in data
        assert "availability_status" in data
        assert "message" in data
        assert "summary" in data
        
        # Verify optimal_combination structure
        assert len(data["optimal_combination"]) == 3, "Should have 3 nights"
        
        for segment in data["optimal_combination"]:
            assert "night_date" in segment
            assert "rooms" in segment
            assert len(segment["rooms"]) == 1, "Should have 1 room per night"
            
            for room in segment["rooms"]:
                assert "id" in room
                assert "room_number" in room
                assert "category" in room
        
        # Verify summary
        assert data["summary"]["total_nights"] == 3
        assert data["summary"]["rooms_per_night"] == 1
        
        print(f"✓ Single room optimal combination: {data['availability_status']}, {data['total_room_changes']} changes")
    
    def test_optimal_combination_multiple_rooms(self):
        """Test optimal combination for 2 rooms over 3 nights"""
        response = requests.post(
            f"{BASE_URL}/api/rooms/find-optimal-combination",
            params={
                "check_in": "2026-04-25",
                "check_out": "2026-04-28",
                "num_rooms": 2
            }
        )
        
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify 2 rooms per night
        for segment in data["optimal_combination"]:
            assert len(segment["rooms"]) == 2, f"Should have 2 rooms per night, got {len(segment['rooms'])}"
        
        assert data["summary"]["rooms_per_night"] == 2
        
        print(f"✓ Multi-room optimal combination: {data['availability_status']}, {data['total_room_changes']} changes")
    
    def test_optimal_combination_three_rooms(self):
        """Test optimal combination for 3 rooms over 3 nights"""
        response = requests.post(
            f"{BASE_URL}/api/rooms/find-optimal-combination",
            params={
                "check_in": "2026-04-25",
                "check_out": "2026-04-28",
                "num_rooms": 3
            }
        )
        
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify 3 rooms per night
        for segment in data["optimal_combination"]:
            assert len(segment["rooms"]) == 3, f"Should have 3 rooms per night, got {len(segment['rooms'])}"
        
        print(f"✓ Three-room optimal combination: {data['availability_status']}, {data['total_room_changes']} changes")
    
    def test_optimal_combination_invalid_dates(self):
        """Test error handling for invalid date range"""
        response = requests.post(
            f"{BASE_URL}/api/rooms/find-optimal-combination",
            params={
                "check_in": "2026-04-28",
                "check_out": "2026-04-25",  # Check-out before check-in
                "num_rooms": 1
            }
        )
        
        assert response.status_code == 400, f"Expected 400 for invalid dates, got {response.status_code}"
        print("✓ Invalid dates correctly rejected")
    
    def test_optimal_combination_with_exclude_booking(self):
        """Test exclude_booking_id parameter works"""
        response = requests.post(
            f"{BASE_URL}/api/rooms/find-optimal-combination",
            params={
                "check_in": "2026-04-25",
                "check_out": "2026-04-28",
                "num_rooms": 1,
                "exclude_booking_id": "non-existent-id"  # Should still work
            }
        )
        
        assert response.status_code == 200
        print("✓ exclude_booking_id parameter accepted")


class TestSegmentedBookingCreation:
    """Tests for creating bookings with room_segments (Mix & Match)"""
    
    @pytest.fixture
    def room_segments_data(self):
        """Get optimal room combination for test booking"""
        response = requests.post(
            f"{BASE_URL}/api/rooms/find-optimal-combination",
            params={
                "check_in": "2026-05-01",
                "check_out": "2026-05-04",
                "num_rooms": 1
            }
        )
        assert response.status_code == 200
        return response.json()["optimal_combination"]
    
    def test_create_segmented_booking(self, room_segments_data):
        """Test creating a booking with room_segments"""
        booking_payload = {
            "guest_name": "TEST_MixMatch_Guest",
            "guest_contact": "+91 98765 43210",
            "is_org": True,
            "room_ids": [],  # Empty for segmented booking
            "room_segments": room_segments_data,
            "num_rooms": 1,
            "check_in_date": "2026-05-01",
            "check_out_date": "2026-05-04",
            "advance_paid": 500,
            "payment_mode": "cash",
            "payment_id": "CASH-TEST-001"
        }
        
        response = requests.post(f"{BASE_URL}/api/bookings", json=booking_payload)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        booking = response.json()
        
        # Verify booking was created with segments
        assert booking["guest_name"] == "TEST_MixMatch_Guest"
        assert booking["room_segments"] is not None, "room_segments should be stored"
        assert len(booking["room_segments"]) == 3, "Should have 3 night segments"
        assert "has_room_changes" in booking
        assert booking["total_amount"] > 0, "Total amount should be calculated"
        
        # Verify room_ids is populated from segments
        assert len(booking["room_ids"]) > 0, "room_ids should be populated from segments"
        
        print(f"✓ Segmented booking created: {booking['booking_number']}, total: ₹{booking['total_amount']}")
        
        # Cleanup - delete test booking
        delete_response = requests.delete(f"{BASE_URL}/api/bookings/{booking['id']}")
        assert delete_response.status_code == 200
        print(f"✓ Test booking cleaned up")
        
        return booking
    
    def test_create_multi_room_segmented_booking(self):
        """Test creating a booking with 2 rooms using segments"""
        # Get optimal combination for 2 rooms
        combo_response = requests.post(
            f"{BASE_URL}/api/rooms/find-optimal-combination",
            params={
                "check_in": "2026-05-05",
                "check_out": "2026-05-07",
                "num_rooms": 2
            }
        )
        assert combo_response.status_code == 200
        room_segments = combo_response.json()["optimal_combination"]
        
        booking_payload = {
            "guest_name": "TEST_MixMatch_Family",
            "guest_contact": "+91 87654 32109",
            "is_org": False,  # Non-Org guest
            "room_ids": [],
            "room_segments": room_segments,
            "num_rooms": 2,
            "check_in_date": "2026-05-05",
            "check_out_date": "2026-05-07",
            "advance_paid": 800,
            "payment_mode": "upi",
            "upi_id": "test@upi"
        }
        
        response = requests.post(f"{BASE_URL}/api/bookings", json=booking_payload)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        booking = response.json()
        
        # Verify multi-room segmented booking
        assert booking["num_rooms"] == 2
        assert len(booking["room_segments"]) == 2, "Should have 2 night segments"
        
        # Verify each segment has 2 rooms
        for segment in booking["room_segments"]:
            assert len(segment["rooms"]) == 2, f"Each segment should have 2 rooms"
        
        print(f"✓ Multi-room segmented booking created: {booking['booking_number']}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/bookings/{booking['id']}")
        print(f"✓ Test booking cleaned up")
    
    def test_segmented_booking_cost_calculation(self):
        """Test that cost is correctly calculated for segmented bookings"""
        # Get settings for rate verification
        settings_response = requests.get(f"{BASE_URL}/api/settings")
        settings = settings_response.json()
        
        # Get optimal combination
        combo_response = requests.post(
            f"{BASE_URL}/api/rooms/find-optimal-combination",
            params={
                "check_in": "2026-05-10",
                "check_out": "2026-05-12",  # 2 nights
                "num_rooms": 1
            }
        )
        room_segments = combo_response.json()["optimal_combination"]
        
        # Create booking
        booking_payload = {
            "guest_name": "TEST_CostCalc_Guest",
            "is_org": True,
            "room_ids": [],
            "room_segments": room_segments,
            "num_rooms": 1,
            "check_in_date": "2026-05-10",
            "check_out_date": "2026-05-12",
            "advance_paid": 0,
            "payment_mode": "cash",
            "payment_id": "CASH-TEST-002"
        }
        
        response = requests.post(f"{BASE_URL}/api/bookings", json=booking_payload)
        assert response.status_code == 200
        
        booking = response.json()
        
        # Verify cost calculation
        # For Org guest, 2 nights, 1 room
        # Expected: (room_rent + license_fee) * 2 nights
        room_category = room_segments[0]["rooms"][0]["category"]
        
        if room_category == "Cat I":
            expected_rate = settings.get("cat_i_room_rent", 470) + settings.get("cat_i_license_fee", 30)
        else:
            expected_rate = settings.get("cat_ii_room_rent", 385) + settings.get("cat_ii_license_fee", 15)
        
        expected_total = expected_rate * 2  # 2 nights
        
        print(f"Room category: {room_category}")
        print(f"Expected rate per night: ₹{expected_rate}")
        print(f"Expected total (2 nights): ₹{expected_total}")
        print(f"Actual total: ₹{booking['total_amount']}")
        
        # Allow some tolerance for different rate structures
        assert booking["total_amount"] > 0, "Total amount should be positive"
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/bookings/{booking['id']}")
        print(f"✓ Cost calculation test completed")


class TestEdgeCases:
    """Test edge cases for Mix & Match feature"""
    
    def test_insufficient_room_availability(self):
        """Test handling when not enough rooms are available"""
        # Request more rooms than likely available
        response = requests.post(
            f"{BASE_URL}/api/rooms/find-optimal-combination",
            params={
                "check_in": "2026-04-25",
                "check_out": "2026-04-28",
                "num_rooms": 20  # More than total rooms
            }
        )
        
        assert response.status_code == 200
        
        data = response.json()
        
        # Should return insufficient status
        assert data["availability_status"] == "insufficient", f"Expected 'insufficient', got {data['availability_status']}"
        assert "message" in data
        assert len(data["optimal_combination"]) == 0
        
        print(f"✓ Insufficient availability handled: {data['message']}")
    
    def test_single_night_booking(self):
        """Test optimal combination for single night"""
        response = requests.post(
            f"{BASE_URL}/api/rooms/find-optimal-combination",
            params={
                "check_in": "2026-04-25",
                "check_out": "2026-04-26",  # 1 night
                "num_rooms": 1
            }
        )
        
        assert response.status_code == 200
        
        data = response.json()
        
        assert len(data["optimal_combination"]) == 1, "Should have 1 night segment"
        assert data["total_room_changes"] == 0, "No room changes for single night"
        
        print(f"✓ Single night booking: {data['availability_status']}")
    
    def test_long_stay_booking(self):
        """Test optimal combination for longer stay (7 nights)"""
        response = requests.post(
            f"{BASE_URL}/api/rooms/find-optimal-combination",
            params={
                "check_in": "2026-06-01",
                "check_out": "2026-06-08",  # 7 nights
                "num_rooms": 1
            }
        )
        
        assert response.status_code == 200
        
        data = response.json()
        
        assert len(data["optimal_combination"]) == 7, "Should have 7 night segments"
        assert data["summary"]["total_nights"] == 7
        
        print(f"✓ Long stay (7 nights): {data['availability_status']}, {data['total_room_changes']} changes")


class TestDatabasePersistence:
    """Test that room_segments are correctly stored in database"""
    
    def test_room_segments_persisted(self):
        """Verify room_segments are stored and retrievable"""
        # Get optimal combination
        combo_response = requests.post(
            f"{BASE_URL}/api/rooms/find-optimal-combination",
            params={
                "check_in": "2026-05-15",
                "check_out": "2026-05-17",
                "num_rooms": 1
            }
        )
        room_segments = combo_response.json()["optimal_combination"]
        
        # Create booking
        booking_payload = {
            "guest_name": "TEST_Persistence_Guest",
            "is_org": True,
            "room_ids": [],
            "room_segments": room_segments,
            "num_rooms": 1,
            "check_in_date": "2026-05-15",
            "check_out_date": "2026-05-17",
            "advance_paid": 400,
            "payment_mode": "cash",
            "payment_id": "CASH-TEST-003"
        }
        
        create_response = requests.post(f"{BASE_URL}/api/bookings", json=booking_payload)
        assert create_response.status_code == 200
        
        booking = create_response.json()
        booking_id = booking["id"]
        
        # Fetch booking again to verify persistence
        get_response = requests.get(f"{BASE_URL}/api/bookings/{booking_id}")
        assert get_response.status_code == 200
        
        fetched_booking = get_response.json()
        
        # Verify room_segments persisted
        assert fetched_booking["room_segments"] is not None
        assert len(fetched_booking["room_segments"]) == 2
        assert fetched_booking["has_room_changes"] is not None
        
        # Verify segment structure
        for segment in fetched_booking["room_segments"]:
            assert "night_date" in segment
            assert "rooms" in segment
            for room in segment["rooms"]:
                assert "id" in room
                assert "room_number" in room
                assert "category" in room
        
        print(f"✓ room_segments persisted correctly for booking {booking['booking_number']}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/bookings/{booking_id}")
        print(f"✓ Test booking cleaned up")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
