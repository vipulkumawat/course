import asyncio
import random
import json
from datetime import datetime, timedelta
from faker import Faker

fake = Faker()

class DemoDataGenerator:
    def __init__(self):
        self.services = ['api-gateway', 'user-service', 'payment-service', 'notification-service', 'analytics-service']
        self.log_levels = ['INFO', 'WARN', 'ERROR', 'DEBUG']
        self.endpoints = ['/api/users', '/api/orders', '/api/payments', '/api/notifications', '/health']
        
    def generate_log_entry(self, timestamp=None):
        """Generate a realistic log entry"""
        if not timestamp:
            timestamp = datetime.now() - timedelta(
                hours=random.randint(0, 24),
                minutes=random.randint(0, 59),
                seconds=random.randint(0, 59)
            )
        
        service = random.choice(self.services)
        level = random.choice(self.log_levels)
        endpoint = random.choice(self.endpoints)
        
        # Simulate realistic response times based on service and endpoint
        base_response_time = {
            'api-gateway': 50,
            'user-service': 80,
            'payment-service': 200,
            'notification-service': 30,
            'analytics-service': 150
        }.get(service, 100)
        
        response_time = base_response_time + random.gauss(0, 20)
        response_time = max(10, response_time)  # Minimum 10ms
        
        # Error logs have higher response times
        if level == 'ERROR':
            response_time *= random.uniform(2, 5)
            
        status_code = 200
        if level == 'ERROR':
            status_code = random.choice([400, 401, 403, 404, 500, 502, 503])
        elif level == 'WARN':
            status_code = random.choice([200, 400, 429])
        
        return {
            'timestamp': timestamp.isoformat(),
            'service': service,
            'level': level,
            'message': f"{fake.sentence()} - {endpoint}",
            'response_time': round(response_time, 2),
            'status_code': status_code,
            'endpoint': endpoint,
            'user_id': fake.uuid4()
        }
    
    def generate_batch(self, count=1000):
        """Generate a batch of log entries"""
        entries = []
        for _ in range(count):
            entries.append(self.generate_log_entry())
        return entries
    
    def save_demo_data(self, filename='demo_logs.json', count=10000):
        """Generate and save demo data to file"""
        print(f"Generating {count} demo log entries...")
        entries = self.generate_batch(count)
        
        with open(filename, 'w') as f:
            json.dump(entries, f, indent=2)
        
        print(f"Demo data saved to {filename}")
        return entries

if __name__ == '__main__':
    generator = DemoDataGenerator()
    generator.save_demo_data('demo_logs.json', 5000)
    print("Demo data generation complete!")
