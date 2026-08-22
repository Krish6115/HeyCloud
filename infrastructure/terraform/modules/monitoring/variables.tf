variable "project_name" { type = string }
variable "environment" { type = string }
variable "aws_region" { type = string }

variable "alert_email" {
  description = "Email for alert notifications"
  type        = string
}

variable "stream_processor_function_name" { type = string }
variable "kinesis_stream_name" { 
  type = string 
  default=""
}
variable "dlq_name" { type = string }
variable "api_name" { type = string }
