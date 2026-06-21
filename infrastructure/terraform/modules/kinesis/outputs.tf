output "stream_arn" {
  description = "ARN of the Kinesis data stream"
  value       = aws_kinesis_stream.events.arn
}

output "stream_name" {
  description = "Name of the Kinesis data stream"
  value       = aws_kinesis_stream.events.name
}
