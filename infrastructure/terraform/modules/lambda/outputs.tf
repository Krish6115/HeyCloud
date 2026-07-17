output "stream_processor_arn" {
  value = aws_lambda_function.stream_processor.arn
}

output "stream_processor_function_name" {
  value = aws_lambda_function.stream_processor.function_name
}

output "stream_processor_invoke_arn" {
  value = aws_lambda_function.stream_processor.invoke_arn
}

output "analytics_api_arn" {
  value = aws_lambda_function.analytics_api.arn
}

output "analytics_api_function_name" {
  value = aws_lambda_function.analytics_api.function_name
}

output "analytics_api_invoke_arn" {
  value = aws_lambda_function.analytics_api.invoke_arn
}
