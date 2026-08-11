#!/bin/bash
# =============================================================================
# HeyCloud - Destroy All Infrastructure
# =============================================================================
# WARNING: This will permanently delete all AWS resources!
# Usage: ./scripts/destroy.sh <environment>
# =============================================================================

set -euo pipefail

ENV="${1:-dev}"

echo "============================================"
echo "  ⚠ DESTROYING HeyCloud ${ENV} Infrastructure"
echo "============================================"
echo ""
echo "This will permanently delete:"
echo "  - Kinesis Data Stream"
echo "  - DynamoDB Tables (and all data)"
echo "  - S3 Buckets (and all data)"
echo "  - Lambda Functions"
echo "  - API Gateway"
echo "  - CloudWatch Alarms & Dashboards"
echo "  - SNS Topics"
echo "  - SQS Queues"
echo "  - IAM Roles"
echo ""
read -p "Are you ABSOLUTELY sure? Type 'destroy' to confirm: " CONFIRM

if [ "${CONFIRM}" != "destroy" ]; then
    echo "Aborted."
    exit 1
fi

cd infrastructure/terraform

# Empty S3 buckets before destroying (Terraform can't delete non-empty buckets)
echo "Emptying S3 buckets..."
for BUCKET in $(terraform output -json 2>/dev/null | python3 -c "
import json, sys
data = json.load(sys.stdin)
for k, v in data.items():
    if 's3' in k and 'bucket' in k:
        print(v.get('value', ''))
" 2>/dev/null); do
    if [ -n "${BUCKET}" ]; then
        echo "  → Emptying ${BUCKET}..."
        aws s3 rm "s3://${BUCKET}" --recursive 2>/dev/null || true
    fi
done

echo "Running terraform destroy..."
terraform destroy -var-file="../environments/${ENV}.tfvars" -auto-approve

echo ""
echo "============================================"
echo "  ✓ All ${ENV} infrastructure destroyed."
echo "============================================"
