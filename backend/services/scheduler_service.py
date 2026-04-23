"""
Scheduler Service - Handles automatic scheduled backups
Default: Daily at 02:00 AM IST
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timezone, timedelta
import pytz
import logging

from services.backup_service import perform_incremental_backup, cleanup_old_backups

logger = logging.getLogger(__name__)

# IST timezone
IST = pytz.timezone('Asia/Kolkata')

# Global scheduler instance
scheduler = None
db_instance = None


def init_scheduler(db):
    """Initialize scheduler with default backup job"""
    global scheduler, db_instance
    
    db_instance = db
    
    if scheduler is None:
        scheduler = AsyncIOScheduler(timezone=IST)
        
        # Schedule daily backup at 02:00 AM IST
        scheduler.add_job(
            scheduled_backup_job,
            trigger=CronTrigger(hour=2, minute=0, timezone=IST),
            id='daily_backup',
            name='Daily Automatic Backup',
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
        logger.info("Backup scheduler initialized - Daily backup at 02:00 AM IST")


async def scheduled_backup_job():
    """Job function for scheduled backups"""
    try:
        logger.info("Starting scheduled incremental backup...")
        metadata = await perform_incremental_backup(db_instance)
        
        # Update next scheduled backup time
        next_run = datetime.now(IST) + timedelta(days=1)
        next_run = next_run.replace(hour=2, minute=0, second=0, microsecond=0)
        
        await db_instance.backup_metadata.update_one(
            {"backup_id": metadata["backup_id"]},
            {"$set": {"next_scheduled_backup": next_run}}
        )
        
        logger.info(f"Scheduled backup completed: {metadata['backup_id']}")
        
    except Exception as e:
        logger.error(f"Scheduled backup failed: {str(e)}")
        # Save failure metadata
        await db_instance.backup_metadata.insert_one({
            "backup_id": f"failed_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
            "timestamp": datetime.now(timezone.utc),
            "backup_type": "INCREMENTAL",
            "status": "FAILED",
            "error_message": f"Scheduled backup failed: {str(e)}",
            "scheduled": True
        })


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
                    "updated_at": datetime.now(timezone.utc)
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
        last_backup = await db.backup_metadata.find_one(
            {"status": "SUCCESS"},
            {"_id": 0, "timestamp": 1},
            sort=[("timestamp", -1)]
        )
        
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
