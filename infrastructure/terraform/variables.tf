# =============================================================================
# HeyCloud - Terraform Variables
# =============================================================================
# Purpose: Define all configurable parameters for the platform.
# Convention: Use descriptive names, types, defaults, and validation where
#             appropriate. Variables without defaults are REQUIRED.
# =============================================================================

# -----------------------------------------------------------------------------
# Global
# -----------------------------------------------------------------------------

variable "project_name" {
  description = "Name of the project, used as prefix for all resources"
  type        = string
  default     = "heycloud"

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]*$", var.project_name))
    error_message = "Project name must be lowercase alphanumeric with hyphens."
  }
}

variable "environment" {
  description = "Deployment environment (dev, staging, prod)"
  type        = string

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod."
  }
}

variable "aws_region" {
  description = "AWS region for resource deployment"
  type        = string
  default     = "us-east-1"
}

# -----------------------------------------------------------------------------
# Kinesis
# -----------------------------------------------------------------------------

variable "kinesis_shard_count" {
  description = "Number of shards for the Kinesis stream. Each shard provides 1MB/s write, 2MB/s read"
  type        = number
  default     = 1

  validation {
    condition     = var.kinesis_shard_count >= 1 && var.kinesis_shard_count <= 10
    error_message = "Shard count must be between 1 and 10."
  }
}

variable "kinesis_retention_hours" {
  description = "Data retention period in hours (24-8760)"
  type        = number
  default     = 24
}

# -----------------------------------------------------------------------------
# DynamoDB
# -----------------------------------------------------------------------------

variable "dynamodb_billing_mode" {
  description = "DynamoDB billing mode: PAY_PER_REQUEST (on-demand) or PROVISIONED"
  type        = string
  default     = "PAY_PER_REQUEST"
}

variable "dynamodb_ttl_enabled" {
  description = "Enable TTL on the events table"
  type        = bool
  default     = true
}

# -----------------------------------------------------------------------------
# Lambda
# -----------------------------------------------------------------------------

variable "lambda_runtime" {
  description = "Python runtime version for Lambda functions"
  type        = string
  default     = "python3.12"
}

variable "stream_processor_memory" {
  description = "Memory allocation (MB) for the stream processor Lambda"
  type        = number
  default     = 256
}

variable "stream_processor_timeout" {
  description = "Timeout (seconds) for the stream processor Lambda"
  type        = number
  default     = 60
}

variable "analytics_api_memory" {
  description = "Memory allocation (MB) for the analytics API Lambda"
  type        = number
  default     = 128
}

variable "analytics_api_timeout" {
  description = "Timeout (seconds) for the analytics API Lambda"
  type        = number
  default     = 30
}

variable "lambda_batch_size" {
  description = "Max number of Kinesis records per Lambda invocation"
  type        = number
  default     = 100
}

variable "lambda_batch_window" {
  description = "Max seconds to wait before invoking Lambda (batching window)"
  type        = number
  default     = 5
}

variable "lambda_retry_attempts" {
  description = "Number of retry attempts for failed Lambda invocations"
  type        = number
  default     = 3
}

# -----------------------------------------------------------------------------
# S3
# -----------------------------------------------------------------------------

variable "s3_lifecycle_ia_days" {
  description = "Days before transitioning S3 objects to Infrequent Access"
  type        = number
  default     = 30
}

variable "s3_lifecycle_glacier_days" {
  description = "Days before transitioning S3 objects to Glacier"
  type        = number
  default     = 90
}

variable "s3_lifecycle_expiration_days" {
  description = "Days before expiring (deleting) S3 objects"
  type        = number
  default     = 365
}

# -----------------------------------------------------------------------------
# Monitoring
# -----------------------------------------------------------------------------

variable "alert_email" {
  description = "Email address for SNS alert notifications"
  type        = string
}

variable "cloudwatch_log_retention_days" {
  description = "CloudWatch log group retention in days"
  type        = number
  default     = 7
}

# -----------------------------------------------------------------------------
# API Gateway
# -----------------------------------------------------------------------------

variable "api_throttle_rate_limit" {
  description = "API Gateway throttle rate limit (requests/second)"
  type        = number
  default     = 1000
}

variable "api_throttle_burst_limit" {
  description = "API Gateway throttle burst limit"
  type        = number
  default     = 500
}
