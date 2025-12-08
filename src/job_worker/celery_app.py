"""Celery application configuration for FaultMaven job worker

This module configures Celery for async task processing with Redis backend.
Supports tasks for knowledge ingestion, case cleanup, and other background jobs.

Deployment-neutral Redis configuration:
- Standalone mode (development, self-hosted)
- Sentinel mode (enterprise K8s with HA)
"""

import os
import logging
from celery import Celery
from celery.schedules import crontab

logger = logging.getLogger(__name__)


def get_redis_url() -> str:
    """Construct Redis URL for Celery broker and backend.

    Supports both standalone and Sentinel modes for deployment neutrality.

    Environment Variables:
        REDIS_MODE: "standalone" (default) or "sentinel"

        For standalone:
            REDIS_HOST: Redis hostname (default: localhost)
            REDIS_PORT: Redis port (default: 6379)
            REDIS_DB: Database number (default: 0)
            REDIS_PASSWORD: Optional password

        For sentinel:
            REDIS_SENTINEL_HOSTS: Comma-separated "host:port,host:port"
            REDIS_MASTER_SET: Master set name (default: mymaster)
            REDIS_DB: Database number (default: 0)
            REDIS_PASSWORD: Optional password

    Returns:
        Redis connection URL for Celery

    Examples:
        Standalone: redis://localhost:6379/0
        Standalone with auth: redis://:password@localhost:6379/0
        Sentinel: sentinel://:password@host1:26379;host2:26379/mymaster
    """
    mode = os.getenv("REDIS_MODE", "standalone").lower()
    password = os.getenv("REDIS_PASSWORD", "")
    db_index = os.getenv("REDIS_DB", "0")

    # Build auth string for URL
    auth_str = f":{password}@" if password else ""

    if mode == "sentinel":
        # Sentinel URL format: sentinel://:pass@host1:port1;host2:port2/service_name
        sentinel_hosts = os.getenv("REDIS_SENTINEL_HOSTS", "localhost:26379")
        master_name = os.getenv("REDIS_MASTER_SET", "mymaster")

        # Normalize comma-separated to semicolon-separated (Celery/Kombu format)
        hosts_formatted = sentinel_hosts.replace(",", ";").replace(" ", "")

        url = f"sentinel://{auth_str}{hosts_formatted}/{master_name}"
        logger.info(
            f"Celery using Redis SENTINEL mode: "
            f"master_set={master_name}, "
            f"sentinels={hosts_formatted}"
        )
    else:
        # Standalone URL format: redis://:pass@host:port/db
        host = os.getenv("REDIS_HOST", "localhost")
        port = os.getenv("REDIS_PORT", "6379")

        url = f"redis://{auth_str}{host}:{port}/{db_index}"
        logger.info(
            f"Celery using Redis STANDALONE mode: {host}:{port}/{db_index}"
        )

    return url


# Get deployment-neutral Redis URL
REDIS_URL = get_redis_url()

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

# Broker transport options (for Redis/Sentinel)
app.conf.broker_transport_options = {
    "global_keyprefix": "celery_faultmaven_",
    "visibility_timeout": 3600,  # 1 hour task visibility timeout
    "fanout_prefix": True,
    "fanout_patterns": True,
}

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
