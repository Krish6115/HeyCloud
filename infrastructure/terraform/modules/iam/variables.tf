# =============================================================================
# Module: IAM - Variables
# =============================================================================

variable "project_name" {
  type = string
}

variable "environment" {
  type = string
}

variable "aws_region" {
  type = string
}

variable "account_id" {
  description = "AWS Account ID for constructing ARNs"
  type        = string
}

variable "kinesis_stream_arn" {
  description = "ARN of the Kinesis stream for IAM policies"
  type        = string
  default     = ""
}

variable "dynamodb_events_table_arn" {
  description = "ARN of the DynamoDB events table"
  type        = string
}

variable "dynamodb_aggregations_table_arn" {
  description = "ARN of the DynamoDB aggregations table"
  type        = string
}

variable "s3_data_lake_bucket_arn" {
  description = "ARN of the S3 data lake bucket"
  type        = string
}

variable "dlq_arn" {
  description = "ARN of the SQS dead letter queue"
  type        = string
}

variable "events_queue_arn" {
  description = "ARN of the SQS events queue for Lambda polling"
  type        = string
}

