import logging
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from database import db_manager

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('Scheduler')

scheduler = BackgroundScheduler()

def sync_depin_task():
    """Background task to trigger DePIN point syncing."""
    logger.info("Triggering DePIN point synchronization...")
    from task_queue import queue_manager
    queue_manager.add_task("depin_sync", {})

def start_scheduler():
    if not scheduler.running:
        # Run DePIN sync every 30 minutes
        scheduler.add_job(sync_depin_task, 'interval', minutes=30)
        scheduler.start()
        logger.info("Scheduler started.")

def get_status():
    jobs = scheduler.get_jobs()
    return {
        "status": "Running" if scheduler.running else "Stopped",
        "job_count": len(jobs),
        "next_run": str(jobs[0].next_run_time) if jobs else "None"
    }
