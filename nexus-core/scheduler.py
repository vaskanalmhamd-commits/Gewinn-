from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
import logging
import random
import asyncio
import datetime
import os
import json
import wallet
from youtube_browser import browse_youtube

# Configure logging for tasks
logging.basicConfig(filename='tasks.log', level=logging.INFO, format='%(asctime)s - %(message)s')

scheduler = AsyncIOScheduler()
recent_runs = []

async def sync_multiple_earnings():
    """Daily sync for Multiple Network earnings ($MULTI)."""
    try:
        # Fetching earnings from node log file in Ubuntu environment
        earnings = 0.0
        log_path = '/data/data/com.termux/files/usr/var/lib/proot-distro/installed-distros/ubuntu/root/multiple.log'
        if os.path.exists(log_path):
            try:
                with open(log_path, 'r') as f:
                    content = f.read()
                    import re
                    match = re.search(r'Earnings:\s*(\d+\.\d+)', content)
                    if match:
                        earnings = float(match.group(1))
            except:
                pass

        if earnings > 0:
            wallet.add_earnings(earnings, "multiple")
            logging.info(f"Synced {earnings} $MULTI from node logs")
    except Exception as e:
        logging.error(f"Failed to sync Multiple earnings: {str(e)}")

async def sync_grass_earnings():
    """Periodically sync new GRASS points to wallet balance."""
    try:
        if os.path.exists('config/grass_points.json'):
            with open('config/grass_points.json', 'r') as f:
                data = json.load(f)

            total_points = data.get('points', 0)
            last_synced = data.get('last_synced_points', 0)
            new_points = total_points - last_synced

            if new_points > 0:
                wallet.convert_grass_points(new_points)
                data['last_synced_points'] = total_points
                with open('config/grass_points.json', 'w') as f:
                    json.dump(data, f)
                logging.info(f"Synced {new_points} new GRASS points to wallet")
    except Exception as e:
        logging.error(f"Failed to sync GRASS earnings: {str(e)}")

async def run_youtube_task():
    try:
        logging.info("Starting YouTube task")
        duration = random.randint(300, 900)  # 5-15 minutes
        await browse_youtube(duration)
        logging.info("YouTube task completed successfully")
        # Reward user for successful session
        reward_amount = round(random.uniform(0.005, 0.02), 5)
        try:
            wallet.add_earnings(reward_amount, "youtube")
            logging.info("Added reward %s to wallet", reward_amount)
        except Exception as e:
            logging.error("Failed to add wallet reward: %s", str(e))

        recent_runs.append({
            "status": "success",
            "duration": duration,
            "reward": reward_amount,
            "timestamp": datetime.datetime.now().isoformat()
        })
    except Exception as e:
        logging.error("YouTube task failed: %s", str(e))
        recent_runs.append({
            "status": "failure",
            "error": str(e),
            "timestamp": datetime.datetime.now().isoformat()
        })
    # Keep only last 10 runs
    if len(recent_runs) > 10:
        recent_runs.pop(0)

def start_scheduler(interval_hours=2):
    scheduler.add_job(run_youtube_task, trigger=IntervalTrigger(hours=interval_hours), max_instances=1)
    # Sync GRASS points every hour
    scheduler.add_job(sync_grass_earnings, trigger=IntervalTrigger(hours=1), max_instances=1)
    # Sync Multiple earnings daily
    scheduler.add_job(sync_multiple_earnings, trigger=IntervalTrigger(hours=24), max_instances=1)
    scheduler.start()

def get_status():
    jobs = scheduler.get_jobs()
    next_run = None
    if jobs:
        next_run = jobs[0].next_run_time.isoformat() if jobs[0].next_run_time else None
    return {
        "next_run": next_run,
        "recent_runs": recent_runs[-5:]  # Last 5 runs
    }