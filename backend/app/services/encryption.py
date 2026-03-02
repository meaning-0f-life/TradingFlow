from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
import base64
import os
from typing import Union

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

        # Derive a key from the master key
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'tradingflow_salt',  # In production, use a random salt per installation
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(master_key.encode()))
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