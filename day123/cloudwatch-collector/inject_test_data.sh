#!/bin/bash
# Script to continuously inject test data into the CloudWatch collector

echo "Injecting test data into CloudWatch collector..."
echo "Press Ctrl+C to stop"

while true; do
    RESPONSE=$(curl -s -X POST http://localhost:5000/api/test/inject \
        -H "Content-Type: application/json" \
        -d '{"count": 100}')
    
    if [ $? -eq 0 ]; then
        echo "$(date '+%Y-%m-%d %H:%M:%S') - $(echo $RESPONSE | grep -o '"message":"[^"]*"')"
    else
        echo "$(date '+%Y-%m-%d %H:%M:%S') - Failed to inject data"
    fi
    
    sleep 2
done

