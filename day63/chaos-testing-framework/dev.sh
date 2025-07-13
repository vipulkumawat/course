#!/bin/bash

# Development utilities for Chaos Testing Framework
echo "🔧 Chaos Testing Framework Development Tools"

case "$1" in
    "lint")
        echo "🔍 Running linting..."
        source venv/bin/activate
        flake8 src/ --max-line-length=100
        black --check src/
        mypy src/
        ;;
    "format")
        echo "🎨 Formatting code..."
        source venv/bin/activate
        black src/
        ;;
    "check")
        echo "✅ Running development checks..."
        source venv/bin/activate
        python -m py_compile src/chaos/failure_injector.py
        python -m py_compile src/monitoring/system_monitor.py
        python -m py_compile src/recovery/recovery_validator.py
        python -m py_compile src/web/main.py
        echo "All Python files compile successfully"
        ;;
    "install")
        echo "📦 Installing development dependencies..."
        source venv/bin/activate
        pip install -r requirements.txt
        cd frontend && npm install
        ;;
    "clean")
        echo "🧹 Cleaning up..."
        rm -rf __pycache__ src/__pycache__ tests/__pycache__
        rm -rf .pytest_cache htmlcov .coverage
        rm -f backend.pid frontend.pid
        find . -name "*.pyc" -delete
        ;;
    *)
        echo "Usage: $0 {lint|format|check|install|clean}"
        echo ""
        echo "Commands:"
        echo "  lint     - Run code linting"
        echo "  format   - Format code with black"
        echo "  check    - Check Python syntax"
        echo "  install  - Install all dependencies"
        echo "  clean    - Clean up temporary files"
        ;;
esac
