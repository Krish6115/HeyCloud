output "dlq_arn" {
  value = aws_sqs_queue.dlq.arn
}

output "dlq_url" {
  value = aws_sqs_queue.dlq.url
}

output "dlq_name" {
  value = aws_sqs_queue.dlq.name
}

output "events_queue_arn" {
  description = "ARN of the primary SQS events queue"
  value       = aws_sqs_queue.events.arn
}

output "events_queue_url" {
  description = "URL of the primary SQS events queue"
  value       = aws_sqs_queue.events.url
}

output "events_queue_name" {
  description = "Name of the primary SQS events queue"
  value       = aws_sqs_queue.events.name
}

