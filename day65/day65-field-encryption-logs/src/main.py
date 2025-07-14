import asyncio
import logging
import signal
import sys
import json
from typing import List, Dict, Any
from src.pipeline.log_processor import LogProcessor
from src.web.dashboard import app
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class FieldEncryptionService:
    """Main service for field-level encryption demonstration."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.log_processor = LogProcessor()
        self.running = False
        
    async def start_demo_processing(self):
        """Start demo log processing to show encryption in action."""
        self.running = True
        self.logger.info("Starting field encryption demo processing...")
        
        # Sample log data for demonstration
        sample_logs = [
            {
                "id": "log_001",
                "timestamp": "2025-05-16T10:30:00Z",
                "user_email": "john.doe@example.com",
                "phone": "555-123-4567",
                "request_id": "req_12345",
                "action": "login_attempt",
                "ip_address": "192.168.1.100"
            },
            {
                "id": "log_002",
                "timestamp": "2025-05-16T10:31:00Z",
                "customer_phone": "555-987-6543",
                "order_id": "ord_67890",
                "payment_method": "credit_card",
                "amount": 99.99,
                "currency": "USD"
            },
            {
                "id": "log_003",
                "timestamp": "2025-05-16T10:32:00Z",
                "support_email": "support@company.com",
                "user_ssn": "123-45-6789",
                "case_id": "case_111",
                "priority": "high",
                "department": "billing"
            },
            {
                "id": "log_004",
                "timestamp": "2025-05-16T10:33:00Z",
                "api_key": "sk_live_1234567890abcdef",
                "endpoint": "/api/v1/users",
                "method": "POST",
                "response_time": 150,
                "status_code": 200
            }
        ]
        
        counter = 0
        while self.running:
            try:
                # Process each sample log
                for original_log in sample_logs:
                    if not self.running:
                        break
                    
                    # Create a copy to avoid modifying the original
                    log_entry = original_log.copy()
                    log_entry["id"] = f"{log_entry['id']}_batch_{counter}"
                    
                    # Process log with encryption
                    processed_log = await self.log_processor.process_log(log_entry)
                    
                    # Validate and log encryption results
                    self._validate_encryption(original_log, processed_log, log_entry['id'])
                    
                    self.logger.info(f"Processed log: {log_entry['id']}")
                    
                    # Wait between logs
                    await asyncio.sleep(2)
                
                counter += 1
                await asyncio.sleep(5)  # Wait before next batch
                
            except Exception as e:
                self.logger.error(f"Error in demo processing: {e}")
                await asyncio.sleep(10)
    
    def _validate_encryption(self, original_log: Dict, processed_log: Dict, log_id: str):
        """Validate that encryption is working correctly and print results."""
        encrypted_fields = []
        unchanged_fields = []
        
        for field_name, field_value in processed_log.items():
            if field_name == '_processing':
                continue
                
            if isinstance(field_value, dict) and field_value.get('_encrypted'):
                # This field was encrypted
                original_value = original_log.get(field_name, 'N/A')
                encrypted_fields.append({
                    'field': field_name,
                    'original': original_value,
                    'encrypted_value': field_value['_metadata']['encrypted_value'][:20] + '...',
                    'type': field_value['_original_type'],
                    'key_id': field_value['_metadata']['key_id']
                })
            else:
                # This field was not encrypted
                unchanged_fields.append(field_name)
        
        # Print validation results
        print(f"\n🔐 ENCRYPTION VALIDATION for {log_id}")
        print("=" * 60)
        
        if encrypted_fields:
            print(f"✅ ENCRYPTED FIELDS ({len(encrypted_fields)}):")
            for field in encrypted_fields:
                print(f"   📧 {field['field']} ({field['type']})")
                print(f"      Original: {field['original']}")
                print(f"      Encrypted: {field['encrypted_value']}")
                print(f"      Key: {field['key_id']}")
                print()
        else:
            print("❌ NO FIELDS WERE ENCRYPTED!")
            print("   This indicates a problem with field detection or encryption.")
            print()
        
        if unchanged_fields:
            print(f"📝 UNCHANGED FIELDS ({len(unchanged_fields)}):")
            for field in unchanged_fields:
                print(f"   • {field}")
            print()
        
        # Print full processed log for debugging
        print("📋 FULL PROCESSED LOG:")
        print(json.dumps(processed_log, indent=2))
        print("=" * 60)
    
    def stop(self):
        """Stop the demo processing."""
        self.running = False
        self.logger.info("Stopping field encryption demo...")

async def start_web_dashboard():
    """Start the web dashboard."""
    config = uvicorn.Config(app, host="0.0.0.0", port=8000, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

async def main():
    """Main application entry point."""
    service = FieldEncryptionService()
    
    # Handle shutdown gracefully
    def signal_handler(signum, frame):
        print("\nShutting down gracefully...")
        service.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start both demo processing and web dashboard
    await asyncio.gather(
        service.start_demo_processing(),
        start_web_dashboard()
    )

if __name__ == "__main__":
    asyncio.run(main())
