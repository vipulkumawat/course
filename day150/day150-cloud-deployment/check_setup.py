#!/usr/bin/env python3
"""
Check if the Flask app can start correctly
"""
import sys
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent

print("🔍 Checking setup...")
print(f"Project root: {PROJECT_ROOT}")

# Check if venv exists
venv_python = PROJECT_ROOT / "venv" / "bin" / "python"
if venv_python.exists():
    print(f"✅ Virtual environment found: {venv_python}")
else:
    print(f"❌ Virtual environment not found at: {venv_python}")
    print("   Run: python3 -m venv venv")

# Check if Flask is installed
try:
    import flask
    print(f"✅ Flask is installed: {flask.__version__}")
except ImportError:
    print("❌ Flask is not installed")
    print("   Run: pip install -r requirements.txt")

# Check if app.py exists
app_py = PROJECT_ROOT / "web" / "app.py"
if app_py.exists():
    print(f"✅ Flask app found: {app_py}")
else:
    print(f"❌ Flask app not found: {app_py}")

# Check if template exists
template = PROJECT_ROOT / "web" / "templates" / "dashboard.html"
if template.exists():
    print(f"✅ Template found: {template}")
else:
    print(f"❌ Template not found: {template}")

# Try to import the app
try:
    sys.path.insert(0, str(PROJECT_ROOT))
    os.chdir(PROJECT_ROOT / "web")
    from app import app
    print("✅ Flask app can be imported successfully")
    print("✅ Setup looks good! You can start the server with:")
    print("   python web/app.py")
    print("   or")
    print("   ./run_flask.sh")
except Exception as e:
    print(f"❌ Error importing Flask app: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
