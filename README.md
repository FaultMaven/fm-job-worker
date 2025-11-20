# fm-job-worker

FaultMaven Job Worker - Celery-based async task processing for background jobs.

## Overview

This service handles asynchronous background tasks for FaultMaven:

- **Knowledge Ingestion**: Process document uploads, generate embeddings
- **Case Cleanup**: Archive old cases, delete ephemeral evidence collections
- **Post-mortem Generation**: Create comprehensive case summaries

## Architecture

- **Celery**: Distributed task queue
- **Redis**: Message broker and result backend
- **Celery Beat**: Periodic task scheduler

## Tasks

### Knowledge Tasks
- `ingest_document`: Process uploaded documents and create ChromaDB embeddings
- `update_embeddings`: Rebuild embeddings for knowledge base collections

### Case Tasks
- `cleanup_old_cases`: Archive/delete cases older than 90 days (runs daily at 2 AM UTC)
- `cleanup_case_evidence`: Delete ephemeral case evidence collections (runs daily at 3 AM UTC)
- `generate_postmortem`: Create post-mortem documentation for resolved cases

## Usage

### Running Worker

```bash
# Single worker
celery -A job_worker.celery_app worker --loglevel=info

# Multiple workers
celery -A job_worker.celery_app worker --loglevel=info --concurrency=4

# With autoscale
celery -A job_worker.celery_app worker --loglevel=info --autoscale=10,3
```

### Running Beat Scheduler

```bash
celery -A job_worker.celery_app beat --loglevel=info
```

### Docker

```bash
# Worker
docker build -t faultmaven/fm-job-worker .
docker run -e REDIS_HOST=redis -e REDIS_PORT=6379 faultmaven/fm-job-worker

# Beat scheduler
docker build -f Dockerfile.beat -t faultmaven/fm-job-worker-beat .
docker run -e REDIS_HOST=redis -e REDIS_PORT=6379 faultmaven/fm-job-worker-beat
```

## Configuration

Environment variables:

- `REDIS_HOST`: Redis server hostname (default: `localhost`)
- `REDIS_PORT`: Redis server port (default: `6379`)
- `REDIS_DB`: Redis database number (default: `0`)

## Development

```bash
# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black src tests
```

## License

MIT
