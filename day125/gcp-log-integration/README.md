# Day 125: GCP Logging Integration

Production-ready integration for ingesting Google Cloud Platform logs into unified log processing system.

## Quick Start
```bash
# 1. Configure your GCP projects
vim config/projects.yaml

# 2. Add service account credentials
cp your-service-account.json config/credentials/

# 3. Run tests
pytest tests/ -v

# 4. Start ingestion
python -m src.multi_project_manager

# 5. View dashboard
open http://localhost:8000
```

## Features

- ✅ Multi-project concurrent ingestion
- ✅ Real-time streaming with Cloud Logging API
- ✅ Checkpoint-based recovery
- ✅ Resource metadata enrichment
- ✅ Rate limiting and quota management
- ✅ Real-time monitoring dashboard

## Configuration

Edit `config/projects.yaml` to add your GCP projects.

See `config/credentials/README.md` for service account setup instructions.

## Testing
```bash
# Run unit tests
pytest tests/ -v

# Load test
python tests/load_test.py

# Integration test
python tests/integration_test.py
```

## Deployment
```bash
# Docker deployment
docker-compose up -d

# Kubernetes deployment
kubectl apply -f k8s/
```

## Documentation

- [GCP Client Documentation](docs/gcp_client.md)
- [Multi-Project Manager](docs/multi_project.md)
- [Troubleshooting Guide](docs/troubleshooting.md)
