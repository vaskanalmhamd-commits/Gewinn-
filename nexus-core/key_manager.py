import logging
from database import db_manager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('KeyManager')

def get_next_key(provider):
    """
    Round-Robin distribution: Fetches keys for a provider,
    sorted by last_used (ascending), and returns the oldest one.
    """
    provider = provider.lower()
    keys = db_manager.get_keys(provider)

    if not keys:
        logger.error(f"No keys found for provider: {provider}")
        raise ValueError(f"No keys available for provider {provider}")

    # Round-robin: oldest used key is first in the sorted list
    selected_key = keys[0]
    return selected_key['decrypted_key']

def add_key(provider, key_text):
    db_manager.add_key(provider, key_text)

def list_keys():
    keys = db_manager.get_keys()
    masked_keys = []
    for k in keys:
        key_text = k['decrypted_key']
        masked = key_text[:2] + '*' * (len(key_text) - 4) + key_text[-2:] if len(key_text) > 4 else key_text
        masked_keys.append({
            'id': k['id'],
            'provider': k['provider'],
            'key': masked,
            'remaining_quota': k['remaining_quota'],
            'last_used': k['last_used']
        })
    return masked_keys

def delete_key(key_id):
    # db_manager.delete_key(key_id)
    # Not implemented in database.py yet, but logic is simplified
    pass
