# =============================================================================
# Module: SQS - Dead Letter Queue
# =============================================================================
# Purpose: Capture failed events that Lambda couldn't process.
# Why DLQ:
#   - Prevents data loss when processing fails
#   - Enables manual investigation and replay
#   - Decouples failure handling from main pipeline
#   - 14-day retention gives ops team time to respond
#   - CloudWatch alarm on DLQ depth alerts on failures
# =============================================================================

resource "aws_sqs_queue" "dlq" {
  name                       = "${var.project_name}-${var.environment}-dlq"
  message_retention_seconds  = 1209600  # 14 days (maximum)
  visibility_timeout_seconds = 300      # 5 minutes
  receive_wait_time_seconds  = 10       # Long polling (cost optimization)

  # Server-side encryption
  sqs_managed_sse_enabled = true

  tags = {
    Name    = "${var.project_name}-${var.environment}-dlq"
    Service = "sqs"
    Purpose = "dead-letter-queue"
  }
}

# =============================================================================
# Primary Events Queue — streaming ingestion point
# =============================================================================
# Purpose: Receives events from the producer and triggers the stream
#          processor Lambda via event source mapping.
# Why SQS over Kinesis:
#   - No subscription requirement on the AWS account
#   - Fully serverless, pay-per-message pricing
#   - Native Lambda event source mapping with batch support
#   - Built-in DLQ redrive for failed messages
#   - Simpler operational model for dev/staging environments
# =============================================================================

resource "aws_sqs_queue" "events" {
  name                       = "${var.project_name}-${var.environment}-events-queue"
  message_retention_seconds  = 345600   # 4 days
  visibility_timeout_seconds = 90       # 1.5x Lambda timeout (60s) — AWS best practice
  receive_wait_time_seconds  = 10       # Long polling (reduces empty receives & cost)
  max_message_size           = 262144   # 256 KB (max)
  delay_seconds              = 0        # No delivery delay

  # Server-side encryption
  sqs_managed_sse_enabled = true

  # Failed messages go to DLQ after 3 attempts
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dlq.arn
    maxReceiveCount     = 3
  })

  tags = {
    Name    = "${var.project_name}-${var.environment}-events-queue"
    Service = "sqs"
    Purpose = "event-ingestion"
  }
}
