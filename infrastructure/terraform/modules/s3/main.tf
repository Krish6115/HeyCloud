# =============================================================================
# Module: S3
# =============================================================================
# Purpose: Cold storage / data lake for event archival + Lambda artifacts.
# Why S3:
#   - Unlimited scalable storage at $0.023/GB
#   - Lifecycle policies auto-tier data (Standard → IA → Glacier)
#   - Foundation for Athena/Glue analytics (future)
#   - Versioning protects against accidental overwrites
#   - Server-side encryption by default
# =============================================================================

# -----------------------------------------------------------------------------
# Data Lake Bucket - Archived events
# -----------------------------------------------------------------------------
resource "aws_s3_bucket" "data_lake" {
  bucket = "${var.project_name}-${var.environment}-data-lake-${var.account_id}"

  tags = {
    Name    = "${var.project_name}-${var.environment}-data-lake"
    Service = "s3"
    Purpose = "cold-storage"
  }
}

# Enable versioning for data protection
resource "aws_s3_bucket_versioning" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id

  versioning_configuration {
    status = "Enabled"
  }
}

# Server-side encryption (AES-256)
resource "aws_s3_bucket_server_side_encryption_configuration" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = true
  }
}

# Block all public access
resource "aws_s3_bucket_public_access_block" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Lifecycle policy: Standard → IA → Glacier → Delete
resource "aws_s3_bucket_lifecycle_configuration" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id

  rule {
    id     = "archive-old-events"
    status = "Enabled"

    filter {
      prefix = "raw/"
    }

    transition {
      days          = var.lifecycle_ia_days
      storage_class = "STANDARD_IA"
    }

    transition {
      days          = var.lifecycle_glacier_days
      storage_class = "GLACIER"
    }

    expiration {
      days = var.lifecycle_expiration_days
    }
  }
}

# -----------------------------------------------------------------------------
# Lambda Artifacts Bucket - Deployment packages
# -----------------------------------------------------------------------------
resource "aws_s3_bucket" "lambda_artifacts" {
  bucket = "${var.project_name}-${var.environment}-lambda-artifacts-${var.account_id}"

  tags = {
    Name    = "${var.project_name}-${var.environment}-lambda-artifacts"
    Service = "s3"
    Purpose = "deployment"
  }
}

resource "aws_s3_bucket_versioning" "lambda_artifacts" {
  bucket = aws_s3_bucket.lambda_artifacts.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "lambda_artifacts" {
  bucket = aws_s3_bucket.lambda_artifacts.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "lambda_artifacts" {
  bucket = aws_s3_bucket.lambda_artifacts.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
