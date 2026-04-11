"""
Backup Service - Handles full and incremental backups
"""
import json
import os
from datetime import datetime, timezone, timedelta
import pytz

# IST timezone
IST = pytz.timezone('Asia/Kolkata')
from pathlib import Path
from typing import Dict, List, Optional
from uuid import uuid4
import logging

logger = logging.getLogger(__name__)

# Backup directory
# Use relative path for Render deployment compatibility
BACKUP_DIR = Path(__file__).parent.parent / "backups"  # backend/backups
BACKUP_DIR.mkdir(parents=True, exist_ok=True)  # Create parent dirs if needed

# Collections to backup
COLLECTIONS_TO_BACKUP = [
    "bookings",
    "rooms",
    "settings",
    "staff",
    "refunds",
    "app_settings"  # Include app settings
]


async def get_last_backup_metadata(db) -> Optional[Dict]:
    """Get metadata of the last successful backup"""
    backup = await db.backup_metadata.find_one(
        {"status": "SUCCESS"},
        {"_id": 0},
        sort=[("timestamp", -1)]
    )
    return backup


async def perform_full_backup(db) -> Dict:
    """
    Perform full backup of all collections
    Returns backup metadata
    """
    try:
        backup_id = str(uuid4())
        timestamp = datetime.now(timezone.utc)
        filename = f"backup_full_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        file_path = BACKUP_DIR / filename
        
        backup_data = {
            "backup_id": backup_id,
            "timestamp": timestamp.isoformat(),
            "backup_type": "FULL",
            "collections": {}
        }
        
        record_count = {}
        start_time = datetime.now(timezone.utc)
        
        # Backup each collection
        for collection_name in COLLECTIONS_TO_BACKUP:
            try:
                collection = db[collection_name]
                documents = await collection.find({}, {"_id": 0}).to_list(None)
                backup_data["collections"][collection_name] = documents
                record_count[collection_name] = len(documents)
                logger.info(f"Backed up {len(documents)} records from {collection_name}")
            except Exception as e:
                logger.error(f"Error backing up {collection_name}: {str(e)}")
                record_count[collection_name] = 0
        
        # Write to file
        with open(file_path, 'w') as f:
            json.dump(backup_data, f, indent=2)
        
        duration = (datetime.now(timezone.utc) - start_time).total_seconds()
        
        # Save metadata to DB
        metadata = {
            "backup_id": backup_id,
            "timestamp": timestamp.isoformat(),  # Convert to ISO string
            "backup_type": "FULL",
            "record_count": record_count,
            "file_path": str(file_path),
            "file_size_mb": round(file_path.stat().st_size / (1024 * 1024), 2),
            "status": "SUCCESS",
            "duration_seconds": round(duration, 2),
            "next_scheduled_backup": None  # Will be set by scheduler
        }
        
        await db.backup_metadata.insert_one({**metadata, "_id": backup_id})
        
        logger.info(f"Full backup completed: {backup_id}")
        return metadata
        
    except Exception as e:
        logger.error(f"Full backup failed: {str(e)}")
        # Save failed metadata
        metadata = {
            "backup_id": str(uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),  # Convert to ISO string
            "backup_type": "FULL",
            "status": "FAILED",
            "error_message": str(e),
            "duration_seconds": 0
        }
        await db.backup_metadata.insert_one({**metadata, "_id": metadata["backup_id"]})
        raise


async def perform_incremental_backup(db) -> Dict:
    """
    Perform incremental backup (only new/updated records since last backup)
    Returns backup metadata
    """
    try:
        # Get last successful backup
        last_backup = await get_last_backup_metadata(db)
        
        if not last_backup:
            logger.info("No previous backup found, performing full backup")
            return await perform_full_backup(db)
        
        last_backup_time = last_backup["timestamp"]
        if isinstance(last_backup_time, str):
            last_backup_time = datetime.fromisoformat(last_backup_time)
        
        backup_id = str(uuid4())
        timestamp = datetime.now(timezone.utc)
        filename = f"backup_incr_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        file_path = BACKUP_DIR / filename
        
        backup_data = {
            "backup_id": backup_id,
            "timestamp": timestamp.isoformat(),
            "backup_type": "INCREMENTAL",
            "since": last_backup_time.isoformat(),
            "collections": {}
        }
        
        record_count = {}
        start_time = datetime.now(timezone.utc)
        
        # Backup each collection (only new/updated records)
        for collection_name in COLLECTIONS_TO_BACKUP:
            try:
                collection = db[collection_name]
                
                # Query for records created or updated after last backup
                query = {
                    "$or": [
                        {"created_at": {"$gt": last_backup_time}},
                        {"updated_at": {"$gt": last_backup_time}}
                    ]
                }
                
                documents = await collection.find(query, {"_id": 0}).to_list(None)
                backup_data["collections"][collection_name] = documents
                record_count[collection_name] = len(documents)
                
                if len(documents) > 0:
                    logger.info(f"Backed up {len(documents)} new/updated records from {collection_name}")
            except Exception as e:
                logger.error(f"Error backing up {collection_name}: {str(e)}")
                record_count[collection_name] = 0
        
        # Write to file
        with open(file_path, 'w') as f:
            json.dump(backup_data, f, indent=2)
        
        duration = (datetime.now(timezone.utc) - start_time).total_seconds()
        
        # Save metadata to DB
        metadata = {
            "backup_id": backup_id,
            "timestamp": timestamp.isoformat(),  # Convert to ISO string
            "backup_type": "INCREMENTAL",
            "record_count": record_count,
            "file_path": str(file_path),
            "file_size_mb": round(file_path.stat().st_size / (1024 * 1024), 2),
            "status": "SUCCESS",
            "duration_seconds": round(duration, 2),
            "since_backup": last_backup["backup_id"]
        }
        
        await db.backup_metadata.insert_one({**metadata, "_id": backup_id})
        
        total_records = sum(record_count.values())
        logger.info(f"Incremental backup completed: {backup_id} ({total_records} records)")
        return metadata
        
    except Exception as e:
        logger.error(f"Incremental backup failed: {str(e)}")
        metadata = {
            "backup_id": str(uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),  # Convert to ISO string
            "backup_type": "INCREMENTAL",
            "status": "FAILED",
            "error_message": str(e),
            "duration_seconds": 0
        }
        await db.backup_metadata.insert_one({**metadata, "_id": metadata["backup_id"]})
        raise


async def get_backup_history(db, limit: int = 50) -> List[Dict]:
    """Get backup history (last N backups)"""
    backups = await db.backup_metadata.find(
        {},
        {"_id": 0},
        sort=[("timestamp", -1)],
        limit=limit
    ).to_list(limit)
    return backups


async def cleanup_old_backups(db, retention_days: int = 90):
    """
    Delete backups older than retention period
    Default: 90 days (3 months)
    """
    try:
        cutoff_date = datetime.now(timezone.utc).timestamp() - (retention_days * 24 * 60 * 60)
        cutoff_datetime = datetime.fromtimestamp(cutoff_date, tz=timezone.utc)
        
        # Find old backups
        old_backups = await db.backup_metadata.find(
            {"timestamp": {"$lt": cutoff_datetime}},
            {"_id": 0, "backup_id": 1, "file_path": 1}
        ).to_list(None)
        
        deleted_count = 0
        for backup in old_backups:
            # Delete file
            file_path = Path(backup.get("file_path", ""))
            if file_path.exists():
                file_path.unlink()
                logger.info(f"Deleted old backup file: {file_path}")
            
            # Delete metadata
            await db.backup_metadata.delete_one({"backup_id": backup["backup_id"]})
            deleted_count += 1
        
        logger.info(f"Cleaned up {deleted_count} old backups (older than {retention_days} days)")
        return deleted_count
        
    except Exception as e:
        logger.error(f"Error cleaning up old backups: {str(e)}")
        return 0


async def validate_backup(backup_id: str, db) -> bool:
    """Validate backup file exists and is readable"""
    try:
        metadata = await db.backup_metadata.find_one(
            {"backup_id": backup_id},
            {"_id": 0}
        )
        
        if not metadata:
            return False
        
        file_path = Path(metadata.get("file_path", ""))
        if not file_path.exists():
            return False
        
        # Try to read and parse JSON
        with open(file_path, 'r') as f:
            data = json.load(f)
            return "backup_id" in data and "collections" in data
            
    except Exception as e:
        logger.error(f"Backup validation failed: {str(e)}")
        return False
