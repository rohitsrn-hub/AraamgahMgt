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


def _as_datetime(value):
    if isinstance(value, str):
        value = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if isinstance(value, datetime) and value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value


async def merge_backup_data(backup_data: Dict, db, dry_run: bool = False) -> Dict:
    """Merge a backup's documents into the database (MERGE strategy).

    - a document whose "id" is not in the database is added;
    - one that is already there is replaced only if the backup's copy is
      NEWER (updated_at / created_at); otherwise the live one is kept;
    - nothing is ever deleted.
    dry_run=True only counts what would happen."""
    stats = {}
    for collection_name, documents in backup_data.get("collections", {}).items():
        collection = db[collection_name]
        added = updated = kept = 0
        for doc in documents:
            doc_id = doc.get("id")
            existing = await collection.find_one({"id": doc_id}, {"_id": 0}) if doc_id else None
            if existing is None:
                added += 1
                if not dry_run:
                    await collection.insert_one(dict(doc))
                continue
            backup_time = _as_datetime(doc.get("updated_at") or doc.get("created_at"))
            existing_time = _as_datetime(existing.get("updated_at") or existing.get("created_at"))
            if backup_time and existing_time and backup_time <= existing_time:
                kept += 1
                continue
            updated += 1
            if not dry_run:
                await collection.update_one({"id": doc_id}, {"$set": doc})
        stats[collection_name] = {"added": added, "updated": updated, "kept_live_version": kept, "total": len(documents)}
    return stats


async def restore_full(backup_id: str, db) -> Dict:
    """
    Restore entire backup using MERGE strategy
    - Keeps existing records if they're newer
    - Adds missing records from backup
    """
    from services.backup_service import load_backup_data
    try:
        # Get backup metadata
        metadata = await db.backup_metadata.find_one(
            {"backup_id": backup_id},
            {"_id": 0}
        )
        
        if not metadata:
            raise ValueError(f"Backup {backup_id} not found")

        # From the file if it is still on the server, otherwise from the
        # copy kept in the database.
        backup_data = await load_backup_data(db, metadata)

        restore_stats = {
            "backup_id": backup_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "collections_restored": {},
            "strategy": "MERGE"
        }

        try:
            for name, counts in (await merge_backup_data(backup_data, db)).items():
                restore_stats["collections_restored"][name] = {
                    "merged": counts["added"] + counts["updated"],
                    "skipped": counts["kept_live_version"],
                    "total": counts["total"],
                }
                logger.info(f"Restored {name}: {counts}")
        except Exception as e:
            logger.error(f"Error restoring: {str(e)}")
            restore_stats["collections_restored"]["error"] = {"error": str(e)}

        # Save restore log. Insert a COPY: insert_one() adds a Mongo "_id"
        # (an ObjectId) to the dict it is given, and the API then failed to
        # turn that into JSON — so every restore that had just SUCCEEDED was
        # reported to the admin as "Restore failed".
        await db.restore_logs.insert_one(dict(restore_stats))
        
        return restore_stats
        
    except Exception as e:
        logger.error(f"Restore failed: {str(e)}")
        raise


async def restore_last_backup(db) -> Dict:
    """Restore the most recent successful backup"""
    from services.backup_service import get_last_backup_metadata
    last_backup = await get_last_backup_metadata(db)
    
    if not last_backup:
        raise ValueError("No successful backup found")
    
    return await restore_full(last_backup["backup_id"], db)


async def restore_by_date_range(start_date: datetime, end_date: datetime, db) -> Dict:
    """
    Restore all backups within a date range using MERGE strategy
    """
    try:
        # Find all backups in range. Timestamps are stored both as dates and
        # as ISO strings and Mongo never matches a string against a date
        # bound (nor orders the two sensibly), so filter in Python on the
        # parsed value. This used to find nothing and every date-range
        # restore failed with "No successful backups found".
        from services.backup_service import list_backup_metadata, parse_backup_timestamp

        def _utc(dt: datetime) -> datetime:
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)

        lo, hi = _utc(start_date), _utc(end_date)
        backups = [
            b for b in reversed(await list_backup_metadata(db, {"status": "SUCCESS"}))  # oldest first
            if (ts := parse_backup_timestamp(b.get("timestamp"))) and lo <= ts <= hi
        ]
        
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
