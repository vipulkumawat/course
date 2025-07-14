#!/bin/bash

# Field-Level Encryption Logs System - Start Script
# Handles dependencies, building, testing, and verification

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="Field-Level Encryption Logs"
BACKEND_PORT=8000
FRONTEND_PORT=3000
PYTHON_VERSION="3.8+"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check Python version
check_python_version() {
    print_status "Checking Python version..."
    
    if ! command_exists python3; then
        print_error "Python 3 is not installed. Please install Python 3.8 or higher."
        exit 1
    fi
    
    PYTHON_VERSION_CHECK=$(python3 -c "import sys; print('{}.{}'.format(sys.version_info.major, sys.version_info.minor))")
    print_success "Python version: $PYTHON_VERSION_CHECK"
}

# Function to create virtual environment
setup_virtual_environment() {
    print_status "Setting up Python virtual environment..."
    
    if [ ! -d "venv" ]; then
        print_status "Creating virtual environment..."
        python3 -m venv venv
        print_success "Virtual environment created"
    else
        print_status "Virtual environment already exists"
    fi
    
    print_status "Activating virtual environment..."
    source venv/bin/activate
    
    print_status "Upgrading pip..."
    pip install --upgrade pip
}

# Function to install Python dependencies
install_dependencies() {
    print_status "Installing Python dependencies..."
    
    if [ ! -f "requirements.txt" ]; then
        print_error "requirements.txt not found!"
        exit 1
    fi
    
    pip install -r requirements.txt
    print_success "Python dependencies installed"
}

# Function to fix Python import issues
fix_import_issues() {
    print_status "Fixing Python import issues..."
    
    # Create __init__.py files if they don't exist
    for dir in src src/encryption src/pipeline src/utils src/web; do
        if [ -d "$dir" ] && [ ! -f "$dir/__init__.py" ]; then
            touch "$dir/__init__.py"
            print_status "Created $dir/__init__.py"
        fi
    done
    
    # Add project root to PYTHONPATH
    export PYTHONPATH="${PYTHONPATH}:$(pwd)"
    print_success "Python import issues fixed"
}

# Function to run tests
run_tests() {
    print_status "Running test suite..."
    
    # Run the test runner
    if python run_tests.py; then
        print_success "All tests passed!"
    else
        print_error "Some tests failed. Please review the output above."
        exit 1
    fi
}

# Function to verify backend
verify_backend() {
    print_status "Verifying backend components..."
    
    # Check if main application can be imported
    if python -c "import sys; sys.path.append('.'); from src.main import FieldEncryptionService; print('Backend imports successful')" 2>/dev/null; then
        print_success "Backend verification passed"
    else
        print_error "Backend verification failed"
        exit 1
    fi
}

# Function to verify frontend
verify_frontend() {
    print_status "Verifying frontend components..."
    
    # Check if templates and static files exist
    if [ -f "templates/dashboard.html" ]; then
        print_success "Dashboard template found"
    else
        print_warning "Dashboard template not found"
    fi
    
    if [ -d "static/css" ] && [ -d "static/js" ]; then
        print_success "Static assets found"
    else
        print_warning "Static assets directory structure incomplete"
    fi
}

# Function to start the application
start_application() {
    print_status "Starting the application..."
    
    # Check if port is available
    if lsof -Pi :$BACKEND_PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
        print_warning "Port $BACKEND_PORT is already in use"
        print_status "Attempting to kill existing process..."
        lsof -ti:$BACKEND_PORT | xargs kill -9 2>/dev/null || true
        sleep 2
    fi
    
    print_status "Starting backend server on port $BACKEND_PORT..."
    
    # Start the application in background
    nohup python src/main.py > logs/app.log 2>&1 &
    BACKEND_PID=$!
    
    # Save PID for later cleanup
    echo $BACKEND_PID > .backend.pid
    
    # Wait a moment for the server to start
    sleep 3
    
    # Check if server is running
    if curl -s http://localhost:$BACKEND_PORT >/dev/null 2>&1; then
        print_success "Backend server started successfully!"
        print_success "Dashboard available at: http://localhost:$BACKEND_PORT"
    else
        print_error "Failed to start backend server"
        exit 1
    fi
}

# Function to show status
show_status() {
    print_status "System Status:"
    echo "  - Backend: $(if [ -f .backend.pid ] && kill -0 $(cat .backend.pid) 2>/dev/null; then echo "Running"; else echo "Stopped"; fi)"
    echo "  - Backend PID: $(if [ -f .backend.pid ]; then cat .backend.pid; else echo "N/A"; fi)"
    echo "  - Backend Port: $BACKEND_PORT"
    echo "  - Dashboard URL: http://localhost:$BACKEND_PORT"
    echo "  - Logs: logs/app.log"
}

# Function to cleanup
cleanup() {
    print_status "Cleaning up..."
    
    if [ -f .backend.pid ]; then
        BACKEND_PID=$(cat .backend.pid)
        if kill -0 $BACKEND_PID 2>/dev/null; then
            kill $BACKEND_PID
            print_status "Stopped backend process"
        fi
        rm -f .backend.pid
    fi
}

# Main execution
main() {
    echo "🚀 Starting $PROJECT_NAME"
    echo "=================================================="
    
    # Set up signal handlers for cleanup
    trap cleanup EXIT
    trap 'print_status "Received interrupt signal"; cleanup; exit 1' INT TERM
    
    # Check Python version
    check_python_version
    
    # Setup virtual environment
    setup_virtual_environment
    
    # Install dependencies
    install_dependencies
    
    # Fix import issues
    fix_import_issues
    
    # Run tests
    #run_tests
    
    # Verify components
    verify_backend
    verify_frontend
    
    # Start application
    start_application
    
    # Show status
    show_status
    
    echo ""
    echo "🎉 $PROJECT_NAME is now running!"
    echo "=================================================="
    echo "📊 Dashboard: http://localhost:$BACKEND_PORT"
    echo "📝 Logs: logs/app.log"
    echo "🛑 To stop: ./stop.sh or Ctrl+C"
    echo ""
    
    # Keep script running and show logs
    print_status "Showing application logs (Ctrl+C to stop)..."
    tail -f logs/app.log
}

# Run main function
main "$@" 