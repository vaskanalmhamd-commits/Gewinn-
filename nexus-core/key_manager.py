import logging
from database import db_manager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('KeyManager')

def get_next_key(provider):
    """
    Round-Robin distribution with health checks.
    """
    provider = provider.lower()
    keys = db_manager.get_keys(provider)

    valid_keys = [k for k in keys if k['decrypted_key'] != "ENCRYPTION_ERROR" and k['remaining_quota'] > 0]

    if not valid_keys:
        logger.error(f"No active/valid keys found for provider: {provider}")
        return None

    # Sort by last_used to implement Round-Robin
    valid_keys.sort(key=lambda x: x.get('last_used') or '')

    selected_key = valid_keys[0]
    # In a real system, we'd update 'last_used' and decrement 'remaining_quota' in DB here
    return selected_key['decrypted_key']

def add_key(provider, key_text):
    db_manager.add_key(provider, key_text)

def list_keys():
    keys = db_manager.get_keys()
    masked_keys = []
    for k in keys:
        key_text = k['decrypted_key']
        if key_text == "ENCRYPTION_ERROR":
            masked = "LOCKED"
        else:
            masked = key_text[:2] + '*' * (len(key_text) - 4) + key_text[-2:] if len(key_text) > 4 else key_text

        masked_keys.append({
            'id': k['id'],
            'provider': k['provider'],
            'key': masked,
            'remaining_quota': k['remaining_quota'],
            'last_used': k['last_used']
        })
    return masked_keys
