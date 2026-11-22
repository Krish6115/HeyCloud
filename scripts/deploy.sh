#!/bin/bash
# =============================================================================
# HeyCloud - Deployment Script
# =============================================================================
# Fresh-account safe order:
#   1. terraform apply -target=module.s3   (artifacts bucket must exist first)
#   2. package + upload Lambda zips        (Lambda creation needs the zips)
#   3. full terraform apply
#   4. push latest code to the Lambdas, write dashboard/config.js
#
# Prereqs: aws configure, terraform >= 1.5, python 3.12, and the remote state
# bucket/lock table from scripts/bootstrap-terraform.sh.
#
# Usage: ./scripts/deploy.sh [dev|prod]
# =============================================================================

set -euo pipefail

ENV="${1:-dev}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TF_DIR="${PROJECT_ROOT}/infrastructure/terraform"
VARS="-var-file=../environments/${ENV}.tfvars"
PY="${PYTHON:-python}"

echo "=== HeyCloud - Deploying to ${ENV} ==="

cd "${TF_DIR}"
terraform init -input=false

echo "[1/4] Creating storage (artifacts bucket)..."
terraform apply ${VARS} -target=module.s3 -auto-approve
BUCKET_NAME=$(terraform output -raw s3_lambda_artifacts_bucket)

echo "[2/4] Packaging + uploading Lambdas to ${BUCKET_NAME}..."
"${PY}" "${SCRIPT_DIR}/package-lambdas.py" --upload "${BUCKET_NAME}"

echo "[3/4] Applying full infrastructure..."
terraform apply ${VARS} -auto-approve

echo "[4/4] Updating Lambda code..."
for FN in stream_processor analytics_api; do
    NAME=$(terraform output -raw "${FN}_function_name")
    KEY=$(echo "${FN}" | tr '_' '-')
    aws lambda update-function-code --function-name "${NAME}" \
        --s3-bucket "${BUCKET_NAME}" --s3-key "${KEY}/${KEY}.zip" --no-cli-pager >/dev/null
    echo "  updated ${NAME}"
done

API_URL=$(terraform output -raw api_gateway_url)
echo "window.HEYCLOUD_API_URL = '${API_URL%/}/analytics';" > "${PROJECT_ROOT}/dashboard/config.js"

echo ""
echo "=== Deployment complete ==="
echo "  API URL:  ${API_URL}"
echo "  Producer: set API_GATEWAY_URL=${API_URL%/} in .env, then: docker compose up --build"
echo "  Dashboard config written to dashboard/config.js"
