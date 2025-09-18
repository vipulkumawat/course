#!/bin/bash

set -e

echo "🚀 Starting Tiered Storage System"
echo "================================="

# Ensure data directories exist
mkdir -p data/{hot,warm,cold,archive}

# Start backend
echo "🖥️ Starting backend server..."
cd backend
source venv/bin/activate
python -m src.main &
BACKEND_PID=$!
cd ..

# Wait for backend to be ready
echo "⏳ Waiting for backend to be ready..."
sleep 5

# Generate sample data
echo "📊 Generating sample log entries..."
source backend/venv/bin/activate
python3 << 'EOL'
import asyncio
import json
import aiohttp
from datetime import datetime, timedelta
import random

async def generate_sample_data():
    """Generate sample log entries for demonstration"""
    
    services = ['web-api', 'database', 'cache', 'auth-service', 'payment-gateway']
    levels = ['INFO', 'WARN', 'ERROR', 'DEBUG']
    priorities = ['normal', 'high', 'low']
    
    messages = [
        "User authentication successful",
        "Database query executed",
        "Cache hit for user data",
        "Payment processing started", 
        "API request received",
        "Error processing request",
        "Connection timeout occurred",
        "Data migration completed"
    ]
    
    async with aiohttp.ClientSession() as session:
        for i in range(50):
            # Create varied timestamps for demonstration
            base_time = datetime.now() - timedelta(days=random.randint(0, 20))
            
            log_data = {
                "message": random.choice(messages) + f" #{i+1}",
                "level": random.choice(levels),
                "service": random.choice(services),
                "priority": random.choice(priorities),
                "metadata": {
                    "user_id": f"user_{random.randint(1000, 9999)}",
                    "request_id": f"req_{random.randint(10000, 99999)}",
                    "ip_address": f"192.168.1.{random.randint(1, 255)}"
                }
            }
            
            try:
                async with session.post('http://localhost:8000/api/logs', 
                                      json=log_data) as response:
                    if response.status == 200:
                        result = await response.json()
                        print(f"✓ Created log entry {i+1}: {result['entry_id']}")
                    else:
                        print(f"✗ Failed to create log entry {i+1}")
            except Exception as e:
                print(f"✗ Error creating log entry {i+1}: {e}")
            
            await asyncio.sleep(0.1)  # Small delay between requests
    
    print(f"\n🎉 Generated 50 sample log entries!")
    print("📊 Check the dashboard at http://localhost:3000")

asyncio.run(generate_sample_data())
EOL

# Start frontend
echo "⚛️ Starting frontend server..."
cd frontend
npm run dev -- --host 0.0.0.0 --port 3000 &
FRONTEND_PID=$!
cd ..

echo "✅ System started successfully!"
echo ""
echo "🌐 Access Points:"
echo "   Frontend:  http://localhost:3000"
echo "   Backend:   http://localhost:8000"
echo "   API Docs:  http://localhost:8000/docs"
echo ""
echo "🎯 Sample Commands:"
echo "   curl http://localhost:8000/api/stats"
echo "   curl -X POST http://localhost:8000/api/auto-migrate"
echo ""
echo "Press Ctrl+C to stop all services"

# Store PIDs for cleanup
echo $BACKEND_PID > backend.pid
echo $FRONTEND_PID > frontend.pid

# Wait for interrupt
trap 'echo "🛑 Stopping services..."; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; rm -f *.pid; exit 0' INT
wait
