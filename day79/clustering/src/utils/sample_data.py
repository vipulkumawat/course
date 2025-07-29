import random
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any
from dataclasses import dataclass
import uuid

@dataclass
class LogEntry:
    timestamp: str
    service: str
    level: str
    component: str
    message: str
    source_ip: str
    request_size: int
    response_size: int
    response_time: int
    status_code: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp,
            'service': self.service,
            'level': self.level,
            'component': self.component,
            'message': self.message,
            'source_ip': self.source_ip,
            'request_size': self.request_size,
            'response_size': self.response_size,
            'response_time': self.response_time,
            'status_code': self.status_code
        }

def generate_sample_logs(count: int = 100) -> List[LogEntry]:
    """Generate sample log entries for testing and demonstration"""
    
    services = ['auth', 'user', 'payment', 'inventory', 'recommendation']
    levels = ['INFO', 'WARN', 'ERROR', 'DEBUG']
    components = ['api', 'database', 'cache', 'queue', 'worker']
    
    # Message templates by service and level
    message_templates = {
        'auth': {
            'INFO': [
                'User {} successfully authenticated',
                'Session created for user {}',
                'Password reset requested for {}',
                'OAuth token refreshed for user {}'
            ],
            'WARN': [
                'Multiple failed login attempts for user {}',
                'Suspicious login pattern detected from IP {}',
                'Account locked due to failed attempts: {}',
                'Unusual access time for user {}'
            ],
            'ERROR': [
                'Authentication failed for user {}',
                'Database connection failed during auth',
                'JWT token validation failed for {}',
                'LDAP server unreachable for user {}'
            ]
        },
        'payment': {
            'INFO': [
                'Payment processed successfully: ${}',
                'Credit card authorized for amount ${}',
                'Refund processed for transaction {}',
                'Payment method updated for user {}'
            ],
            'WARN': [
                'High-value transaction flagged: ${}',
                'Payment retry attempt {} for user {}',
                'Unusual spending pattern detected for {}',
                'Credit card expires soon for user {}'
            ],
            'ERROR': [
                'Payment processing failed: {}',
                'Credit card declined for user {}',
                'Payment gateway timeout for transaction {}',
                'Insufficient funds for user {}'
            ]
        },
        'inventory': {
            'INFO': [
                'Stock updated for product {}: {} units',
                'Product {} added to catalog',
                'Inventory sync completed for warehouse {}',
                'Low stock alert threshold updated for {}'
            ],
            'WARN': [
                'Low stock warning for product {}: {} remaining',
                'Unusual order quantity for product {}: {}',
                'Supplier delivery delayed for product {}',
                'Price fluctuation detected for product {}'
            ],
            'ERROR': [
                'Out of stock error for product {}',
                'Inventory database sync failed',
                'Product {} not found in catalog',
                'Warehouse {} connection failed'
            ]
        }
    }
    
    logs = []
    start_time = datetime.now() - timedelta(hours=24)
    
    for i in range(count):
        # Generate timestamp
        timestamp = start_time + timedelta(minutes=random.randint(0, 1440))
        
        # Select service, level, component
        service = random.choice(services)
        level = random.choice(levels)
        component = random.choice(components)
        
        # Generate message
        service_templates = message_templates.get(service, {})
        level_templates = service_templates.get(level, [f'{service} {level.lower()} message'])
        
        if level_templates:
            template = random.choice(level_templates)
            # Fill template with random data
            if '{}' in template:
                fill_data = [
                    f'user_{random.randint(1000, 9999)}',
                    f'{random.randint(10, 500)}',
                    f'192.168.1.{random.randint(1, 255)}',
                    f'prod_{random.randint(100, 999)}',
                    f'txn_{uuid.uuid4().hex[:8]}'
                ]
                message = template.format(*fill_data[:template.count('{}')])
            else:
                message = template
        else:
            message = f'{service} {level.lower()} message {i}'
        
        # Generate network and performance data
        source_ip = f'192.168.{random.randint(1, 10)}.{random.randint(1, 255)}'
        request_size = random.randint(100, 10000)
        response_size = random.randint(500, 50000)
        
        # Response time based on level (errors tend to be slower)
        if level == 'ERROR':
            response_time = random.randint(1000, 5000)  # 1-5 seconds
        elif level == 'WARN':
            response_time = random.randint(500, 2000)   # 0.5-2 seconds
        else:
            response_time = random.randint(50, 500)     # 50-500ms
        
        # Status code based on level
        if level == 'ERROR':
            status_code = random.choice([400, 401, 403, 404, 500, 502, 503])
        elif level == 'WARN':
            status_code = random.choice([200, 201, 202, 400, 429])
        else:
            status_code = random.choice([200, 201, 202, 204])
        
        log_entry = LogEntry(
            timestamp=timestamp.isoformat(),
            service=service,
            level=level,
            component=component,
            message=message,
            source_ip=source_ip,
            request_size=request_size,
            response_size=response_size,
            response_time=response_time,
            status_code=status_code
        )
        
        logs.append(log_entry)
    
    # Sort by timestamp
    logs.sort(key=lambda x: x.timestamp)
    
    return logs
