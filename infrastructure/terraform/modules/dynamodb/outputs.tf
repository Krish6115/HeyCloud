output "events_table_name" {
  value = aws_dynamodb_table.events.name
}

output "events_table_arn" {
  value = aws_dynamodb_table.events.arn
}

output "aggregations_table_name" {
  value = aws_dynamodb_table.aggregations.name
}

output "aggregations_table_arn" {
  value = aws_dynamodb_table.aggregations.arn
}
