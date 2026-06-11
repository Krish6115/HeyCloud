# =============================================================================
# HeyCloud - Terraform Providers
# =============================================================================
# Purpose: Configure required providers and their versions.
# Why: Pinning provider versions prevents breaking changes from upstream
#      updates. This is a production best practice — never use "latest".
# =============================================================================

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# -----------------------------------------------------------------------------
# AWS Provider Configuration
# -----------------------------------------------------------------------------
# The region is parameterized via variables to support multi-environment
# deployments (dev/staging/prod) without code changes.
# Credentials are resolved via:
#   1. Environment variables (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
#   2. Shared credentials file (~/.aws/credentials)
#   3. IAM instance profile (EC2/ECS)
#   4. OIDC (GitHub Actions)
# NEVER hardcode credentials in Terraform files.
# -----------------------------------------------------------------------------

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
      Repository  = "HeyCloud"
    }
  }
}
