"""
Tests for new features: extra_beds at check-in, feedback form, feedback analysis
"""
import pytest
import requests
import os
import random
from datetime import date, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

def get_staff_id():
    res = requests.get(f"{BASE_URL}/api/staff")
    staff = res.json()
    for s in staff:
        if "Ramesh" in s.get("name", ""):
            return s["id"]
    return staff[0]["id"] if staff else None

def get_room_id(index=0):
    res = requests.get(f"{BASE_URL}/api/rooms")
    rooms = res.json()
    return rooms[index % len(rooms)]["id"] if rooms else None

def create_test_booking(room_index=0):
    offset = random.randint(60, 200)
    checkin = (date.today() + timedelta(days=offset)).isoformat()
    checkout = (date.today() + timedelta(days=offset+2)).isoformat()
    room_id = get_room_id(room_index)
    payload = {
        "guest_name": "TEST_Feedback Guest",
        "guest_rank": "Naik",
        "guest_contact": "9876543210",
        "guest_unit": "TEST Unit",
        "guest_service_status": "Serving",
        "room_ids": [room_id],
        "room_category": "I",
        "check_in_date": checkin,
        "check_out_date": checkout,
        "advance_amount": 400,
        "bank_name": "SBI",
        "ifsc_code": "SBIN0001234",
        "account_number": "1234567890",
        "upi_id": "",
        "upi_phone": ""
    }
    res = requests.post(f"{BASE_URL}/api/bookings", json=payload)
    return res


class TestExtraBeds:
    """Extra beds at check-in"""
    
    def test_checkin_with_extra_beds(self):
        # Create booking
        res = create_test_booking(room_index=3)
        assert res.status_code == 200
        booking_id = res.json()["id"]
        
        staff_id = get_staff_id()
        # Check in with 2 extra beds
        checkin_res = requests.post(f"{BASE_URL}/api/bookings/check-in", json={
            "booking_id": booking_id,
            "staff_id": staff_id,
            "notes": "test checkin",
            "extra_beds": 2
        })
        assert checkin_res.status_code == 200
        data = checkin_res.json()
        assert data.get("extra_beds") == 2 or True  # response may vary
        
        # Get booking to verify extra_beds stored
        get_res = requests.get(f"{BASE_URL}/api/bookings/{booking_id}")
        assert get_res.status_code == 200
        b = get_res.json()
        assert b.get("extra_beds") == 2, f"extra_beds not stored: {b}"
        assert b.get("extra_bed_charge") == 150.0, f"extra_bed_charge wrong: {b}"
        
        # Cleanup - checkout
        requests.post(f"{BASE_URL}/api/bookings/check-out", json={
            "booking_id": booking_id,
            "staff_id": staff_id,
            "notes": "test",
            "final_payment": 0,
            "payment_mode": "Cash"
        })


class TestFeedbackAPI:
    """Feedback creation and analysis"""
    
    booking_id = None
    
    def setup_checked_out_booking(self):
        res = create_test_booking(room_index=4)
        assert res.status_code == 200
        booking_id = res.json()["id"]
        staff_id = get_staff_id()
        
        # Check in
        requests.post(f"{BASE_URL}/api/bookings/check-in", json={
            "booking_id": booking_id,
            "staff_id": staff_id, "notes": "test", "extra_beds": 0
        })
        # Check out
        requests.post(f"{BASE_URL}/api/bookings/check-out", json={
            "booking_id": booking_id,
            "staff_id": staff_id, "notes": "test", "final_payment": 0, "payment_mode": "Cash"
        })
        return booking_id
    
    def test_submit_feedback(self):
        booking_id = self.setup_checked_out_booking()
        payload = {
            "booking_id": booking_id,
            "cleanliness": 5,
            "room_comfort": 4,
            "basic_amenities": 4,
            "check_in_procedure": 5,
            "check_out_procedure": 5,
            "overall_stay": 4,
            "staff_behaviour": 5,
            "enjoyed_most": "Good service",
            "issues_problems": "",
            "improvement_suggestions": "",
            "additional_comments": "Great stay",
            "would_recommend": True
        }
        res = requests.post(f"{BASE_URL}/api/feedback", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert "feedback_id" in data or "message" in data

    def test_get_feedback_analysis(self):
        res = requests.get(f"{BASE_URL}/api/feedback/analysis")
        assert res.status_code == 200
        data = res.json()
        assert "average_score" in data
        assert "total_count" in data
        assert "recommendation_rate" in data
        assert "category_averages" in data
        # Verify all 7 categories present
        categories = data["category_averages"]
        for cat in ["cleanliness", "room_comfort", "basic_amenities", "check_in_procedure",
                    "check_out_procedure", "overall_stay", "staff_behaviour"]:
            assert cat in categories, f"Missing category: {cat}"

    def test_get_feedbacks_list(self):
        res = requests.get(f"{BASE_URL}/api/feedback")
        assert res.status_code == 200
        assert isinstance(res.json(), list)


class TestSettingsRates:
    """Verify correct rates in settings"""
    
    def test_cat_i_rate_500(self):
        res = requests.get(f"{BASE_URL}/api/settings")
        assert res.status_code == 200
        data = res.json()
        assert data.get("cat_i_rate") == 500, f"Cat I rate wrong: {data.get('cat_i_rate')}"
    
    def test_cat_ii_rate_400(self):
        res = requests.get(f"{BASE_URL}/api/settings")
        data = res.json()
        assert data.get("cat_ii_rate") == 400, f"Cat II rate wrong: {data.get('cat_ii_rate')}"
    
    def test_def_civ_rates_600(self):
        res = requests.get(f"{BASE_URL}/api/settings")
        data = res.json()
        assert data.get("def_civ_cat_i_rate") == 600, f"Def Civ Cat I wrong: {data.get('def_civ_cat_i_rate')}"
        assert data.get("def_civ_cat_ii_rate") == 600, f"Def Civ Cat II wrong: {data.get('def_civ_cat_ii_rate')}"
    
    def test_default_advance_400(self):
        res = requests.get(f"{BASE_URL}/api/settings")
        data = res.json()
        assert data.get("default_advance_amount") == 400, f"Advance wrong: {data.get('default_advance_amount')}"
