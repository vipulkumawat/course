#!/bin/bash
set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🚀 Starting Day 152: Kubernetes Operator"
echo "========================================"

# Check for duplicate API server processes
if [ -f api.pid ]; then
    OLD_PID=$(cat api.pid)
    if ps -p $OLD_PID > /dev/null 2>&1; then
        echo "⚠️  API server already running (PID: $OLD_PID). Stopping it..."
        kill $OLD_PID 2>/dev/null || true
        rm api.pid
    fi
fi

# Check if Kind cluster exists
if ! kind get clusters | grep -q "log-operator"; then
    echo "📦 Creating Kind cluster..."
    kind create cluster --name log-operator --config - <<CLUSTER_CONFIG
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
  - role: control-plane
  - role: worker
CLUSTER_CONFIG
    echo "✅ Cluster created"
else
    echo "✅ Using existing cluster"
fi

# Create Python virtual environment
if [ ! -d "venv" ]; then
    echo "🐍 Creating Python 3.11 virtual environment..."
    python3.11 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Install CRDs
echo "📝 Installing Custom Resource Definitions..."
kubectl apply -f src/crds/

# Create RBAC
echo "🔐 Creating RBAC resources..."
kubectl apply -f deployment/rbac/

# Build operator Docker image
echo "🐳 Building operator Docker image..."
docker build -t log-operator:latest .

# Load image into Kind cluster
echo "📥 Loading image into Kind cluster..."
kind load docker-image log-operator:latest --name log-operator

# Deploy operator
echo "🚀 Deploying operator..."
kubectl apply -f deployment/operator/deployment.yaml

# Wait for operator to be ready
echo "⏳ Waiting for operator to be ready..."
kubectl wait --for=condition=available --timeout=60s deployment/log-operator

# Create example LogProcessors
echo "📋 Creating example LogProcessor resources..."
kubectl apply -f examples/error-processor.yaml
kubectl apply -f examples/info-processor.yaml

# Start API server in background
echo "🌐 Starting API server..."
cd "$SCRIPT_DIR"
python src/api/server.py > api.log 2>&1 &
API_PID=$!
echo $API_PID > api.pid
echo "API server started with PID: $API_PID"

sleep 5

echo ""
echo "✅ Setup complete!"
echo ""
echo "📊 Dashboard: http://localhost:8000"
echo "🔍 Check operator logs: kubectl logs -f deployment/log-operator"
echo "📋 List processors: kubectl get logprocessors"
echo ""
echo "To stop: ./stop.sh"
