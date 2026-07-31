# =============================================================================
# HeyCloud - Root Terraform Configuration
# =============================================================================
# Purpose: Wire all infrastructure modules together.
# Order: Data sources → Storage → Networking → Compute → Monitoring
#
# Module dependency graph:
#   S3, SQS, Kinesis, DynamoDB → IAM → Lambda → API Gateway → Monitoring
# =============================================================================

# Get current AWS account ID (used for ARN construction)
data "aws_caller_identity" "current" {}

# =============================================================================
# Storage Layer
# =============================================================================

module "s3" {
  source = "./modules/s3"

  project_name              = var.project_name
  environment               = var.environment
  account_id                = data.aws_caller_identity.current.account_id
  lifecycle_ia_days          = var.s3_lifecycle_ia_days
  lifecycle_glacier_days     = var.s3_lifecycle_glacier_days
  lifecycle_expiration_days  = var.s3_lifecycle_expiration_days
}

module "dynamodb" {
  source = "./modules/dynamodb"

  project_name  = var.project_name
  environment   = var.environment
  billing_mode  = var.dynamodb_billing_mode
  ttl_enabled   = var.dynamodb_ttl_enabled
}

module "sqs" {
  source = "./modules/sqs"

  project_name = var.project_name
  environment  = var.environment
}

# =============================================================================
# Streaming Layer
# =============================================================================
# Kinesis is disabled due to AWS account subscription limits.
# Streaming is handled via SQS (events queue).

# =============================================================================
# Security Layer
# =============================================================================

module "iam" {
  source = "./modules/iam"

  project_name                   = var.project_name
  environment                    = var.environment
  aws_region                     = var.aws_region
  account_id                     = data.aws_caller_identity.current.account_id
  dynamodb_events_table_arn      = module.dynamodb.events_table_arn
  dynamodb_aggregations_table_arn = module.dynamodb.aggregations_table_arn
  s3_data_lake_bucket_arn        = module.s3.data_lake_bucket_arn
  events_queue_arn               = module.sqs.events_queue_arn
  dlq_arn                        = module.sqs.dlq_arn
}

# =============================================================================
# Compute Layer
# =============================================================================

module "lambda" {
  source = "./modules/lambda"

  project_name                    = var.project_name
  environment                     = var.environment
  runtime                         = var.lambda_runtime
  stream_processor_role_arn       = module.iam.stream_processor_role_arn
  analytics_api_role_arn          = module.iam.analytics_api_role_arn
  events_queue_arn                = module.sqs.events_queue_arn
  dlq_arn                         = module.sqs.dlq_arn
  lambda_artifacts_bucket         = module.s3.lambda_artifacts_bucket_name
  dynamodb_events_table_name      = module.dynamodb.events_table_name
  dynamodb_aggregations_table_name = module.dynamodb.aggregations_table_name
  s3_data_lake_bucket_name        = module.s3.data_lake_bucket_name
  stream_processor_memory         = var.stream_processor_memory
  stream_processor_timeout        = var.stream_processor_timeout
  analytics_api_memory            = var.analytics_api_memory
  analytics_api_timeout           = var.analytics_api_timeout
  batch_size                      = var.lambda_batch_size
  batch_window                    = var.lambda_batch_window
  retry_attempts                  = var.lambda_retry_attempts
  log_retention_days              = var.cloudwatch_log_retention_days
}

# =============================================================================
# API Layer
# =============================================================================

module "api_gateway" {
  source = "./modules/api_gateway"

  project_name                = var.project_name
  environment                 = var.environment
  aws_region                  = var.aws_region
  analytics_api_invoke_arn    = module.lambda.analytics_api_invoke_arn
  analytics_api_function_name = module.lambda.analytics_api_function_name
  throttle_rate_limit         = var.api_throttle_rate_limit
  throttle_burst_limit        = var.api_throttle_burst_limit
}

# =============================================================================
# Monitoring Layer
# =============================================================================

module "monitoring" {
  source = "./modules/monitoring"

  project_name                   = var.project_name
  environment                    = var.environment
  aws_region                     = var.aws_region
  alert_email                    = var.alert_email
  stream_processor_function_name = module.lambda.stream_processor_function_name
  dlq_name                       = module.sqs.dlq_name
  api_name                       = "${var.project_name}-${var.environment}-api"
}
