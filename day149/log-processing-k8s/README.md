# Day 149: Kubernetes Deployment Definitions

Complete Kubernetes deployment for distributed log processing system.

## Quick Start

### Option 1: Local Kind Cluster

```bash
# 1. Create Kind cluster
kind create cluster --name log-processing

# 2. Build images
./scripts/build-images.sh

# 3. Load images to Kind
kind load docker-image log-processing-storage:latest --name log-processing
kind load docker-image log-processing-query:latest --name log-processing
kind load docker-image log-processing-collector:latest --name log-processing
kind load docker-image log-processing-dashboard:latest --name log-processing

# 4. Deploy to cluster
./scripts/deploy-kind.sh

# 5. Verify deployment
./scripts/verify-deployment.sh

# 6. Access dashboard
kubectl port-forward -n log-processing svc/dashboard 3000:3000
# Open http://localhost:3000
```

### Option 2: Docker Compose (Local Testing)

```bash
# Build and start
docker-compose up --build

# Access services
# - RabbitMQ Management: http://localhost:15672
# - Query Coordinator: http://localhost:8080/health
# - Storage Node: http://localhost:9090/health
```

## Testing

```bash
# Run integration tests
python tests/test_deployment.py

# Manual verification
kubectl get all -n log-processing
kubectl logs -n log-processing -l app=query-coordinator
```

## Cleanup

```bash
# Delete deployment
./scripts/cleanup.sh

# Delete Kind cluster
kind delete cluster --name log-processing
```

## Architecture

- **Storage Nodes**: StatefulSet with persistent volumes
- **RabbitMQ**: StatefulSet for message queuing
- **Query Coordinators**: Deployment (3 replicas)
- **Log Collectors**: Deployment (2 replicas)
- **Dashboard**: Deployment (2 replicas) with LoadBalancer

## File Structure

```
k8s-manifests/
├── base/              # Base Kubernetes manifests
└── overlays/          # Environment-specific overlays
    ├── dev/
    ├── staging/
    └── production/
```
