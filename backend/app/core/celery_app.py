import os
import logging
from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

logger = logging.getLogger("costwise.celery")

# Initialize Celery app
celery_app = Celery(
    "costwise_tasks",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.core.tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 min max per task
    broker_connection_retry_on_startup=True,
)

# Periodic Celery Beat Schedule
celery_app.conf.beat_schedule = {
    "daily-anomaly-and-renewal-scan": {
        "task": "app.core.tasks.daily_anomaly_and_renewal_scan",
        "schedule": crontab(hour=2, minute=0),  # Daily at 02:00 UTC
    },
    "weekly-savings-optimization-analysis": {
        "task": "app.core.tasks.weekly_savings_optimization_analysis",
        "schedule": crontab(hour=3, minute=0, day_of_week="monday"),  # Weekly Monday 03:00 UTC
    },
    "monthly-financial-report-generation": {
        "task": "app.core.tasks.monthly_financial_report_generation",
        "schedule": crontab(hour=4, minute=0, day_of_month=1),  # 1st of month 04:00 UTC
    },
}
