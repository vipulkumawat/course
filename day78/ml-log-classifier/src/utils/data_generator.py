import pandas as pd
import random
from datetime import datetime, timedelta
import json

def generate_sample_logs(num_logs=1000):
    """Generate sample log data for training"""
    
    # Sample log templates with patterns
    log_templates = {
        'INFO': [
            "User {} logged in successfully",
            "Request processed for endpoint {} in {}ms",
            "Cache hit for key {}",
            "Database connection established",
            "Service {} started successfully"
        ],
        'WARNING': [
            "High memory usage detected: {}%",
            "Slow query detected: {}ms",
            "Connection pool size approaching limit",
            "Deprecated API endpoint {} accessed",
            "Retry attempt {} for operation {}"
        ],
        'ERROR': [
            "Failed to connect to database: {}",
            "Authentication failed for user {}",
            "Invalid request format: {}",
            "Service {} is unavailable",
            "Timeout occurred for operation {}"
        ],
        'CRITICAL': [
            "System out of memory",
            "Database connection lost",
            "Security breach detected from IP {}",
            "Service {} crashed with exit code {}",
            "Disk space critically low: {}% remaining"
        ]
    }
    
    category_mapping = {
        'INFO': ['APPLICATION', 'SYSTEM'],
        'WARNING': ['PERFORMANCE', 'SYSTEM'],
        'ERROR': ['APPLICATION', 'SYSTEM', 'SECURITY'],
        'CRITICAL': ['SYSTEM', 'SECURITY']
    }
    
    services = ['web-server', 'auth-service', 'database', 'cache', 'api-gateway']
    components = ['handler', 'controller', 'repository', 'service', 'middleware']
    
    logs = []
    base_time = datetime.now() - timedelta(days=30)
    
    for i in range(num_logs):
        # Choose severity with realistic distribution
        severity = random.choices(
            ['INFO', 'WARNING', 'ERROR', 'CRITICAL'],
            weights=[70, 20, 8, 2]
        )[0]
        
        # Choose category based on severity
        category = random.choice(category_mapping[severity])
        
        # Generate message
        template = random.choice(log_templates[severity])
        
        # Fill template with random values
        if '{}' in template:
            placeholder_count = template.count('{}')
            
            if 'user' in template.lower():
                message = template.format(f"user_{random.randint(1000, 9999)}")
            elif 'endpoint' in template.lower() and 'ms' in template:
                # Handle "Request processed for endpoint {} in {}ms"
                message = template.format(
                    f"/api/v1/{random.choice(['users', 'orders', 'products'])}",
                    random.randint(10, 2000)
                )
            elif 'endpoint' in template.lower():
                message = template.format(f"/api/v1/{random.choice(['users', 'orders', 'products'])}")
            elif 'ms' in template:
                message = template.format(random.randint(10, 2000))
            elif 'service' in template.lower() and 'exit code' in template:
                # Handle "Service {} crashed with exit code {}"
                message = template.format(
                    random.choice(services),
                    random.choice([1, 2, 130, 255])
                )
            elif 'service' in template.lower():
                message = template.format(random.choice(services))
            elif 'IP' in template:
                message = template.format(f"192.168.{random.randint(1,255)}.{random.randint(1,255)}")
            elif '%' in template:
                message = template.format(random.randint(50, 99))
            elif 'exit code' in template:
                message = template.format(random.choice([1, 2, 130, 255]))
            elif 'operation' in template.lower() and placeholder_count == 2:
                # Handle "Retry attempt {} for operation {}"
                message = template.format(
                    random.randint(1, 5), 
                    random.choice(['operation', 'request', 'task'])
                )
            elif 'operation' in template.lower():
                message = template.format(random.choice(['operation', 'request', 'task']))
            else:
                message = template.format(random.choice(['operation', 'request', 'task']))
        else:
            message = template
        
        # Generate timestamp
        timestamp = base_time + timedelta(
            days=random.randint(0, 29),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59)
        )
        
        # Generate metadata
        metadata = {
            'service': random.choice(services),
            'component': random.choice(components),
            'request_id': f"req_{random.randint(100000, 999999)}",
            'user_id': f"user_{random.randint(1000, 9999)}" if random.random() > 0.3 else None
        }
        
        logs.append({
            'timestamp': timestamp.isoformat(),
            'message': message,
            'severity': severity,
            'category': category,
            'metadata': metadata
        })
    
    return pd.DataFrame(logs)

if __name__ == "__main__":
    # Generate training data
    print("Generating sample training data...")
    df = generate_sample_logs(1000)
    
    # Save to CSV
    df.to_csv("data/training/sample_logs.csv", index=False)
    print(f"Generated {len(df)} sample logs saved to data/training/sample_logs.csv")
    
    # Display distribution
    print("\nSeverity distribution:")
    print(df['severity'].value_counts())
    
    print("\nCategory distribution:")
    print(df['category'].value_counts()) 