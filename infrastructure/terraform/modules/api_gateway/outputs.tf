output "api_url" {
  description = "Base URL of the API Gateway stage"
  value       = aws_api_gateway_stage.main.invoke_url
}

output "api_key_value" {
  description = "API key value (sensitive)"
  value       = aws_api_gateway_api_key.main.value
  sensitive   = true
}

output "rest_api_id" {
  value = aws_api_gateway_rest_api.main.id
}
