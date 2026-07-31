# =============================================================================
# HeyCloud - Root Terraform Outputs
# =============================================================================
# Purpose: Expose key resource identifiers for other services and CI/CD.
# These values are used by the event producer, frontend, and deployment scripts.
# =============================================================================

output "api_gateway_url" {
  description = "API Gateway base URL for sending events"
  value       = module.api_gateway.api_url
}

output "api_key" {
  description = "API key for authenticating requests"
  value       = module.api_gateway.api_key_value
  sensitive   = true
}


output "dynamodb_events_table" {
  description = "DynamoDB events table name"
  value       = module.dynamodb.events_table_name
}

output "dynamodb_aggregations_table" {
  description = "DynamoDB aggregations table name"
  value       = module.dynamodb.aggregations_table_name
}

output "s3_data_lake_bucket" {
  description = "S3 data lake bucket name"
  value       = module.s3.data_lake_bucket_name
}

output "s3_lambda_artifacts_bucket" {
  description = "S3 Lambda artifacts bucket name"
  value       = module.s3.lambda_artifacts_bucket_name
}

output "sns_alerts_topic" {
  description = "SNS topic ARN for alerts"
  value       = module.monitoring.sns_topic_arn
}

output "cloudwatch_dashboard" {
  description = "CloudWatch dashboard name"
  value       = module.monitoring.dashboard_name
}

output "dlq_url" {
  description = "SQS Dead Letter Queue URL"
  value       = module.sqs.dlq_url
}

output "events_queue_url" {
  description = "SQS Events Queue URL"
  value       = module.sqs.events_queue_url
}
