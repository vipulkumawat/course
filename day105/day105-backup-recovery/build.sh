#!/bin/bash

set -e

echo "🏗️ Building Day 105: Automated Backup and Recovery System"
echo "=========================================================="

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "🐍 Creating Python virtual environment..."
    python3.11 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Create necessary directories
echo "📁 Ensuring all directories exist..."
mkdir -p logs backups recovery/{restored,pit,api_restore}

# Generate sample log files for demonstration
echo "📝 Creating sample log files..."
for i in {1..20}; do
    echo "$(date): Sample log entry $i - Application started" >> logs/app.log
    echo "$(date): Sample log entry $i - Processing request ID: REQ$i" >> logs/app.log
    echo "$(date): Sample log entry $i - Database query executed successfully" >> logs/app.log
done

echo "✅ Build completed successfully!"
echo ""
echo "Next steps:"
echo "  1. Run tests: ./test.sh"
echo "  2. Start system: ./start.sh"
echo "  3. Open dashboard: http://localhost:8105"
