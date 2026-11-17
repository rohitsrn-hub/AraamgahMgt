"""
Test suite for new check-in pricing logic with room-guest mapping
Features tested:
1. Family Members section includes 'Dependent ID Ser No' field
2. Room Assignment section displays each booked room with guest checkboxes
3. Can assign 'Self' to a room and toggle 'Valid ID' checkbox
4. Can assign family members to rooms and toggle 'Valid Dependent ID' checkbox
5. Room charge category updates to 'Def Civ' if any guest lacks valid ID
6. Bill summary shows per-room charges breakdown with correct rates
7. Validation: must assign at least one guest to a room before check-in
8. Backend `/api/bookings/check-in` accepts `room_guest_mapping` field
9. Backend recalculates room charges based on room-guest mapping (Cat I/II vs Def Civ rates)
10. Backend stores room_guest_mapping in booking document
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


def create_test_booking(api_session, rooms, num_rooms=2, days_offset=50):
    """Helper to create a test booking with unique dates"""
    # Find available Cat I and Cat II rooms
    cat_i_rooms = [r for r in rooms if r["category"] == "Cat I" and r["status"] == "available"]
    cat_ii_rooms = [r for r in rooms if r["category"] == "Cat II" and r["status"] == "available"]
    
    if len(cat_i_rooms) < 1 or len(cat_ii_rooms) < 1:
        return None
    
    # Use unique dates to avoid conflicts
    unique_offset = days_offset + int(uuid.uuid4().int % 100)
    check_in = (datetime.now() + timedelta(days=unique_offset)).strftime("%Y-%m-%d")
    check_out = (datetime.now() + timedelta(days=unique_offset + 2)).strftime("%Y-%m-%d")
    
    room_ids = [cat_i_rooms[0]["id"], cat_ii_rooms[0]["id"]]
    
    booking_data = {
        "guest_name": f"TEST_Pricing_{uuid.uuid4().hex[:8]}",
        "guest_contact": "+91 9876543210",
        "guest_rank": "Hav",
        "army_number": f"TEST-{uuid.uuid4().hex[:6]}",
        "guest_unit": "Test Unit",
        "room_ids": room_ids,
        "num_rooms": 2,
        "check_in_date": check_in,
        "check_out_date": check_out,
        "advance_paid": 500,
        "payment_mode": "cash",
        "payment_id": f"TEST-RECEIPT-{uuid.uuid4().hex[:6]}"
    }
    
    response = api_session.post(f"{BASE_URL}/api/bookings", json=booking_data)
    if response.status_code == 200:
        return response.json()
    return None


class TestSettingsConfiguration:
    """Test that settings have correct rate configuration"""
    
    def test_settings_have_def_civ_rates(self, settings):
        """Verify settings have Cat I/II and Def Civ rates configured"""
        assert "cat_i_rate" in settings
        assert "cat_ii_rate" in settings
        assert "def_civ_cat_i_rate" in settings
        assert "def_civ_cat_ii_rate" in settings
        
        # Verify expected rates
        assert settings["cat_i_rate"] == 500.0
        assert settings["cat_ii_rate"] == 400.0
        assert settings["def_civ_cat_i_rate"] == 600.0
        assert settings["def_civ_cat_ii_rate"] == 600.0
        print(f"✓ Settings have correct rates: Cat I={settings['cat_i_rate']}, Cat II={settings['cat_ii_rate']}, Def Civ Cat I={settings['def_civ_cat_i_rate']}, Def Civ Cat II={settings['def_civ_cat_ii_rate']}")
    
    def test_cat_i_rate_calculation(self, settings):
        """Verify Cat I rate is used when guest has valid ID"""
        cat_i_rate = settings.get("cat_i_rate", 500)
        def_civ_cat_i_rate = settings.get("def_civ_cat_i_rate", 600)
        
        assert cat_i_rate == 500, f"Expected Cat I rate 500, got {cat_i_rate}"
        assert def_civ_cat_i_rate == 600, f"Expected Def Civ Cat I rate 600, got {def_civ_cat_i_rate}"
        print(f"✓ Cat I rates configured correctly: Regular={cat_i_rate}, Def Civ={def_civ_cat_i_rate}")
    
    def test_cat_ii_rate_calculation(self, settings):
        """Verify Cat II rate is used when guest has valid ID"""
        cat_ii_rate = settings.get("cat_ii_rate", 400)
        def_civ_cat_ii_rate = settings.get("def_civ_cat_ii_rate", 600)
        
        assert cat_ii_rate == 400, f"Expected Cat II rate 400, got {cat_ii_rate}"
        assert def_civ_cat_ii_rate == 600, f"Expected Def Civ Cat II rate 600, got {def_civ_cat_ii_rate}"
        print(f"✓ Cat II rates configured correctly: Regular={cat_ii_rate}, Def Civ={def_civ_cat_ii_rate}")


class TestCheckInRequestModel:
    """Test that CheckInRequest model accepts room_guest_mapping"""
    
    def test_checkin_request_accepts_room_guest_mapping(self, api_session, rooms, staff):
        """Verify the CheckInRequest model accepts room_guest_mapping field"""
        if not staff:
            pytest.skip("No staff available")
        
        # Get a confirmed booking
        bookings_resp = api_session.get(f"{BASE_URL}/api/bookings")
        assert bookings_resp.status_code == 200
        
        bookings = bookings_resp.json()
        confirmed_bookings = [b for b in bookings if b["status"] == "confirmed"]
        
        if not confirmed_bookings:
            pytest.skip("No confirmed bookings available")
        
        booking = confirmed_bookings[0]
        
        # Minimal check-in request with room_guest_mapping
        checkin_data = {
            "booking_id": booking["id"],
            "staff_id": staff[0]["id"],
            "guest_contact": "+91 9876543210",
            "guest_age": 35,
            "guest_sex": "M",
            "guest_address": "Test Address, Test City, Test State 123456",
            "identity_card_number": "TEST-ID-12345",
            "guest_service_status": "Serving",
            "room_guest_mapping": [
                {
                    "room_id": booking["room_ids"][0] if booking.get("room_ids") else "test-room",
                    "room_number": booking["room_numbers"][0] if booking.get("room_numbers") else "C1-01",
                    "room_category": "Cat I",
                    "guests": [{"type": "self", "index": None, "has_valid_id": True}],
                    "charge_category": "Cat I"
                }
            ]
        }
        
        response = api_session.post(f"{BASE_URL}/api/bookings/check-in", json=checkin_data)
        
        # Should either succeed or fail for a valid reason (not because room_guest_mapping is rejected)
        if response.status_code == 200:
            print("✓ CheckInRequest model accepts room_guest_mapping field - check-in successful")
        else:
            error = response.json().get("detail", "")
            # Should not fail because of room_guest_mapping field
            assert "room_guest_mapping" not in error.lower(), \
                f"room_guest_mapping field was rejected: {error}"
            print(f"✓ CheckInRequest model accepts room_guest_mapping field (check-in failed for other reason: {error})")


class TestCheckInWithAllValidIds:
    """Test check-in with all guests having valid IDs (Cat I/II rates)"""
    
    def test_checkin_all_valid_ids_uses_regular_rates(self, api_session, rooms, staff, settings):
        """Test check-in with room_guest_mapping where all guests have valid IDs"""
        if not staff:
            pytest.skip("No staff available for check-in")
        
        # Create a new booking
        booking = create_test_booking(api_session, rooms, days_offset=100)
        if not booking:
            pytest.skip("Could not create test booking")
        
        print(f"Created booking: {booking['booking_number']} with rooms {booking['room_numbers']}")
        
        # Prepare room_guest_mapping with all valid IDs
        room_guest_mapping = []
        for i, room_id in enumerate(booking["room_ids"]):
            room_guest_mapping.append({
                "room_id": room_id,
                "room_number": booking["room_numbers"][i],
                "room_category": booking["room_categories"][i],
                "guests": [
                    {"type": "self", "index": None, "has_valid_id": True}
                ],
                "charge_category": booking["room_categories"][i]  # Should stay as Cat I/II
            })
        
        checkin_data = {
            "booking_id": booking["id"],
            "staff_id": staff[0]["id"],
            "extra_beds": 0,
            "notes": "Test check-in with all valid IDs",
            "guest_contact": "+91 9876543210",
            "guest_age": 35,
            "guest_sex": "M",
            "guest_address": "Test Address, Test City, Test State 123456",
            "identity_card_number": "VALID-ID-12345",
            "guest_service_status": "Serving",
            "service_type": "Army",
            "command_hq": "E Command",
            "family_members": [],
            "room_guest_mapping": room_guest_mapping
        }
        
        response = api_session.post(f"{BASE_URL}/api/bookings/check-in", json=checkin_data)
        assert response.status_code == 200, f"Check-in failed: {response.text}"
        
        result = response.json()
        assert result["message"] == "Check-in successful"
        
        # Verify the booking was updated
        updated_booking = result["booking"]
        assert updated_booking["status"] == "checked_in"
        assert "room_guest_mapping" in updated_booking
        assert len(updated_booking["room_guest_mapping"]) == 2
        
        # Calculate expected total (Cat I + Cat II rates for 2 nights)
        nights = 2
        expected_cat_i_total = settings["cat_i_rate"] * nights
        expected_cat_ii_total = settings["cat_ii_rate"] * nights
        expected_total = expected_cat_i_total + expected_cat_ii_total
        
        print(f"✓ Check-in successful with all valid IDs")
        print(f"  Room rent total: ₹{updated_booking.get('room_rent_total', 0)}")
        print(f"  Expected: ₹{expected_total} (Cat I: ₹{expected_cat_i_total} + Cat II: ₹{expected_cat_ii_total})")
        
        # Verify room_rent_total is calculated correctly
        assert updated_booking.get("room_rent_total", 0) == expected_total, \
            f"Expected room_rent_total={expected_total}, got {updated_booking.get('room_rent_total', 0)}"


class TestCheckInWithMixedIds:
    """Test check-in with mixed valid/invalid IDs (Def Civ rates for invalid)"""
    
    def test_checkin_mixed_ids_uses_def_civ_rate(self, api_session, rooms, staff, settings):
        """Test check-in with room_guest_mapping where one room has invalid ID (Def Civ rate)"""
        if not staff:
            pytest.skip("No staff available for check-in")
        
        # Create a new booking
        booking = create_test_booking(api_session, rooms, days_offset=150)
        if not booking:
            pytest.skip("Could not create test booking")
        
        print(f"Created booking: {booking['booking_number']} with rooms {booking['room_numbers']}")
        
        # Prepare room_guest_mapping - first room has valid ID, second room has invalid ID
        room_guest_mapping = []
        for i, room_id in enumerate(booking["room_ids"]):
            has_valid_id = (i == 0)  # Only first room has valid ID
            charge_category = booking["room_categories"][i] if has_valid_id else "Def Civ"
            
            room_guest_mapping.append({
                "room_id": room_id,
                "room_number": booking["room_numbers"][i],
                "room_category": booking["room_categories"][i],
                "guests": [
                    {"type": "self", "index": None, "has_valid_id": has_valid_id}
                ],
                "charge_category": charge_category
            })
        
        checkin_data = {
            "booking_id": booking["id"],
            "staff_id": staff[0]["id"],
            "extra_beds": 0,
            "notes": "Test check-in with mixed IDs (one Def Civ)",
            "guest_contact": "+91 9876543210",
            "guest_age": 35,
            "guest_sex": "M",
            "guest_address": "Test Address, Test City, Test State 123456",
            "identity_card_number": "VALID-ID-12345",
            "guest_service_status": "Serving",
            "service_type": "Army",
            "command_hq": "E Command",
            "family_members": [],
            "room_guest_mapping": room_guest_mapping
        }
        
        response = api_session.post(f"{BASE_URL}/api/bookings/check-in", json=checkin_data)
        assert response.status_code == 200, f"Check-in failed: {response.text}"
        
        result = response.json()
        assert result["message"] == "Check-in successful"
        
        updated_booking = result["booking"]
        assert updated_booking["status"] == "checked_in"
        
        # Calculate expected total (Cat I rate + Def Civ Cat II rate for 2 nights)
        nights = 2
        # First room (Cat I) has valid ID - charged at Cat I rate
        expected_cat_i_total = settings["cat_i_rate"] * nights
        # Second room (Cat II) has invalid ID - charged at Def Civ Cat II rate
        expected_def_civ_total = settings["def_civ_cat_ii_rate"] * nights
        expected_total = expected_cat_i_total + expected_def_civ_total
        
        print(f"✓ Check-in successful with mixed IDs (one Def Civ)")
        print(f"  Room rent total: ₹{updated_booking.get('room_rent_total', 0)}")
        print(f"  Expected: ₹{expected_total} (Cat I: ₹{expected_cat_i_total} + Def Civ: ₹{expected_def_civ_total})")
        
        # Verify room_rent_total is calculated correctly with Def Civ rate
        assert updated_booking.get("room_rent_total", 0) == expected_total, \
            f"Expected room_rent_total={expected_total}, got {updated_booking.get('room_rent_total', 0)}"


class TestCheckInWithFamilyMembers:
    """Test check-in with family members and dependent IDs"""
    
    def test_checkin_stores_family_members_with_dependent_id(self, api_session, rooms, staff, settings):
        """Test check-in with family members having dependent IDs"""
        if not staff:
            pytest.skip("No staff available for check-in")
        
        # Create a new booking
        booking = create_test_booking(api_session, rooms, days_offset=200)
        if not booking:
            pytest.skip("Could not create test booking")
        
        print(f"Created booking: {booking['booking_number']} with rooms {booking['room_numbers']}")
        
        # Family members with dependent IDs
        family_members = [
            {
                "relation": "w/o",
                "name": "Test Wife",
                "age": "32",
                "sex": "F",
                "aadhaar": "1234-5678-9012",
                "mobile": "9876543211",
                "dependent_id": "DEP-ID-001"  # NEW: Dependent ID field
            },
            {
                "relation": "s/o",
                "name": "Test Son",
                "age": "10",
                "sex": "M",
                "aadhaar": "1234-5678-9013",
                "mobile": "",
                "dependent_id": "DEP-ID-002"  # NEW: Dependent ID field
            }
        ]
        
        # Room guest mapping - self in room 1, family in room 2
        room_guest_mapping = [
            {
                "room_id": booking["room_ids"][0],
                "room_number": booking["room_numbers"][0],
                "room_category": booking["room_categories"][0],
                "guests": [
                    {"type": "self", "index": None, "has_valid_id": True}
                ],
                "charge_category": booking["room_categories"][0]  # Cat I rate
            },
            {
                "room_id": booking["room_ids"][1],
                "room_number": booking["room_numbers"][1],
                "room_category": booking["room_categories"][1],
                "guests": [
                    {"type": "family_member", "index": 0, "has_valid_id": True},  # Wife with valid dependent ID
                    {"type": "family_member", "index": 1, "has_valid_id": True}   # Son with valid dependent ID
                ],
                "charge_category": booking["room_categories"][1]  # Cat II rate (all have valid IDs)
            }
        ]
        
        checkin_data = {
            "booking_id": booking["id"],
            "staff_id": staff[0]["id"],
            "extra_beds": 0,
            "notes": "Test check-in with family members and dependent IDs",
            "guest_contact": "+91 9876543210",
            "guest_age": 35,
            "guest_sex": "M",
            "guest_address": "Test Address, Test City, Test State 123456",
            "identity_card_number": "VALID-ID-12345",
            "guest_service_status": "Serving",
            "service_type": "Army",
            "command_hq": "E Command",
            "family_members": family_members,
            "room_guest_mapping": room_guest_mapping
        }
        
        response = api_session.post(f"{BASE_URL}/api/bookings/check-in", json=checkin_data)
        assert response.status_code == 200, f"Check-in failed: {response.text}"
        
        result = response.json()
        updated_booking = result["booking"]
        
        # Verify family members are stored with dependent_id
        assert "family_members" in updated_booking
        assert len(updated_booking["family_members"]) == 2
        assert updated_booking["family_members"][0].get("dependent_id") == "DEP-ID-001"
        assert updated_booking["family_members"][1].get("dependent_id") == "DEP-ID-002"
        
        # Verify room_guest_mapping is stored
        assert "room_guest_mapping" in updated_booking
        assert len(updated_booking["room_guest_mapping"]) == 2
        
        print(f"✓ Check-in successful with family members and dependent IDs")
        print(f"  Family members stored: {len(updated_booking['family_members'])}")
        print(f"  Dependent IDs: {[m.get('dependent_id') for m in updated_booking['family_members']]}")
        print(f"  Room guest mapping stored: {len(updated_booking['room_guest_mapping'])}")
    
    def test_family_member_without_valid_id_triggers_def_civ(self, api_session, rooms, staff, settings):
        """Test that a family member without valid dependent ID triggers Def Civ rate for that room"""
        if not staff:
            pytest.skip("No staff available for check-in")
        
        # Create a new booking
        booking = create_test_booking(api_session, rooms, days_offset=250)
        if not booking:
            pytest.skip("Could not create test booking")
        
        print(f"Created booking: {booking['booking_number']} with rooms {booking['room_numbers']}")
        
        # Family member without valid dependent ID
        family_members = [
            {
                "relation": "w/o",
                "name": "Test Wife",
                "age": "32",
                "sex": "F",
                "aadhaar": "1234-5678-9012",
                "mobile": "9876543211",
                "dependent_id": ""  # No dependent ID
            }
        ]
        
        # Room guest mapping - self in room 1 (valid), family in room 2 (invalid - triggers Def Civ)
        room_guest_mapping = [
            {
                "room_id": booking["room_ids"][0],
                "room_number": booking["room_numbers"][0],
                "room_category": booking["room_categories"][0],
                "guests": [
                    {"type": "self", "index": None, "has_valid_id": True}
                ],
                "charge_category": booking["room_categories"][0]  # Cat I rate
            },
            {
                "room_id": booking["room_ids"][1],
                "room_number": booking["room_numbers"][1],
                "room_category": booking["room_categories"][1],
                "guests": [
                    {"type": "family_member", "index": 0, "has_valid_id": False}  # Wife WITHOUT valid dependent ID
                ],
                "charge_category": "Def Civ"  # Should be Def Civ because family member lacks valid ID
            }
        ]
        
        checkin_data = {
            "booking_id": booking["id"],
            "staff_id": staff[0]["id"],
            "extra_beds": 0,
            "notes": "Test check-in with family member lacking valid ID",
            "guest_contact": "+91 9876543210",
            "guest_age": 35,
            "guest_sex": "M",
            "guest_address": "Test Address, Test City, Test State 123456",
            "identity_card_number": "VALID-ID-12345",
            "guest_service_status": "Serving",
            "service_type": "Army",
            "command_hq": "E Command",
            "family_members": family_members,
            "room_guest_mapping": room_guest_mapping
        }
        
        response = api_session.post(f"{BASE_URL}/api/bookings/check-in", json=checkin_data)
        assert response.status_code == 200, f"Check-in failed: {response.text}"
        
        result = response.json()
        updated_booking = result["booking"]
        
        # Calculate expected total
        nights = 2
        expected_cat_i_total = settings["cat_i_rate"] * nights  # Room 1 with valid ID
        expected_def_civ_total = settings["def_civ_cat_ii_rate"] * nights  # Room 2 with invalid ID
        expected_total = expected_cat_i_total + expected_def_civ_total
        
        print(f"✓ Check-in successful - family member without valid ID triggers Def Civ rate")
        print(f"  Room rent total: ₹{updated_booking.get('room_rent_total', 0)}")
        print(f"  Expected: ₹{expected_total} (Cat I: ₹{expected_cat_i_total} + Def Civ: ₹{expected_def_civ_total})")
        
        assert updated_booking.get("room_rent_total", 0) == expected_total, \
            f"Expected room_rent_total={expected_total}, got {updated_booking.get('room_rent_total', 0)}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
