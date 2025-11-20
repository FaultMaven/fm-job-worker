"""Celery application configuration for FaultMaven job worker

This module configures Celery for async task processing with Redis backend.
Supports tasks for knowledge ingestion, case cleanup, and other background jobs.
"""

import os
from celery import Celery
from celery.schedules import crontab

# Redis configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")
REDIS_DB = os.getenv("REDIS_DB", "0")
REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"

# Create Celery app
app = Celery(
    "faultmaven",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=[
        "job_worker.tasks.knowledge_tasks",
        "job_worker.tasks.case_tasks",
    ],
)

# Celery configuration
app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour hard limit
    task_soft_time_limit=3300,  # 55 minutes soft limit
    worker_prefetch_multiplier=1,  # Fetch one task at a time
    worker_max_tasks_per_child=100,  # Restart worker after 100 tasks
)

# Periodic task schedule
app.conf.beat_schedule = {
    "cleanup-old-cases": {
        "task": "job_worker.tasks.case_tasks.cleanup_old_cases",
        "schedule": crontab(hour=2, minute=0),  # Daily at 2 AM UTC
    },
    "cleanup-case-evidence": {
        "task": "job_worker.tasks.case_tasks.cleanup_case_evidence",
        "schedule": crontab(hour=3, minute=0),  # Daily at 3 AM UTC
    },
}

if __name__ == "__main__":
    app.start()
