import os
import base64
import json
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from datetime import datetime, timedelta
import logging

@dataclass
class EncryptedField:
    encrypted_value: str
    key_id: str
    algorithm: str
    field_type: str
    encryption_timestamp: str
    iv: str = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class EncryptionKey:
    key_id: str
    key_value: bytes
    created_at: datetime
    expires_at: datetime
    algorithm: str = "AES-256-GCM"
    
    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at

class EncryptionEngine:
    """AES-256-GCM encryption engine for field-level encryption."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.current_key = self._generate_key()
        self.key_cache = {self.current_key.key_id: self.current_key}
        
    def encrypt_field(self, plaintext: str, field_type: str) -> EncryptedField:
        """Encrypt a single field using AES-256-GCM."""
        try:
            key = self._get_current_key()
            
            # Generate random IV for GCM (96 bits recommended)
            iv = os.urandom(12)
            
            # Create cipher
            cipher = Cipher(
                algorithms.AES(key.key_value),
                modes.GCM(iv),
                backend=default_backend()
            )
            encryptor = cipher.encryptor()
            
            # Encrypt the plaintext
            ciphertext = encryptor.update(plaintext.encode('utf-8'))
            encryptor.finalize()
            
            # Get authentication tag
            auth_tag = encryptor.tag
            
            # Combine IV + auth_tag + ciphertext for storage
            encrypted_data = iv + auth_tag + ciphertext
            encoded_data = base64.b64encode(encrypted_data).decode('utf-8')
            
            return EncryptedField(
                encrypted_value=encoded_data,
                key_id=key.key_id,
                algorithm=key.algorithm,
                field_type=field_type,
                encryption_timestamp=datetime.utcnow().isoformat(),
                iv=base64.b64encode(iv).decode('utf-8')
            )
            
        except Exception as e:
            self.logger.error(f"Encryption failed for field type {field_type}: {e}")
            raise
    
    def decrypt_field(self, encrypted_field: EncryptedField) -> str:
        """Decrypt a field using AES-256-GCM."""
        try:
            key = self._get_key_by_id(encrypted_field.key_id)
            if not key:
                raise ValueError(f"Key {encrypted_field.key_id} not found")
            
            # Decode the encrypted data
            encrypted_data = base64.b64decode(encrypted_field.encrypted_value)
            
            # Extract components
            iv = encrypted_data[:12]  # First 12 bytes
            auth_tag = encrypted_data[12:28]  # Next 16 bytes  
            ciphertext = encrypted_data[28:]  # Remaining bytes
            
            # Create cipher for decryption
            cipher = Cipher(
                algorithms.AES(key.key_value),
                modes.GCM(iv, auth_tag),
                backend=default_backend()
            )
            decryptor = cipher.decryptor()
            
            # Decrypt and verify
            plaintext = decryptor.update(ciphertext)
            decryptor.finalize()  # Verifies authentication tag
            
            return plaintext.decode('utf-8')
            
        except Exception as e:
            self.logger.error(f"Decryption failed for key {encrypted_field.key_id}: {e}")
            raise
    
    def _generate_key(self) -> EncryptionKey:
        """Generate a new AES-256 encryption key."""
        key_id = f"key-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
        key_value = os.urandom(32)  # 256 bits
        created_at = datetime.utcnow()
        expires_at = created_at + timedelta(days=30)
        
        return EncryptionKey(
            key_id=key_id,
            key_value=key_value,
            created_at=created_at,
            expires_at=expires_at
        )
    
    def _get_current_key(self) -> EncryptionKey:
        """Get current encryption key, rotating if necessary."""
        if self.current_key.is_expired():
            self.logger.info(f"Rotating expired key {self.current_key.key_id}")
            self.current_key = self._generate_key()
            self.key_cache[self.current_key.key_id] = self.current_key
            
        return self.current_key
    
    def _get_key_by_id(self, key_id: str) -> Optional[EncryptionKey]:
        """Retrieve key by ID from cache."""
        return self.key_cache.get(key_id)
    
    def get_key_stats(self) -> Dict[str, Any]:
        """Get key management statistics."""
        return {
            'current_key_id': self.current_key.key_id,
            'key_count': len(self.key_cache),
            'current_key_expires': self.current_key.expires_at.isoformat(),
            'keys_in_cache': list(self.key_cache.keys())
        }
