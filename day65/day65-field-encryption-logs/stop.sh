#!/bin/bash

# Field-Level Encryption Logs System - Stop Script

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BACKEND_PORT=8000

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

# Function to stop backend process
stop_backend() {
    print_status "Stopping backend server..."
    
    # Stop by PID file if it exists
    if [ -f .backend.pid ]; then
        BACKEND_PID=$(cat .backend.pid)
        if kill -0 $BACKEND_PID 2>/dev/null; then
            print_status "Stopping process $BACKEND_PID..."
            kill $BACKEND_PID
            sleep 2
            
            # Force kill if still running
            if kill -0 $BACKEND_PID 2>/dev/null; then
                print_warning "Process still running, force killing..."
                kill -9 $BACKEND_PID
            fi
            
            print_success "Backend process stopped"
        else
            print_warning "Backend process not running (PID: $BACKEND_PID)"
        fi
        rm -f .backend.pid
    else
        print_warning "No PID file found"
    fi
    
    # Also kill any process using the backend port
    if lsof -Pi :$BACKEND_PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
        print_status "Killing processes on port $BACKEND_PORT..."
        lsof -ti:$BACKEND_PORT | xargs kill -9 2>/dev/null || true
        print_success "Port $BACKEND_PORT cleared"
    fi
}

# Function to cleanup temporary files
cleanup_temp_files() {
    print_status "Cleaning up temporary files..."
    
    # Remove PID files
    rm -f .backend.pid
    
    # Remove any temporary log files
    if [ -f "logs/app.log" ]; then
        print_status "Backing up log file..."
        mv logs/app.log "logs/app.log.$(date +%Y%m%d_%H%M%S)"
    fi
    
    print_success "Cleanup completed"
}

# Function to show final status
show_status() {
    print_status "Final Status:"
    echo "  - Backend: $(if lsof -Pi :$BACKEND_PORT -sTCP:LISTEN -t >/dev/null 2>&1; then echo "Still Running"; else echo "Stopped"; fi)"
    echo "  - Port $BACKEND_PORT: $(if lsof -Pi :$BACKEND_PORT -sTCP:LISTEN -t >/dev/null 2>&1; then echo "In Use"; else echo "Available"; fi)"
}

# Main execution
main() {
    echo "🛑 Stopping Field-Level Encryption Logs System"
    echo "=================================================="
    
    # Stop backend
    stop_backend
    
    # Cleanup
    cleanup_temp_files
    
    # Show final status
    show_status
    
    echo ""
    print_success "System stopped successfully!"
    echo "=================================================="
}

# Run main function
main "$@" 