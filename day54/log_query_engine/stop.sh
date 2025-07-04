#!/bin/bash

# Log Query Engine - Stop Script
# This script stops the distributed log query engine

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

# Function to stop Python processes
stop_python() {
    print_status "Stopping Log Query Engine Python processes..."
    
    # Find and kill Python processes running run_system.py
    local pids=$(pgrep -f "python.*run_system.py" || true)
    
    if [ -n "$pids" ]; then
        print_status "Found Python processes: $pids"
        echo "$pids" | xargs kill -TERM
        
        # Wait a bit for graceful shutdown
        sleep 2
        
        # Force kill if still running
        local remaining_pids=$(pgrep -f "python.*run_system.py" || true)
        if [ -n "$remaining_pids" ]; then
            print_warning "Force killing remaining processes: $remaining_pids"
            echo "$remaining_pids" | xargs kill -KILL
        fi
        
        print_success "Python processes stopped successfully"
    else
        print_warning "No Python processes found running run_system.py"
    fi
    
    # Also kill any uvicorn processes on port 8000
    local uvicorn_pids=$(lsof -ti:8000 2>/dev/null || true)
    if [ -n "$uvicorn_pids" ]; then
        print_status "Stopping uvicorn processes on port 8000: $uvicorn_pids"
        echo "$uvicorn_pids" | xargs kill -TERM
        sleep 1
        echo "$uvicorn_pids" | xargs kill -KILL 2>/dev/null || true
    fi
}

# Function to stop Docker Compose services
stop_docker() {
    print_status "Stopping Log Query Engine Docker Compose services..."
    
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
    
    # Check if docker-compose.yml exists
    if [ ! -f "docker-compose.yml" ]; then
        print_error "docker-compose.yml not found in current directory"
        exit 1
    fi
    
    # Stop the services
    print_status "Stopping Docker Compose services..."
    docker-compose down
    
    # Remove any dangling containers
    local dangling_containers=$(docker ps -a --filter "name=log_query_engine" --format "{{.ID}}" 2>/dev/null || true)
    if [ -n "$dangling_containers" ]; then
        print_status "Removing dangling containers..."
        echo "$dangling_containers" | xargs docker rm -f 2>/dev/null || true
    fi
    
    print_success "Docker Compose services stopped successfully"
}

# Function to stop all (both Python and Docker)
stop_all() {
    print_status "Stopping all Log Query Engine services..."
    
    stop_python
    echo ""
    stop_docker
    
    print_success "All services stopped successfully"
}

# Function to check what's running
check_status() {
    print_status "Checking Log Query Engine status..."
    echo ""
    
    # Check Python processes
    local python_pids=$(pgrep -f "python.*run_system.py" || true)
    if [ -n "$python_pids" ]; then
        print_status "Python processes running: $python_pids"
    else
        print_status "No Python processes found"
    fi
    
    # Check Docker services
    if command_exists docker && command_exists docker-compose && [ -f "docker-compose.yml" ]; then
        local docker_services=$(docker-compose ps --services --filter "status=running" 2>/dev/null || true)
        if [ -n "$docker_services" ]; then
            print_status "Docker services running:"
            echo "$docker_services" | while read service; do
                echo "  - $service"
            done
        else
            print_status "No Docker services running"
        fi
    fi
    
    # Check ports
    echo ""
    print_status "Port status:"
    for port in 8000 8001 8002 8003; do
        if port_in_use $port; then
            local process=$(lsof -i :$port | grep LISTEN | head -1 | awk '{print $1}' || echo "unknown")
            print_warning "Port $port is in use by: $process"
        else
            print_success "Port $port is free"
        fi
    done
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTION]"
    echo ""
    echo "Options:"
    echo "  python, py, p    Stop Python processes (default)"
    echo "  docker, d        Stop Docker Compose services"
    echo "  all, a           Stop both Python and Docker services"
    echo "  status, s        Check what's currently running"
    echo "  help, h          Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0               # Stop Python processes"
    echo "  $0 python        # Stop Python processes"
    echo "  $0 docker        # Stop Docker Compose services"
    echo "  $0 all           # Stop everything"
    echo "  $0 status        # Check current status"
}

# Main script logic
main() {
    print_status "🛑 Log Query Engine - Stop Script"
    echo ""
    
    # Parse command line arguments
    case "${1:-python}" in
        python|py|p)
            stop_python
            ;;
        docker|d)
            stop_docker
            ;;
        all|a)
            stop_all
            ;;
        status|s)
            check_status
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