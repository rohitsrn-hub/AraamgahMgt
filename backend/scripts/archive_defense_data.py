"""
SECURITY: Archive Defense Data Before Sanitization
Creates CSV export of all sensitive defense-related data for offline storage.
File can be deleted after verification.
"""
import asyncio
import csv
from datetime import datetime
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

# Load environment variables
ROOT_DIR = Path(__file__).parent.parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

async def archive_defense_data():
    """Export all defense-related data to CSV archive"""
    
    print("🔒 DEFENSE DATA ARCHIVE - SECURITY OPERATION")
    print("=" * 60)
    
    # Get all bookings with defense data
    bookings = await db.bookings.find({}, {"_id": 0}).to_list(5000)
    
    if not bookings:
        print("⚠️  No bookings found to archive")
        return
    
    # Archive file path
    archive_path = ROOT_DIR / "DEFENSE_DATA_ARCHIVE.csv"
    
    # CSV headers
    headers = [
        "booking_id",
        "booking_number",
        "guest_name",
        "guest_contact",
        "guest_aadhaar",
        "rank",
        "army_number",
        "unit",
        "command_hq",
        "service_type",
        "identity_card_number",
        "serving_status",
        "check_in_date",
        "check_out_date",
        "status",
        "family_members_with_dependent_ids"
    ]
    
    archived_count = 0
    
    with open(archive_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers)
        writer.writeheader()
        
        for booking in bookings:
            # Collect family members with dependent IDs
            family_info = []
            for fm in booking.get("family_members", []):
                if fm.get("dependent_id"):
                    family_info.append(f"{fm.get('name')}:{fm.get('dependent_id')}")
            
            row = {
                "booking_id": booking.get("id", ""),
                "booking_number": booking.get("booking_number", ""),
                "guest_name": booking.get("guest_name", ""),
                "guest_contact": booking.get("guest_contact", ""),
                "guest_aadhaar": booking.get("aadhaar_number", ""),
                "rank": booking.get("guest_rank", ""),
                "army_number": booking.get("army_number", ""),
                "unit": booking.get("guest_unit", ""),
                "command_hq": booking.get("command_hq", ""),
                "service_type": booking.get("service_type", ""),
                "identity_card_number": booking.get("identity_card_number", ""),
                "serving_status": booking.get("serving_status", ""),
                "check_in_date": booking.get("check_in_date", ""),
                "check_out_date": booking.get("check_out_date", ""),
                "status": booking.get("status", ""),
                "family_members_with_dependent_ids": "; ".join(family_info) if family_info else ""
            }
            
            writer.writerow(row)
            archived_count += 1
    
    print(f"✅ Archived {archived_count} bookings to:")
    print(f"   {archive_path}")
    print()
    print("📋 Archive contains:")
    print("   - All guest ranks and army numbers")
    print("   - Unit and command information")
    print("   - Identity card numbers")
    print("   - Service type and status")
    print("   - Family member dependent IDs")
    print()
    print("⚠️  IMPORTANT:")
    print("   - Store this file securely offline")
    print("   - Delete from server after verification")
    print("   - This data will be PERMANENTLY REMOVED from database")
    print()

if __name__ == "__main__":
    asyncio.run(archive_defense_data())
