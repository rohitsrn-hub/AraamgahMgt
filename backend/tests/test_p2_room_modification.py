"""
Test suite for P2: Check-In Flexibility - Room Modification During Check-In
Features tested:
1. GET /api/rooms/available - Returns available rooms for date range
2. PUT /api/bookings/{id}/update-rooms - Updates room assignments for confirmed bookings
3. Room modification blocked for checked-in bookings
4. Conflict detection for room availability
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
    staff_list = response.json()
    if not staff_list:
        # Create a test staff member
        create_response = api_session.post(f"{BASE_URL}/api/staff", json={
            "name": "TEST_P2_Staff",
            "staff_type": "Army",
            "designation": "Duty NCO"
        })
        assert create_response.status_code == 200
        return [create_response.json()]
    return staff_list


class TestRoomsAvailableEndpoint:
    """Test GET /api/rooms/available endpoint"""
    
    def test_get_available_rooms_basic(self, api_session, rooms):
        """Test basic available rooms query"""
        check_in = (datetime.now() + timedelta(days=100)).strftime("%Y-%m-%d")
        check_out = (datetime.now() + timedelta(days=102)).strftime("%Y-%m-%d")
        
        response = api_session.get(f"{BASE_URL}/api/rooms/available", params={
            "check_in": check_in,
            "check_out": check_out
        })
        
        assert response.status_code == 200, f"Failed: {response.text}"
        available_rooms = response.json()
        
        assert isinstance(available_rooms, list), "Response should be a list"
        print(f"✓ GET /api/rooms/available returned {len(available_rooms)} rooms")
        
        # Verify room structure
        if available_rooms:
            room = available_rooms[0]
            assert "id" in room, "Room should have id"
            assert "room_number" in room, "Room should have room_number"
            assert "category" in room, "Room should have category"
            assert "status" in room, "Room should have status"
            print(f"  Sample room: {room['room_number']} ({room['category']})")
    
    def test_available_rooms_excludes_booked_rooms(self, api_session, rooms):
        """Test that booked rooms are excluded from available rooms"""
        # Create a booking first
        available_rooms = [r for r in rooms if r["status"] == "available"]
        if len(available_rooms) < 2:
            pytest.skip("Need at least 2 available rooms")
        
        unique_offset = 200 + int(uuid.uuid4().int % 100)
        check_in = (datetime.now() + timedelta(days=unique_offset)).strftime("%Y-%m-%d")
        check_out = (datetime.now() + timedelta(days=unique_offset + 2)).strftime("%Y-%m-%d")
        
        # Book one room
        booking_data = {
            "guest_name": f"TEST_P2_Exclude_{uuid.uuid4().hex[:8]}",
            "guest_contact": "+91 9876543210",
            "guest_rank": "Hav",
            "room_ids": [available_rooms[0]["id"]],
            "num_rooms": 1,
            "check_in_date": check_in,
            "check_out_date": check_out,
            "advance_paid": 500,
            "payment_mode": "cash",
            "payment_id": f"CASH-{uuid.uuid4().hex[:8]}"
        }
        
        booking_response = api_session.post(f"{BASE_URL}/api/bookings", json=booking_data)
        assert booking_response.status_code == 200, f"Booking failed: {booking_response.text}"
        booking = booking_response.json()
        
        # Check available rooms for same dates
        avail_response = api_session.get(f"{BASE_URL}/api/rooms/available", params={
            "check_in": check_in,
            "check_out": check_out
        })
        
        assert avail_response.status_code == 200
        available_now = avail_response.json()
        
        # The booked room should NOT be in available rooms
        booked_room_ids = [r["id"] for r in available_now]
        assert available_rooms[0]["id"] not in booked_room_ids, "Booked room should not be in available rooms"
        
        print(f"✓ Booked room {available_rooms[0]['room_number']} correctly excluded from available rooms")
    
    def test_available_rooms_with_exclude_booking_id(self, api_session, rooms):
        """Test exclude_booking_id parameter shows rooms from that booking as available"""
        available_rooms = [r for r in rooms if r["status"] == "available"]
        if not available_rooms:
            pytest.skip("No available rooms")
        
        unique_offset = 300 + int(uuid.uuid4().int % 100)
        check_in = (datetime.now() + timedelta(days=unique_offset)).strftime("%Y-%m-%d")
        check_out = (datetime.now() + timedelta(days=unique_offset + 2)).strftime("%Y-%m-%d")
        
        # Create a booking
        booking_data = {
            "guest_name": f"TEST_P2_ExcludeBooking_{uuid.uuid4().hex[:8]}",
            "guest_contact": "+91 9876543211",
            "guest_rank": "Nk",
            "room_ids": [available_rooms[0]["id"]],
            "num_rooms": 1,
            "check_in_date": check_in,
            "check_out_date": check_out,
            "advance_paid": 400,
            "payment_mode": "cash",
            "payment_id": f"CASH-{uuid.uuid4().hex[:8]}"
        }
        
        booking_response = api_session.post(f"{BASE_URL}/api/bookings", json=booking_data)
        assert booking_response.status_code == 200
        booking = booking_response.json()
        
        # Check available rooms WITH exclude_booking_id
        avail_response = api_session.get(f"{BASE_URL}/api/rooms/available", params={
            "check_in": check_in,
            "check_out": check_out,
            "exclude_booking_id": booking["id"]
        })
        
        assert avail_response.status_code == 200
        available_with_exclude = avail_response.json()
        
        # The booked room SHOULD be in available rooms when excluding this booking
        available_room_ids = [r["id"] for r in available_with_exclude]
        assert available_rooms[0]["id"] in available_room_ids, "Room should be available when excluding its booking"
        
        print(f"✓ exclude_booking_id correctly shows room {available_rooms[0]['room_number']} as available")


class TestUpdateRoomsEndpoint:
    """Test PUT /api/bookings/{id}/update-rooms endpoint"""
    
    def test_update_rooms_for_confirmed_booking(self, api_session, rooms):
        """Test updating room assignments for a confirmed booking"""
        available_rooms = [r for r in rooms if r["status"] == "available"]
        if len(available_rooms) < 2:
            pytest.skip("Need at least 2 available rooms")
        
        unique_offset = 400 + int(uuid.uuid4().int % 100)
        check_in = (datetime.now() + timedelta(days=unique_offset)).strftime("%Y-%m-%d")
        check_out = (datetime.now() + timedelta(days=unique_offset + 2)).strftime("%Y-%m-%d")
        
        # Create booking with first room
        booking_data = {
            "guest_name": f"TEST_P2_UpdateRooms_{uuid.uuid4().hex[:8]}",
            "guest_contact": "+91 9876543212",
            "guest_rank": "Sgt",
            "room_ids": [available_rooms[0]["id"]],
            "num_rooms": 1,
            "check_in_date": check_in,
            "check_out_date": check_out,
            "advance_paid": 500,
            "payment_mode": "upi",
            "payment_id": f"UPI-{uuid.uuid4().hex[:8]}"
        }
        
        booking_response = api_session.post(f"{BASE_URL}/api/bookings", json=booking_data)
        assert booking_response.status_code == 200
        booking = booking_response.json()
        
        assert booking["status"] == "confirmed", "Booking should be confirmed"
        assert booking["room_ids"] == [available_rooms[0]["id"]], "Initial room should be set"
        
        # Update to second room
        update_response = api_session.put(
            f"{BASE_URL}/api/bookings/{booking['id']}/update-rooms",
            json={"room_ids": [available_rooms[1]["id"]]}
        )
        
        assert update_response.status_code == 200, f"Update failed: {update_response.text}"
        result = update_response.json()
        
        assert "booking" in result, "Response should contain booking"
        updated_booking = result["booking"]
        
        assert updated_booking["room_ids"] == [available_rooms[1]["id"]], "Room should be updated"
        assert updated_booking["room_numbers"] == [available_rooms[1]["room_number"]], "Room number should be updated"
        
        print(f"✓ Room updated from {available_rooms[0]['room_number']} to {available_rooms[1]['room_number']}")
    
    def test_update_rooms_blocked_for_checked_in_booking(self, api_session, rooms, staff):
        """Test that room modification is blocked for checked-in bookings"""
        if not staff:
            pytest.skip("No staff available")
        
        # Create booking with today's check-in date
        check_in = datetime.now().strftime("%Y-%m-%d")  # Today for check-in
        check_out = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
        
        # Get truly available rooms for today using the available endpoint
        avail_response = api_session.get(f"{BASE_URL}/api/rooms/available", params={
            "check_in": check_in,
            "check_out": check_out
        })
        assert avail_response.status_code == 200
        available_rooms = avail_response.json()
        
        if len(available_rooms) < 2:
            pytest.skip("Need at least 2 available rooms for today")
        
        booking_data = {
            "guest_name": f"TEST_P2_CheckedIn_{uuid.uuid4().hex[:8]}",
            "guest_contact": "+91 9876543213",
            "guest_rank": "PO",
            "room_ids": [available_rooms[0]["id"]],
            "num_rooms": 1,
            "check_in_date": check_in,
            "check_out_date": check_out,
            "advance_paid": 500,
            "payment_mode": "cash",
            "payment_id": f"CASH-{uuid.uuid4().hex[:8]}"
        }
        
        booking_response = api_session.post(f"{BASE_URL}/api/bookings", json=booking_data)
        assert booking_response.status_code == 200, f"Booking failed: {booking_response.text}"
        booking = booking_response.json()
        
        # Check-in the booking
        checkin_data = {
            "booking_id": booking["id"],
            "staff_id": staff[0]["id"],
            "extra_beds": 0,
            "guest_contact": "+91 9876543213",
            "guest_age": 35,
            "guest_sex": "M",
            "guest_address": "Test Address for P2 Testing, City 123456",
            "identity_card_number": "ID123456789",
            "guest_service_status": "Serving"
        }
        
        checkin_response = api_session.post(f"{BASE_URL}/api/bookings/check-in", json=checkin_data)
        assert checkin_response.status_code == 200, f"Check-in failed: {checkin_response.text}"
        
        # Verify booking is checked-in
        get_response = api_session.get(f"{BASE_URL}/api/bookings/{booking['id']}")
        assert get_response.status_code == 200
        checked_in_booking = get_response.json()
        assert checked_in_booking["status"] == "checked_in", "Booking should be checked-in"
        
        # Try to update rooms - should fail
        update_response = api_session.put(
            f"{BASE_URL}/api/bookings/{booking['id']}/update-rooms",
            json={"room_ids": [available_rooms[1]["id"]]}
        )
        
        assert update_response.status_code == 400, "Should fail for checked-in booking"
        error = update_response.json()
        assert "confirmed" in error.get("detail", "").lower(), "Error should mention confirmed status"
        
        print(f"✓ Room modification correctly blocked for checked-in booking")
    
    def test_update_rooms_validates_room_count(self, api_session, rooms):
        """Test that update-rooms validates room count matches original"""
        unique_offset = 500 + int(uuid.uuid4().int % 100)
        check_in = (datetime.now() + timedelta(days=unique_offset)).strftime("%Y-%m-%d")
        check_out = (datetime.now() + timedelta(days=unique_offset + 2)).strftime("%Y-%m-%d")
        
        # Get truly available rooms for the date range
        avail_response = api_session.get(f"{BASE_URL}/api/rooms/available", params={
            "check_in": check_in,
            "check_out": check_out
        })
        assert avail_response.status_code == 200
        available_rooms = avail_response.json()
        
        if len(available_rooms) < 3:
            pytest.skip("Need at least 3 available rooms")
        
        # Create booking with 2 rooms
        booking_data = {
            "guest_name": f"TEST_P2_RoomCount_{uuid.uuid4().hex[:8]}",
            "guest_contact": "+91 9876543214",
            "guest_rank": "Nb Sub",
            "room_ids": [available_rooms[0]["id"], available_rooms[1]["id"]],
            "num_rooms": 2,
            "check_in_date": check_in,
            "check_out_date": check_out,
            "advance_paid": 800,
            "payment_mode": "cash",
            "payment_id": f"CASH-{uuid.uuid4().hex[:8]}"
        }
        
        booking_response = api_session.post(f"{BASE_URL}/api/bookings", json=booking_data)
        assert booking_response.status_code == 200, f"Booking failed: {booking_response.text}"
        booking = booking_response.json()
        
        # Try to update with only 1 room - should fail
        update_response = api_session.put(
            f"{BASE_URL}/api/bookings/{booking['id']}/update-rooms",
            json={"room_ids": [available_rooms[2]["id"]]}  # Only 1 room instead of 2
        )
        
        assert update_response.status_code == 400, "Should fail when room count doesn't match"
        
        print(f"✓ Room count validation working correctly")
    
    def test_update_rooms_updates_categories(self, api_session, rooms):
        """Test that update-rooms also updates room_categories"""
        cat_i_rooms = [r for r in rooms if r["category"] == "Cat I" and r["status"] == "available"]
        cat_ii_rooms = [r for r in rooms if r["category"] == "Cat II" and r["status"] == "available"]
        
        if not cat_i_rooms or not cat_ii_rooms:
            pytest.skip("Need both Cat I and Cat II rooms")
        
        unique_offset = 550 + int(uuid.uuid4().int % 100)
        check_in = (datetime.now() + timedelta(days=unique_offset)).strftime("%Y-%m-%d")
        check_out = (datetime.now() + timedelta(days=unique_offset + 2)).strftime("%Y-%m-%d")
        
        # Create booking with Cat I room
        booking_data = {
            "guest_name": f"TEST_P2_Category_{uuid.uuid4().hex[:8]}",
            "guest_contact": "+91 9876543215",
            "guest_rank": "JWO",
            "room_ids": [cat_i_rooms[0]["id"]],
            "num_rooms": 1,
            "check_in_date": check_in,
            "check_out_date": check_out,
            "advance_paid": 500,
            "payment_mode": "cash",
            "payment_id": f"CASH-{uuid.uuid4().hex[:8]}"
        }
        
        booking_response = api_session.post(f"{BASE_URL}/api/bookings", json=booking_data)
        assert booking_response.status_code == 200
        booking = booking_response.json()
        
        assert booking["room_categories"] == ["Cat I"], "Initial category should be Cat I"
        
        # Update to Cat II room
        update_response = api_session.put(
            f"{BASE_URL}/api/bookings/{booking['id']}/update-rooms",
            json={"room_ids": [cat_ii_rooms[0]["id"]]}
        )
        
        assert update_response.status_code == 200
        result = update_response.json()
        updated_booking = result["booking"]
        
        assert updated_booking["room_categories"] == ["Cat II"], "Category should be updated to Cat II"
        
        print(f"✓ Room category updated from Cat I to Cat II")


class TestRoomModificationIntegration:
    """Integration tests for room modification flow"""
    
    def test_full_room_modification_flow(self, api_session, rooms, staff):
        """Test complete flow: create booking -> modify rooms -> check-in"""
        if not staff:
            pytest.skip("No staff available")
        
        # Create booking with today's check-in
        check_in = datetime.now().strftime("%Y-%m-%d")
        check_out = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
        
        # Get truly available rooms for today
        avail_response = api_session.get(f"{BASE_URL}/api/rooms/available", params={
            "check_in": check_in,
            "check_out": check_out
        })
        assert avail_response.status_code == 200
        available_rooms = avail_response.json()
        
        if len(available_rooms) < 2:
            pytest.skip("Need at least 2 available rooms for today")
        
        booking_data = {
            "guest_name": f"TEST_P2_FullFlow_{uuid.uuid4().hex[:8]}",
            "guest_contact": "+91 9876543216",
            "guest_rank": "CPO",
            "room_ids": [available_rooms[0]["id"]],
            "num_rooms": 1,
            "check_in_date": check_in,
            "check_out_date": check_out,
            "advance_paid": 500,
            "payment_mode": "cash",
            "payment_id": f"CASH-{uuid.uuid4().hex[:8]}"
        }
        
        # Step 1: Create booking
        booking_response = api_session.post(f"{BASE_URL}/api/bookings", json=booking_data)
        assert booking_response.status_code == 200
        booking = booking_response.json()
        print(f"  Step 1: Booking created with room {available_rooms[0]['room_number']}")
        
        # Step 2: Get available rooms for modification
        avail_response = api_session.get(f"{BASE_URL}/api/rooms/available", params={
            "check_in": check_in,
            "check_out": check_out,
            "exclude_booking_id": booking["id"]
        })
        assert avail_response.status_code == 200
        available_for_change = avail_response.json()
        print(f"  Step 2: Found {len(available_for_change)} rooms available for modification")
        
        # Step 3: Modify room assignment
        new_room = next((r for r in available_for_change if r["id"] != available_rooms[0]["id"]), None)
        if new_room:
            update_response = api_session.put(
                f"{BASE_URL}/api/bookings/{booking['id']}/update-rooms",
                json={"room_ids": [new_room["id"]]}
            )
            assert update_response.status_code == 200
            print(f"  Step 3: Room changed to {new_room['room_number']}")
            
            # Refresh booking
            get_response = api_session.get(f"{BASE_URL}/api/bookings/{booking['id']}")
            booking = get_response.json()
        
        # Step 4: Check-in with modified room
        checkin_data = {
            "booking_id": booking["id"],
            "staff_id": staff[0]["id"],
            "extra_beds": 0,
            "guest_contact": "+91 9876543216",
            "guest_age": 40,
            "guest_sex": "M",
            "guest_address": "Full Flow Test Address, City 123456",
            "identity_card_number": "FULLFLOW123",
            "guest_service_status": "Serving"
        }
        
        checkin_response = api_session.post(f"{BASE_URL}/api/bookings/check-in", json=checkin_data)
        assert checkin_response.status_code == 200, f"Check-in failed: {checkin_response.text}"
        print(f"  Step 4: Check-in successful")
        
        # Verify final state
        final_response = api_session.get(f"{BASE_URL}/api/bookings/{booking['id']}")
        final_booking = final_response.json()
        
        assert final_booking["status"] == "checked_in", "Booking should be checked-in"
        print(f"✓ Full room modification flow completed successfully")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
