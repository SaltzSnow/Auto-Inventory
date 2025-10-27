"""Celery application configuration."""
from celery import Celery
import os

# Get Redis URL from environment
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

# Create Celery instance
celery_app = Celery(
    "ai_inventory",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["tasks.receipt_tasks"]
)

# Configure Celery
celery_app.conf.update(
    task_time_limit=600,  # 10 minutes hard limit
    task_soft_time_limit=540,  # 9 minutes soft limit
    task_acks_late=True,  # Acknowledge task after completion
    task_reject_on_worker_lost=True,  # Reject task if worker dies
    task_track_started=True,  # Track when task starts
    result_expires=3600,  # Results expire after 1 hour
    worker_prefetch_multiplier=1,  # Process one task at a time
    worker_max_tasks_per_child=50,  # Restart worker after 50 tasks
)

if __name__ == "__main__":
    celery_app.start()
