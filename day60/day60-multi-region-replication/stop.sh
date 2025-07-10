#!/bin/bash

# Day 60: Multi-Region Log Replication System - Stop Script
# =========================================================

set -e  # Exit on any error

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

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if process is running
process_running() {
    local pid=$1
    if kill -0 $pid 2>/dev/null; then
        return 0
    else
        return 1
    fi
}

# Function to stop process gracefully
stop_process() {
    local pid=$1
    local process_name=$2
    
    if [ -n "$pid" ] && process_running $pid; then
        print_status "Stopping $process_name (PID: $pid)..."
        
        # Try graceful shutdown first
        kill -TERM $pid 2>/dev/null
        
        # Wait for graceful shutdown
        local count=0
        while process_running $pid && [ $count -lt 10 ]; do
            sleep 1
            count=$((count + 1))
        done
        
        # Force kill if still running
        if process_running $pid; then
            print_warning "Force killing $process_name (PID: $pid)..."
            kill -KILL $pid 2>/dev/null
        fi
        
        print_success "$process_name stopped"
    else
        print_status "$process_name is not running"
    fi
}

# Function to stop Python applications
stop_python_apps() {
    print_status "Stopping Python applications..."
    
    # Stop main application
    if [ -f ".main.pid" ]; then
        local main_pid=$(cat .main.pid)
        stop_process $main_pid "Main Application"
        rm -f .main.pid
    fi
    
    # Stop dashboard
    if [ -f ".dashboard.pid" ]; then
        local dashboard_pid=$(cat .dashboard.pid)
        stop_process $dashboard_pid "Dashboard"
        rm -f .dashboard.pid
    fi
    
    # Stop region instances
    for pid_file in .region_*.pid; do
        if [ -f "$pid_file" ]; then
            local region_pid=$(cat "$pid_file")
            local port=$(echo "$pid_file" | sed 's/\.region_\([0-9]*\)\.pid/\1/')
            stop_process $region_pid "Region Instance (port $port)"
            rm -f "$pid_file"
        fi
    done
    
    # Kill any remaining Python processes on our ports
    for port in 8000 8001 8002 8080; do
        local pids=$(lsof -ti:$port 2>/dev/null || true)
        if [ -n "$pids" ]; then
            for pid in $pids; do
                stop_process $pid "Process on port $port"
            done
        fi
    done
}

# Function to stop Redis
stop_redis() {
    print_status "Stopping Redis server..."
    
    if command_exists "redis-cli"; then
        # Try graceful shutdown
        redis-cli -p 6379 shutdown 2>/dev/null || true
        
        # Check if Redis is still running
        if pgrep -f "redis-server" >/dev/null; then
            print_warning "Force stopping Redis..."
            pkill -f "redis-server" 2>/dev/null || true
        fi
        
        print_success "Redis stopped"
    else
        print_warning "Redis CLI not found, trying to kill Redis processes..."
        pkill -f "redis-server" 2>/dev/null || true
    fi
}

# Function to stop PostgreSQL
stop_postgresql() {
    print_status "Stopping PostgreSQL..."
    
    if command_exists "docker"; then
        # Stop PostgreSQL container
        if docker ps -q -f name=day60-postgres | grep -q .; then
            print_status "Stopping PostgreSQL container..."
            docker stop day60-postgres 2>/dev/null || true
            docker rm day60-postgres 2>/dev/null || true
            print_success "PostgreSQL container stopped"
        else
            print_status "PostgreSQL container is not running"
        fi
    else
        print_warning "Docker not found, PostgreSQL may still be running"
    fi
}

# Function to stop Docker containers
stop_docker_containers() {
    print_status "Stopping Docker containers..."
    
    if command_exists "docker"; then
        # Stop all containers with day60 prefix
        local containers=$(docker ps -q -f name=day60 2>/dev/null || true)
        if [ -n "$containers" ]; then
            print_status "Stopping day60 containers..."
            docker stop $containers 2>/dev/null || true
            docker rm $containers 2>/dev/null || true
            print_success "Docker containers stopped"
        else
            print_status "No day60 containers running"
        fi
    else
        print_warning "Docker not found"
    fi
}

# Function to clean up temporary files
cleanup_files() {
    print_status "Cleaning up temporary files..."
    
    # Remove PID files
    rm -f .main.pid .region_*.pid
    
    # Remove log files (optional)
    if [ "$1" = "--clean-logs" ]; then
        print_status "Removing log files..."
        rm -rf logs/* 2>/dev/null || true
        print_success "Log files cleaned"
    fi
    
    # Remove data files (optional)
    if [ "$1" = "--clean-data" ]; then
        print_status "Removing data files..."
        rm -rf data/* 2>/dev/null || true
        print_success "Data files cleaned"
    fi
    
    print_success "Cleanup completed"
}

# Function to show running processes
show_running_processes() {
    print_status "Checking for running processes..."
    
    local found_processes=false
    
    # Check for Python processes on our ports
    for port in 8000 8001 8002; do
        local pids=$(lsof -ti:$port 2>/dev/null || true)
        if [ -n "$pids" ]; then
            echo "  • Port $port: $(echo $pids | tr '\n' ' ')"
            found_processes=true
        fi
    done
    
    # Check for Redis
    if pgrep -f "redis-server" >/dev/null; then
        echo "  • Redis: $(pgrep -f redis-server)"
        found_processes=true
    fi
    
    # Check for PostgreSQL
    if command_exists "docker" && docker ps -q -f name=day60-postgres | grep -q .; then
        echo "  • PostgreSQL: $(docker ps -q -f name=day60-postgres)"
        found_processes=true
    fi
    
    if [ "$found_processes" = false ]; then
        print_success "No running processes found"
    fi
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo
    echo "Options:"
    echo "  --clean-logs    Remove log files during cleanup"
    echo "  --clean-data    Remove data files during cleanup"
    echo "  --check         Only check for running processes"
    echo "  --help          Show this help message"
    echo
    echo "Examples:"
    echo "  $0                    # Stop all services"
    echo "  $0 --clean-logs       # Stop services and clean logs"
    echo "  $0 --clean-data       # Stop services and clean all data"
    echo "  $0 --check            # Only check running processes"
}

# Main execution
main() {
    echo "🛑 Day 60: Multi-Region Log Replication System - Stop Script"
    echo "============================================================"
    echo
    
    # Parse command line arguments
    local clean_logs=false
    local clean_data=false
    local check_only=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --clean-logs)
                clean_logs=true
                shift
                ;;
            --clean-data)
                clean_data=true
                shift
                ;;
            --check)
                check_only=true
                shift
                ;;
            --help)
                show_usage
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
    
    if [ "$check_only" = true ]; then
        show_running_processes
        exit 0
    fi
    
    # Stop all services
    print_status "Stopping all services..."
    
    # Stop Python applications
    stop_python_apps
    
    # Stop Redis
    stop_redis
    
    # Stop PostgreSQL
    stop_postgresql
    
    # Stop Docker containers
    stop_docker_containers
    
    # Cleanup files
    local cleanup_args=""
    if [ "$clean_logs" = true ]; then
        cleanup_args="--clean-logs"
    fi
    if [ "$clean_data" = true ]; then
        cleanup_args="$cleanup_args --clean-data"
    fi
    cleanup_files $cleanup_args
    
    # Final check
    echo
    print_status "Final status check:"
    show_running_processes
    
    echo
    print_success "All services stopped successfully!"
    echo
    echo "📋 Summary:"
    echo "  • Python applications: Stopped"
    echo "  • Redis server: Stopped"
    echo "  • PostgreSQL: Stopped"
    echo "  • Docker containers: Stopped"
    echo "  • Temporary files: Cleaned"
    if [ "$clean_logs" = true ]; then
        echo "  • Log files: Removed"
    fi
    if [ "$clean_data" = true ]; then
        echo "  • Data files: Removed"
    fi
    echo
    echo "🚀 To restart the system:"
    echo "  ./start.sh"
    echo
}

# Run main function
main "$@" 