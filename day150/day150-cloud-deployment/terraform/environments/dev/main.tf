# Development Environment Configuration

terraform {
  required_version = ">= 1.7.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }

  backend "s3" {
    bucket         = "log-platform-terraform-state-dev"
    key            = "dev/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-state-lock"
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "DistributedLogPlatform"
      Environment = "dev"
      ManagedBy   = "Terraform"
      CostCenter  = "Engineering"
    }
  }
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "log-platform-dev"
}

locals {
  common_tags = {
    Project     = "DistributedLogPlatform"
    Environment = "dev"
    ManagedBy   = "Terraform"
  }
}

# Network Module
module "network" {
  source = "../../modules/aws/network"

  vpc_name             = "${var.project_name}-vpc"
  vpc_cidr             = "10.0.0.0/16"
  availability_zones   = ["us-east-1a", "us-east-1b"]
  public_subnet_cidrs  = ["10.0.1.0/24", "10.0.2.0/24"]
  private_subnet_cidrs = ["10.0.10.0/24", "10.0.11.0/24"]
  database_subnet_cidrs = ["10.0.20.0/24", "10.0.21.0/24"]
  environment          = "dev"
  tags                 = local.common_tags
}

# Compute Module
module "compute" {
  source = "../../modules/aws/compute"

  cluster_name = "${var.project_name}-eks"
  vpc_id       = module.network.vpc_id
  subnet_ids   = module.network.private_subnet_ids
  
  node_groups = {
    collectors = {
      instance_type = "t3.medium"
      desired_size  = 2
      min_size      = 1
      max_size      = 3
    }
    processors = {
      instance_type = "t3.large"
      desired_size  = 2
      min_size      = 1
      max_size      = 4
    }
  }

  environment = "dev"
  tags        = local.common_tags
}

# Storage Module
module "storage" {
  source = "../../modules/aws/storage"

  identifier_prefix  = var.project_name
  vpc_id             = module.network.vpc_id
  subnet_ids         = module.network.database_subnet_ids
  db_instance_class  = "db.t3.small"
  cache_node_type    = "cache.t3.micro"
  environment        = "dev"
  tags               = local.common_tags
}

# Outputs
output "eks_cluster_endpoint" {
  description = "EKS cluster endpoint"
  value       = module.compute.cluster_endpoint
}

output "db_endpoint" {
  description = "Database endpoint"
  value       = module.storage.db_endpoint
  sensitive   = true
}

output "redis_endpoint" {
  description = "Redis endpoint"
  value       = module.storage.redis_endpoint
}
