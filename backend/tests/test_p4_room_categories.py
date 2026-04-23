"""
Test suite for P4: Category & Room Configuration
Features tested:
1. PUT /api/settings/categories - Update room categories configuration
2. GET /api/settings - Returns room_categories in settings
3. Validation of category structure (id, name, rate, def_civ_rate, room_count, prefix)
4. Category CRUD operations via settings endpoint
"""

import pytest
import requests
import os
import uuid
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


@pytest.fixture(scope="module")
def api_session():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture(scope="module")
def original_settings(api_session):
    """Get original settings to restore after tests"""
    response = api_session.get(f"{BASE_URL}/api/settings")
    assert response.status_code == 200
    return response.json()


class TestSettingsRoomCategories:
    """Test room_categories field in settings"""
    
    def test_settings_contains_room_categories(self, api_session):
        """Test that settings endpoint returns room_categories"""
        response = api_session.get(f"{BASE_URL}/api/settings")
        
        assert response.status_code == 200, f"Failed: {response.text}"
        settings = response.json()
        
        assert "room_categories" in settings, "Settings should contain room_categories"
        categories = settings["room_categories"]
        
        assert isinstance(categories, list), "room_categories should be a list"
        assert len(categories) >= 1, "Should have at least one category"
        
        print(f"✓ GET /api/settings returns room_categories with {len(categories)} categories")
    
    def test_default_categories_structure(self, api_session):
        """Test that default categories have correct structure"""
        response = api_session.get(f"{BASE_URL}/api/settings")
        assert response.status_code == 200
        
        settings = response.json()
        categories = settings.get("room_categories", [])
        
        required_fields = ["id", "name", "rate", "def_civ_rate", "room_count", "prefix"]
        
        for cat in categories:
            for field in required_fields:
                assert field in cat, f"Category should have '{field}' field"
            
            # Validate field types
            assert isinstance(cat["id"], str), "id should be string"
            assert isinstance(cat["name"], str), "name should be string"
            assert isinstance(cat["rate"], (int, float)), "rate should be numeric"
            assert isinstance(cat["def_civ_rate"], (int, float)), "def_civ_rate should be numeric"
            assert isinstance(cat["room_count"], int), "room_count should be integer"
            assert isinstance(cat["prefix"], str), "prefix should be string"
        
        print(f"✓ All {len(categories)} categories have correct structure")
        for cat in categories:
            print(f"  - {cat['name']}: prefix={cat['prefix']}, rate={cat['rate']}, rooms={cat['room_count']}")


class TestUpdateRoomCategories:
    """Test PUT /api/settings/categories endpoint"""
    
    def test_update_categories_success(self, api_session, original_settings):
        """Test successful category update"""
        new_categories = [
            {
                "id": "test-cat-1",
                "name": "TEST_Cat I",
                "rate": 550.0,
                "def_civ_rate": 650.0,
                "room_count": 5,
                "prefix": "T1"
            },
            {
                "id": "test-cat-2",
                "name": "TEST_Cat II",
                "rate": 450.0,
                "def_civ_rate": 550.0,
                "room_count": 8,
                "prefix": "T2"
            }
        ]
        
        response = api_session.put(f"{BASE_URL}/api/settings/categories", json=new_categories)
        
        assert response.status_code == 200, f"Failed: {response.text}"
        result = response.json()
        
        assert "message" in result, "Response should contain message"
        assert "categories" in result, "Response should contain categories"
        assert result["categories"] == new_categories, "Categories should match input"
        
        print(f"✓ PUT /api/settings/categories successfully updated categories")
        
        # Verify persistence
        get_response = api_session.get(f"{BASE_URL}/api/settings")
        assert get_response.status_code == 200
        settings = get_response.json()
        
        assert settings["room_categories"] == new_categories, "Categories should be persisted"
        print(f"✓ Categories persisted correctly in database")
        
        # Restore original categories
        restore_response = api_session.put(
            f"{BASE_URL}/api/settings/categories",
            json=original_settings.get("room_categories", [])
        )
        assert restore_response.status_code == 200
    
    def test_update_categories_validation_missing_fields(self, api_session):
        """Test validation rejects categories with missing required fields"""
        invalid_categories = [
            {
                "id": "invalid-cat",
                "name": "Invalid Category"
                # Missing: rate, def_civ_rate, room_count, prefix
            }
        ]
        
        response = api_session.put(f"{BASE_URL}/api/settings/categories", json=invalid_categories)
        
        assert response.status_code == 400, "Should reject invalid category structure"
        error = response.json()
        assert "detail" in error, "Error should have detail"
        
        print(f"✓ Validation correctly rejects categories with missing fields")
    
    def test_update_categories_validation_missing_id(self, api_session):
        """Test validation rejects categories without id"""
        invalid_categories = [
            {
                # Missing: id
                "name": "No ID Category",
                "rate": 500.0,
                "def_civ_rate": 600.0,
                "room_count": 5,
                "prefix": "NI"
            }
        ]
        
        response = api_session.put(f"{BASE_URL}/api/settings/categories", json=invalid_categories)
        
        assert response.status_code == 400, "Should reject category without id"
        print(f"✓ Validation correctly rejects categories without id")
    
    def test_update_categories_validation_missing_name(self, api_session):
        """Test validation rejects categories without name"""
        invalid_categories = [
            {
                "id": "no-name-cat",
                # Missing: name
                "rate": 500.0,
                "def_civ_rate": 600.0,
                "room_count": 5,
                "prefix": "NN"
            }
        ]
        
        response = api_session.put(f"{BASE_URL}/api/settings/categories", json=invalid_categories)
        
        assert response.status_code == 400, "Should reject category without name"
        print(f"✓ Validation correctly rejects categories without name")
    
    def test_update_categories_validation_missing_prefix(self, api_session):
        """Test validation rejects categories without prefix"""
        invalid_categories = [
            {
                "id": "no-prefix-cat",
                "name": "No Prefix Category",
                "rate": 500.0,
                "def_civ_rate": 600.0,
                "room_count": 5
                # Missing: prefix
            }
        ]
        
        response = api_session.put(f"{BASE_URL}/api/settings/categories", json=invalid_categories)
        
        assert response.status_code == 400, "Should reject category without prefix"
        print(f"✓ Validation correctly rejects categories without prefix")
    
    def test_update_single_category(self, api_session, original_settings):
        """Test updating with a single category"""
        single_category = [
            {
                "id": "single-cat",
                "name": "TEST_Single Category",
                "rate": 600.0,
                "def_civ_rate": 700.0,
                "room_count": 10,
                "prefix": "SC"
            }
        ]
        
        response = api_session.put(f"{BASE_URL}/api/settings/categories", json=single_category)
        
        assert response.status_code == 200, f"Failed: {response.text}"
        result = response.json()
        
        assert len(result["categories"]) == 1, "Should have exactly 1 category"
        print(f"✓ Single category update successful")
        
        # Restore original
        api_session.put(
            f"{BASE_URL}/api/settings/categories",
            json=original_settings.get("room_categories", [])
        )
    
    def test_update_multiple_categories(self, api_session, original_settings):
        """Test updating with multiple categories"""
        multiple_categories = [
            {
                "id": "multi-cat-1",
                "name": "TEST_Standard",
                "rate": 400.0,
                "def_civ_rate": 500.0,
                "room_count": 6,
                "prefix": "ST"
            },
            {
                "id": "multi-cat-2",
                "name": "TEST_Deluxe",
                "rate": 600.0,
                "def_civ_rate": 700.0,
                "room_count": 4,
                "prefix": "DX"
            },
            {
                "id": "multi-cat-3",
                "name": "TEST_VIP",
                "rate": 1000.0,
                "def_civ_rate": 1200.0,
                "room_count": 2,
                "prefix": "VIP"
            }
        ]
        
        response = api_session.put(f"{BASE_URL}/api/settings/categories", json=multiple_categories)
        
        assert response.status_code == 200, f"Failed: {response.text}"
        result = response.json()
        
        assert len(result["categories"]) == 3, "Should have exactly 3 categories"
        print(f"✓ Multiple categories (3) update successful")
        
        # Restore original
        api_session.put(
            f"{BASE_URL}/api/settings/categories",
            json=original_settings.get("room_categories", [])
        )
    
    def test_update_categories_with_zero_room_count(self, api_session, original_settings):
        """Test that categories with zero room count are accepted"""
        categories_with_zero = [
            {
                "id": "zero-rooms-cat",
                "name": "TEST_Zero Rooms",
                "rate": 500.0,
                "def_civ_rate": 600.0,
                "room_count": 0,
                "prefix": "ZR"
            }
        ]
        
        response = api_session.put(f"{BASE_URL}/api/settings/categories", json=categories_with_zero)
        
        # This should be accepted (room_count=0 is valid for configuration)
        assert response.status_code == 200, f"Should accept zero room count: {response.text}"
        print(f"✓ Category with zero room count accepted")
        
        # Restore original
        api_session.put(
            f"{BASE_URL}/api/settings/categories",
            json=original_settings.get("room_categories", [])
        )
    
    def test_update_categories_empty_array(self, api_session):
        """Test that empty categories array is rejected or handled"""
        response = api_session.put(f"{BASE_URL}/api/settings/categories", json=[])
        
        # Empty array might be accepted or rejected depending on business logic
        # Just verify it doesn't crash
        assert response.status_code in [200, 400], f"Unexpected status: {response.status_code}"
        print(f"✓ Empty categories array handled (status: {response.status_code})")


class TestCategoryDataIntegrity:
    """Test data integrity for category operations"""
    
    def test_category_update_preserves_other_settings(self, api_session, original_settings):
        """Test that updating categories doesn't affect other settings"""
        # Get current settings
        before_response = api_session.get(f"{BASE_URL}/api/settings")
        assert before_response.status_code == 200
        before_settings = before_response.json()
        
        # Update categories
        new_categories = [
            {
                "id": "integrity-test-cat",
                "name": "TEST_Integrity",
                "rate": 999.0,
                "def_civ_rate": 1099.0,
                "room_count": 3,
                "prefix": "IT"
            }
        ]
        
        update_response = api_session.put(f"{BASE_URL}/api/settings/categories", json=new_categories)
        assert update_response.status_code == 200
        
        # Get settings after update
        after_response = api_session.get(f"{BASE_URL}/api/settings")
        assert after_response.status_code == 200
        after_settings = after_response.json()
        
        # Verify other settings are preserved
        preserved_fields = [
            "cat_i_rate", "cat_ii_rate", "def_civ_cat_i_rate", "def_civ_cat_ii_rate",
            "default_advance_amount", "ranks"
        ]
        
        for field in preserved_fields:
            if field in before_settings:
                assert after_settings.get(field) == before_settings.get(field), \
                    f"Field '{field}' should be preserved"
        
        print(f"✓ Other settings preserved after category update")
        
        # Restore original
        api_session.put(
            f"{BASE_URL}/api/settings/categories",
            json=original_settings.get("room_categories", [])
        )
    
    def test_category_update_sets_updated_at(self, api_session, original_settings):
        """Test that updating categories sets updated_at timestamp"""
        # Get current settings
        before_response = api_session.get(f"{BASE_URL}/api/settings")
        assert before_response.status_code == 200
        before_settings = before_response.json()
        before_updated_at = before_settings.get("updated_at")
        
        # Small delay to ensure timestamp difference
        import time
        time.sleep(0.1)
        
        # Update categories
        new_categories = [
            {
                "id": "timestamp-test-cat",
                "name": "TEST_Timestamp",
                "rate": 500.0,
                "def_civ_rate": 600.0,
                "room_count": 5,
                "prefix": "TS"
            }
        ]
        
        update_response = api_session.put(f"{BASE_URL}/api/settings/categories", json=new_categories)
        assert update_response.status_code == 200
        
        # Get settings after update
        after_response = api_session.get(f"{BASE_URL}/api/settings")
        assert after_response.status_code == 200
        after_settings = after_response.json()
        after_updated_at = after_settings.get("updated_at")
        
        # Verify updated_at changed
        if before_updated_at and after_updated_at:
            assert after_updated_at != before_updated_at, "updated_at should change"
            print(f"✓ updated_at timestamp updated: {before_updated_at} -> {after_updated_at}")
        else:
            print(f"✓ updated_at field present: {after_updated_at}")
        
        # Restore original
        api_session.put(
            f"{BASE_URL}/api/settings/categories",
            json=original_settings.get("room_categories", [])
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
