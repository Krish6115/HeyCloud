# =============================================================================
# Module: DynamoDB
# =============================================================================
# Purpose: Hot storage for recent events and pre-computed aggregations.
# Why DynamoDB:
#   - Single-digit millisecond latency at any scale
#   - Fully managed, serverless (on-demand mode)
#   - TTL auto-deletes expired records (no cron jobs)
#   - GSIs enable flexible query patterns
#   - Point-in-time recovery protects against accidental deletes
# =============================================================================

# -----------------------------------------------------------------------------
# Events Table - Stores individual streaming events
# -----------------------------------------------------------------------------
resource "aws_dynamodb_table" "events" {
  name         = "${var.project_name}-${var.environment}-events"
  billing_mode = var.billing_mode
  hash_key     = "PK"
  range_key    = "SK"

  # Composite key: PK = event_type#YYYY-MM-DD, SK = timestamp#event_id
  attribute {
    name = "PK"
    type = "S"
  }

  attribute {
    name = "SK"
    type = "S"
  }

  # GSI for user activity queries
  attribute {
    name = "user_id"
    type = "S"
  }

  # GSI for product analytics
  attribute {
    name = "product_id"
    type = "S"
  }

  # Global Secondary Index: Query by user
  global_secondary_index {
    name            = "UserIndex"
    hash_key        = "user_id"
    range_key       = "SK"
    projection_type = "ALL"
  }

  # Global Secondary Index: Query by product
  global_secondary_index {
    name            = "ProductIndex"
    hash_key        = "product_id"
    range_key       = "SK"
    projection_type = "ALL"
  }

  # TTL - automatically delete records after expiry
  ttl {
    attribute_name = "ttl"
    enabled        = var.ttl_enabled
  }

  # Point-in-time recovery - protects against accidental data loss
  point_in_time_recovery {
    enabled = var.environment == "prod" ? true : false
  }

  tags = {
    Name    = "${var.project_name}-${var.environment}-events"
    Service = "dynamodb"
  }
}

# -----------------------------------------------------------------------------
# Aggregations Table - Stores pre-computed metrics
# -----------------------------------------------------------------------------
resource "aws_dynamodb_table" "aggregations" {
  name         = "${var.project_name}-${var.environment}-aggregations"
  billing_mode = var.billing_mode
  hash_key     = "PK"
  range_key    = "SK"

  # PK = metric_name#YYYY-MM-DD, SK = time_window (e.g., minute#14:30)
  attribute {
    name = "PK"
    type = "S"
  }

  attribute {
    name = "SK"
    type = "S"
  }

  ttl {
    attribute_name = "ttl"
    enabled        = var.ttl_enabled
  }

  tags = {
    Name    = "${var.project_name}-${var.environment}-aggregations"
    Service = "dynamodb"
  }
}
