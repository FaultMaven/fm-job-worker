# FaultMaven Job Worker - PUBLIC Open Source Version
# Apache 2.0 License

# Stage 1: Builder
FROM python:3.11-slim AS builder

WORKDIR /app

# Install poetry
RUN pip install --no-cache-dir poetry==1.7.0

# Copy fm-core-lib first (required dependency)
COPY fm-core-lib/ ./fm-core-lib/

# Copy dependency files
COPY pyproject.toml poetry.lock* ./

# Export dependencies to requirements.txt (no dev dependencies)
# Fallback to manual list if poetry export fails due to path dependencies
RUN poetry export -f requirements.txt --output requirements.txt --without-hashes --without dev || \
    echo "celery[redis]>=5.3.0\nredis>=5.0.0\ntenacity>=8.3.0\npython-dotenv>=1.0.0" > requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim

WORKDIR /app

# Install fm-core-lib FIRST (needed by requirements.txt if poetry export didn't fallback)
COPY --from=builder /app/fm-core-lib/ ./fm-core-lib/
RUN pip install --no-cache-dir ./fm-core-lib

# Copy requirements and install
COPY --from=builder /app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/

# Set PYTHONPATH to include src directory
ENV PYTHONPATH=/app/src:$PYTHONPATH
ENV PYTHONUNBUFFERED=1

# Redis connection defaults (override via environment)
ENV REDIS_HOST=localhost
ENV REDIS_PORT=6379
ENV REDIS_DB=0

# Run Celery worker
CMD ["celery", "-A", "job_worker.celery_app", "worker", "--loglevel=info"]
