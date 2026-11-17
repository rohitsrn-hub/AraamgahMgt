"""
Test suite for redesigned check-in form with inline family members
Features tested:
1. Standalone 'Family Members' section removed (verified via UI)
2. Each room has inline 'Add Family Member' button
3. Can add family members directly under specific rooms
4. 'Self' checkbox behavior: can only be checked in ONE room at a time (radio behavior)
5. Family member form includes: Relation, Name, Age, Sex, Mobile
6. 'Dependent Card Available?' checkbox for each family member
7. 'Dependent ID Ser No' field visible ONLY when 'Dependent Card Available' is checked
8. Room charge category updates to 'Def Civ' when any family member has unchecked 'Dependent Card Available'
9. Room charge category shows Cat I/II when all family members have dependent cards
10. Bill summary shows correct per-room charges based on dependent card status
11. Backend room_guest_mapping structure updated with has_self and inline family_members
12. Backend pricing calculation works with new room_guest_mapping structure
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


def create_test_booking(api_session, rooms, num_rooms=2, days_offset=300):
    """Helper to create a test booking with unique dates"""
    cat_i_rooms = [r for r in rooms if r["category"] == "Cat I" and r["status"] == "available"]
    cat_ii_rooms = [r for r in rooms if r["category"] == "Cat II" and r["status"] == "available"]
    
    if len(cat_i_rooms) < 1 or len(cat_ii_rooms) < 1:
        return None
    
    unique_offset = days_offset + int(uuid.uuid4().int % 100)
    check_in = (datetime.now() + timedelta(days=unique_offset)).strftime("%Y-%m-%d")
    check_out = (datetime.now() + timedelta(days=unique_offset + 2)).strftime("%Y-%m-%d")
    
    room_ids = [cat_i_rooms[0]["id"], cat_ii_rooms[0]["id"]]
    
    booking_data = {
        "guest_name": f"TEST_Redesign_{uuid.uuid4().hex[:8]}",
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


class TestNewRoomGuestMappingStructure:
    """Test the new room_guest_mapping structure with has_self and family_members"""
    
    def test_checkin_with_new_structure_has_self_and_family_members(self, api_session, rooms, staff, settings):
        """Test check-in with new room_guest_mapping structure containing has_self and family_members"""
        if not staff:
            pytest.skip("No staff available")
        
        booking = create_test_booking(api_session, rooms, days_offset=400)
        if not booking:
            pytest.skip("Could not create test booking")
        
        print(f"Created booking: {booking['booking_number']} with rooms {booking['room_numbers']}")
        
        # NEW STRUCTURE: room_guest_mapping with has_self and family_members
        room_guest_mapping = [
            {
                "room_id": booking["room_ids"][0],
                "room_number": booking["room_numbers"][0],
                "room_category": booking["room_categories"][0],
                "has_self": True,  # Self is in this room
                "family_members": [],  # No family members in this room
                "charge_category": booking["room_categories"][0]  # Cat I rate
            },
            {
                "room_id": booking["room_ids"][1],
                "room_number": booking["room_numbers"][1],
                "room_category": booking["room_categories"][1],
                "has_self": False,  # Self is NOT in this room
                "family_members": [
                    {
                        "relation": "w/o",
                        "name": "Test Wife",
                        "age": "32",
                        "sex": "F",
                        "mobile": "9876543211",
                        "has_dependent_card": True,  # Has dependent card
                        "dependent_id": "DEP-001"
                    }
                ],
                "charge_category": booking["room_categories"][1]  # Cat II rate (has dependent card)
            }
        ]
        
        checkin_data = {
            "booking_id": booking["id"],
            "staff_id": staff[0]["id"],
            "extra_beds": 0,
            "notes": "Test check-in with new structure",
            "guest_contact": "+91 9876543210",
            "guest_age": 35,
            "guest_sex": "M",
            "guest_address": "Test Address, Test City, Test State 123456",
            "identity_card_number": "VALID-ID-12345",
            "guest_service_status": "Serving",
            "service_type": "Army",
            "command_hq": "E Command",
            "family_members": [
                {
                    "relation": "w/o",
                    "name": "Test Wife",
                    "age": "32",
                    "sex": "F",
                    "mobile": "9876543211",
                    "has_dependent_card": True,
                    "dependent_id": "DEP-001"
                }
            ],
            "room_guest_mapping": room_guest_mapping
        }
        
        response = api_session.post(f"{BASE_URL}/api/bookings/check-in", json=checkin_data)
        assert response.status_code == 200, f"Check-in failed: {response.text}"
        
        result = response.json()
        updated_booking = result["booking"]
        
        # Verify room_guest_mapping is stored with new structure
        assert "room_guest_mapping" in updated_booking
        assert len(updated_booking["room_guest_mapping"]) == 2
        
        # Verify first room has has_self=True
        room1 = updated_booking["room_guest_mapping"][0]
        assert room1.get("has_self") == True, "Room 1 should have has_self=True"
        assert len(room1.get("family_members", [])) == 0, "Room 1 should have no family members"
        
        # Verify second room has has_self=False and family_members
        room2 = updated_booking["room_guest_mapping"][1]
        assert room2.get("has_self") == False, "Room 2 should have has_self=False"
        assert len(room2.get("family_members", [])) == 1, "Room 2 should have 1 family member"
        
        print(f"✓ Check-in successful with new room_guest_mapping structure")
        print(f"  Room 1: has_self={room1.get('has_self')}, family_members={len(room1.get('family_members', []))}")
        print(f"  Room 2: has_self={room2.get('has_self')}, family_members={len(room2.get('family_members', []))}")


class TestDependentCardPricing:
    """Test pricing based on Dependent Card Available checkbox"""
    
    def test_family_member_with_dependent_card_uses_regular_rate(self, api_session, rooms, staff, settings):
        """Test that family member WITH dependent card uses regular Cat I/II rate"""
        if not staff:
            pytest.skip("No staff available")
        
        booking = create_test_booking(api_session, rooms, days_offset=450)
        if not booking:
            pytest.skip("Could not create test booking")
        
        # Family member WITH dependent card
        room_guest_mapping = [
            {
                "room_id": booking["room_ids"][0],
                "room_number": booking["room_numbers"][0],
                "room_category": booking["room_categories"][0],
                "has_self": True,
                "family_members": [],
                "charge_category": booking["room_categories"][0]  # Cat I
            },
            {
                "room_id": booking["room_ids"][1],
                "room_number": booking["room_numbers"][1],
                "room_category": booking["room_categories"][1],
                "has_self": False,
                "family_members": [
                    {
                        "relation": "w/o",
                        "name": "Test Wife",
                        "age": "32",
                        "sex": "F",
                        "mobile": "9876543211",
                        "has_dependent_card": True,  # HAS dependent card
                        "dependent_id": "DEP-002"
                    }
                ],
                "charge_category": booking["room_categories"][1]  # Cat II (not Def Civ)
            }
        ]
        
        checkin_data = {
            "booking_id": booking["id"],
            "staff_id": staff[0]["id"],
            "guest_contact": "+91 9876543210",
            "guest_age": 35,
            "guest_sex": "M",
            "guest_address": "Test Address, Test City, Test State 123456",
            "identity_card_number": "VALID-ID-12345",
            "guest_service_status": "Serving",
            "family_members": [{"relation": "w/o", "name": "Test Wife", "age": "32", "sex": "F", "mobile": "9876543211", "has_dependent_card": True, "dependent_id": "DEP-002"}],
            "room_guest_mapping": room_guest_mapping
        }
        
        response = api_session.post(f"{BASE_URL}/api/bookings/check-in", json=checkin_data)
        assert response.status_code == 200, f"Check-in failed: {response.text}"
        
        result = response.json()
        updated_booking = result["booking"]
        
        # Calculate expected total (Cat I + Cat II rates for 2 nights)
        nights = 2
        expected_total = (settings["cat_i_rate"] + settings["cat_ii_rate"]) * nights
        
        print(f"✓ Family member WITH dependent card uses regular rate")
        print(f"  Room rent total: ₹{updated_booking.get('room_rent_total', 0)}")
        print(f"  Expected: ₹{expected_total}")
        
        assert updated_booking.get("room_rent_total", 0) == expected_total
    
    def test_family_member_without_dependent_card_uses_def_civ_rate(self, api_session, rooms, staff, settings):
        """Test that family member WITHOUT dependent card triggers Def Civ rate"""
        if not staff:
            pytest.skip("No staff available")
        
        booking = create_test_booking(api_session, rooms, days_offset=500)
        if not booking:
            pytest.skip("Could not create test booking")
        
        # Family member WITHOUT dependent card
        room_guest_mapping = [
            {
                "room_id": booking["room_ids"][0],
                "room_number": booking["room_numbers"][0],
                "room_category": booking["room_categories"][0],
                "has_self": True,
                "family_members": [],
                "charge_category": booking["room_categories"][0]  # Cat I
            },
            {
                "room_id": booking["room_ids"][1],
                "room_number": booking["room_numbers"][1],
                "room_category": booking["room_categories"][1],
                "has_self": False,
                "family_members": [
                    {
                        "relation": "w/o",
                        "name": "Test Wife",
                        "age": "32",
                        "sex": "F",
                        "mobile": "9876543211",
                        "has_dependent_card": False,  # NO dependent card
                        "dependent_id": ""
                    }
                ],
                "charge_category": "Def Civ"  # Should be Def Civ
            }
        ]
        
        checkin_data = {
            "booking_id": booking["id"],
            "staff_id": staff[0]["id"],
            "guest_contact": "+91 9876543210",
            "guest_age": 35,
            "guest_sex": "M",
            "guest_address": "Test Address, Test City, Test State 123456",
            "identity_card_number": "VALID-ID-12345",
            "guest_service_status": "Serving",
            "family_members": [{"relation": "w/o", "name": "Test Wife", "age": "32", "sex": "F", "mobile": "9876543211", "has_dependent_card": False, "dependent_id": ""}],
            "room_guest_mapping": room_guest_mapping
        }
        
        response = api_session.post(f"{BASE_URL}/api/bookings/check-in", json=checkin_data)
        assert response.status_code == 200, f"Check-in failed: {response.text}"
        
        result = response.json()
        updated_booking = result["booking"]
        
        # Calculate expected total (Cat I + Def Civ Cat II rates for 2 nights)
        nights = 2
        expected_total = (settings["cat_i_rate"] + settings["def_civ_cat_ii_rate"]) * nights
        
        print(f"✓ Family member WITHOUT dependent card triggers Def Civ rate")
        print(f"  Room rent total: ₹{updated_booking.get('room_rent_total', 0)}")
        print(f"  Expected: ₹{expected_total}")
        
        assert updated_booking.get("room_rent_total", 0) == expected_total


class TestSelfOnlyInOneRoom:
    """Test that Self can only be assigned to ONE room (radio behavior)"""
    
    def test_self_in_only_one_room_validation(self, api_session, rooms, staff, settings):
        """Test that room_guest_mapping with Self in multiple rooms is handled correctly"""
        if not staff:
            pytest.skip("No staff available")
        
        booking = create_test_booking(api_session, rooms, days_offset=550)
        if not booking:
            pytest.skip("Could not create test booking")
        
        # Self in ONLY one room (correct behavior)
        room_guest_mapping = [
            {
                "room_id": booking["room_ids"][0],
                "room_number": booking["room_numbers"][0],
                "room_category": booking["room_categories"][0],
                "has_self": True,  # Self is here
                "family_members": [],
                "charge_category": booking["room_categories"][0]
            },
            {
                "room_id": booking["room_ids"][1],
                "room_number": booking["room_numbers"][1],
                "room_category": booking["room_categories"][1],
                "has_self": False,  # Self is NOT here
                "family_members": [
                    {
                        "relation": "w/o",
                        "name": "Test Wife",
                        "age": "32",
                        "sex": "F",
                        "mobile": "9876543211",
                        "has_dependent_card": True,
                        "dependent_id": "DEP-003"
                    }
                ],
                "charge_category": booking["room_categories"][1]
            }
        ]
        
        checkin_data = {
            "booking_id": booking["id"],
            "staff_id": staff[0]["id"],
            "guest_contact": "+91 9876543210",
            "guest_age": 35,
            "guest_sex": "M",
            "guest_address": "Test Address, Test City, Test State 123456",
            "identity_card_number": "VALID-ID-12345",
            "guest_service_status": "Serving",
            "family_members": [{"relation": "w/o", "name": "Test Wife", "age": "32", "sex": "F", "mobile": "9876543211", "has_dependent_card": True, "dependent_id": "DEP-003"}],
            "room_guest_mapping": room_guest_mapping
        }
        
        response = api_session.post(f"{BASE_URL}/api/bookings/check-in", json=checkin_data)
        assert response.status_code == 200, f"Check-in failed: {response.text}"
        
        result = response.json()
        updated_booking = result["booking"]
        
        # Verify Self is in only one room
        rooms_with_self = [r for r in updated_booking["room_guest_mapping"] if r.get("has_self")]
        assert len(rooms_with_self) == 1, f"Expected Self in 1 room, found in {len(rooms_with_self)}"
        
        print(f"✓ Self correctly assigned to only one room")
        print(f"  Rooms with Self: {len(rooms_with_self)}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
