# AWS Storage Module - RDS and ElastiCache for Log Platform

variable "identifier_prefix" {
  description = "Prefix for resource identifiers"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "subnet_ids" {
  description = "Subnet IDs for database"
  type        = list(string)
}

variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.medium"
}

variable "cache_node_type" {
  description = "ElastiCache node type"
  type        = string
  default     = "cache.t3.micro"
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "tags" {
  description = "Resource tags"
  type        = map(string)
  default     = {}
}

# DB Subnet Group
resource "aws_db_subnet_group" "main" {
  name       = "${var.identifier_prefix}-db-subnet"
  subnet_ids = var.subnet_ids

  tags = merge(
    var.tags,
    {
      Name = "${var.identifier_prefix}-db-subnet"
    }
  )
}

# Security Group for RDS
resource "aws_security_group" "rds" {
  name        = "${var.identifier_prefix}-rds-sg"
  description = "Security group for RDS PostgreSQL"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/8"]
    description = "PostgreSQL access from VPC"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound"
  }

  tags = merge(
    var.tags,
    {
      Name = "${var.identifier_prefix}-rds-sg"
    }
  )
}

# RDS PostgreSQL Instance
resource "aws_db_instance" "postgres" {
  identifier     = "${var.identifier_prefix}-postgres"
  engine         = "postgres"
  engine_version = "15.5"
  instance_class = var.db_instance_class

  allocated_storage     = 100
  max_allocated_storage = 1000
  storage_type          = "gp3"
  storage_encrypted     = true

  db_name  = "logplatform"
  username = "logadmin"
  password = random_password.db_password.result

  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]

  backup_retention_period = var.environment == "prod" ? 30 : 7
  backup_window           = "03:00-04:00"
  maintenance_window      = "sun:04:00-sun:05:00"

  enabled_cloudwatch_logs_exports = ["postgresql", "upgrade"]
  
  skip_final_snapshot       = var.environment != "prod"
  final_snapshot_identifier = var.environment == "prod" ? "${var.identifier_prefix}-final-snapshot-${formatdate("YYYY-MM-DD-hhmm", timestamp())}" : null

  tags = merge(
    var.tags,
    {
      Name = "${var.identifier_prefix}-postgres"
    }
  )
}

# Random password for database
resource "random_password" "db_password" {
  length  = 32
  special = true
}

# Store password in Secrets Manager
resource "aws_secretsmanager_secret" "db_password" {
  name = "${var.identifier_prefix}/db-password"

  tags = var.tags
}

resource "aws_secretsmanager_secret_version" "db_password" {
  secret_id     = aws_secretsmanager_secret.db_password.id
  secret_string = random_password.db_password.result
}

# ElastiCache Subnet Group
resource "aws_elasticache_subnet_group" "main" {
  name       = "${var.identifier_prefix}-cache-subnet"
  subnet_ids = var.subnet_ids

  tags = merge(
    var.tags,
    {
      Name = "${var.identifier_prefix}-cache-subnet"
    }
  )
}

# Security Group for ElastiCache
resource "aws_security_group" "redis" {
  name        = "${var.identifier_prefix}-redis-sg"
  description = "Security group for ElastiCache Redis"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 6379
    to_port     = 6379
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/8"]
    description = "Redis access from VPC"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound"
  }

  tags = merge(
    var.tags,
    {
      Name = "${var.identifier_prefix}-redis-sg"
    }
  )
}

# ElastiCache Redis Cluster
resource "aws_elasticache_cluster" "redis" {
  cluster_id           = "${var.identifier_prefix}-redis"
  engine               = "redis"
  engine_version       = "7.0"
  node_type            = var.cache_node_type
  num_cache_nodes      = 1
  parameter_group_name = "default.redis7"
  port                 = 6379
  subnet_group_name    = aws_elasticache_subnet_group.main.name
  security_group_ids   = [aws_security_group.redis.id]

  snapshot_retention_limit = var.environment == "prod" ? 5 : 0
  snapshot_window          = "03:00-05:00"

  tags = merge(
    var.tags,
    {
      Name = "${var.identifier_prefix}-redis"
    }
  )
}

# Outputs
output "db_endpoint" {
  description = "RDS endpoint"
  value       = aws_db_instance.postgres.endpoint
}

output "db_name" {
  description = "Database name"
  value       = aws_db_instance.postgres.db_name
}

output "db_password_secret_arn" {
  description = "ARN of secret containing database password"
  value       = aws_secretsmanager_secret.db_password.arn
}

output "redis_endpoint" {
  description = "Redis endpoint"
  value       = "${aws_elasticache_cluster.redis.cache_nodes[0].address}:${aws_elasticache_cluster.redis.cache_nodes[0].port}"
}
