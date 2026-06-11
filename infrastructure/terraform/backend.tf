# =============================================================================
# HeyCloud - Terraform Backend Configuration
# =============================================================================
# Purpose: Store Terraform state remotely in S3 with DynamoDB state locking.
#
# Why Remote State:
#   - Team collaboration: Multiple engineers can work on the same infra
#   - State locking: Prevents concurrent modifications (DynamoDB)
#   - Versioning: S3 versioning enables state recovery
#   - Security: State contains sensitive data, S3 encryption protects it
#
# IMPORTANT: The S3 bucket and DynamoDB table must be created BEFORE
# running `terraform init`. Use the bootstrap script or create manually:
#
#   aws s3api create-bucket --bucket heycloud-terraform-state --region us-east-1
#   aws s3api put-bucket-versioning --bucket heycloud-terraform-state \
#       --versioning-configuration Status=Enabled
#   aws dynamodb create-table --table-name heycloud-terraform-locks \
#       --attribute-definitions AttributeName=LockID,AttributeType=S \
#       --key-schema AttributeName=LockID,KeyType=HASH \
#       --billing-mode PAY_PER_REQUEST --region us-east-1
# =============================================================================

terraform {
  backend "s3" {
    bucket         = "heycloud-terraform-state"
    key            = "heycloud/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "heycloud-terraform-locks"
    encrypt        = true
  }
}
