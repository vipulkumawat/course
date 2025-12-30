#!/bin/bash

echo "🔍 Verifying deployment..."

echo ""
echo "1. Checking pods..."
kubectl get pods -n log-processing

echo ""
echo "2. Checking services..."
kubectl get svc -n log-processing

echo ""
echo "3. Testing query coordinator health..."
QUERY_POD=$(kubectl get pod -n log-processing -l app=query-coordinator -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
if [ -n "$QUERY_POD" ]; then
  QUERY_READY=$(kubectl get pod -n log-processing $QUERY_POD -o jsonpath='{.status.containerStatuses[?(@.name=="query-coordinator")].ready}' 2>/dev/null)
  if [ "$QUERY_READY" = "true" ]; then
    kubectl exec -n log-processing $QUERY_POD -c query-coordinator -- python3 -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8080/health').read().decode())" 2>/dev/null || \
    kubectl exec -n log-processing $QUERY_POD -c query-coordinator -- python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8080/health').read().decode())" 2>/dev/null || \
    echo "⚠️  Query coordinator not ready yet"
  else
    echo "⚠️  Query coordinator container not ready (waiting for RabbitMQ)"
  fi
else
  echo "⚠️  No query coordinator pods found"
fi

echo ""
echo "4. Testing storage node health..."
STORAGE_POD=$(kubectl get pod -n log-processing -l app=storage-node -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
if [ -n "$STORAGE_POD" ]; then
  kubectl exec -n log-processing $STORAGE_POD -- python3 -c "import urllib.request; print(urllib.request.urlopen('http://localhost:9090/health').read().decode())" 2>/dev/null || \
  kubectl exec -n log-processing $STORAGE_POD -- python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:9090/health').read().decode())" 2>/dev/null || \
  echo "⚠️  Storage node health check failed"
else
  echo "⚠️  No storage node pods found"
fi

echo ""
echo "5. Checking RabbitMQ..."
kubectl exec -n log-processing rabbitmq-0 -- rabbitmq-diagnostics ping

echo ""
echo "✅ Verification complete!"
