variable "project_name" { type = string }
variable "environment" { type = string }

variable "runtime" {
  type    = string
  default = "python3.12"
}

variable "stream_processor_role_arn" { type = string }
variable "analytics_api_role_arn" { type = string }
variable "events_queue_arn" {
  description = "ARN of the SQS events queue for event source mapping"
  type        = string
}
variable "dlq_arn" { type = string }

variable "lambda_artifacts_bucket" { type = string }
variable "dynamodb_events_table_name" { type = string }
variable "dynamodb_aggregations_table_name" { type = string }
variable "s3_data_lake_bucket_name" { type = string }

variable "stream_processor_memory" {
  type    = number
  default = 256
}

variable "stream_processor_timeout" {
  type    = number
  default = 60
}

variable "analytics_api_memory" {
  type    = number
  default = 128
}

variable "analytics_api_timeout" {
  type    = number
  default = 30
}

variable "batch_size" {
  type    = number
  default = 100
}

variable "batch_window" {
  type    = number
  default = 5
}

variable "retry_attempts" {
  type    = number
  default = 3
}

variable "log_retention_days" {
  type    = number
  default = 7
}
