import os
import base64
import logging
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.fernet import Fernet
from cryptography.exceptions import InvalidKey

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('Security')

# Salt file path
SALT_FILE = os.path.join(os.path.dirname(__file__), 'config', '.salt')

class SecurityManager:
    _instance = None
    _fernet = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SecurityManager, cls).__new__(cls)
        return cls._instance

    def initialize(self, master_password: str):
        """Initialize the Fernet instance using the master password."""
        salt = self._get_or_create_salt()
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(master_password.encode()))
        self._fernet = Fernet(key)
        logger.info("Security manager initialized successfully.")

    def _get_or_create_salt(self):
        """Retrieve or generate a unique salt for key derivation."""
        os.makedirs(os.path.dirname(SALT_FILE), exist_ok=True)
        if os.path.exists(SALT_FILE):
            with open(SALT_FILE, 'rb') as f:
                return f.read()
        else:
            salt = os.urandom(16)
            with open(SALT_FILE, 'wb') as f:
                f.write(salt)
            return salt

    def encrypt(self, data: str) -> str:
        """Encrypt a string and return the base64-encoded ciphertext."""
        if not self._fernet:
            raise RuntimeError("Security manager not initialized. Master password required.")
        return self._fernet.encrypt(data.encode()).decode()

    def decrypt(self, ciphertext: str) -> str:
        """Decrypt a ciphertext string and return the plaintext."""
        if not self._fernet:
            raise RuntimeError("Security manager not initialized. Master password required.")
        try:
            return self._fernet.decrypt(ciphertext.encode()).decode()
        except InvalidKey:
            logger.error("Decryption failed. Invalid master password or corrupted data.")
            raise ValueError("Invalid master password or corrupted data.")

# Global instance
security_manager = SecurityManager()
