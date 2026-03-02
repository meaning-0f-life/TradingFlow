from cryptography.fernet import Fernet
import hashlib
import base64

class EncryptionService:
    """Service for encrypting and decrypting sensitive data"""

    def __init__(self, master_key: str):
        """
        Initialize encryption service with master key

        Args:
            master_key: Master encryption key (should be stored in environment variables)
        """
        if not master_key:
            raise ValueError("Master encryption key is required")

        # Derive a 32-byte key from the master key using SHA256
        key_bytes = hashlib.sha256(master_key.encode()).digest()
        # Encode to URL-safe base64 for Fernet
        key = base64.urlsafe_b64encode(key_bytes)
        self.cipher = Fernet(key)

    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt a string

        Args:
            plaintext: String to encrypt

        Returns:
            Encrypted string (base64 encoded)
        """
        if not plaintext:
            return ""
        encrypted = self.cipher.encrypt(plaintext.encode())
        return encrypted.decode()

    def decrypt(self, encrypted_text: str) -> str:
        """
        Decrypt a string

        Args:
            encrypted_text: Encrypted string (base64 encoded)

        Returns:
            Decrypted string
        """
        if not encrypted_text:
            return ""
        decrypted = self.cipher.decrypt(encrypted_text.encode())
        return decrypted.decode()

    @staticmethod
    def generate_key() -> str:
        """Generate a new random encryption key"""
        return Fernet.generate_key().decode()