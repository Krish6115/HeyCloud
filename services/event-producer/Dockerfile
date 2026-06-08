# =============================================================================
# HeyCloud Event Producer - Dockerfile
# =============================================================================
# Multi-stage build for minimal image size.
# Stage 1: Install dependencies
# Stage 2: Copy only what's needed
# =============================================================================

FROM python:3.12-slim AS builder

WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --target=/build/deps -r requirements.txt

# =============================================================================
# Production image
# =============================================================================
FROM python:3.12-slim

# Security: run as non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# Copy installed dependencies from builder stage
COPY --from=builder /build/deps /usr/local/lib/python3.12/site-packages/

# Copy application code
COPY . .

# Switch to non-root user
USER appuser

# Health check: verify Python can import the app
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "from config import config; print('healthy')" || exit 1

# Ensure Python output is not buffered (important for Docker logs)
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

ENTRYPOINT ["python", "main.py"]
