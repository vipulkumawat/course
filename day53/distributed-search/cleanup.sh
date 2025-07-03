#!/bin/bash
# Demo Cleanup Script for Distributed Search System
# This script stops all services and cleans up resources

echo "🧹 Cleaning up Distributed Search System"
echo "========================================"

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

# Function to check if a port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Function to stop process by PID file
stop_process_by_pid() {
    local pid_file=$1
    local process_name=$2
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p "$pid" >/dev/null 2>&1; then
            print_status "Stopping $process_name (PID: $pid)..."
            kill "$pid" 2>/dev/null || true
            sleep 2
            
            # Force kill if still running
            if ps -p "$pid" >/dev/null 2>&1; then
                print_warning "Force killing $process_name..."
                kill -9 "$pid" 2>/dev/null || true
            fi
            
            rm -f "$pid_file"
            print_success "Stopped $process_name"
        else
            print_warning "$process_name was not running (PID: $pid)"
            rm -f "$pid_file"
        fi
    else
        print_warning "PID file not found for $process_name"
    fi
}

# Step 1: Stop Search Nodes
stop_search_nodes() {
    print_status "Stopping search nodes..."
    
    # Stop nodes using PID files
    for i in {1..4}; do
        node_id="node-$i"
        pid_file="logs/$node_id.pid"
        stop_process_by_pid "$pid_file" "$node_id"
    done
    
    # Stop coordinator
    stop_process_by_pid "logs/coordinator.pid" "coordinator"
    
    # Stop web dashboard
    stop_process_by_pid "logs/web-dashboard.pid" "web-dashboard"
    
    # Also kill any processes on our ports as backup
    for port in 8101 8102 8103 8104 8000 8080; do
        if check_port $port; then
            print_warning "Found process still running on port $port. Force stopping..."
            lsof -ti:$port | xargs kill -9 2>/dev/null || true
        fi
    done
    
    # Verify all ports are free
    all_ports_free=true
    for port in 8101 8102 8103 8104 8000 8080; do
        if check_port $port; then
            print_error "Port $port is still in use"
            all_ports_free=false
        fi
    done
    
    if [ "$all_ports_free" = true ]; then
        print_success "All search nodes stopped"
    else
        print_warning "Some ports may still be in use"
    fi
}

# Step 2: Stop Redis (Optional)
stop_redis() {
    print_status "Checking Redis status..."
    
    if redis-cli ping >/dev/null 2>&1; then
        echo ""
        echo "Redis is currently running."
        read -p "Do you want to stop Redis? (y/N): " -n 1 -r
        echo
        
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            print_status "Stopping Redis..."
            
            # Try graceful shutdown
            redis-cli shutdown 2>/dev/null || true
            sleep 2
            
            # Check if still running
            if redis-cli ping >/dev/null 2>&1; then
                print_warning "Redis still running. Force stopping..."
                
                # Find Redis process and kill it
                redis_pid=$(pgrep redis-server 2>/dev/null || true)
                if [ -n "$redis_pid" ]; then
                    kill -9 "$redis_pid" 2>/dev/null || true
                fi
            fi
            
            if ! redis-cli ping >/dev/null 2>&1; then
                print_success "Redis stopped"
            else
                print_error "Failed to stop Redis"
            fi
        else
            print_status "Keeping Redis running"
        fi
    else
        print_status "Redis is not running"
    fi
}

# Step 3: Clean up logs and temporary files
cleanup_files() {
    print_status "Cleaning up files..."
    
    # Remove PID files
    rm -f logs/*.pid 2>/dev/null || true
    
    # Optionally clean log files
    if [ -d "logs" ] && [ "$(ls -A logs 2>/dev/null)" ]; then
        echo ""
        read -p "Do you want to clean log files? (y/N): " -n 1 -r
        echo
        
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            print_status "Cleaning log files..."
            rm -f logs/*.log 2>/dev/null || true
            print_success "Log files cleaned"
        else
            print_status "Keeping log files"
        fi
    fi
    
    # Clean up any temporary files
    find . -name "*.pyc" -delete 2>/dev/null || true
    find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
}

# Step 4: Show cleanup summary
show_cleanup_summary() {
    print_status "Cleanup Summary:"
    echo ""
    
    # Check what's still running
    echo "📊 System Status After Cleanup:"
    
    # Check search nodes
    nodes_running=0
    for i in {1..4}; do
        port=$((8100 + i))
        if check_port $port; then
            echo "  ❌ Node-$i: Still running on port $port"
            nodes_running=$((nodes_running + 1))
        else
            echo "  ✅ Node-$i: Stopped"
        fi
    done
    
    # Check Redis
    if redis-cli ping >/dev/null 2>&1; then
        echo "  ⚠️  Redis: Still running"
    else
        echo "  ✅ Redis: Stopped"
    fi
    
    echo ""
    
    if [ $nodes_running -eq 0 ]; then
        print_success "All search nodes have been stopped"
    else
        print_warning "$nodes_running search node(s) may still be running"
    fi
    
    echo ""
    echo "🔧 To restart the system, run: ./demo_start.sh"
}

# Main execution
main() {
    echo "🎯 Distributed Search System Cleanup"
    echo "===================================="
    
    stop_search_nodes
    stop_redis
    cleanup_files
    show_cleanup_summary
    
    echo ""
    print_success "🎉 Cleanup completed!"
    echo ""
    echo "The distributed search system has been stopped."
    echo "All resources have been cleaned up."
    echo ""
}

# Handle interrupt gracefully
trap 'echo ""; print_warning "Interrupted by user"; exit 1' INT

# Run main function
main "$@" 