#!/bin/bash
# Complete Build, Test & Deploy Instructions for Day 53

echo "🚀 Day 53: Distributed Search System - Complete Build Guide"

# Step 1: Environment Setup
setup_environment() {
    echo "1️⃣ Setting up environment..."
    
    # Check Python version
    python_version=$(python3.11 --version 2>/dev/null || python3 --version)
    echo "Python version: $python_version"
    
    # Check Redis availability
    if command -v redis-server >/dev/null 2>&1; then
        echo "✅ Redis found"
    else
        echo "❌ Redis not found. Installing..."
        # macOS: brew install redis
        # Ubuntu: sudo apt install redis-server
        docker run -d --name redis -p 6379:6379 redis:7-alpine
    fi
    
    # Create project structure if not exists
    if [ ! -d "distributed-search" ]; then
        mkdir -p distributed-search/{src/{coordinator,node,storage},tests,config,logs,web,docker}
        cd distributed-search
    else
        cd distributed-search
    fi
    
    # Activate virtual environment if it exists
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
    else
        echo "⚠️  Virtual environment not found, using system Python"
    fi
}

# Step 2: Start Infrastructure
start_infrastructure() {
    echo "2️⃣ Starting infrastructure..."
    
    # Start Redis if not running
    redis-cli ping >/dev/null 2>&1 || {
        echo "Starting Redis..."
        redis-server --daemonize yes
        sleep 2
    }
    
    # Verify Redis connection
    if redis-cli ping >/dev/null 2>&1; then
        echo "✅ Redis running"
    else
        echo "❌ Redis failed to start"
        exit 1
    fi
}

# Step 3: Build and Test
build_and_test() {
    echo "3️⃣ Building and testing system..."
    
    # Run unit tests
    echo "Running unit tests..."
    python3 -m pytest tests/test_distributed_search.py -v
    
    if [ $? -eq 0 ]; then
        echo "✅ Unit tests passed"
    else
        echo "❌ Unit tests failed"
        return 1
    fi
    
    # Start index nodes in background
    echo "Starting index nodes..."
    
    # Kill any existing processes on our ports
    for port in 8101 8102 8103 8104; do
        lsof -ti:$port | xargs kill -9 2>/dev/null || true
    done
    
    # Start 4 index nodes
    for i in {1..4}; do
        echo "Starting node-$i on port 810$i"
        python3 src/node/main.py node-$i > logs/node-$i.log 2>&1 &
        sleep 1
    done
    
    # Wait for nodes to be ready
    echo "Waiting for nodes to start..."
    sleep 5
    
    # Test node health
    for i in {1..4}; do
        port=$((8100 + i))
        if curl -s http://localhost:$port/health >/dev/null; then
            echo "✅ Node-$i healthy"
        else
            echo "❌ Node-$i not responding"
        fi
    done
}

# Step 4: Load Test Data
load_test_data() {
    echo "4️⃣ Loading test data..."
    
    # Sample log documents
    declare -a docs=(
        "doc1:User authentication error in login system"
        "doc2:Database connection timeout during query execution" 
        "doc3:Payment processing failed with error code 500"
        "doc4:User login successful from IP 192.168.1.100"
        "doc5:Database backup completed successfully"
        "doc6:Security alert: Multiple failed login attempts"
        "doc7:Payment gateway error during transaction"
        "doc8:Database index rebuild started"
        "doc9:User session expired during checkout"
        "doc10:System monitoring alert: High CPU usage"
    )
    
    # Distribute documents across nodes
    for i in "${!docs[@]}"; do
        IFS=':' read -r doc_id content <<< "${docs[$i]}"
        node_port=$((8101 + (i % 4)))
        
        echo "Indexing $doc_id on port $node_port"
        curl -s -X POST "http://localhost:$node_port/index" \
             -H "Content-Type: application/json" \
             -d "{\"doc_id\": \"$doc_id\", \"content\": \"$content\"}" || true
    done
    
    echo "✅ Test data loaded"
}

# Step 5: Run Demonstration
run_demonstration() {
    echo "5️⃣ Running search demonstrations..."
    
    # Test queries
    declare -a queries=("error" "login" "database" "payment")
    
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
                    echo "$result" | jq -r '.documents[] | "    - \(.id): \(.content[:50])..."'
                    total_results=$((total_results + count))
                fi
            fi
        done
        
        echo "  Total results found: $total_results"
    done
}

# Step 6: Performance Testing
performance_test() {
    echo "6️⃣ Running performance tests..."
    
    echo "Testing search latency..."
    
    # Measure search performance
    start_time=$(date +%s%N)
    for i in {1..100}; do
        curl -s -X POST "http://localhost:8101/search" \
             -H "Content-Type: application/json" \
             -d '{"terms": ["error"]}' >/dev/null
    done
    end_time=$(date +%s%N)
    
    total_time=$(((end_time - start_time) / 1000000))  # Convert to milliseconds
    avg_latency=$((total_time / 100))
    
    echo "Average search latency: ${avg_latency}ms"
    
    if [ "$avg_latency" -lt 100 ]; then
        echo "✅ Performance test passed (< 100ms)"
    else
        echo "⚠️  Performance slower than expected"
    fi
}

# Step 7: Integration Test
integration_test() {
    echo "7️⃣ Running integration tests..."
    
    python3 -m pytest tests/test_integration.py -v -s
    
    if [ $? -eq 0 ]; then
        echo "✅ Integration tests passed"
    else
        echo "❌ Integration tests failed"
    fi
}

# Step 8: Cleanup
cleanup() {
    echo "8️⃣ Cleaning up..."
    
    # Kill node processes
    for port in 8101 8102 8103 8104; do
        lsof -ti:$port | xargs kill -9 2>/dev/null || true
    done
    
    echo "✅ Cleanup completed"
}

# Main execution flow
main() {
    echo "🎯 Starting Day 53 Distributed Search System"
    echo "=============================================="
    
    setup_environment
    start_infrastructure
    build_and_test
    load_test_data
    run_demonstration
    performance_test
    integration_test
    
    echo ""
    echo "🎉 Day 53 Complete! Distributed search system is running."
    echo ""
    echo "✅ Achievements unlocked:"
    echo "  - Consistent hash ring distribution"
    echo "  - Multi-node index storage"
    echo "  - Distributed query coordination"
    echo "  - Fault-tolerant search"
    echo ""
    echo "🔧 Manual testing commands:"
    echo "  curl -X POST http://localhost:8101/search -H 'Content-Type: application/json' -d '{\"terms\": [\"error\"]}'"
    echo "  curl http://localhost:8101/stats"
    echo ""
    echo "🧹 Run 'bash $0 cleanup' to stop all services"
}

# Handle command line arguments
case "${1:-}" in
    "cleanup")
        cleanup
        ;;
    *)
        main
        ;;
esac