#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🛑 Stopping Day 152: Kubernetes Operator"

# Stop API server
if [ -f api.pid ]; then
    API_PID=$(cat api.pid)
    if ps -p $API_PID > /dev/null 2>&1; then
        echo "Stopping API server (PID: $API_PID)..."
        kill $API_PID 2>/dev/null || true
    fi
    rm -f api.pid
fi

# Delete example resources
kubectl delete -f examples/ --ignore-not-found=true

# Delete operator
kubectl delete -f deployment/operator/deployment.yaml --ignore-not-found=true

# Delete CRDs (this will delete all custom resources)
kubectl delete -f src/crds/ --ignore-not-found=true

# Delete cluster
kind delete cluster --name log-operator

echo "✅ Cleanup complete"
