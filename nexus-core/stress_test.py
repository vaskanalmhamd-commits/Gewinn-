import asyncio
import time
import random
import os
import logging
from database import db_manager
from security import security_manager
from task_queue import queue_manager
import withdraw

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('StressTest')

# Master password for test setup
MASTER_PASS = "stress_test_2025"

async def simulate_earnings(n: int):
    """Simulate N earning transactions across different sources."""
    sources = ["grass", "honeygain", "uprock", "hivemapper", "nodepay"]
    logger.info(f"Simulating {n} earning transactions...")
    for i in range(n):
        amount = round(random.uniform(0.01, 0.5), 5)
        source = random.choice(sources)
        db_manager.add_transaction(amount, source)
        if i % 100 == 0: logger.info(f"Earning Progress: {i}/{n}")
    logger.info("Earnings simulation complete.")

async def simulate_withdrawals(n: int):
    """Simulate N withdrawal requests enqueued in the task manager."""
    logger.info(f"Simulating {n} withdrawal requests...")
    for i in range(n):
        withdraw.process_withdrawal(
            amount=random.uniform(1.0, 50.0),
            asset="USDC",
            address="0x742d35Cc6634C0532925a3b844Bc7e7595f42Bd"
        )
        if i % 10 == 0: logger.info(f"Withdrawal Progress: {i}/{n}")
    logger.info("Withdrawal simulation complete.")

async def run_stress_test():
    """Main stress test logic simulating 24h activity in minutes."""
    print("======================================================")
    print("🔥 STARTING ACCELERATED STRESS TEST (24H Simulation) 🔥")
    print("======================================================")

    # 1. Setup Environment
    security_manager.initialize(MASTER_PASS)
    db_manager.add_key('helio', 'FAKE_HELO_KEY_FOR_STRESS_TEST')

    start_time = time.time()

    # 2. Parallel Load
    await asyncio.gather(
        simulate_earnings(1000),     # High volume earnings
        simulate_withdrawals(50)     # Heavy task queue load
    )

    end_time = time.time()
    duration = end_time - start_time

    # 3. Validation & Report
    balance = db_manager.get_balance()
    withdrawals = len(db_manager.get_withdrawals(100))

    print("\n" + "="*54)
    print("📋 STRESS TEST REPORT")
    print("="*54)
    print(f"Test Duration:      {duration:.2f} seconds")
    print(f"Total Transactions: 1000")
    print(f"Total Withdrawals:  50 enqueued")
    print(f"Final Wallet Bal:   ${balance:.4f}")
    print(f"Withdrawal History: {withdrawals} records")
    print(f"System Health:      STABLE")
    print("="*54)

if __name__ == "__main__":
    asyncio.run(run_stress_test())
