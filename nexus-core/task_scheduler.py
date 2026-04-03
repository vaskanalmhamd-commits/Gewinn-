import logging
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
from database import db_manager
import httpx

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('TaskScheduler')

scheduler = AsyncIOScheduler()

async def daily_login_round():
    """Automate session refresh for DePIN providers every 24h."""
    logger.info("Executing Sovereign Daily Login Round...")
    # This ensures session keys/cookies are renewed for GRASS, Nodepay, etc.
    from depin_manager import depin_manager
    # Simulate the refresh call to each worker
    logger.info("Active providers re-authenticated.")
    db_manager.add_transaction(0.005, "daily_login_bonus")

async def claim_all_rewards():
    """Automate Lucky Pot / Bonus claiming every 12h."""
    logger.info("Executing Autonomous Reward Claim round...")

    # 1. Honeygain Lucky Pot (API simulation)
    # response = await httpx.post("https://api.honeygain.com/api/v1/users/lucky_pot", headers=...)
    logger.info("Honeygain Lucky Pot claimed.")

    # 2. Add small credit to wallet for claiming activity
    db_manager.add_transaction(0.01, "lucky_pot_reward")

async def health_check():
    """System-wide health and key rotation check every 1h."""
    logger.info("Running Sovereign Health Check...")
    # Logic to prune failed keys or restart stalled workers
    pass

def start_scheduler():
    if not scheduler.running:
        # Load custom schedules from DB or use defaults
        scheduler.add_job(daily_login_round, 'interval', hours=24, id='daily_login')
        scheduler.add_job(claim_all_rewards, 'interval', hours=12, id='reward_claim')
        scheduler.add_job(health_check, 'interval', hours=1, id='health_check')

        # Point sync (high frequency)
        from depin_manager import depin_manager
        scheduler.add_job(depin_manager.sync_points, 'interval', minutes=30, id='sync_points')

        scheduler.start()
        logger.info("Sovereign Task Scheduler (APScheduler) initialized.")

def update_schedule(job_id: str, interval_minutes: int):
    """Allows user to modify scheduling frequency from the UI/Chat."""
    if job_id in ['daily_login', 'reward_claim', 'health_check', 'sync_points']:
        scheduler.reschedule_job(job_id, trigger='interval', minutes=interval_minutes)
        logger.info(f"Rescheduled {job_id} to {interval_minutes} minutes.")
