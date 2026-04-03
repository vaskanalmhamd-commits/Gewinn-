from dotenv import load_dotenv
import os

load_dotenv('config/keys.env')

keys = {}
indices = {}

for key, value in os.environ.items():
    if key.endswith('_APIKEY'):
        provider = key.replace('_APIKEY', '').upper()
        keys[provider] = value.split(',')
        indices[provider] = 0

def get_next_key(provider):
    provider = provider.upper()
    if provider not in keys:
        raise ValueError(f"No keys for provider {provider}")
    key_list = keys[provider]
    if not key_list:
        raise ValueError(f"No keys available for provider {provider}")
    key = key_list[indices[provider]]
    indices[provider] = (indices[provider] + 1) % len(key_list)
    return key