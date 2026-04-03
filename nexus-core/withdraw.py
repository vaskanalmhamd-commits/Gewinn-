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
    """
    Process a withdrawal using the Helio API.
    Called by the SimplePyQ background worker.
    """
    amount = data.get('amount', 0.0)
    asset = data.get('asset', 'Unknown')
    address = data.get('address', 'Unknown')
    w_id = data.get('w_id') or str(uuid.uuid4())
    
    # 1. Fetch encrypted Helio API Key from DB
    keys = db_manager.get_keys(HELIO_KEY_PROVIDER)
    if not keys or keys[0]['decrypted_key'] == "ENCRYPTION_ERROR":
        logger.error("Helio API key not found or decryption failed. Withdrawal aborted.")
        db_manager.record_withdrawal(w_id, amount, asset, address, status='failed')
        return
    
    api_key = keys[0]['decrypted_key']
    
    # 2. Check Wallet Balance
    balance = db_manager.get_balance()
    if amount > balance:
        logger.error(f"Insufficient balance for withdrawal: {balance} < {amount}")
        db_manager.record_withdrawal(w_id, amount, asset, address, status='insufficient_funds')
        return

    # 3. Request Helio Payout
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{HELIO_API_URL}/payouts",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={
                    "amount": amount,
                    "currency": asset,
                    "recipientAddress": address,
                    "network": "solana" if asset == "USDC" else "ethereum"
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                result = response.json()
                tx_hash = result.get('txHash')
                logger.info(f"Helio withdrawal successful: {tx_hash}")

                # 4. Record Success & Deduct Balance
                db_manager.add_transaction(-amount, f"withdrawal_{asset}", status='completed')
                db_manager.record_withdrawal(w_id, amount, asset, address, tx_hash=tx_hash, status='completed')
            else:
                logger.error(f"Helio API error: {response.status_code} - {response.text}")
                db_manager.record_withdrawal(w_id, amount, asset, address, status='api_error')

    except Exception as e:
        logger.error(f"Error during Helio payout processing: {e}")
        db_manager.record_withdrawal(w_id, amount, asset, address, status='system_error')

# --- UI Helper Functions ---
def process_withdrawal(amount: float, asset: str, address: str):
    from task_queue import queue_manager
    w_id = str(uuid.uuid4())
    # Log initial pending state in DB
    db_manager.record_withdrawal(w_id, amount, asset, address, status='pending')
    # Enqueue for background processing
    queue_manager.add_task("withdrawals", {
        "amount": amount,
        "asset": asset,
        "address": address,
        "w_id": w_id
    })
    return {"success": True, "message": "Withdrawal enqueued", "id": w_id}

def get_withdrawal_history(limit: int = 20):
    return db_manager.get_withdrawals(limit)

def get_withdrawal_stats():
    withdrawals = db_manager.get_withdrawals(500)
    total = sum(w['amount'] for w in withdrawals if w['status'] == 'completed')
    return {
        "total_withdrawn": total,
        "withdrawal_count": len(withdrawals),
        "supported_assets": ["BTC", "USDT", "ETH", "USDC"]
    }
