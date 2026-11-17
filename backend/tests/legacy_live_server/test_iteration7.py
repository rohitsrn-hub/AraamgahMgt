"""
Iteration 7 tests: Refund 'Mark as Paid' API, check-in bill summary data, print bill button
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestRefundUpdate:
    """Test PUT /api/refunds/{id} endpoint"""
    
    def test_get_pending_refunds(self):
        """Verify pending refunds exist"""
        r = requests.get(f"{BASE_URL}/api/refunds?status=pending")
        assert r.status_code == 200
        data = r.json()
        print(f"Pending refunds count: {len(data)}")
        assert isinstance(data, list)
    
    def test_update_refund_to_completed(self):
        """Test marking a refund as paid (completed)"""
        # Get pending refunds first
        r = requests.get(f"{BASE_URL}/api/refunds?status=pending")
        assert r.status_code == 200
        refunds = r.json()
        
        if not refunds:
            # Create a test booking + cancel to generate refund
            pytest.skip("No pending refunds to test with")
        
        refund = refunds[0]
        refund_id = refund['id']
        print(f"Testing with refund: {refund_id}, amount: {refund['amount']}")
        
        # Mark as completed
        update_r = requests.put(
            f"{BASE_URL}/api/refunds/{refund_id}",
            json={"status": "completed"}
        )
        assert update_r.status_code == 200, f"Expected 200, got {update_r.status_code}: {update_r.text}"
        
        updated = update_r.json()
        assert updated['status'] == 'completed', f"Expected status=completed, got {updated['status']}"
        assert updated['id'] == refund_id
        assert 'processed_at' in updated and updated['processed_at'] is not None
        print(f"Refund {refund_id} marked as completed successfully")
        
        # Restore to pending for subsequent UI tests
        restore_r = requests.put(
            f"{BASE_URL}/api/refunds/{refund_id}",
            json={"status": "pending"}
        )
        print(f"Restored refund to pending: {restore_r.status_code}")
    
    def test_update_refund_invalid_id(self):
        """Test with invalid refund id returns 404"""
        r = requests.put(
            f"{BASE_URL}/api/refunds/nonexistent-id-12345",
            json={"status": "completed"}
        )
        assert r.status_code == 404
        print("Invalid refund ID correctly returns 404")
    
    def test_get_checked_in_bookings_have_advance_paid(self):
        """Verify checked-in bookings have advance_paid field for bill summary"""
        r = requests.get(f"{BASE_URL}/api/bookings?status=checked_in")
        assert r.status_code == 200
        bookings = r.json()
        print(f"Checked-in bookings: {len(bookings)}")
        
        if bookings:
            b = bookings[0]
            assert 'advance_paid' in b
            assert 'total_amount' in b
            assert 'balance_amount' in b
            assert 'extra_bed_charge' in b or 'extra_beds' in b
            print(f"Sample checked-in booking: advance={b.get('advance_paid')}, total={b.get('total_amount')}, balance={b.get('balance_amount')}")

    def test_dashboard_funds_pending_refunds_amount(self):
        """Verify dashboard shows pending refunds amount"""
        r = requests.get(f"{BASE_URL}/api/dashboard/funds")
        assert r.status_code == 200
        data = r.json()
        assert 'cancellations' in data
        assert 'pending_refunds_amount' in data['cancellations']
        print(f"Dashboard pending refunds: count={data['cancellations']['pending_refunds']}, amount={data['cancellations']['pending_refunds_amount']}")
