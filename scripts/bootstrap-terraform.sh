#!/bin/bash
# =============================================================================
# HeyCloud - Terraform Backend Bootstrap Script
# =============================================================================
# Purpose: Create the S3 bucket and DynamoDB table needed for Terraform
#          remote state BEFORE running `terraform init`.
#
# Usage:   chmod +x scripts/bootstrap-terraform.sh
#          ./scripts/bootstrap-terraform.sh
#
# NOTE: This only needs to be run ONCE per AWS account.
# =============================================================================

set -euo pipefail

BUCKET_NAME="heycloud-terraform-state"
TABLE_NAME="heycloud-terraform-locks"
REGION="us-east-1"

echo "============================================"
echo "  HeyCloud - Terraform Backend Bootstrap"
echo "============================================"

# Create S3 bucket for state
echo "[1/4] Creating S3 bucket: ${BUCKET_NAME}..."
if aws s3api head-bucket --bucket "${BUCKET_NAME}" 2>/dev/null; then
    echo "  → Bucket already exists, skipping."
else
    aws s3api create-bucket \
        --bucket "${BUCKET_NAME}" \
        --region "${REGION}"
    echo "  → Bucket created."
fi

# Enable versioning
echo "[2/4] Enabling versioning..."
aws s3api put-bucket-versioning \
    --bucket "${BUCKET_NAME}" \
    --versioning-configuration Status=Enabled
echo "  → Versioning enabled."

# Enable encryption
echo "[3/4] Enabling server-side encryption..."
aws s3api put-bucket-encryption \
    --bucket "${BUCKET_NAME}" \
    --server-side-encryption-configuration '{
        "Rules": [
            {
                "ApplyServerSideEncryptionByDefault": {
                    "SSEAlgorithm": "AES256"
                },
                "BucketKeyEnabled": true
            }
        ]
    }'
echo "  → Encryption enabled."

# Create DynamoDB table for state locking
echo "[4/4] Creating DynamoDB table: ${TABLE_NAME}..."
if aws dynamodb describe-table --table-name "${TABLE_NAME}" --region "${REGION}" 2>/dev/null; then
    echo "  → Table already exists, skipping."
else
    aws dynamodb create-table \
        --table-name "${TABLE_NAME}" \
        --attribute-definitions AttributeName=LockID,AttributeType=S \
        --key-schema AttributeName=LockID,KeyType=HASH \
        --billing-mode PAY_PER_REQUEST \
        --region "${REGION}"
    echo "  → Table created."
fi

echo ""
echo "============================================"
echo "  Bootstrap complete!"
echo "  You can now run: make init"
echo "============================================"
