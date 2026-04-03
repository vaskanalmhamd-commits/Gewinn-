from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import logging
import random
import asyncio
import datetime
import wallet
from youtube_browser import browse_youtube

# Configure logging for tasks
logging.basicConfig(filename='tasks.log', level=logging.INFO, format='%(asctime)s - %(message)s')

scheduler = BackgroundScheduler()
recent_runs = []

async def sync_grass_earnings():
    """Periodically sync GRASS points to wallet balance."""
    try:
        if os.path.exists('grass_points.json'):
            with open('grass_points.json', 'r') as f:
                data = json.load(f)
                points = data.get('points', 0)
                if points > 0:
                    wallet.convert_grass_points(points)
                    logging.info(f"Synced {points} GRASS points to wallet")
                    # Optionally reset points after sync or track 'synced_points'
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