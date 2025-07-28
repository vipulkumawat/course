#!/bin/bash

echo "🚀 Starting ML Log Classifier System"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3.11 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies if needed
if [ ! -f "venv/installed" ]; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
    python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('wordnet')"
    touch venv/installed
fi

# Set Python path
export PYTHONPATH="$(pwd):$PYTHONPATH"

# Generate sample data if needed
if [ ! -f "data/training/sample_logs.csv" ]; then
    echo "Generating sample training data..."
    python src/utils/data_generator.py
fi

# Start the API server
echo "Starting ML Log Classifier API..."
python src/api/main.py &
API_PID=$!

echo "API started with PID: $API_PID"
echo "Dashboard available at: http://localhost:8000"
echo "Press Ctrl+C to stop"

# Store PID for cleanup
echo $API_PID > .api.pid

# Wait for interrupt
wait $API_PID 