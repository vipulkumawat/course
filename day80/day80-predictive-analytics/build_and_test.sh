#!/bin/bash
echo "🔧 Building and Testing Day 80: Predictive Analytics System"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    python3.11 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Create necessary directories
mkdir -p {data,models/trained,logs}

# Run tests
echo "🧪 Running tests..."
python -m pytest tests/ -v

# Generate sample data
echo "📊 Generating sample data..."
python src/utils/data_generator.py

# Train models
echo "🤖 Training models..."
python src/models/model_trainer.py

# Test API endpoints
echo "🌐 Testing API..."
python -c "
from src.api.main import app
from fastapi.testclient import TestClient

client = TestClient(app)
response = client.get('/health')
print(f'Health check: {response.status_code}')
print(response.json())

response = client.get('/predictions')
print(f'Predictions: {response.status_code}')
"

echo "✅ Build and test completed successfully!"
