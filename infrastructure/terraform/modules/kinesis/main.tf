# =============================================================================
# Module: Kinesis Data Stream
# =============================================================================
# Purpose: Real-time event ingestion stream.
# Why Kinesis:
#   - Sub-second latency for real-time processing
#   - Ordered records per shard (partition key)
#   - Native Lambda event source mapping
#   - Replay capability within retention window
#   - Scales via shard splitting/merging
# =============================================================================

resource "aws_kinesis_stream" "events" {
  name             = "${var.project_name}-${var.environment}-event-stream"
  shard_count      = var.shard_count
  retention_period = var.retention_hours

  # Server-side encryption at rest using AWS managed key
  encryption_type = "KMS"
  kms_key_id      = "alias/aws/kinesis"

  # Stream mode: ON_DEMAND auto-scales shards but costs more
  # PROVISIONED gives us explicit control and predictable costs
  stream_mode_details {
    stream_mode = "PROVISIONED"
  }

  tags = {
    Name    = "${var.project_name}-${var.environment}-event-stream"
    Service = "kinesis"
  }
}
