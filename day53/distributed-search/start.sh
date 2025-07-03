#!/bin/bash
# Demo Start Script for Distributed Search System
# This script starts the complete distributed search system with test data

set -e  # Exit on any error

echo "🚀 Starting Distributed Search System Demo"
echo "=========================================="

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

# Function to wait for service to be ready
wait_for_service() {
    local url=$1
    local max_attempts=30
    local attempt=1
    
    print_status "Waiting for service at $url..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s "$url" >/dev/null 2>&1; then
            print_success "Service ready at $url"
            return 0
        fi
        
        echo -n "."
        sleep 1
        attempt=$((attempt + 1))
    done
    
    print_error "Service at $url failed to start within $max_attempts seconds"
    return 1
}

# Step 1: Environment Setup
setup_environment() {
    print_status "Setting up environment..."
    
    # Check Python version
    if command -v python3.11 >/dev/null 2>&1; then
        PYTHON_CMD="python3.11"
    elif command -v python3 >/dev/null 2>&1; then
        PYTHON_CMD="python3"
    else
        print_error "Python 3 not found"
        exit 1
    fi
    
    print_success "Using Python: $($PYTHON_CMD --version)"
    
    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        print_warning "Virtual environment not found. Creating..."
        $PYTHON_CMD -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Install dependencies if needed
    if [ ! -f "venv/lib/python*/site-packages/fastapi" ]; then
        print_status "Installing dependencies..."
        pip install -r requirements.txt
    fi
    
    print_success "Environment setup complete"
}

# Step 2: Start Infrastructure
start_infrastructure() {
    print_status "Starting infrastructure..."
    
    # Check if Redis is running
    if ! redis-cli ping >/dev/null 2>&1; then
        print_status "Starting Redis..."
        
        # Try to start Redis server
        if command -v redis-server >/dev/null 2>&1; then
            redis-server --daemonize yes
            sleep 2
        else
            print_error "Redis server not found. Please install Redis or start it manually."
            exit 1
        fi
    fi
    
    # Verify Redis connection
    if redis-cli ping >/dev/null 2>&1; then
        print_success "Redis is running"
    else
        print_error "Failed to start Redis"
        exit 1
    fi
}

# Step 3: Start Search Nodes
start_search_nodes() {
    print_status "Starting search nodes..."
    
    # Kill any existing processes on our ports
    for port in 8101 8102 8103 8104; do
        if check_port $port; then
            print_warning "Port $port is in use. Stopping existing process..."
            lsof -ti:$port | xargs kill -9 2>/dev/null || true
            sleep 1
        fi
    done
    
    # Create logs directory if it doesn't exist
    mkdir -p logs
    
    # Start 4 index nodes
    for i in {1..4}; do
        node_id="node-$i"
        port=$((8100 + i))
        
        print_status "Starting $node_id on port $port"
        
        # Start node in background
        $PYTHON_CMD src/node/main.py $node_id > logs/$node_id.log 2>&1 &
        echo $! > logs/$node_id.pid
        
        sleep 1
    done
    
    # Wait for all nodes to be ready
    print_status "Waiting for nodes to start..."
    sleep 3
    
    # Test node health
    all_healthy=true
    for i in {1..4}; do
        port=$((8100 + i))
        if wait_for_service "http://localhost:$port/health"; then
            print_success "Node-$i healthy"
        else
            print_error "Node-$i not responding"
            all_healthy=false
        fi
    done
    
    if [ "$all_healthy" = false ]; then
        print_error "Some nodes failed to start properly"
        exit 1
    fi
    
    print_success "All search nodes are running"
}

# Step 3.5: Start Coordinator
start_coordinator() {
    print_status "Starting coordinator (main dashboard) on port 8000..."
    # Kill any existing process on port 8000
    if check_port 8000; then
        print_warning "Port 8000 is in use. Stopping existing process..."
        lsof -ti:8000 | xargs kill -9 2>/dev/null || true
        sleep 1
    fi
    # Start coordinator in background
    $PYTHON_CMD src/coordinator/main.py > logs/coordinator.log 2>&1 &
    echo $! > logs/coordinator.pid
}

wait_for_coordinator() {
    wait_for_service "http://localhost:8000/health"
}

# Step 3.6: Start Web Dashboard
start_web_dashboard() {
    print_status "Starting web dashboard on port 8080..."
    # Kill any existing process on port 8080
    if check_port 8080; then
        print_warning "Port 8080 is in use. Stopping existing process..."
        lsof -ti:8080 | xargs kill -9 2>/dev/null || true
        sleep 1
    fi
    # Start web dashboard in background
    $PYTHON_CMD web/server.py > logs/web-dashboard.log 2>&1 &
    echo $! > logs/web-dashboard.pid
    sleep 2
}

# Step 4: Load Test Data
load_test_data() {
    print_status "Loading test data..."
    
    # Sample log documents with more realistic content
    declare -a docs=(
        "doc1:User authentication error in login system - Invalid credentials provided"
        "doc2:Database connection timeout during query execution - Connection pool exhausted"
        "doc3:Payment processing failed with error code 500 - Gateway timeout"
        "doc4:User login successful from IP 192.168.1.100 - Session created"
        "doc5:Database backup completed successfully - 2.5GB data backed up"
        "doc6:Security alert: Multiple failed login attempts from IP 10.0.0.15"
        "doc7:Payment gateway error during transaction - SSL certificate expired"
        "doc8:Database index rebuild started - Optimizing query performance"
        "doc9:User session expired during checkout - Auto-logout after 30 minutes"
        "doc10:System monitoring alert: High CPU usage detected - 95% utilization"
        "doc11:API rate limit exceeded for user account - Too many requests"
        "doc12:Database query optimization completed - 40% performance improvement"
        "doc13:User password reset requested - Email sent to user@example.com"
        "doc14:Payment transaction successful - Order #12345 processed"
        "doc15:Database maintenance scheduled - Weekly cleanup at 2 AM"
        "doc16:Security scan completed - No vulnerabilities found"
        "doc17:User profile updated - Email preferences changed"
        "doc18:Database connection restored - Network issue resolved"
        "doc19:Payment refund processed - Customer satisfaction guarantee"
        "doc20:System backup verification passed - Data integrity confirmed"
    )
    
    # Distribute documents across nodes using consistent hashing
    for i in "${!docs[@]}"; do
        IFS=':' read -r doc_id content <<< "${docs[$i]}"
        node_port=$((8101 + (i % 4)))
        
        print_status "Indexing $doc_id on port $node_port"
        
        # Use the correct API format - doc_id and content as query parameters
        response=$(curl -s -X POST "http://localhost:$node_port/index?doc_id=$doc_id&content=$(echo "$content" | sed 's/ /%20/g')" 2>/dev/null)
        
        if [ $? -eq 0 ]; then
            print_success "Indexed $doc_id successfully"
        else
            print_warning "Failed to index $doc_id: $response"
        fi
    done
    
    print_success "Test data loading complete"
}

# Step 5: Run Demo Searches
run_demo_searches() {
    print_status "Running demo searches..."
    
    # Test queries
    declare -a queries=("error" "login" "database" "payment" "security" "user")
    
    for query in "${queries[@]}"; do
        echo ""
        echo "🔍 Searching for: '$query'"
        echo "----------------------------------------"
        
        total_results=0
        
        # Query all nodes (simulating coordinator behavior)
        for port in 8101 8102 8103 8104; do
            result=$(curl -s -X POST "http://localhost:$port/search" \
                          -H "Content-Type: application/json" \
                          -d "{\"terms\": [\"$query\"]}" 2>/dev/null)
            
            if [ $? -eq 0 ] && echo "$result" | jq -e '.documents' >/dev/null 2>&1; then
                count=$(echo "$result" | jq '.documents | length')
                if [ "$count" -gt 0 ]; then
                    echo "  Node (port $port): $count results"
                    echo "$result" | jq -r '.documents[] | "    - \(.id): \(.content[:60])..."'
                    total_results=$((total_results + count))
                fi
            fi
        done
        
        echo "  Total results found: $total_results"
    done
}

# Step 6: Show System Status
show_system_status() {
    print_status "System Status:"
    echo ""
    
    # Show running processes
    echo "📊 Running Processes:"
    for i in {1..4}; do
        port=$((8100 + i))
        if check_port $port; then
            echo "  ✅ Node-$i: http://localhost:$port"
        else
            echo "  ❌ Node-$i: Not running"
        fi
    done
    
    # Coordinator
    if check_port 8000; then
        echo "  ✅ Coordinator: http://localhost:8000 (API)"
    else
        echo "  ❌ Coordinator: Not running"
    fi
    
    # Web Dashboard
    if check_port 8080; then
        echo "  ✅ Web Dashboard: http://localhost:8080/dashboard.html"
    else
        echo "  ❌ Web Dashboard: Not running"
    fi
    
    # Show Redis status
    if redis-cli ping >/dev/null 2>&1; then
        echo "  ✅ Redis: Running"
    else
        echo "  ❌ Redis: Not running"
    fi
    
    echo ""
    echo "🔧 Manual Testing Commands:"
    echo "  # Web Dashboard (recommended):"
    echo "  open http://localhost:8080/dashboard.html"
    echo ""
    echo "  # Search via coordinator API:"
    echo "  curl -X POST http://localhost:8000/search \\"
    echo "       -H 'Content-Type: application/json' \\"
    echo "       -d '{\"terms\": [\"error\"]}'"
    echo ""
    echo "  # Coordinator API info:"
    echo "  curl http://localhost:8000/"
    echo ""
    echo "  # Get node statistics:"
    echo "  curl http://localhost:8101/stats"
    echo ""
    echo "  # Health check:"
    echo "  curl http://localhost:8101/health"
    echo ""
    echo "🧹 To stop the system, run: ./demo_cleanup.sh"
}

# Main execution
main() {
    echo "🎯 Distributed Search System Demo"
    echo "================================="
    
    setup_environment
    start_infrastructure
    start_search_nodes
    start_coordinator
    wait_for_coordinator
    start_web_dashboard
    load_test_data
    run_demo_searches
    show_system_status
    
    echo ""
    print_success "🎉 Demo started successfully!"
    echo ""
    echo "The distributed search system is now running with:"
    echo "  • 4 search nodes (ports 8101-8104)"
    echo "  • Coordinator API (port 8000)"
    echo "  • Web Dashboard (port 8080)"
    echo "  • Redis backend for storage"
    echo "  • 20 sample documents indexed"
    echo "  • Consistent hashing distribution"
    echo ""
}

# Run main function
main "$@" 