# Multi-Cloud Deployment Guide

## Prerequisites

### Required Tools
- Terraform >= 1.7.0
- Python 3.11+
- Cloud CLI tools (AWS CLI, Azure CLI, or gcloud)
- kubectl (for Kubernetes management)

### Cloud Provider Setup

#### AWS
```bash
# Configure AWS credentials
aws configure

# Create S3 bucket for Terraform state
aws s3 mb s3://log-platform-terraform-state-dev
aws s3 versioning enable s3://log-platform-terraform-state-dev

# Create DynamoDB table for state locking
aws dynamodb create-table \
  --table-name terraform-state-lock \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST
```

#### Azure
```bash
# Login to Azure
az login

# Create resource group for Terraform state
az group create --name terraform-state --location eastus

# Create storage account
az storage account create \
  --resource-group terraform-state \
  --name logplatformtfstate \
  --sku Standard_LRS
```

#### GCP
```bash
# Login to GCP
gcloud auth login

# Set project
gcloud config set project YOUR_PROJECT_ID

# Create bucket for Terraform state
gsutil mb gs://log-platform-terraform-state
```

## Deployment Steps

### 1. Environment Preparation
```bash
# Clone repository
git clone YOUR_REPO
cd day150-cloud-deployment

# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Deploy Development Environment
```bash
# Deploy to AWS Dev
python scripts/deploy.py \
  --environment dev \
  --cloud aws

# Monitor deployment via dashboard
python web/app.py
# Open http://localhost:5000 in browser
```

### 3. Verify Deployment
```bash
# Configure kubectl
aws eks update-kubeconfig \
  --region us-east-1 \
  --name log-platform-dev-eks

# Verify cluster
kubectl get nodes
kubectl get pods --all-namespaces
```

### 4. Deploy to Other Clouds
```bash
# Azure
python scripts/deploy.py --environment dev --cloud azure

# GCP
python scripts/deploy.py --environment dev --cloud gcp
```

## Cost Optimization

### Development Environment
- Use smaller instance types (t3.small, t3.medium)
- Single availability zone
- Minimal redundancy
- **Estimated: $150/month**

### Staging Environment
- Production-like but smaller scale
- Multi-AZ for testing
- Limited auto-scaling
- **Estimated: $500/month**

### Production Environment
- Full redundancy and HA
- Multi-region capability
- Aggressive auto-scaling
- **Estimated: $2,500/month**

## Troubleshooting

### Terraform Init Fails
```bash
# Clean and reinitialize
rm -rf .terraform .terraform.lock.hcl
terraform init
```

### State Lock Issues
```bash
# Force unlock (use with caution)
terraform force-unlock LOCK_ID
```

### Permission Errors
```bash
# Verify cloud credentials
aws sts get-caller-identity  # AWS
az account show              # Azure
gcloud auth list             # GCP
```

## Security Best Practices

1. **Never commit credentials** to version control
2. **Use remote state** with encryption
3. **Enable state locking** to prevent concurrent modifications
4. **Implement least privilege** IAM policies
5. **Rotate credentials** regularly
6. **Enable audit logging** on all resources
7. **Use private subnets** for workloads
8. **Implement network security groups** properly

## Next Steps

After deployment:
1. Configure CI/CD pipeline (Day 151)
2. Set up monitoring and alerting
3. Implement backup and disaster recovery
4. Configure auto-scaling policies
5. Optimize costs based on actual usage
