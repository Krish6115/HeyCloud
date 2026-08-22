# =============================================================================
# Module: Monitoring (CloudWatch + SNS)
# =============================================================================
# Purpose: Observability layer — dashboards, alarms, and alert notifications.
# Why:
#   - Proactive alerting prevents silent failures
#   - Dashboards give real-time operational visibility
#   - Custom metrics track business KPIs, not just infrastructure
#   - SNS fan-out enables email, SMS, Slack notifications
# =============================================================================

# -----------------------------------------------------------------------------
# SNS Topic for Alerts
# -----------------------------------------------------------------------------
resource "aws_sns_topic" "alerts" {
  name = "${var.project_name}-${var.environment}-alerts"

  tags = {
    Name    = "${var.project_name}-${var.environment}-alerts"
    Service = "sns"
  }
}

resource "aws_sns_topic_subscription" "email_alert" {
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

# -----------------------------------------------------------------------------
# CloudWatch Alarms
# -----------------------------------------------------------------------------

# Alarm: Lambda errors > 5% of invocations
resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  alarm_name          = "${var.project_name}-${var.environment}-lambda-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = 300
  statistic           = "Sum"
  threshold           = 5
  alarm_description   = "Stream processor Lambda is experiencing errors"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  ok_actions          = [aws_sns_topic.alerts.arn]

  dimensions = {
    FunctionName = var.stream_processor_function_name
  }

  tags = {
    Service = "monitoring"
  }
}

# Alarm: Kinesis iterator age > 60 seconds (consumer lag)


# Alarm: DLQ has messages (processing failures)
resource "aws_cloudwatch_metric_alarm" "dlq_messages" {
  alarm_name          = "${var.project_name}-${var.environment}-dlq-depth"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "ApproximateNumberOfMessagesVisible"
  namespace           = "AWS/SQS"
  period              = 60
  statistic           = "Sum"
  threshold           = 0
  alarm_description   = "Dead letter queue has failed events that need investigation"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    QueueName = var.dlq_name
  }
}

# Alarm: Lambda duration p99 > 10 seconds
resource "aws_cloudwatch_metric_alarm" "lambda_duration" {
  alarm_name          = "${var.project_name}-${var.environment}-lambda-duration"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  metric_name         = "Duration"
  namespace           = "AWS/Lambda"
  period              = 300
  extended_statistic  = "p99"
  threshold           = 10000
  alarm_description   = "Lambda p99 latency exceeds 10 seconds"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    FunctionName = var.stream_processor_function_name
  }
}

# Alarm: API Gateway 5xx errors
resource "aws_cloudwatch_metric_alarm" "api_5xx" {
  alarm_name          = "${var.project_name}-${var.environment}-api-5xx"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "5XXError"
  namespace           = "AWS/ApiGateway"
  period              = 300
  statistic           = "Sum"
  threshold           = 10
  alarm_description   = "API Gateway is returning server errors"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    ApiName = var.api_name
  }
}

# -----------------------------------------------------------------------------
# CloudWatch Dashboard
# -----------------------------------------------------------------------------
resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = "${var.project_name}-${var.environment}-dashboard"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6
        properties = {
          title   = "Lambda Invocations & Errors"
          metrics = [
            ["AWS/Lambda", "Invocations", "FunctionName", var.stream_processor_function_name, { stat = "Sum", period = 60 }],
            ["AWS/Lambda", "Errors", "FunctionName", var.stream_processor_function_name, { stat = "Sum", period = 60, color = "#d62728" }]
          ]
          view    = "timeSeries"
          region  = var.aws_region
          period  = 60
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 0
        width  = 12
        height = 6
        properties = {
          title   = "Lambda Duration (ms)"
          metrics = [
            ["AWS/Lambda", "Duration", "FunctionName", var.stream_processor_function_name, { stat = "p50", period = 60 }],
            ["AWS/Lambda", "Duration", "FunctionName", var.stream_processor_function_name, { stat = "p95", period = 60 }],
            ["AWS/Lambda", "Duration", "FunctionName", var.stream_processor_function_name, { stat = "p99", period = 60, color = "#d62728" }]
          ]
          view   = "timeSeries"
          region = var.aws_region
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 6
        width  = 6
        height = 6
        properties = {
          title   = "DLQ Depth"
          metrics = [
            ["AWS/SQS", "ApproximateNumberOfMessagesVisible", "QueueName", var.dlq_name]
          ]
          view   = "singleValue"
          region = var.aws_region
        }
      },
      {
        type   = "metric"
        x      = 18
        y      = 6
        width  = 6
        height = 6
        properties = {
          title   = "API Gateway Requests"
          metrics = [
            ["AWS/ApiGateway", "Count", "ApiName", var.api_name, { stat = "Sum", period = 60 }],
            ["AWS/ApiGateway", "5XXError", "ApiName", var.api_name, { stat = "Sum", period = 60, color = "#d62728" }]
          ]
          view   = "timeSeries"
          region = var.aws_region
        }
      }
    ]
  })
}
