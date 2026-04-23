"""
Restore Service - Handles data restoration from backups
Strategy: MERGE (keep newer records, don't overwrite existing)
"""
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


async def restore_full(backup_id: str, db) -> Dict:
    """
    Restore entire backup using MERGE strategy
    - Keeps existing records if they're newer
    - Adds missing records from backup
    """
    try:
        # Get backup metadata
        metadata = await db.backup_metadata.find_one(
            {"backup_id": backup_id},
            {"_id": 0}
        )
        
        if not metadata:
            raise ValueError(f"Backup {backup_id} not found")
        
        file_path = Path(metadata["file_path"])
        if not file_path.exists():
            raise FileNotFoundError(f"Backup file not found: {file_path}")
        
        # Load backup data
        with open(file_path, 'r') as f:
            backup_data = json.load(f)
        
        restore_stats = {
            "backup_id": backup_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "collections_restored": {},
            "strategy": "MERGE"
        }
        
        # Restore each collection
        for collection_name, documents in backup_data.get("collections", {}).items():
            try:
                collection = db[collection_name]
                merged_count = 0
                skipped_count = 0
                
                for doc in documents:
                    # Check if document exists (by 'id' field)
                    doc_id = doc.get("id")
                    if not doc_id:
                        # Insert if no ID field
                        await collection.insert_one(doc)
                        merged_count += 1
                        continue
                    
                    existing = await collection.find_one({"id": doc_id}, {"_id": 0})
                    
                    if not existing:
                        # Insert new document
                        await collection.insert_one(doc)
                        merged_count += 1
                    else:
                        # Compare timestamps - keep newer version
                        backup_time = doc.get("updated_at") or doc.get("created_at")
                        existing_time = existing.get("updated_at") or existing.get("created_at")
                        
                        if backup_time and existing_time:
                            if isinstance(backup_time, str):
                                backup_time = datetime.fromisoformat(backup_time.replace('Z', '+00:00'))
                            if isinstance(existing_time, str):
                                existing_time = datetime.fromisoformat(existing_time.replace('Z', '+00:00'))
                            
                            if backup_time > existing_time:
                                # Backup is newer, update
                                await collection.update_one(
                                    {"id": doc_id},
                                    {"$set": doc}
                                )
                                merged_count += 1
                            else:
                                # Existing is newer, skip
                                skipped_count += 1
                        else:
                            # No timestamp, merge anyway
                            await collection.update_one(
                                {"id": doc_id},
                                {"$set": doc}
                            )
                            merged_count += 1
                
                restore_stats["collections_restored"][collection_name] = {
                    "merged": merged_count,
                    "skipped": skipped_count,
                    "total": len(documents)
                }
                
                logger.info(f"Restored {collection_name}: {merged_count} merged, {skipped_count} skipped")
                
            except Exception as e:
                logger.error(f"Error restoring {collection_name}: {str(e)}")
                restore_stats["collections_restored"][collection_name] = {
                    "error": str(e)
                }
        
        # Save restore log
        await db.restore_logs.insert_one(restore_stats)
        
        return restore_stats
        
    except Exception as e:
        logger.error(f"Restore failed: {str(e)}")
        raise


async def restore_last_backup(db) -> Dict:
    """Restore the most recent successful backup"""
    last_backup = await db.backup_metadata.find_one(
        {"status": "SUCCESS"},
        {"_id": 0},
        sort=[("timestamp", -1)]
    )
    
    if not last_backup:
        raise ValueError("No successful backup found")
    
    return await restore_full(last_backup["backup_id"], db)


async def restore_by_date_range(start_date: datetime, end_date: datetime, db) -> Dict:
    """
    Restore all backups within a date range using MERGE strategy
    """
    try:
        # Find all backups in range
        backups = await db.backup_metadata.find(
            {
                "timestamp": {
                    "$gte": start_date,
                    "$lte": end_date
                },
                "status": "SUCCESS"
            },
            {"_id": 0, "backup_id": 1, "timestamp": 1},
            sort=[("timestamp", 1)]  # Oldest first
        ).to_list(None)
        
        if not backups:
            raise ValueError(f"No successful backups found between {start_date} and {end_date}")
        
        restore_results = []
        
        # Restore each backup in chronological order
        for backup in backups:
            result = await restore_full(backup["backup_id"], db)
            restore_results.append(result)
        
        return {
            "date_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "backups_restored": len(backups),
            "results": restore_results
        }
        
    except Exception as e:
        logger.error(f"Date range restore failed: {str(e)}")
        raise


async def get_restore_history(db, limit: int = 20) -> List[Dict]:
    """Get restore operation history"""
    logs = await db.restore_logs.find(
        {},
        {"_id": 0},
        sort=[("timestamp", -1)],
        limit=limit
    ).to_list(limit)
    return logs
