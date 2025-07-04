import random
import uuid
from datetime import datetime, timedelta
from typing import List
from ..models.log_entry import LogEntry

class LogGenerator:
    def __init__(self):
        self.services = ['user-api', 'payment-api', 'order-api', 'notification-api', 'analytics-api']
        self.levels = ['debug', 'info', 'warn', 'error']
        self.regions = ['us-west-2', 'us-east-1', 'eu-west-1', 'ap-southeast-1']
        self.messages = [
            'Request processed successfully',
            'Database connection timeout',
            'User authentication failed',
            'Payment processing completed',
            'Order validation error',
            'Cache miss for user data',
            'API rate limit exceeded',
            'Background job started',
            'Configuration updated',
            'Health check passed'
        ]
        
    def generate_logs(self, count: int = 100) -> List[LogEntry]:
        """Generate sample log entries"""
        logs = []
        base_time = datetime.now() - timedelta(hours=24)
        
        for i in range(count):
            # Weight levels (more info/debug, fewer errors)
            level_weights = {'debug': 0.3, 'info': 0.5, 'warn': 0.15, 'error': 0.05}
            level = random.choices(list(level_weights.keys()), weights=list(level_weights.values()))[0]
            
            # Generate response time based on level
            if level == 'error':
                response_time = random.randint(1000, 5000)  # Slow for errors
            elif level == 'warn':
                response_time = random.randint(500, 1500)
            else:
                response_time = random.randint(10, 800)
                
            log = LogEntry(
                id=str(uuid.uuid4()),
                timestamp=base_time + timedelta(seconds=i * 60 + random.randint(0, 59)),
                service=random.choice(self.services),
                level=level,
                message=random.choice(self.messages),
                metadata={'generated': True, 'batch_id': f'batch_{i // 20}'},
                source_ip=f"192.168.1.{random.randint(1, 255)}",
                request_id=f"req_{random.randint(10000, 99999)}",
                region=random.choice(self.regions),
                response_time=response_time
            )
            logs.append(log)
            
        return logs
        
    def generate_real_time_log(self) -> LogEntry:
        """Generate a single real-time log entry"""
        logs = self.generate_logs(1)
        logs[0].timestamp = datetime.now()
        return logs[0]
