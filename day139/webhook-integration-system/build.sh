#!/bin/bash

set -e

echo "🏗️  Building Webhook Integration System..."

# Create and activate virtual environment
echo "🐍 Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "📦 Installing dependencies..."
pip install --upgrade pip
pip install -r backend/requirements.txt

# Run database migrations
echo "🗄️  Setting up database..."
cd backend
python -c "
from sqlalchemy import create_engine
from src.models.webhook import Base
from config.config import settings
engine = create_engine(settings.database_url)
Base.metadata.create_all(bind=engine)
print('Database initialized successfully')
"
cd ..

# Run tests
echo "🧪 Running tests..."
python -m pytest tests/ -v

echo "✅ Build completed successfully!"
echo "🚀 Run './start.sh' to start the system"
echo "📊 Dashboard available at: http://localhost:8000"
