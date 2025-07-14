import json
import asyncio
from typing import Dict, Any, List
from datetime import datetime
from src.encryption.field_detector import FieldDetector, DetectedField
from src.encryption.encryption_engine import EncryptionEngine, EncryptedField
from src.pipeline.metadata_handler import MetadataHandler
import logging

class LogProcessor:
    """Main log processing pipeline with field-level encryption."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.field_detector = FieldDetector()
        self.encryption_engine = EncryptionEngine()
        self.metadata_handler = MetadataHandler()
        
        # Statistics
        self.stats = {
            'logs_processed': 0,
            'fields_encrypted': 0,
            'fields_detected': 0,
            'errors': 0
        }
    
    async def process_log(self, log_entry: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single log entry with field-level encryption."""
        try:
            # Create a copy to avoid modifying original
            processed_log = log_entry.copy()
            
            # Add processing metadata
            processed_log['_processing'] = {
                'timestamp': datetime.utcnow().isoformat(),
                'processor_version': '1.0.0',
                'encrypted_fields': []
            }
            
            # Detect sensitive fields
            detected_fields = self.field_detector.detect_sensitive_fields(log_entry)
            self.stats['fields_detected'] += len(detected_fields)
            
            # Encrypt detected fields
            for detected_field in detected_fields:
                encrypted_field = self.encryption_engine.encrypt_field(
                    detected_field.field_value,
                    detected_field.field_type
                )
                
                # Replace original field with encrypted version
                processed_log[detected_field.field_name] = {
                    '_encrypted': True,
                    '_metadata': encrypted_field.to_dict(),
                    '_original_type': detected_field.field_type
                }
                
                # Track encrypted field
                processed_log['_processing']['encrypted_fields'].append({
                    'field_name': detected_field.field_name,
                    'field_type': detected_field.field_type,
                    'key_id': encrypted_field.key_id
                })
                
                self.stats['fields_encrypted'] += 1
            
            # Store metadata
            await self.metadata_handler.store_log_metadata(
                log_id=processed_log.get('id', 'unknown'),
                metadata=processed_log['_processing']
            )
            
            self.stats['logs_processed'] += 1
            return processed_log
            
        except Exception as e:
            self.logger.error(f"Failed to process log: {e}")
            self.stats['errors'] += 1
            raise
    
    async def process_batch(self, log_entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process multiple log entries concurrently."""
        tasks = [self.process_log(log_entry) for log_entry in log_entries]
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    def decrypt_log(self, encrypted_log: Dict[str, Any]) -> Dict[str, Any]:
        """Decrypt a previously encrypted log entry."""
        try:
            decrypted_log = encrypted_log.copy()
            
            for field_name, field_value in encrypted_log.items():
                if isinstance(field_value, dict) and field_value.get('_encrypted'):
                    # Extract encrypted field metadata
                    metadata = field_value['_metadata']
                    encrypted_field = EncryptedField(**metadata)
                    
                    # Decrypt the field
                    decrypted_value = self.encryption_engine.decrypt_field(encrypted_field)
                    decrypted_log[field_name] = decrypted_value
            
            return decrypted_log
            
        except Exception as e:
            self.logger.error(f"Failed to decrypt log: {e}")
            raise
    
    def get_stats(self) -> Dict[str, Any]:
        """Get processing statistics."""
        stats = self.stats.copy()
        stats.update({
            'field_detector_stats': self.field_detector.get_detection_stats(),
            'encryption_stats': self.encryption_engine.get_key_stats()
        })
        return stats
    
    def reset_stats(self):
        """Reset processing statistics."""
        self.stats = {
            'logs_processed': 0,
            'fields_encrypted': 0,
            'fields_detected': 0,
            'errors': 0
        }
