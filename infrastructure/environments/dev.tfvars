# =============================================================================
# HeyCloud - Dev Environment Variables
# =============================================================================
# Purpose: Environment-specific overrides for development.
# Usage:   terraform plan -var-file=../environments/dev.tfvars
# =============================================================================

environment = "dev"
aws_region  = "us-east-1"

# Kinesis - minimal for cost savings in dev
kinesis_shard_count    = 1
kinesis_retention_hours = 24

# DynamoDB - on-demand (no capacity planning needed)
dynamodb_billing_mode = "PAY_PER_REQUEST"
dynamodb_ttl_enabled  = true

# Lambda - smaller allocations for dev
stream_processor_memory  = 256
stream_processor_timeout = 60
analytics_api_memory     = 128
analytics_api_timeout    = 30
lambda_batch_size        = 100
lambda_batch_window      = 5
lambda_retry_attempts    = 3

# S3 lifecycle - shorter retention for dev
s3_lifecycle_ia_days          = 30
s3_lifecycle_glacier_days     = 90
s3_lifecycle_expiration_days  = 365

# Monitoring
alert_email                   = "ashwakpathem@gmail.com"
cloudwatch_log_retention_days = 7

# API Gateway
api_throttle_rate_limit  = 100
api_throttle_burst_limit = 50
