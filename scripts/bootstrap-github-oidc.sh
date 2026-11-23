#!/bin/bash
# =============================================================================
# HeyCloud - GitHub Actions OIDC bootstrap (run once per AWS account)
# =============================================================================
# Creates the GitHub OIDC identity provider and an IAM role that only this
# repository's workflows can assume. Then add the printed role ARN as the
# GitHub secret AWS_ROLE_ARN (Settings -> Secrets and variables -> Actions).
#
# Usage: ./scripts/bootstrap-github-oidc.sh <github-owner>/<repo>
#   e.g. ./scripts/bootstrap-github-oidc.sh Krish6115/HeyCloud
#
# Note: AdministratorAccess keeps setup simple for a project account.
#       Scope it down for anything shared or production.
# =============================================================================

set -euo pipefail

REPO="${1:?usage: $0 <owner>/<repo>}"
ROLE_NAME="heycloud-github-actions"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
PROVIDER_ARN="arn:aws:iam::${ACCOUNT_ID}:oidc-provider/token.actions.githubusercontent.com"

echo "[1/3] OIDC provider..."
if aws iam get-open-id-connect-provider --open-id-connect-provider-arn "${PROVIDER_ARN}" >/dev/null 2>&1; then
    echo "  already exists"
else
    aws iam create-open-id-connect-provider \
        --url https://token.actions.githubusercontent.com \
        --client-id-list sts.amazonaws.com \
        --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1 >/dev/null
    echo "  created"
fi

echo "[2/3] IAM role ${ROLE_NAME}..."
TRUST=$(cat <<JSON
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"Federated": "${PROVIDER_ARN}"},
    "Action": "sts:AssumeRoleWithWebIdentity",
    "Condition": {
      "StringEquals": {"token.actions.githubusercontent.com:aud": "sts.amazonaws.com"},
      "StringLike": {"token.actions.githubusercontent.com:sub": "repo:${REPO}:*"}
    }
  }]
}
JSON
)
if aws iam get-role --role-name "${ROLE_NAME}" >/dev/null 2>&1; then
    aws iam update-assume-role-policy --role-name "${ROLE_NAME}" --policy-document "${TRUST}"
    echo "  trust policy updated"
else
    aws iam create-role --role-name "${ROLE_NAME}" --assume-role-policy-document "${TRUST}" >/dev/null
    echo "  created"
fi

echo "[3/3] Attaching permissions..."
aws iam attach-role-policy --role-name "${ROLE_NAME}" \
    --policy-arn arn:aws:iam::aws:policy/AdministratorAccess

echo ""
echo "Add this as the GitHub secret AWS_ROLE_ARN:"
echo "  arn:aws:iam::${ACCOUNT_ID}:role/${ROLE_NAME}"
