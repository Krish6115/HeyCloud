# =============================================================================
# Module: IAM - Outputs
# =============================================================================

output "stream_processor_role_arn" {
  description = "ARN of the stream processor Lambda execution role"
  value       = aws_iam_role.stream_processor.arn
}

output "analytics_api_role_arn" {
  description = "ARN of the analytics API Lambda execution role"
  value       = aws_iam_role.analytics_api.arn
}

output "api_gateway_kinesis_role_arn" {
  description = "ARN of the API Gateway Kinesis integration role"
  value       = aws_iam_role.api_gateway_kinesis.arn
}
