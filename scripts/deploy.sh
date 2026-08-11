#!/bin/bash
# =============================================================================
# HeyCloud - Deployment Script
# =============================================================================
# End-to-end deployment: package → upload → terraform apply → update lambdas
#
# Usage: ./scripts/deploy.sh <environment> (dev|prod)
# =============================================================================

set -euo pipefail

ENV="${1:-dev}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "============================================"
echo "  HeyCloud - Deploying to ${ENV}"
echo "============================================"

# Step 1: Package Lambda functions
echo ""
echo "[Step 1/4] Packaging Lambda functions..."
BUCKET_NAME=$(cd "${PROJECT_ROOT}/infrastructure/terraform" && terraform output -raw s3_lambda_artifacts_bucket 2>/dev/null || echo "")

if [ -z "${BUCKET_NAME}" ]; then
    echo "  ⚠ Terraform output not available. Running terraform first..."
    cd "${PROJECT_ROOT}/infrastructure/terraform"
    terraform init -input=false
    terraform apply -var-file="../environments/${ENV}.tfvars" -auto-approve
    BUCKET_NAME=$(terraform output -raw s3_lambda_artifacts_bucket)
fi

bash "${SCRIPT_DIR}/package-lambdas.sh" "${BUCKET_NAME}" --upload

# Step 2: Apply infrastructure changes
echo ""
echo "[Step 2/4] Applying Terraform changes..."
cd "${PROJECT_ROOT}/infrastructure/terraform"
terraform apply -var-file="../environments/${ENV}.tfvars" -auto-approve

# Step 3: Update Lambda function code
echo ""
echo "[Step 3/4] Updating Lambda function code..."

SP_FUNCTION=$(terraform output -raw stream_processor_function_name 2>/dev/null || echo "heycloud-${ENV}-stream-processor")
AA_FUNCTION=$(terraform output -raw analytics_api_function_name 2>/dev/null || echo "heycloud-${ENV}-analytics-api")

echo "  → Updating ${SP_FUNCTION}..."
aws lambda update-function-code \
    --function-name "${SP_FUNCTION}" \
    --s3-bucket "${BUCKET_NAME}" \
    --s3-key "stream-processor/stream-processor.zip" \
    --no-cli-pager

echo "  → Updating ${AA_FUNCTION}..."
aws lambda update-function-code \
    --function-name "${AA_FUNCTION}" \
    --s3-bucket "${BUCKET_NAME}" \
    --s3-key "analytics-api/analytics-api.zip" \
    --no-cli-pager

# Step 4: Output deployment info
echo ""
echo "[Step 4/4] Deployment info..."
API_URL=$(terraform output -raw api_gateway_url 2>/dev/null || echo "N/A")

echo ""
echo "============================================"
echo "  ✓ Deployment complete!"
echo "  Environment: ${ENV}"
echo "  API URL: ${API_URL}"
echo "============================================"
