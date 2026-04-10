"""
SECURITY: Database Sanitization Script
Removes all defense-related data and converts to Org/Non-Org system
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
ROOT_DIR = Path(__file__).parent.parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Color categories for organization system
COLORS = [
    "Red", "Green", "Brown", "Orange", "Yellow",
    "Violet", "Black", "Blue", "White", "Light Blue"
]

async def sanitize_database():
    """
    Remove all defense data and convert to Org/Non-Org system
    
    Mapping Logic:
    - rank != "Def Civ" → is_org = true, org_color = null (to be filled at checkout)
    - rank == "Def Civ" → is_org = false, org_color = null
    
    Removes:
    - rank, army_number, unit, command_hq, service_type
    - identity_card_number, serving_status
    
    Adds:
    - is_org (boolean)
    - org_color (string, nullable)
    
    Family members:
    - Renames dependent_id → org_id
    """
    
    print("🔒 DATABASE SANITIZATION - SECURITY OPERATION")
    print("=" * 60)
    print()
    
    # Step 1: Sanitize bookings collection
    print("📊 Step 1: Sanitizing bookings collection...")
    bookings = await db.bookings.find({}).to_list(5000)
    
    sanitized_count = 0
    org_count = 0
    non_org_count = 0
    
    for booking in bookings:
        # Determine if Org or Non-Org based on old rank
        old_rank = (booking.get("guest_rank") or "").strip()
        is_org = old_rank.lower() != "def civ" if old_rank else False
        
        if is_org:
            org_count += 1
        else:
            non_org_count += 1
        
        # Build update document
        update_doc = {
            "$set": {
                "is_org": is_org,
                "org_color": None  # To be filled during checkout
            },
            "$unset": {
                "guest_rank": "",
                "army_number": "",
                "guest_unit": "",
                "command_hq": "",
                "service_type": "",
                "identity_card_number": "",
                "serving_status": ""
            }
        }
        
        # Update family members: dependent_id → org_id
        if "family_members" in booking and booking["family_members"]:
            updated_family = []
            for fm in booking["family_members"]:
                # Rename dependent_id to org_id
                if "dependent_id" in fm:
                    fm["org_id"] = fm.pop("dependent_id")
                if "has_dependent_card" in fm:
                    fm["has_org_card"] = fm.pop("has_dependent_card")
                updated_family.append(fm)
            
            update_doc["$set"]["family_members"] = updated_family
        
        # Execute update
        await db.bookings.update_one(
            {"id": booking["id"]},
            update_doc
        )
        
        sanitized_count += 1
    
    print(f"   ✅ Sanitized {sanitized_count} bookings")
    print(f"   📊 Organization guests: {org_count}")
    print(f"   📊 Non-Org guests: {non_org_count}")
    print()
    
    # Step 2: Update app_settings
    print("📊 Step 2: Updating app_settings...")
    
    settings = await db.app_settings.find_one({}, {"_id": 0})
    
    if settings:
        update_settings = {
            "$set": {
                "colors": COLORS,
                "non_org_room_rent": settings.get("def_civ_room_rent", 570),
                "non_org_license_fee": settings.get("def_civ_license_fee", 30)
            },
            "$unset": {
                "commands": "",
                "def_civ_room_rent": "",
                "def_civ_license_fee": ""
            }
        }
        
        await db.app_settings.update_one({}, update_settings)
        print("   ✅ Settings updated: Commands → Colors, Def Civ → Non-Org")
    else:
        # Create default settings if not exists
        default_settings = {
            "colors": COLORS,
            "cat_i_room_rent": 470,
            "cat_i_license_fee": 30,
            "cat_ii_room_rent": 385,
            "cat_ii_license_fee": 15,
            "non_org_room_rent": 570,
            "non_org_license_fee": 30,
            "extra_bed_charge": 75
        }
        await db.app_settings.insert_one(default_settings)
        print("   ✅ Default settings created")
    
    print()
    
    # Step 3: Summary
    print("=" * 60)
    print("✅ SANITIZATION COMPLETE")
    print()
    print("📋 Summary:")
    print(f"   • {sanitized_count} bookings sanitized")
    print(f"   • {org_count} marked as Organization")
    print(f"   • {non_org_count} marked as Non-Org")
    print(f"   • {len(COLORS)} color categories available")
    print()
    print("🔒 REMOVED DATA:")
    print("   ✗ Rank")
    print("   ✗ Army/Service Number")
    print("   ✗ Unit")
    print("   ✗ Command HQ")
    print("   ✗ Service Type")
    print("   ✗ Identity Card Number")
    print("   ✗ Serving Status")
    print()
    print("➕ ADDED DATA:")
    print("   ✓ is_org (Organization/Non-Org classification)")
    print("   ✓ org_color (to be filled at checkout)")
    print("   ✓ Renamed: dependent_id → org_id")
    print()
    print("⚠️  NEXT STEPS:")
    print("   1. Verify archive file: /app/backend/DEFENSE_DATA_ARCHIVE.csv")
    print("   2. Update backend code to use new schema")
    print("   3. Update frontend forms")
    print("   4. Test pricing logic (should be unchanged)")
    print()

if __name__ == "__main__":
    asyncio.run(sanitize_database())
