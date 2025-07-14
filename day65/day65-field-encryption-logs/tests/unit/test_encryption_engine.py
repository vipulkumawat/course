import pytest
from src.encryption.encryption_engine import EncryptionEngine, EncryptedField

class TestEncryptionEngine:
    """Test suite for encryption engine functionality."""
    
    def setup_method(self):
        self.engine = EncryptionEngine()
    
    def test_encrypt_field(self):
        """Test field encryption."""
        plaintext = "john.doe@example.com"
        field_type = "email"
        
        encrypted = self.engine.encrypt_field(plaintext, field_type)
        
        assert isinstance(encrypted, EncryptedField)
        assert encrypted.field_type == field_type
        assert encrypted.algorithm == "AES-256-GCM"
        assert encrypted.encrypted_value != plaintext
        assert len(encrypted.encrypted_value) > 0
    
    def test_decrypt_field(self):
        """Test field decryption."""
        plaintext = "555-123-4567"
        field_type = "phone"
        
        # Encrypt first
        encrypted = self.engine.encrypt_field(plaintext, field_type)
        
        # Then decrypt
        decrypted = self.engine.decrypt_field(encrypted)
        
        assert decrypted == plaintext
    
    def test_encrypt_decrypt_cycle(self):
        """Test complete encryption-decryption cycle."""
        test_values = [
            "john.doe@example.com",
            "555-987-6543",
            "secret_api_key_12345",
            "123-45-6789"
        ]
        
        for plaintext in test_values:
            encrypted = self.engine.encrypt_field(plaintext, "test")
            decrypted = self.engine.decrypt_field(encrypted)
            assert decrypted == plaintext
    
    def test_different_encryptions(self):
        """Test that same plaintext produces different ciphertexts."""
        plaintext = "john.doe@example.com"
        
        encrypted1 = self.engine.encrypt_field(plaintext, "email")
        encrypted2 = self.engine.encrypt_field(plaintext, "email")
        
        # Should be different due to random IV
        assert encrypted1.encrypted_value != encrypted2.encrypted_value
        
        # But both should decrypt to same plaintext
        decrypted1 = self.engine.decrypt_field(encrypted1)
        decrypted2 = self.engine.decrypt_field(encrypted2)
        
        assert decrypted1 == decrypted2 == plaintext
    
    def test_key_stats(self):
        """Test key statistics retrieval."""
        stats = self.engine.get_key_stats()
        
        assert 'current_key_id' in stats
        assert 'key_count' in stats
        assert 'current_key_expires' in stats
        assert stats['key_count'] >= 1
