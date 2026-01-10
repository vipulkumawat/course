#!/bin/bash
# Demo script to create test LogProcessor resources for dashboard metrics

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🎬 Running Demo: Creating test LogProcessor resources..."

# Apply example processors if they don't exist
if ! kubectl get logprocessor error-processor > /dev/null 2>&1; then
    echo "Creating error-processor..."
    kubectl apply -f examples/error-processor.yaml
fi

if ! kubectl get logprocessor info-processor > /dev/null 2>&1; then
    echo "Creating info-processor..."
    kubectl apply -f examples/info-processor.yaml
fi

# Wait a bit for operator to process
sleep 3

echo "✅ Demo resources created!"
echo "Check dashboard at http://localhost:8000"
