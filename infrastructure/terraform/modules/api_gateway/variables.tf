variable "project_name" { type = string }
variable "environment" { type = string }
variable "aws_region" { type = string }

variable "kinesis_stream_name" { 
  type = string 
  default=""
}
variable "api_gateway_kinesis_role_arn" { 
  type = string 
  default=""
}
variable "analytics_api_invoke_arn" { type = string }
variable "analytics_api_function_name" { type = string }

variable "throttle_rate_limit" {
  type    = number
  default = 1000
}

variable "throttle_burst_limit" {
  type    = number
  default = 500
}
