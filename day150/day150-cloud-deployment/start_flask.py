#!/usr/bin/env python3
"""
Simple Flask startup script to ensure the app runs correctly
"""
import sys
import os
from pathlib import Path

# Add the project root to the path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# Change to the web directory
os.chdir(PROJECT_ROOT / "web")

# Import and run the Flask app
try:
    from app import app
    print("🚀 Starting Flask application...")
    print("📡 Dashboard will be available at: http://localhost:5000")
    print("🛑 Press Ctrl+C to stop the server")
    print("")
    app.run(host='0.0.0.0', port=5000, debug=True)
except Exception as e:
    print(f"❌ Error starting Flask app: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
