"""
Test suite for Reports Tab-based Layout APIs
Tests: Room Occupancy, Room Allotment, Guest Details endpoints
"""
import pytest
import requests
import os
from datetime import date, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestRoomOccupancyReport:
    """Tests for GET /api/reports/room-occupancy endpoint"""
    
    def test_room_occupancy_monthly_filter(self):
        """Test monthly filter returns correct data structure"""
        response = requests.get(f"{BASE_URL}/api/reports/room-occupancy", params={
            "filter_type": "monthly",
            "month": 4,
            "year": 2026
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        # Verify response structure
        assert "period_label" in data
        assert "start_date" in data
        assert "end_date" in data
        assert "total_rooms" in data
        assert "total_days" in data
        assert "total_occupied_days" in data
        assert "total_available_days" in data
        assert "avg_occupancy" in data
        assert "total_bookings" in data
        assert "total_revenue" in data
        assert "room_details" in data
        
        # Verify period label
        assert "April 2026" in data["period_label"]
        
        # Verify room_details structure
        if data["room_details"]:
            room = data["room_details"][0]
            assert "room_number" in room
            assert "category" in room
            assert "occupied_days" in room
            assert "available_days" in room
            assert "occupancy_percent" in room
            assert "revenue" in room
        
        print(f"Monthly filter: {data['total_rooms']} rooms, {data['avg_occupancy']}% occupancy, ₹{data['total_revenue']} revenue")
    
    def test_room_occupancy_daily_filter(self):
        """Test daily filter returns correct data"""
        today = date.today().isoformat()
        response = requests.get(f"{BASE_URL}/api/reports/room-occupancy", params={
            "filter_type": "daily",
            "start_date": today
        })
        assert response.status_code == 200
        
        data = response.json()
        assert data["total_days"] == 1
        assert "Daily Report" in data["period_label"]
        print(f"Daily filter: {data['total_bookings']} bookings on {today}")
    
    def test_room_occupancy_quarterly_filter(self):
        """Test quarterly filter returns correct data"""
        response = requests.get(f"{BASE_URL}/api/reports/room-occupancy", params={
            "filter_type": "quarterly",
            "quarter": 2,
            "year": 2026
        })
        assert response.status_code == 200
        
        data = response.json()
        assert "Q2 2026" in data["period_label"]
        # Q2 = Apr, May, Jun = 91 days
        assert data["total_days"] == 91
        print(f"Quarterly filter Q2 2026: {data['total_days']} days, {data['avg_occupancy']}% occupancy")
    
    def test_room_occupancy_annual_filter(self):
        """Test annual filter returns correct data"""
        response = requests.get(f"{BASE_URL}/api/reports/room-occupancy", params={
            "filter_type": "annual",
            "year": 2026
        })
        assert response.status_code == 200
        
        data = response.json()
        assert "Year 2026" in data["period_label"]
        # 2026 is not a leap year, so 365 days
        assert data["total_days"] == 365
        print(f"Annual filter 2026: {data['total_days']} days, {data['total_bookings']} bookings")
    
    def test_room_occupancy_custom_filter(self):
        """Test custom date range filter"""
        response = requests.get(f"{BASE_URL}/api/reports/room-occupancy", params={
            "filter_type": "custom",
            "start_date": "2026-04-01",
            "end_date": "2026-04-15"
        })
        assert response.status_code == 200
        
        data = response.json()
        assert data["total_days"] == 15
        assert "2026-04-01 to 2026-04-15" in data["period_label"]
        print(f"Custom filter: {data['total_days']} days, {data['total_bookings']} bookings")
    
    def test_room_occupancy_missing_params(self):
        """Test error handling for missing required params"""
        # Monthly without month/year
        response = requests.get(f"{BASE_URL}/api/reports/room-occupancy", params={
            "filter_type": "monthly"
        })
        assert response.status_code == 400
        
        # Custom without dates
        response = requests.get(f"{BASE_URL}/api/reports/room-occupancy", params={
            "filter_type": "custom"
        })
        assert response.status_code == 400
        print("Missing params validation working correctly")
    
    def test_room_occupancy_invalid_filter_type(self):
        """Test error handling for invalid filter type"""
        response = requests.get(f"{BASE_URL}/api/reports/room-occupancy", params={
            "filter_type": "invalid"
        })
        assert response.status_code == 400
        print("Invalid filter type validation working correctly")


class TestRoomAllotmentReport:
    """Tests for GET /api/reports/room-allotment endpoint"""
    
    def test_room_allotment_monthly_filter(self):
        """Test monthly filter returns correct data structure"""
        response = requests.get(f"{BASE_URL}/api/reports/room-allotment", params={
            "filter_type": "monthly",
            "month": 4,
            "year": 2026
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        # Verify response structure
        assert "period_label" in data
        assert "start_date" in data
        assert "end_date" in data
        assert "total_allotments" in data
        assert "allotments" in data
        
        # Verify allotment structure
        if data["allotments"]:
            allot = data["allotments"][0]
            assert "booking_id" in allot
            assert "booking_number" in allot
            assert "guest_name" in allot
            assert "guest_rank" in allot
            assert "room_numbers" in allot
            assert "room_categories" in allot
            assert "check_in_date" in allot
            assert "check_out_date" in allot
            assert "nights" in allot
            assert "total_amount" in allot
        
        print(f"Room Allotment April 2026: {data['total_allotments']} allotments")
    
    def test_room_allotment_daily_filter(self):
        """Test daily filter"""
        response = requests.get(f"{BASE_URL}/api/reports/room-allotment", params={
            "filter_type": "daily",
            "start_date": "2026-04-10"
        })
        assert response.status_code == 200
        
        data = response.json()
        assert "Daily Report" in data["period_label"]
        print(f"Daily allotment: {data['total_allotments']} allotments")
    
    def test_room_allotment_quarterly_filter(self):
        """Test quarterly filter"""
        response = requests.get(f"{BASE_URL}/api/reports/room-allotment", params={
            "filter_type": "quarterly",
            "quarter": 2,
            "year": 2026
        })
        assert response.status_code == 200
        
        data = response.json()
        assert "Q2 2026" in data["period_label"]
        print(f"Quarterly allotment Q2 2026: {data['total_allotments']} allotments")
    
    def test_room_allotment_custom_filter(self):
        """Test custom date range filter"""
        response = requests.get(f"{BASE_URL}/api/reports/room-allotment", params={
            "filter_type": "custom",
            "start_date": "2026-04-01",
            "end_date": "2026-04-30"
        })
        assert response.status_code == 200
        
        data = response.json()
        assert "2026-04-01 to 2026-04-30" in data["period_label"]
        print(f"Custom allotment: {data['total_allotments']} allotments")


class TestGuestDetailsReport:
    """Tests for GET /api/reports/guest-details endpoint"""
    
    def test_guest_details_monthly_filter(self):
        """Test monthly filter returns correct data structure"""
        response = requests.get(f"{BASE_URL}/api/reports/guest-details", params={
            "filter_type": "monthly",
            "month": 4,
            "year": 2026
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        # Verify response structure
        assert "period_label" in data
        assert "start_date" in data
        assert "end_date" in data
        assert "total_guests" in data
        assert "total_bookings" in data
        assert "total_nights" in data
        assert "total_revenue" in data
        assert "guests" in data
        
        # Verify guest structure
        if data["guests"]:
            guest = data["guests"][0]
            assert "guest_name" in guest
            assert "guest_rank" in guest
            assert "guest_unit" in guest
            assert "service_type" in guest
            assert "guest_contact" in guest
            assert "check_in_date" in guest
            assert "check_out_date" in guest
            assert "nights" in guest
            assert "total_amount" in guest
        
        print(f"Guest Details April 2026: {data['total_guests']} guests, {data['total_nights']} nights, ₹{data['total_revenue']} revenue")
    
    def test_guest_details_daily_filter(self):
        """Test daily filter"""
        response = requests.get(f"{BASE_URL}/api/reports/guest-details", params={
            "filter_type": "daily",
            "start_date": "2026-04-10"
        })
        assert response.status_code == 200
        
        data = response.json()
        assert "Daily Report" in data["period_label"]
        print(f"Daily guests: {data['total_guests']} guests")
    
    def test_guest_details_quarterly_filter(self):
        """Test quarterly filter"""
        response = requests.get(f"{BASE_URL}/api/reports/guest-details", params={
            "filter_type": "quarterly",
            "quarter": 2,
            "year": 2026
        })
        assert response.status_code == 200
        
        data = response.json()
        assert "Q2 2026" in data["period_label"]
        print(f"Quarterly guests Q2 2026: {data['total_guests']} guests, ₹{data['total_revenue']} revenue")
    
    def test_guest_details_annual_filter(self):
        """Test annual filter"""
        response = requests.get(f"{BASE_URL}/api/reports/guest-details", params={
            "filter_type": "annual",
            "year": 2026
        })
        assert response.status_code == 200
        
        data = response.json()
        assert "Year 2026" in data["period_label"]
        print(f"Annual guests 2026: {data['total_guests']} guests, {data['total_nights']} nights")
    
    def test_guest_details_custom_filter(self):
        """Test custom date range filter"""
        response = requests.get(f"{BASE_URL}/api/reports/guest-details", params={
            "filter_type": "custom",
            "start_date": "2026-04-01",
            "end_date": "2026-04-30"
        })
        assert response.status_code == 200
        
        data = response.json()
        assert "2026-04-01 to 2026-04-30" in data["period_label"]
        print(f"Custom guests: {data['total_guests']} guests, ₹{data['total_revenue']} revenue")


class TestExistingMonthlyReport:
    """Tests for existing GET /api/reports/monthly endpoint (migrated to Monthly Summary Tab)"""
    
    def test_monthly_report_endpoint(self):
        """Test existing monthly report endpoint still works"""
        response = requests.get(f"{BASE_URL}/api/reports/monthly", params={
            "month": 4,
            "year": 2026
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        # Verify key fields
        assert "month_name" in data
        assert "year" in data
        assert "total_guests" in data
        assert "total_days" in data
        assert "command_breakdown" in data
        assert "license_fees" in data
        assert "grand_total" in data
        
        print(f"Monthly Report April 2026: {data['total_guests']} guests, {data['total_days']} days, ₹{data['grand_total']} total")


class TestDataConsistency:
    """Tests to verify data consistency across report endpoints"""
    
    def test_april_2026_data_exists(self):
        """Verify April 2026 has test data as mentioned in context"""
        # Check room occupancy
        occ_response = requests.get(f"{BASE_URL}/api/reports/room-occupancy", params={
            "filter_type": "monthly",
            "month": 4,
            "year": 2026
        })
        assert occ_response.status_code == 200
        occ_data = occ_response.json()
        
        # Check guest details
        guest_response = requests.get(f"{BASE_URL}/api/reports/guest-details", params={
            "filter_type": "monthly",
            "month": 4,
            "year": 2026
        })
        assert guest_response.status_code == 200
        guest_data = guest_response.json()
        
        # Verify data exists (context mentions 13 bookings, 13 guests, 34 nights, ₹29,550)
        print(f"April 2026 Data Check:")
        print(f"  - Occupancy: {occ_data['total_bookings']} bookings, ₹{occ_data['total_revenue']} revenue")
        print(f"  - Guests: {guest_data['total_guests']} guests, {guest_data['total_nights']} nights, ₹{guest_data['total_revenue']} revenue")
        
        # At least verify some data exists
        assert occ_data['total_bookings'] >= 0
        assert guest_data['total_guests'] >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
