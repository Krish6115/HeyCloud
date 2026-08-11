#!/bin/bash
# =============================================================================
# HeyCloud - Lambda Packaging Script
# =============================================================================
# Purpose: Package Lambda functions as ZIP artifacts and upload to S3.
#
# Usage:
#   ./scripts/package-lambdas.sh <s3-bucket-name> [--upload]
#
# What it does:
#   1. Installs Python dependencies into a temp directory
#   2. Copies application code alongside dependencies
#   3. Creates a ZIP file for each Lambda function
#   4. Optionally uploads to S3 for Terraform/Lambda deployment
#
# This matches the Terraform Lambda config:
#   s3_key = "stream-processor/stream-processor.zip"
#   s3_key = "analytics-api/analytics-api.zip"
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BUILD_DIR="${PROJECT_ROOT}/build"
S3_BUCKET="${1:-}"
UPLOAD="${2:-}"

echo "============================================"
echo "  HeyCloud - Lambda Packager"
echo "============================================"

# Clean previous builds
rm -rf "${BUILD_DIR}"
mkdir -p "${BUILD_DIR}"

# =========================================================================
# Package: Stream Processor
# =========================================================================
echo ""
echo "[1/2] Packaging stream-processor..."

SP_DIR="${BUILD_DIR}/stream-processor"
SP_SRC="${PROJECT_ROOT}/services/stream-processor"
SP_ZIP="${BUILD_DIR}/stream-processor.zip"

mkdir -p "${SP_DIR}"

# Install dependencies
echo "  → Installing dependencies..."
pip install -q -r "${SP_SRC}/requirements.txt" -t "${SP_DIR}" --no-cache-dir 2>/dev/null

# Copy application code
echo "  → Copying application code..."
cp "${SP_SRC}/handler.py" "${SP_DIR}/"
cp -r "${SP_SRC}/processors" "${SP_DIR}/"
cp -r "${SP_SRC}/storage" "${SP_DIR}/"
cp -r "${SP_SRC}/models" "${SP_DIR}/"
cp -r "${SP_SRC}/utils" "${SP_DIR}/"

# Create ZIP
echo "  → Creating ZIP archive..."
cd "${SP_DIR}" && zip -r -q "${SP_ZIP}" . -x "*.pyc" "__pycache__/*" "*.dist-info/*"
cd "${PROJECT_ROOT}"

SP_SIZE=$(du -h "${SP_ZIP}" | cut -f1)
echo "  ✓ stream-processor.zip created (${SP_SIZE})"

# =========================================================================
# Package: Analytics API
# =========================================================================
echo ""
echo "[2/2] Packaging analytics-api..."

AA_DIR="${BUILD_DIR}/analytics-api"
AA_SRC="${PROJECT_ROOT}/api/analytics"
AA_ZIP="${BUILD_DIR}/analytics-api.zip"

mkdir -p "${AA_DIR}"

# Install dependencies
echo "  → Installing dependencies..."
pip install -q -r "${AA_SRC}/requirements.txt" -t "${AA_DIR}" --no-cache-dir 2>/dev/null

# Copy application code
echo "  → Copying application code..."
cp "${AA_SRC}/handler.py" "${AA_DIR}/"
cp -r "${AA_SRC}/queries" "${AA_DIR}/"
cp -r "${AA_SRC}/utils" "${AA_DIR}/"

# Create ZIP
echo "  → Creating ZIP archive..."
cd "${AA_DIR}" && zip -r -q "${AA_ZIP}" . -x "*.pyc" "__pycache__/*" "*.dist-info/*"
cd "${PROJECT_ROOT}"

AA_SIZE=$(du -h "${AA_ZIP}" | cut -f1)
echo "  ✓ analytics-api.zip created (${AA_SIZE})"

# =========================================================================
# Upload to S3 (optional)
# =========================================================================
if [ "${UPLOAD}" = "--upload" ] && [ -n "${S3_BUCKET}" ]; then
    echo ""
    echo "Uploading to S3 bucket: ${S3_BUCKET}..."

    echo "  → Uploading stream-processor.zip..."
    aws s3 cp "${SP_ZIP}" "s3://${S3_BUCKET}/stream-processor/stream-processor.zip"

    echo "  → Uploading analytics-api.zip..."
    aws s3 cp "${AA_ZIP}" "s3://${S3_BUCKET}/analytics-api/analytics-api.zip"

    echo "  ✓ Upload complete!"
elif [ -n "${S3_BUCKET}" ]; then
    echo ""
    echo "To upload, run: $0 ${S3_BUCKET} --upload"
fi

echo ""
echo "============================================"
echo "  Packaging complete!"
echo "  Artifacts in: ${BUILD_DIR}/"
echo "============================================"
