#!/bin/bash
set -e

echo "🔨 Building NLP Query System..."

# Create virtual environment
python3.11 -m venv venv || python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
# Try with legacy resolver if dependency resolution fails
pip install -r requirements.txt --use-deprecated=legacy-resolver || pip install -r requirements.txt

# Download spaCy model (optional)
python -m spacy download en_core_web_sm 2>/dev/null || echo "Warning: spaCy model download failed, will use basic features"

echo "✅ Build complete!"
