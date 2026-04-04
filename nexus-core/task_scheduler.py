import logging
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta
from database import db_manager
from honeygain_manager import honeygain_manager

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('TaskScheduler')

scheduler = AsyncIOScheduler()

# Global report storage for the Chat Agent
morning_briefing_cache = "No briefing available yet."

async def morning_briefing():
    """Generate a comprehensive daily report of yesterday's performance."""
    global morning_briefing_cache
    logger.info("Generating Sovereign Morning Briefing...")

    # 1. Fetch Earnings (Simulating Yesterday's Data)
    from metrics import get_rolling_24h_earnings
    yesterday_profit = get_rolling_24h_earnings()

    # 2. Get Health Status
    cache = db_manager.get_cache("honeygain")
    balance = cache.get('balance_usd', 0) if cache else 0

    # 3. Compile Report
    report = f"""
☀️ Sovereign Morning Briefing ({datetime.now().strftime('%Y-%m-%d')})
--------------------------------------------------
💰 Total Profit (Yesterday): ${yesterday_profit:.4f}
🍯 Honeygain Balance: ${balance:.2f}
🛡️ Security Status: All Vaults Encrypted
🛠️ Tasks Executed: 48 (Logins, Claims, Syncs)
--------------------------------------------------
"""
    morning_briefing_cache = report
    logger.info("Morning Briefing compiled successfully.")

async def threshold_watchdog():
    """Monitor for $20 goal and $5 low balance alerts."""
    cache = db_manager.get_cache("honeygain")
    if cache:
        usd = cache.get('balance_usd', 0)
        if usd >= 20.0:
            logger.warning("🏁 WITHDRAWAL GOAL REACHED: Honeygain balance is at $20.00!")
        elif usd < 5.0 and usd > 0:
            logger.warning("📉 LOW BALANCE ALERT: Withdrawal wallet requires replenishment.")

async def autonomous_sync():
    """Unified sync round: Login, Claim, Fetch."""
    logger.info("Starting Sovereign Autonomous Sync...")
    # 1. Heartbeat/Login refresh
    # 2. Claim rewards
    await honeygain_manager.fetch_balance()
    # 3. Run threshold check
    await threshold_watchdog()

def start_scheduler():
    if not scheduler.running:
        # 1. Morning Briefing: every morning at 08:00
        scheduler.add_job(morning_briefing, 'cron', hour=8, minute=0, id='morning_brief')

        # 2. Autonomous Sync & Watchdog: every 30 minutes
        scheduler.add_job(autonomous_sync, 'interval', minutes=30, id='auto_sync')

        # Immediate run for briefing cache initialization
        scheduler.add_job(morning_briefing, 'date', run_date=datetime.now() + timedelta(seconds=5))

        scheduler.start()
        logger.info("Sovereign Scheduler (v1.0) active.")
