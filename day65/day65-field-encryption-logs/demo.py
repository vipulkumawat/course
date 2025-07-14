#!/usr/bin/env python3
"""
Demo script for Field-Level Encryption System
Demonstrates the encryption capabilities with sample data.
"""

import asyncio
import json
import time
from src.pipeline.log_processor import LogProcessor

async def run_demo():
    """Run encryption demonstration."""
    print("🔐 Field-Level Encryption Demo")
    print("=" * 50)
    
    processor = LogProcessor()
    
    # Sample logs with various sensitive data
    sample_logs = [
        {
            "id": "ecommerce_001",
            "timestamp": "2025-05-16T14:30:00Z",
            "customer_email": "john.doe@example.com",
            "phone": "555-123-4567",
            "order_id": "ord_abc123",
            "payment_method": "credit_card",
            "amount": 149.99
        },
        {
            "id": "support_002", 
            "timestamp": "2025-05-16T14:31:00Z",
            "support_email": "help@company.com",
            "customer_ssn": "123-45-6789",
            "case_id": "case_456",
            "priority": "high"
        },
        {
            "id": "api_003",
            "timestamp": "2025-05-16T14:32:00Z",
            "api_key": "sk_live_abcdef123456",
            "endpoint": "/api/v1/users",
            "method": "POST",
            "response_time": 150
        }
    ]
    
    print("\n🔍 Processing logs with field-level encryption...")
    
    encrypted_logs = []
    for i, log in enumerate(sample_logs, 1):
        print(f"\n--- Processing Log {i} ---")
        print(f"Original: {json.dumps(log, indent=2)}")
        
        # Encrypt
        encrypted = await processor.process_log(log)
        encrypted_logs.append(encrypted)
        
        print(f"\nEncrypted fields: {len(encrypted['_processing']['encrypted_fields'])}")
        for field_info in encrypted['_processing']['encrypted_fields']:
            print(f"  ✓ {field_info['field_name']} ({field_info['field_type']})")
        
        time.sleep(1)
    
    print("\n🔓 Testing decryption...")
    
    for i, encrypted_log in enumerate(encrypted_logs, 1):
        print(f"\n--- Decrypting Log {i} ---")
        
        # Decrypt
        decrypted = processor.decrypt_log(encrypted_log)
        
        print("Decryption successful! ✓")
        
        # Show a sample decrypted field
        for field_name, field_value in decrypted.items():
            if not field_name.startswith('_') and isinstance(field_value, str) and '@' in field_value:
                print(f"  Sample: {field_name} = {field_value}")
                break
    
    # Show final statistics
    print("\n📊 Final Statistics")
    print("-" * 30)
    stats = processor.get_stats()
    print(f"Logs processed: {stats['logs_processed']}")
    print(f"Fields encrypted: {stats['fields_encrypted']}")
    print(f"Fields detected: {stats['fields_detected']}")
    print(f"Errors: {stats['errors']}")
    
    print("\n✅ Demo completed successfully!")
    print("\n🌐 Start the web dashboard: python src/main.py")
    print("   Then visit: http://localhost:8000")

if __name__ == "__main__":
    asyncio.run(run_demo())
