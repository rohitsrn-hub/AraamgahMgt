"""
Scheduler Service - Handles automatic scheduled backups

Default: daily at 14:00 IST, PLUS a catch-up: whenever someone is using the
app and the last full backup is more than 20 hours old, one is taken in the
background (see maybe_trigger_backup).

Why not 02:00 any more: the backend runs on a free Render web service, which
(as far as we understand it) sleeps when nobody is using it, and a sleeping
server cannot run an in-process scheduled job. Nobody uses the app at 2 am,
so a 2 am backup effectively never ran. The catch-up fires from real use, so
it runs whenever the app is awake, and the cron time is moved into the working
day for the days it happens to be awake anyway.
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timezone, timedelta
import asyncio
import time
import pytz
import logging

from services.backup_service import (
    perform_full_backup, cleanup_old_backups, get_last_backup_metadata,
    list_backup_metadata, parse_backup_timestamp,
)

logger = logging.getLogger(__name__)

# IST timezone
IST = pytz.timezone('Asia/Kolkata')

# Global scheduler instance
scheduler = None
db_instance = None


DEFAULT_BACKUP_HOUR = 14
DEFAULT_BACKUP_MINUTE = 0
CATCH_UP_AFTER_HOURS = 20          # take a backup on use if the last one is older than this
_CHECK_EVERY_SECONDS = 600         # look at most this often
_RETRY_AFTER_FAILURE_SECONDS = 3600
_state = {"checked_at": None, "failed_at": None, "running": False}
_tasks = set()                     # keeps background tasks alive until they finish


def init_scheduler(db, hour: int = DEFAULT_BACKUP_HOUR, minute: int = DEFAULT_BACKUP_MINUTE):
    """Initialize scheduler with the daily backup job (at the saved time, if any)."""
    global scheduler, db_instance

    db_instance = db

    if scheduler is None:
        scheduler = AsyncIOScheduler(timezone=IST)

        scheduler.add_job(
            scheduled_backup_job,
            trigger=CronTrigger(hour=hour, minute=minute, timezone=IST),
            id='daily_backup',
            name=f'Daily Automatic Backup at {hour:02d}:{minute:02d} IST',
            replace_existing=True
        )

        # Schedule cleanup job weekly (Sunday 03:00 AM IST)
        scheduler.add_job(
            cleanup_job,
            trigger=CronTrigger(day_of_week='sun', hour=3, minute=0, timezone=IST),
            id='weekly_cleanup',
            name='Weekly Backup Cleanup',
            replace_existing=True
        )

        scheduler.start()
        logger.info(f"Backup scheduler initialized - daily backup at {hour:02d}:{minute:02d} IST")


async def scheduled_backup_job():
    """Daily scheduled backup (a FULL one — the data is small, and a full backup
    is self-contained, unlike a chain of incrementals)."""
    await ensure_recent_backup(db_instance, max_age_hours=0)


async def ensure_recent_backup(db, max_age_hours: float = CATCH_UP_AFTER_HOURS):
    """Take a full backup unless a successful FULL one already exists that is
    newer than max_age_hours. Safe to call often and concurrently: only one
    runs at a time, and after a failure it waits an hour before trying again
    (so a broken backup can't hammer the database on every request).
    Returns the new backup's metadata, or None if nothing was done."""
    if _state["running"]:
        return None
    _state["running"] = True
    try:
        if max_age_hours > 0:
            fulls = await list_backup_metadata(db, {"status": "SUCCESS", "backup_type": "FULL"})
            last = parse_backup_timestamp(fulls[0].get("timestamp")) if fulls else None
            if last and (datetime.now(timezone.utc) - last) < timedelta(hours=max_age_hours):
                return None
            failed_at = _state["failed_at"]
            if failed_at is not None and (time.monotonic() - failed_at) < _RETRY_AFTER_FAILURE_SECONDS:
                return None
        logger.info("Taking a full backup...")
        metadata = await perform_full_backup(db)
        _state["failed_at"] = None
        logger.info(f"Backup completed: {metadata['backup_id']}")
        return metadata
    except Exception as e:
        _state["failed_at"] = time.monotonic()
        logger.error(f"Backup failed: {str(e)}")   # perform_full_backup already recorded the FAILED row
        return None
    finally:
        _state["running"] = False


def maybe_trigger_backup(db):
    """Called on every authenticated request. Cheap: at most once every ten
    minutes it starts ensure_recent_backup() in the background, without making
    the request wait for it."""
    now = time.monotonic()
    last_check = _state["checked_at"]
    if _state["running"] or (last_check is not None and now - last_check < _CHECK_EVERY_SECONDS):
        return
    _state["checked_at"] = now
    try:
        task = asyncio.get_running_loop().create_task(ensure_recent_backup(db))
    except RuntimeError:       # no running loop (not inside a request)
        return
    _tasks.add(task)
    task.add_done_callback(_tasks.discard)


async def cleanup_job():
    """Job function for cleanup old backups (90 days retention)"""
    try:
        logger.info("Starting backup cleanup (90 days retention)...")
        deleted = await cleanup_old_backups(db_instance, retention_days=90)
        logger.info(f"Cleanup completed: {deleted} old backups removed")
    except Exception as e:
        logger.error(f"Cleanup job failed: {str(e)}")


async def update_backup_schedule(hour: int, minute: int, db):
    """Update scheduled backup time"""
    global scheduler
    
    if scheduler is None:
        raise ValueError("Scheduler not initialized")
    
    try:
        # Remove existing job
        scheduler.remove_job('daily_backup')
        
        # Add new job with updated time
        scheduler.add_job(
            scheduled_backup_job,
            trigger=CronTrigger(hour=hour, minute=minute, timezone=IST),
            id='daily_backup',
            name=f'Daily Automatic Backup at {hour:02d}:{minute:02d} IST',
            replace_existing=True
        )
        
        # Save schedule to settings
        await db.app_settings.update_one(
            {},
            {"$set": {
                "backup_schedule": {
                    "hour": hour,
                    "minute": minute,
                    "timezone": "IST",
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
            }},
            upsert=True
        )
        
        logger.info(f"Backup schedule updated to {hour:02d}:{minute:02d} IST")
        return {"success": True, "schedule": f"{hour:02d}:{minute:02d} IST"}
        
    except Exception as e:
        logger.error(f"Failed to update schedule: {str(e)}")
        raise


async def check_missed_backups(db) -> dict:
    """
    Check if scheduled backup was missed
    Returns: {
        "missed": bool,
        "last_backup": datetime or None,
        "hours_since_last": int
    }
    """
    try:
        # Get last successful backup
        # Not find_one(sort=timestamp): see backup_service.list_backup_metadata.
        last_backup = await get_last_backup_metadata(db)
        
        if not last_backup:
            return {
                "missed": True,
                "last_backup": None,
                "hours_since_last": None,
                "message": "No successful backup found"
            }
        
        last_time = last_backup["timestamp"]
        if isinstance(last_time, str):
            last_time = datetime.fromisoformat(last_time.replace('Z', '+00:00'))
        
        # Ensure last_time is timezone-aware (UTC)
        if last_time.tzinfo is None:
            last_time = last_time.replace(tzinfo=timezone.utc)
        
        # Calculate hours since last backup (both now timezone-aware)
        now_utc = datetime.now(timezone.utc)
        hours_since = (now_utc - last_time).total_seconds() / 3600
        
        # If last backup was more than 26 hours ago, consider it missed
        missed = hours_since > 26
        
        return {
            "missed": missed,
            "last_backup": last_time.isoformat(),
            "hours_since_last": round(hours_since, 1),
            "message": f"Last backup was {round(hours_since, 1)} hours ago" if missed else "Backup is up to date"
        }
        
    except Exception as e:
        logger.error(f"Error checking missed backups: {str(e)}")
        return {
            "missed": True,
            "error": str(e)
        }


def get_scheduler_status():
    """Get current scheduler status"""
    if scheduler is None:
        return {"running": False}
    
    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run": job.next_run_time.isoformat() if job.next_run_time else None
        })
    
    return {
        "running": scheduler.running,
        "jobs": jobs
    }
