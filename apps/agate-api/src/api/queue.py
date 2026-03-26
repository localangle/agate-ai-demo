"""Celery client for enqueueing tasks."""

import os
from celery import Celery

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Number of queues for round-robin distribution
# Should match typical worker count (2-10 workers, using 4 queues for good distribution)
NUM_QUEUES = int(os.getenv("CELERY_NUM_QUEUES", "4"))

# Create Celery client (doesn't run tasks, just enqueues them)
celery_app = Celery(
    "agate",
    broker=REDIS_URL,
    backend=REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)


def get_queue_for_item(item_id: int) -> str:
    """
    Route task to queue based on item ID hash for round-robin distribution.
    
    This ensures tasks are distributed evenly across queues, which helps
    balance load across workers even when task durations vary.
    
    Args:
        item_id: ProcessedItem ID
        
    Returns:
        Queue name (e.g., "queue-0", "queue-1", etc.)
    """
    queue_index = item_id % NUM_QUEUES
    queue_name = f"queue-{queue_index}"
    # Log queue distribution for diagnostics
    import logging
    logger = logging.getLogger(__name__)
    logger.debug(f"[Queue Routing] Item {item_id} -> queue-{queue_index} (using {NUM_QUEUES} queues)")
    return queue_name

