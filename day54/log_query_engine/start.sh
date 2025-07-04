#!/bin/bash

# Log Query Engine - Start Script
# This script starts the distributed log query engine

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if port is in use
port_in_use() {
    lsof -i :$1 >/dev/null 2>&1
}

# Function to start with Python
start_python() {
    print_status "Starting Log Query Engine with Python..."
    
    # Check if Python is available
    if ! command_exists python3; then
        print_error "Python 3 is not installed or not in PATH"
        exit 1
    fi
    
    # Check if virtual environment exists
    if [ -d "venv" ]; then
        print_status "Activating virtual environment..."
        source venv/bin/activate
    else
        print_warning "No virtual environment found. Installing dependencies globally..."
        pip3 install -r requirements.txt
    fi
    
    # Check if port 8000 is available
    if port_in_use 8000; then
        print_error "Port 8000 is already in use. Please stop the existing service first."
        exit 1
    fi
    
    # Start the application
    print_status "Starting application on http://localhost:8000"
    python3 run_system.py
}

# Function to start with Docker Compose
start_docker() {
    print_status "Starting Log Query Engine with Docker Compose..."
    
    # Check if Docker is available
    if ! command_exists docker; then
        print_error "Docker is not installed or not in PATH"
        exit 1
    fi
    
    # Check if Docker Compose is available
    if ! command_exists docker-compose; then
        print_error "Docker Compose is not installed or not in PATH"
        exit 1
    fi
    
    # Check if Docker daemon is running
    if ! docker info >/dev/null 2>&1; then
        print_error "Docker daemon is not running. Please start Docker first."
        exit 1
    fi
    
    # Check if ports are available
    for port in 8000 8001 8002 8003; do
        if port_in_use $port; then
            print_error "Port $port is already in use. Please stop the existing service first."
            exit 1
        fi
    done
    
    # Start the services
    print_status "Starting Docker Compose services..."
    docker-compose up -d
    
    print_success "Log Query Engine started successfully!"
    print_status "API Server: http://localhost:8000"
    print_status "Web Interface: http://localhost:8000"
    print_status "Health Check: http://localhost:8000/api/health"
    print_status "Mock Nodes: http://localhost:8001, http://localhost:8002, http://localhost:8003"
    print_status "Use 'docker-compose logs -f' to view logs"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTION]"
    echo ""
    echo "Options:"
    echo "  python, py, p    Start with Python (default)"
    echo "  docker, d        Start with Docker Compose"
    echo "  help, h          Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0               # Start with Python"
    echo "  $0 python        # Start with Python"
    echo "  $0 docker        # Start with Docker Compose"
}

# Main script logic
main() {
    print_status "🚀 Log Query Engine - Start Script"
    echo ""
    
    # Parse command line arguments
    case "${1:-python}" in
        python|py|p)
            start_python
            ;;
        docker|d)
            start_docker
            ;;
        help|h|--help|-h)
            show_usage
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@" 