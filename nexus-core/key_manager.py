import logging
from datetime import datetime
from database import db_manager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('KeyManager')

class KeyClient:
    """Pre-configured Client Object returned to the AI Agent."""
    def __init__(self, key_id: int, provider: str, raw_key: str, base_url: str):
        self.id = key_id
        self.provider = provider
        self.raw_key = raw_key
        self.base_url = base_url or self._default_url(provider)
        self.headers = {"Authorization": f"Bearer {raw_key}", "Content-Type": "application/json"}

    def _default_url(self, provider):
        urls = {
            "openai": "https://api.openai.com/v1",
            "anthropic": "https://api.anthropic.com/v1",
            "groq": "https://api.groq.com/openai/v1",
            "gemini": "https://generativelanguage.googleapis.com/v1beta",
            "huggingface": "https://api-inference.huggingface.co/models"
        }
        return urls.get(provider.lower(), "")

    def report_success(self):
        db_manager.update_key_health(self.id, failure=False)

    def report_failure(self, rate_limit=False):
        db_manager.update_key_health(self.id, failure=True, rate_limit=rate_limit)

def get_next_key(provider) -> KeyClient:
    """
    Universal Key Manager: Returns a KeyClient object with
    Round-Robin selection and Health monitoring.
    """
    provider = provider.lower()
    keys = db_manager.get_keys(provider)

    # Filter for valid and non-suspended keys
    now = datetime.now().isoformat()
    valid_keys = []
    for k in keys:
        if k['decrypted_key'] == "ENCRYPTION_ERROR": continue
        if k['suspended_until'] and k['suspended_until'] > now: continue
        if k['remaining_quota'] <= 0: continue
        valid_keys.append(k)

    if not valid_keys:
        logger.error(f"No active keys found for provider: {provider}")
        return None

    # Select oldest used key (Round-Robin)
    valid_keys.sort(key=lambda x: x.get('last_used') or '')
    selected = valid_keys[0]

    return KeyClient(
        key_id=selected['id'],
        provider=selected['provider'],
        raw_key=selected['decrypted_key'],
        base_url=selected['base_url']
    )

def add_key(provider, key_text, base_url=None):
    db_manager.add_key(provider, key_text, base_url)

def list_keys():
    keys = db_manager.get_keys()
    masked_keys = []
    now = datetime.now().isoformat()
    for k in keys:
        key_text = k['decrypted_key']
        status = "Active"
        if key_text == "ENCRYPTION_ERROR": status = "Locked"
        elif k['suspended_until'] and k['suspended_until'] > now: status = f"Suspended until {k['suspended_until']}"

        masked = key_text[:2] + '*' * (len(key_text) - 4) + key_text[-2:] if len(key_text) > 4 else key_text
        masked_keys.append({
            'id': k['id'],
            'provider': k['provider'],
            'key': masked,
            'status': status,
            'quota': k['remaining_quota'],
            'last_used': k['last_used']
        })
    return masked_keys
