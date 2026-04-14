#!/usr/bin/env python3
"""
Script to update room rates in settings
Run this to fix incorrect room rates in database
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
import sys
from pathlib import Path

# Add parent directory to path to import from backend
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

async def update_room_rates():
    """Update room rates to correct default values"""
    
    # Connect to MongoDB
    mongo_url = os.environ.get('MONGO_URL')
    db_name = os.environ.get('DB_NAME')
    
    if not mongo_url or not db_name:
        print("❌ MONGO_URL or DB_NAME not set in environment")
        return
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    print(f"📊 Connected to database: {db_name}")
    
    # Check current settings
    current_settings = await db.settings.find_one({}, {'_id': 0})
    
    if current_settings:
        print("\n📋 Current Settings:")
        print(f"  Org Cat I Rate: ₹{current_settings.get('cat_i_rate', 'NOT SET')}")
        print(f"  Org Cat II Rate: ₹{current_settings.get('cat_ii_rate', 'NOT SET')}")
        print(f"  Non-Org Cat I Rate: ₹{current_settings.get('def_civ_cat_i_rate', 'NOT SET')}")
        print(f"  Non-Org Cat II Rate: ₹{current_settings.get('def_civ_cat_ii_rate', 'NOT SET')}")
        print(f"  Default Advance: ₹{current_settings.get('default_advance_amount', 'NOT SET')}")
    else:
        print("\n⚠️  No settings found in database")
    
    # New correct values
    new_values = {
        "cat_i_rate": 500.0,  # Org Cat I
        "cat_ii_rate": 400.0,  # Org Cat II
        "def_civ_cat_i_rate": 600.0,  # Non-Org Cat I
        "def_civ_cat_ii_rate": 600.0,  # Non-Org Cat II
        "default_advance_amount": 400.0  # Fixed advance
    }
    
    print("\n✅ Updating to correct values:")
    print(f"  Org Cat I Rate: ₹{new_values['cat_i_rate']}")
    print(f"  Org Cat II Rate: ₹{new_values['cat_ii_rate']}")
    print(f"  Non-Org Cat I Rate: ₹{new_values['def_civ_cat_i_rate']}")
    print(f"  Non-Org Cat II Rate: ₹{new_values['def_civ_cat_ii_rate']}")
    print(f"  Default Advance: ₹{new_values['default_advance_amount']}")
    
    # Update settings
    result = await db.settings.update_one(
        {},
        {"$set": new_values},
        upsert=True
    )
    
    if result.modified_count > 0 or result.upserted_id:
        print("\n🎉 Settings updated successfully!")
    else:
        print("\n✓ Settings already have correct values")
    
    # Verify update
    updated_settings = await db.settings.find_one({}, {'_id': 0})
    print("\n📋 Verified Settings After Update:")
    print(f"  Org Cat I Rate: ₹{updated_settings.get('cat_i_rate')}")
    print(f"  Org Cat II Rate: ₹{updated_settings.get('cat_ii_rate')}")
    print(f"  Non-Org Cat I Rate: ₹{updated_settings.get('def_civ_cat_i_rate')}")
    print(f"  Non-Org Cat II Rate: ₹{updated_settings.get('def_civ_cat_ii_rate')}")
    print(f"  Default Advance: ₹{updated_settings.get('default_advance_amount')}")
    
    client.close()
    print("\n✅ Done! Room rates have been updated.")
    print("\n📝 Note: Refresh your browser to see the changes in the booking form.")

if __name__ == "__main__":
    print("🔧 SARAI Room Rate Update Script")
    print("=" * 50)
    asyncio.run(update_room_rates())
