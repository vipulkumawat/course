#!/bin/bash

echo "🚀 Deploying to Kind cluster..."

# Apply all manifests
kubectl apply -k k8s-manifests/base/

echo "⏳ Waiting for deployments to be ready..."

kubectl wait --for=condition=ready pod \
  -l app=rabbitmq \
  -n log-processing \
  --timeout=120s

kubectl wait --for=condition=ready pod \
  -l app=storage-node \
  -n log-processing \
  --timeout=120s

kubectl wait --for=condition=ready pod \
  -l app=query-coordinator \
  -n log-processing \
  --timeout=120s

kubectl wait --for=condition=ready pod \
  -l app=dashboard \
  -n log-processing \
  --timeout=120s

echo "✅ Deployment complete!"
echo ""
echo "📊 Deployment status:"
kubectl get pods -n log-processing
echo ""
echo "🌐 Services:"
kubectl get svc -n log-processing
