#!/bin/bash
# Thin wrapper kept for compatibility: ./scripts/package-lambdas.sh <bucket> [--upload]
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
if [ "${2:-}" = "--upload" ]; then
    python "${SCRIPT_DIR}/package-lambdas.py" --upload "$1"
else
    python "${SCRIPT_DIR}/package-lambdas.py"
fi
