# =============================================================================
# HeyCloud - Production Environment Variables
# =============================================================================

environment = "prod"
aws_region  = "us-east-1"

# Kinesis - 2 shards for production throughput
kinesis_shard_count    = 2
kinesis_retention_hours = 168  # 7 days

# DynamoDB
dynamodb_billing_mode = "PAY_PER_REQUEST"
dynamodb_ttl_enabled  = true

# Lambda - larger allocations for prod
stream_processor_memory  = 512
stream_processor_timeout = 120
analytics_api_memory     = 256
analytics_api_timeout    = 30
lambda_batch_size        = 100
lambda_batch_window      = 5
lambda_retry_attempts    = 3

# S3 lifecycle
s3_lifecycle_ia_days          = 30
s3_lifecycle_glacier_days     = 90
s3_lifecycle_expiration_days  = 365

# Monitoring
alert_email                   = "ops-team@example.com"
cloudwatch_log_retention_days = 30

# API Gateway - higher limits for prod
api_throttle_rate_limit  = 1000
api_throttle_burst_limit = 500
