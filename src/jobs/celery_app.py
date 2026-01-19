"""
Celery Application Configuration
Background task processing for price updates and monitoring.
"""

from celery import Celery
from celery.schedules import crontab

from src.core.config import settings

# Create Celery app
celery_app = Celery(
    "cloudcost",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "src.jobs.price_updater",
        "src.jobs.spot_monitor",
    ],
)

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # Task execution settings
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_time_limit=3600,  # 1 hour max
    task_soft_time_limit=3300,  # 55 minutes soft limit
    
    # Worker settings
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=100,
    
    # Result settings
    result_expires=86400,  # 24 hours
    
    # Retry settings
    task_default_retry_delay=60,
    task_max_retries=3,
)

# Beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    # Update all prices daily at 2 AM UTC
    "update-all-prices-daily": {
        "task": "src.jobs.price_updater.update_all_prices",
        "schedule": crontab(hour=2, minute=0),
        "options": {"queue": "prices"},
    },
    
    # Update spot prices every 5 minutes
    "update-spot-prices": {
        "task": "src.jobs.spot_monitor.monitor_spot_prices",
        "schedule": crontab(minute="*/5"),
        "options": {"queue": "spot"},
    },
    
    # Calculate spot statistics hourly
    "calculate-spot-stats": {
        "task": "src.jobs.spot_monitor.calculate_spot_statistics",
        "schedule": crontab(minute=0),
        "options": {"queue": "analytics"},
    },
}

# Task routing
celery_app.conf.task_routes = {
    "src.jobs.price_updater.*": {"queue": "prices"},
    "src.jobs.spot_monitor.*": {"queue": "spot"},
}

# Task priority
celery_app.conf.task_default_priority = 5
celery_app.conf.task_queue_max_priority = 10

