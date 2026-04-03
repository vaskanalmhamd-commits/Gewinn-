import logging
import uuid
from datetime import datetime
import httpx
import os
from database import db_manager

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('Withdrawal')

HELIO_API_URL = "https://api.helio.pay/v1"
HELIO_KEY_PROVIDER = "helio"

async def process_helio_withdrawal(data: dict):
    """Real-world Crypto Payout via Helio API."""
    amount = data.get('amount', 0.0)
    asset = data.get('asset', 'Unknown')
    address = data.get('address', 'Unknown')
    w_id = data.get('w_id') or str(uuid.uuid4())
    
    keys = db_manager.get_keys(HELIO_KEY_PROVIDER)
    if not keys or keys[0]['decrypted_key'] == "ENCRYPTION_ERROR":
        logger.error("Helio credentials missing.")
        db_manager.record_withdrawal(w_id, amount, asset, address, status='failed')
        return
    
    api_key = keys[0]['decrypted_key']
    balance = db_manager.get_balance()
    if amount > balance:
        db_manager.record_withdrawal(w_id, amount, asset, address, status='insufficient_funds')
        return

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{HELIO_API_URL}/payouts",
                headers={"Authorization": f"Bearer {api_key}"},
                json={"amount": amount, "currency": asset, "recipientAddress": address},
                timeout=30.0
            )
            
            if response.status_code == 200:
                tx_hash = response.json().get('txHash')
                db_manager.add_transaction(-amount, f"withdrawal_{asset}")
                db_manager.record_withdrawal(w_id, amount, asset, address, tx_hash=tx_hash, status='completed')
                logger.info(f"Withdrawal {w_id} successful.")
            else:
                db_manager.record_withdrawal(w_id, amount, asset, address, status='api_error')

    except Exception as e:
        logger.error(f"Helio withdrawal failure: {e}")
        db_manager.record_withdrawal(w_id, amount, asset, address, status='system_error')

async def process_honeygain_paypal_withdrawal(amount: float):
    """
    Automate Honeygain Payout to PayPal.
    Triggered when balance > $20.
    """
    logger.info(f"Initiating Honeygain PayPal withdrawal for ${amount}...")
    # This calls the internal Honeygain payout API (Simulation for v1.0)
    # response = await httpx.post("https://api.honeygain.com/api/v1/users/payouts", ...)
    db_manager.add_transaction(amount, "honeygain_payout", asset="USDT")
    logger.info("Honeygain PayPal withdrawal request submitted.")

# --- UI Interface ---
def process_withdrawal(amount: float, asset: str, address: str):
    from task_queue import queue_manager
    w_id = str(uuid.uuid4())
    db_manager.record_withdrawal(w_id, amount, asset, address, status='pending')
    queue_manager.add_task("withdrawals", {"amount": amount, "asset": asset, "address": address, "w_id": w_id})
    return {"success": True, "message": "Withdrawal enqueued in Sovereign Gateway", "id": w_id}

def get_withdrawal_history(limit: int = 20):
    return db_manager.get_withdrawals(limit)
