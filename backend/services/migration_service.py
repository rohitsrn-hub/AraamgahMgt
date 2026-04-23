"""
One-Time Production Migration Service
Automatically sanitizes defense data on first deployment
"""
import csv
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)

# Migration directory
MIGRATION_DIR = Path(__file__).parent.parent / "migrations"
MIGRATION_DIR.mkdir(parents=True, exist_ok=True)

# Migration ID
MIGRATION_ID = "2026_04_10_sanitize_defense_data"

# Color categories
COLORS = [
    "Red", "Green", "Brown", "Orange", "Yellow",
    "Violet", "Black", "Blue", "White", "Light Blue"
]

class MigrationService:
    """Handles one-time database migrations"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
    
    async def check_migration_status(self, migration_id: str) -> Optional[Dict]:
        """Check if migration has already been completed"""
        return await self.db.migration_status.find_one(
            {"migration_id": migration_id},
            {"_id": 0}
        )
    
    async def mark_migration_started(self, migration_id: str):
        """Mark migration as started"""
        await self.db.migration_status.insert_one({
            "migration_id": migration_id,
            "status": "running",
            "started_at": datetime.now(timezone.utc).isoformat(),
            "completed_at": None,
            "result": None,
            "archive_file": None,
            "logs": []
        })
    
    async def mark_migration_complete(
        self, 
        migration_id: str, 
        result: str, 
        archive_file: Optional[str] = None,
        logs: list = None
    ):
        """Mark migration as completed"""
        await self.db.migration_status.update_one(
            {"migration_id": migration_id},
            {
                "$set": {
                    "status": "completed",
                    "completed_at": datetime.now(timezone.utc).isoformat(),
                    "result": result,
                    "archive_file": archive_file,
                    "logs": logs or []
                }
            }
        )
    
    async def mark_migration_failed(self, migration_id: str, error: str):
        """Mark migration as failed"""
        await self.db.migration_status.update_one(
            {"migration_id": migration_id},
            {
                "$set": {
                    "status": "failed",
                    "completed_at": datetime.now(timezone.utc).isoformat(),
                    "result": f"Failed: {error}",
                    "logs": [error]
                }
            }
        )
    
    async def run_sanitization_migration(self) -> Dict:
        """
        One-time migration: Sanitize defense data
        
        Returns migration result with status
        """
        logs = []
        
        try:
            # Check if already completed
            status = await self.check_migration_status(MIGRATION_ID)
            if status and status.get("status") == "completed":
                logger.info(f"Migration {MIGRATION_ID} already completed")
                return {
                    "status": "already_completed",
                    "message": "Migration already ran successfully",
                    "archive_file": status.get("archive_file")
                }
            
            # Mark as started
            await self.mark_migration_started(MIGRATION_ID)
            logs.append(f"Migration {MIGRATION_ID} started")
            
            # Step 1: Archive defense data
            logger.info("Step 1: Archiving defense data...")
            logs.append("Step 1: Archiving defense data")
            
            bookings = await self.db.bookings.find({}, {"_id": 0}).to_list(5000)
            
            if not bookings:
                logs.append("No bookings found to archive")
                await self.mark_migration_complete(
                    MIGRATION_ID, 
                    "No data to migrate",
                    logs=logs
                )
                return {
                    "status": "success",
                    "message": "No bookings to migrate",
                    "logs": logs
                }
            
            # Create archive file
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            archive_filename = f"DEFENSE_DATA_ARCHIVE_{timestamp}.csv"
            archive_path = MIGRATION_DIR / archive_filename
            
            # Write archive
            headers = [
                "booking_id", "booking_number", "guest_name", "guest_contact",
                "guest_aadhaar", "rank", "army_number", "unit", "command_hq",
                "service_type", "identity_card_number", "serving_status",
                "check_in_date", "check_out_date", "status",
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
                        dep_id = fm.get("dependent_id") or fm.get("org_id", "")
                        if dep_id:
                            family_info.append(f"{fm.get('name')}:{dep_id}")
                    
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
            
            logs.append(f"Archived {archived_count} bookings to {archive_filename}")
            logger.info(f"Archived {archived_count} bookings")
            
            # Step 2: Sanitize bookings
            logger.info("Step 2: Sanitizing bookings...")
            logs.append("Step 2: Sanitizing bookings")
            
            sanitized_count = 0
            org_count = 0
            non_org_count = 0
            
            for booking in bookings:
                # Determine if Org or Non-Org
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
                        "org_color": booking.get("org_color")  # Keep if exists, else None
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
                
                # Update family members
                if "family_members" in booking and booking["family_members"]:
                    updated_family = []
                    for fm in booking["family_members"]:
                        # Rename dependent_id to org_id if exists
                        if "dependent_id" in fm and "org_id" not in fm:
                            fm["org_id"] = fm.pop("dependent_id")
                        if "has_dependent_card" in fm and "has_org_card" not in fm:
                            fm["has_org_card"] = fm.pop("has_dependent_card")
                        updated_family.append(fm)
                    
                    update_doc["$set"]["family_members"] = updated_family
                
                # Execute update
                await self.db.bookings.update_one(
                    {"id": booking["id"]},
                    update_doc
                )
                
                sanitized_count += 1
            
            logs.append(f"Sanitized {sanitized_count} bookings ({org_count} Org, {non_org_count} Non-Org)")
            logger.info(f"Sanitized {sanitized_count} bookings")
            
            # Step 3: Update settings
            logger.info("Step 3: Updating settings...")
            logs.append("Step 3: Updating settings")
            
            settings = await self.db.app_settings.find_one({}, {"_id": 0})
            
            if settings:
                update_settings = {
                    "$set": {
                        "colors": COLORS,
                        "non_org_room_rent": settings.get("def_civ_room_rent") or settings.get("non_org_room_rent", 570),
                        "non_org_license_fee": settings.get("def_civ_license_fee") or settings.get("non_org_license_fee", 30)
                    }
                }
                
                # Only unset if they exist
                unset_fields = {}
                if "commands" in settings:
                    unset_fields["commands"] = ""
                if "def_civ_room_rent" in settings:
                    unset_fields["def_civ_room_rent"] = ""
                if "def_civ_license_fee" in settings:
                    unset_fields["def_civ_license_fee"] = ""
                
                if unset_fields:
                    update_settings["$unset"] = unset_fields
                
                await self.db.app_settings.update_one({}, update_settings)
                logs.append("Settings updated: Commands → Colors, Def Civ → Non-Org")
            
            # Mark as completed
            await self.mark_migration_complete(
                MIGRATION_ID,
                f"Successfully sanitized {sanitized_count} bookings",
                archive_filename,
                logs
            )
            
            logger.info(f"Migration {MIGRATION_ID} completed successfully")
            
            return {
                "status": "success",
                "message": f"Migration completed: {sanitized_count} bookings sanitized",
                "archive_file": archive_filename,
                "stats": {
                    "total": sanitized_count,
                    "org": org_count,
                    "non_org": non_org_count
                },
                "logs": logs
            }
            
        except Exception as e:
            error_msg = f"Migration failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            logs.append(error_msg)
            
            await self.mark_migration_failed(MIGRATION_ID, error_msg)
            
            return {
                "status": "failed",
                "message": error_msg,
                "logs": logs
            }


async def run_startup_migrations(db: AsyncIOMotorDatabase):
    """
    Run all pending migrations on application startup
    Should be called from FastAPI startup event
    """
    logger.info("Checking for pending migrations...")
    
    migration_service = MigrationService(db)
    
    # Run sanitization migration
    result = await migration_service.run_sanitization_migration()
    
    if result["status"] == "success":
        logger.info(f"✅ Migration completed: {result['message']}")
    elif result["status"] == "already_completed":
        logger.info("✅ Migration already completed previously")
    else:
        logger.error(f"❌ Migration failed: {result['message']}")
    
    return result
