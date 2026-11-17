"""
Backup Service - Handles full and incremental backups
"""
import json
import os
import zlib
from datetime import datetime, timezone, timedelta
import pytz

# IST timezone
IST = pytz.timezone('Asia/Kolkata')
from pathlib import Path
from typing import Dict, List, Optional
from uuid import uuid4
import logging
from bson.binary import Binary

logger = logging.getLogger(__name__)

def _json_default(obj):
    """json.dump() fallback for values it can't serialize natively.

    Most documents store created_at/updated_at as ISO strings, but a few
    write paths (e.g. confirm_extension) store a raw BSON/Python datetime
    instead. json.dump has no idea how to serialize that and raises
    'Object of type datetime is not JSON serializable' the first time a
    backup actually reaches one of those documents. Convert to the same
    ISO-string form the rest of the app already uses; anything genuinely
    unexpected still raises, same as json.dump's default behavior.
    """
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")

# Backup directory
# Use relative path for Render deployment compatibility
BACKUP_DIR = Path(__file__).parent.parent / "backups"  # backend/backups
BACKUP_DIR.mkdir(parents=True, exist_ok=True)  # Create parent dirs if needed

# Collections to backup.
# Every collection that holds data the guesthouse cannot recreate. Until the
# Nov 2026 audit this listed only bookings/rooms/staff/refunds/app_settings
# (plus "settings", a collection the app has never written to) — so a restore
# after losing the database would have brought back the bookings but none of
# the payments ledger, guests, user logins, feedback or toiletry stock.
# Each of these documents carries its own "id", which is what restore merges
# on. (counters is deliberately absent: it has no "id" and re-seeds itself
# from the latest booking number.)
COLLECTIONS_TO_BACKUP = [
    "bookings",
    "rooms",
    "staff",
    "refunds",
    "app_settings",
    "payments",
    "guests",
    "users",
    "feedbacks",
    "toiletry_inventory",
    "toiletry_transactions",
]


def parse_backup_timestamp(value) -> Optional[datetime]:
    """A backup record's timestamp as an aware UTC datetime, whichever way it
    was stored. Records written before 11 May 2026 (and the scheduler's
    failure records) hold a real BSON date; every later one holds an ISO
    string. Returns None if it is neither."""
    if isinstance(value, datetime):
        dt = value
    elif isinstance(value, str):
        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    else:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


async def list_backup_metadata(db, query: Optional[Dict] = None) -> List[Dict]:
    """Backup records matching `query`, NEWEST FIRST, ordered in Python.

    Never ask Mongo to sort these by timestamp: with both dates and strings
    in the collection it orders by TYPE first (every date ranks above every
    string), so "newest" came back as the oldest date-typed record — the
    last successful backup read 11 April 2026 for seven months while newer
    backups sat unseen below it. "Restore last backup" had the same flaw and
    would have restored that April backup. The collection is tiny (one record
    per backup), so sorting here is cheap."""
    docs = await db.backup_metadata.find(query or {}, {"_id": 0}).to_list(None)
    oldest = datetime.min.replace(tzinfo=timezone.utc)
    docs.sort(key=lambda d: parse_backup_timestamp(d.get("timestamp")) or oldest, reverse=True)
    return docs


async def get_last_backup_metadata(db) -> Optional[Dict]:
    """Get metadata of the last successful backup"""
    docs = await list_backup_metadata(db, {"status": "SUCCESS"})
    return docs[0] if docs else None


SNAPSHOT_COLLECTION = "backup_snapshots"
MAX_SNAPSHOT_BYTES = 15 * 1024 * 1024   # MongoDB documents are capped at 16 MB


async def collect_full_backup_data(db, backup_id: Optional[str] = None, timestamp: Optional[datetime] = None,
                                   include_users: bool = True) -> Dict:
    """Every collection in COLLECTIONS_TO_BACKUP as one JSON-able dict.

    include_users=False is for a file that leaves the server (the admin
    download): login records, with their password hashes, stay out of it.
    A plain list of who has an account (no hashes) goes in "users_reference"
    instead, so the accounts can be re-created by hand after a recovery."""
    timestamp = timestamp or datetime.now(timezone.utc)
    data = {
        "backup_id": backup_id or str(uuid4()),
        "timestamp": timestamp.isoformat(),
        "backup_type": "FULL",
        "collections": {},
    }
    for collection_name in COLLECTIONS_TO_BACKUP:
        if collection_name == "users" and not include_users:
            continue
        try:
            data["collections"][collection_name] = await db[collection_name].find({}, {"_id": 0}).to_list(None)
        except Exception as e:
            # Never hand back a backup that quietly lacks a collection.
            logger.error(f"Error backing up {collection_name}: {str(e)}")
            raise
    if not include_users:
        users = await db["users"].find({}, {"_id": 0, "password_hash": 0}).to_list(None)
        data["users_reference"] = [
            {k: u.get(k) for k in ("email", "name", "role", "is_active")} for u in users
        ]
    return data


def _compress(data: Dict) -> bytes:
    return zlib.compress(json.dumps(data, default=_json_default, separators=(",", ":")).encode("utf-8"), 6)


async def load_backup_data(db, metadata: Dict) -> Dict:
    """The contents of a backup: from its file if the file still exists,
    otherwise from the copy kept in the database. The file lives on the app
    server's own disk, which on a free Render plan is wiped by every deploy
    and restart — so the copy in the database is the one that survives."""
    file_path = metadata.get("file_path")
    if file_path and Path(file_path).exists():
        with open(file_path, "r") as f:
            return json.load(f)
    snap = await db[SNAPSHOT_COLLECTION].find_one({"backup_id": metadata.get("backup_id")}, {"_id": 0})
    if snap and snap.get("data") is not None:
        return json.loads(zlib.decompress(bytes(snap["data"])).decode("utf-8"))
    raise FileNotFoundError(
        f"Backup {metadata.get('backup_id')} has neither a file on the server nor a copy in the database"
    )


async def perform_full_backup(db) -> Dict:
    """
    Perform full backup of all collections
    Returns backup metadata

    Two copies are kept: a JSON file on the server's disk (as before), and a
    compressed copy in the database (collection backup_snapshots) that
    survives deploys. The file is best-effort; the database copy is the one
    the restore relies on.
    """
    try:
        backup_id = str(uuid4())
        timestamp = datetime.now(timezone.utc)
        start_time = datetime.now(timezone.utc)

        backup_data = await collect_full_backup_data(db, backup_id=backup_id, timestamp=timestamp)
        record_count = {name: len(docs) for name, docs in backup_data["collections"].items()}
        for name, count in record_count.items():
            logger.info(f"Backed up {count} records from {name}")

        # Copy in the database (survives deploys).
        payload = _compress(backup_data)
        if len(payload) > MAX_SNAPSHOT_BYTES:
            raise ValueError(f"Backup is {len(payload) // 1024} KB compressed, over the 15 MB single-document limit")
        await db[SNAPSHOT_COLLECTION].insert_one({
            "backup_id": backup_id, "timestamp": timestamp.isoformat(),
            "backup_type": "FULL", "data": Binary(payload),
        })

        # File on the server's disk (lost on redeploy on a free plan; best effort).
        file_path = None
        file_size_mb = None
        try:
            # short id in the name: two backups in the same second must not share a file
            filename = f"backup_full_{timestamp.strftime('%Y%m%d_%H%M%S')}_{backup_id[:8]}.json"
            file_path = BACKUP_DIR / filename
            with open(file_path, 'w') as f:
                json.dump(backup_data, f, indent=2, default=_json_default)
            file_size_mb = round(file_path.stat().st_size / (1024 * 1024), 2)
        except OSError as e:
            logger.warning(f"Could not write the backup file ({e}); the copy in the database is intact")
            file_path = None

        duration = (datetime.now(timezone.utc) - start_time).total_seconds()

        # Save metadata to DB
        metadata = {
            "backup_id": backup_id,
            "timestamp": timestamp.isoformat(),  # Convert to ISO string
            "backup_type": "FULL",
            "record_count": record_count,
            "file_path": str(file_path) if file_path else None,
            "file_size_mb": file_size_mb,
            "stored_in_database": True,
            "compressed_kb": len(payload) // 1024,
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
                
                # Query for records created or updated after last backup.
                # created_at/updated_at are stored as ISO strings in most
                # documents (serialize_doc) but as BSON dates in a few code
                # paths. Mongo comparisons are type-bracketed — a $gt against
                # a datetime never matches string fields and vice versa — so
                # query BOTH representations or the incremental silently
                # backs up nothing (which is exactly what it did until now).
                last_backup_iso = last_backup_time.isoformat()
                query = {
                    "$or": [
                        {"created_at": {"$gt": last_backup_time}},
                        {"updated_at": {"$gt": last_backup_time}},
                        {"created_at": {"$gt": last_backup_iso}},
                        {"updated_at": {"$gt": last_backup_iso}},
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
            json.dump(backup_data, f, indent=2, default=_json_default)
        
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
    history = (await list_backup_metadata(db))[:limit]
    for b in history:
        # Can this backup actually be restored? Its file may have been wiped by a
        # redeploy; only a copy kept in the database (or a file still on disk) counts.
        b["restorable"] = bool(
            b.get("status") == "SUCCESS"
            and (b.get("stored_in_database") or (b.get("file_path") and Path(b["file_path"]).exists()))
        )
    return history


async def cleanup_old_backups(db, retention_days: int = 90):
    """
    Delete backups older than retention period
    Default: 90 days (3 months)
    """
    try:
        cutoff_date = datetime.now(timezone.utc).timestamp() - (retention_days * 24 * 60 * 60)
        cutoff_datetime = datetime.fromtimestamp(cutoff_date, tz=timezone.utc)
        
        # Find old backups. Backup timestamps are stored as ISO strings, and
        # Mongo never matches a string field against a datetime bound — so
        # comparing with the datetime alone matched nothing and this cleanup
        # had never deleted a single backup. Compare both representations
        # (the scheduler's failure records do store a real datetime).
        old_backups = await db.backup_metadata.find(
            {"$or": [
                {"timestamp": {"$lt": cutoff_datetime.isoformat()}},
                {"timestamp": {"$lt": cutoff_datetime}},
            ]},
            {"_id": 0, "backup_id": 1, "file_path": 1}
        ).to_list(None)
        
        deleted_count = 0
        for backup in old_backups:
            # Delete file
            file_path = Path(backup.get("file_path") or "")
            if backup.get("file_path") and file_path.exists():
                file_path.unlink()
                logger.info(f"Deleted old backup file: {file_path}")
            
            # Delete metadata and the copy kept in the database
            await db.backup_metadata.delete_one({"backup_id": backup["backup_id"]})
            await db[SNAPSHOT_COLLECTION].delete_one({"backup_id": backup["backup_id"]})
            deleted_count += 1
        
        logger.info(f"Cleaned up {deleted_count} old backups (older than {retention_days} days)")
        return deleted_count
        
    except Exception as e:
        logger.error(f"Error cleaning up old backups: {str(e)}")
        return 0


async def validate_backup(backup_id: str, db) -> bool:
    """Validate a backup can be read back (file or database copy)."""
    try:
        metadata = await db.backup_metadata.find_one({"backup_id": backup_id}, {"_id": 0})
        if not metadata:
            return False
        data = await load_backup_data(db, metadata)
        return "backup_id" in data and "collections" in data
    except Exception as e:
        logger.error(f"Backup validation failed: {str(e)}")
        return False
