import os
from celery import Celery

# ==========================================================
# Celery Configuration
# ==========================================================
# Configures the Celery worker and beat for asynchronous tasks
# (e.g., sending emails, scheduled status updates).
# Defaults to Redis on localhost if environment variables are missing.

CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://redis:6379/0")
CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", "redis://redis:6379/0")

celery_app = Celery(
    "hms_celery",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",
    enable_utc=True,
)

# Import tasks to ensure they are registered with the celery instance
import tasks
