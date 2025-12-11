# Multi-stage build for FaultMaven Job Worker
FROM python:3.11-slim AS builder

WORKDIR /app

# Copy fm-core-lib first (required dependency)
COPY fm-core-lib/ ./fm-core-lib/
RUN pip install --no-cache-dir ./fm-core-lib

# Copy all files needed for installation
COPY fm-job-worker/pyproject.toml ./
COPY fm-job-worker/src/ ./src/

# Install package and dependencies
RUN pip install --no-cache-dir -e .

# Production stage
FROM python:3.11-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY fm-job-worker/src/ ./src/

# Environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV REDIS_HOST=localhost
ENV REDIS_PORT=6379
ENV REDIS_DB=0

# Run Celery worker
CMD ["celery", "-A", "job_worker.celery_app", "worker", "--loglevel=info"]
