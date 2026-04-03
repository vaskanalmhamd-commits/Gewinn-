import logging
import threading
import uuid
from datetime import datetime
from typing import Dict, List
import wallet

logging.basicConfig(filename='withdrawals.log', level=logging.INFO, format='%(asctime)s - %(message)s')

withdraw_lock = threading.Lock()
withdrawal_history: List[Dict] = []

class WithdrawalError(Exception):
    """Custom exception for withdrawal operations."""
    pass

def validate_address(address: str, asset: str) -> bool:
    """Validate crypto address format (basic mock validation)."""
    if asset == 'BTC':
        # Mock: BTC addresses start with 1, 3, or bc1
        return len(address) >= 26 and address[0] in '13b'
    elif asset == 'USDT' or asset == 'ETH':
        # Mock: Ethereum-style addresses are 42 chars (0x...)
        return len(address) == 42 and address.startswith('0x')
    return False

def process_crypto_payment(amount: float, asset: str, address: str) -> Dict:
    """Mock crypto payment processor - simulates API call to payment service."""
    # In production, this would call real API like heleket, bitso, etc.
    
    # Simulate network delay
    import time
    time.sleep(0.5)
    
    # Simulate success with 95% probability for demo
    import random
    if random.random() > 0.95:
        raise WithdrawalError(f"Payment gateway timeout")
    
    # Generate mock transaction hash
    tx_hash = f"0x{uuid.uuid4().hex[:64]}"
    
    logging.info(f"Mock crypto payment processed: {amount} {asset} to {address}")
    return {
        'tx_hash': tx_hash,
        'status': 'success',
        'timestamp': datetime.now().isoformat()
    }

def process_withdrawal(amount: float, asset: str, address: str) -> Dict:
    """Process a cryptocurrency withdrawal request."""
    try:
        with withdraw_lock:
            # Validate inputs
            if amount <= 0:
                raise WithdrawalError("Amount must be positive")
            
            if amount > 100:  # Demo limit
                raise WithdrawalError("Amount exceeds daily limit (max 100)")
            
            if not asset in ['BTC', 'USDT', 'ETH']:
                raise WithdrawalError(f"Unsupported asset: {asset}")
            
            if not validate_address(address, asset):
                raise WithdrawalError(f"Invalid {asset} address format")
            
            # Check wallet balance
            current_balance = wallet.get_balance()
            if amount > current_balance:
                raise WithdrawalError(f"Insufficient balance. Current: {current_balance}, Requested: {amount}")
            
            # Process payment (mock)
            payment_result = process_crypto_payment(amount, asset, address)
            
            # Deduct from wallet (negative transaction)
            new_balance = wallet.add_earnings(-amount, f"withdrawal_{asset}", status='withdrawn')
            
            # Record withdrawal
            withdrawal_record = {
                'id': str(uuid.uuid4()),
                'amount': amount,
                'asset': asset,
                'address': address[:10] + '...' + address[-8:],  # Mask address
                'tx_hash': payment_result['tx_hash'],
                'status': 'completed',
                'timestamp': datetime.now().isoformat(),
                'balance_after': new_balance
            }
            
            withdrawal_history.append(withdrawal_record)
            
            # Keep only last 50 withdrawals
            if len(withdrawal_history) > 50:
                withdrawal_history.pop(0)
            
            logging.info(f"Withdrawal processed: {amount} {asset} to {address}, balance after: {new_balance}")
            
            return {
                'success': True,
                'message': 'Withdrawal processed successfully',
                'tx_id': withdrawal_record['id'],
                'tx_hash': payment_result['tx_hash'],
                'new_balance': new_balance
            }
    
    except WithdrawalError as e:
        logging.error(f"Withdrawal failed: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }
    except Exception as e:
        logging.error(f"Unexpected error during withdrawal: {str(e)}")
        return {
            'success': False,
            'error': 'Internal server error'
        }

def get_withdrawal_history(limit: int = 20) -> List[Dict]:
    """Get recent withdrawal history."""
    with withdraw_lock:
        return withdrawal_history[-limit:][::-1]  # Return in reverse chronological order

def get_withdrawal_stats() -> Dict:
    """Get withdrawal statistics."""
    with withdraw_lock:
        total_withdrawn = sum(w['amount'] for w in withdrawal_history)
        return {
            'total_withdrawn': total_withdrawn,
            'withdrawal_count': len(withdrawal_history),
            'supported_assets': ['BTC', 'USDT', 'ETH']
        }
