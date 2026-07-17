# =============================================================================
# Module: Lambda
# =============================================================================
# Purpose: Serverless compute for stream processing and analytics API.
# Why Lambda:
#   - Zero server management
#   - Pay only for execution time (100ms granularity)
#   - Native Kinesis event source mapping
#   - Auto-scales with stream traffic
#   - Built-in retry + DLQ on failure
# =============================================================================

# -----------------------------------------------------------------------------
# Stream Processor Lambda
# -----------------------------------------------------------------------------
resource "aws_lambda_function" "stream_processor" {
  function_name = "${var.project_name}-${var.environment}-stream-processor"
  role          = var.stream_processor_role_arn
  handler       = "handler.lambda_handler"
  runtime       = var.runtime
  timeout       = var.stream_processor_timeout
  memory_size   = var.stream_processor_memory

  # Use S3 for deployment package (production practice)
  s3_bucket = var.lambda_artifacts_bucket
  s3_key    = "stream-processor/stream-processor.zip"

  environment {
    variables = {
      ENVIRONMENT          = var.environment
      EVENTS_TABLE_NAME    = var.dynamodb_events_table_name
      AGGREGATIONS_TABLE_NAME = var.dynamodb_aggregations_table_name
      DATA_LAKE_BUCKET     = var.s3_data_lake_bucket_name
      LOG_LEVEL            = var.environment == "prod" ? "WARNING" : "DEBUG"
      METRICS_NAMESPACE    = "${var.project_name}/${var.environment}"
      POWERTOOLS_SERVICE_NAME = "stream-processor"
    }
  }

  # Reserved concurrency prevents runaway scaling (cost protection)


  tags = {
    Name    = "${var.project_name}-${var.environment}-stream-processor"
    Service = "lambda"
  }

  # Ignore changes to S3 key so CI/CD can update independently
  lifecycle {
    ignore_changes = [s3_key, s3_object_version]
  }
}

# CloudWatch Log Group with retention policy
resource "aws_cloudwatch_log_group" "stream_processor" {
  name              = "/aws/lambda/${aws_lambda_function.stream_processor.function_name}"
  retention_in_days = var.log_retention_days

  tags = {
    Service = "lambda"
  }
}

# SQS → Lambda Event Source Mapping
# Replaces the original Kinesis trigger. SQS is used because the AWS account
# lacks a Kinesis subscription. SQS provides equivalent event-driven behavior
# with native Lambda integration, automatic batch polling, and DLQ support.
resource "aws_lambda_event_source_mapping" "sqs_trigger" {
  event_source_arn = var.events_queue_arn
  function_name    = aws_lambda_function.stream_processor.arn
  enabled          = true

  batch_size                         = var.batch_size
  maximum_batching_window_in_seconds = var.batch_window
}

# -----------------------------------------------------------------------------
# Analytics API Lambda
# -----------------------------------------------------------------------------
resource "aws_lambda_function" "analytics_api" {
  function_name = "${var.project_name}-${var.environment}-analytics-api"
  role          = var.analytics_api_role_arn
  handler       = "handler.lambda_handler"
  runtime       = var.runtime
  timeout       = var.analytics_api_timeout
  memory_size   = var.analytics_api_memory

  s3_bucket = var.lambda_artifacts_bucket
  s3_key    = "analytics-api/analytics-api.zip"

  environment {
    variables = {
      ENVIRONMENT             = var.environment
      EVENTS_TABLE_NAME       = var.dynamodb_events_table_name
      AGGREGATIONS_TABLE_NAME = var.dynamodb_aggregations_table_name
      LOG_LEVEL               = var.environment == "prod" ? "WARNING" : "DEBUG"
      POWERTOOLS_SERVICE_NAME = "analytics-api"
    }
  }



  tags = {
    Name    = "${var.project_name}-${var.environment}-analytics-api"
    Service = "lambda"
  }

  lifecycle {
    ignore_changes = [s3_key, s3_object_version]
  }
}

resource "aws_cloudwatch_log_group" "analytics_api" {
  name              = "/aws/lambda/${aws_lambda_function.analytics_api.function_name}"
  retention_in_days = var.log_retention_days

  tags = {
    Service = "lambda"
  }
}
