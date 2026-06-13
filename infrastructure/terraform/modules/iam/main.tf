# =============================================================================
# Module: IAM
# Purpose: Create least-privilege IAM roles and policies for all services.
# =============================================================================
# Why separate IAM module:
#   - Centralizes security policy management
#   - Each service gets its own role (principle of least privilege)
#   - Easy to audit and review permissions in one place
# =============================================================================

# -----------------------------------------------------------------------------
# Lambda Execution Role - Stream Processor
# -----------------------------------------------------------------------------
resource "aws_iam_role" "stream_processor" {
  name = "${var.project_name}-${var.environment}-stream-processor-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# CloudWatch Logs - allows Lambda to write logs
resource "aws_iam_role_policy" "stream_processor_logs" {
  name = "${var.project_name}-${var.environment}-stream-processor-logs"
  role = aws_iam_role.stream_processor.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:${var.aws_region}:${var.account_id}:*"
      }
    ]
  })
}

# Kinesis - read from stream

# DynamoDB - write events and aggregations
resource "aws_iam_role_policy" "stream_processor_dynamodb" {
  name = "${var.project_name}-${var.environment}-stream-processor-dynamodb"
  role = aws_iam_role.stream_processor.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:BatchWriteItem"
        ]
        Resource = [
          var.dynamodb_events_table_arn,
          var.dynamodb_aggregations_table_arn
        ]
      }
    ]
  })
}

# S3 - write to data lake
resource "aws_iam_role_policy" "stream_processor_s3" {
  name = "${var.project_name}-${var.environment}-stream-processor-s3"
  role = aws_iam_role.stream_processor.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:PutObjectAcl"
        ]
        Resource = "${var.s3_data_lake_bucket_arn}/*"
      }
    ]
  })
}

# SQS - send to dead letter queue
resource "aws_iam_role_policy" "stream_processor_sqs" {
  name = "${var.project_name}-${var.environment}-stream-processor-sqs"
  role = aws_iam_role.stream_processor.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "sqs:SendMessage"
        ]
        Resource = var.dlq_arn
      }
    ]
  })
}

# SQS - poll from events queue (required for Lambda event source mapping)
resource "aws_iam_role_policy" "stream_processor_sqs_events" {
  name = "${var.project_name}-${var.environment}-stream-processor-sqs-events"
  role = aws_iam_role.stream_processor.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes"
        ]
        Resource = var.events_queue_arn
      }
    ]
  })
}

# CloudWatch Metrics - publish custom metrics
resource "aws_iam_role_policy" "stream_processor_metrics" {
  name = "${var.project_name}-${var.environment}-stream-processor-metrics"
  role = aws_iam_role.stream_processor.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "cloudwatch:PutMetricData"
        ]
        Resource = "*"
        Condition = {
          StringEquals = {
            "cloudwatch:namespace" = "${var.project_name}/${var.environment}"
          }
        }
      }
    ]
  })
}

# -----------------------------------------------------------------------------
# Lambda Execution Role - Analytics API
# -----------------------------------------------------------------------------
resource "aws_iam_role" "analytics_api" {
  name = "${var.project_name}-${var.environment}-analytics-api-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "analytics_api_logs" {
  name = "${var.project_name}-${var.environment}-analytics-api-logs"
  role = aws_iam_role.analytics_api.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:${var.aws_region}:${var.account_id}:*"
      }
    ]
  })
}

# DynamoDB - read-only for analytics queries
resource "aws_iam_role_policy" "analytics_api_dynamodb" {
  name = "${var.project_name}-${var.environment}-analytics-api-dynamodb"
  role = aws_iam_role.analytics_api.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:Query",
          "dynamodb:Scan",
          "dynamodb:BatchGetItem"
        ]
        Resource = [
          var.dynamodb_events_table_arn,
          "${var.dynamodb_events_table_arn}/index/*",
          var.dynamodb_aggregations_table_arn,
          "${var.dynamodb_aggregations_table_arn}/index/*"
        ]
      }
    ]
  })
}

# -----------------------------------------------------------------------------
# API Gateway Role - Kinesis Integration
# -----------------------------------------------------------------------------
resource "aws_iam_role" "api_gateway_kinesis" {
  name = "${var.project_name}-${var.environment}-apigw-kinesis-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "apigateway.amazonaws.com"
        }
      }
    ]
  })
}


