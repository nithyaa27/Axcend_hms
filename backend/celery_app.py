import os
from celery import Celery
from celery.schedules import crontab

CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/1")
CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")

celery_app = Celery(
    "hms_tasks",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=['tasks']
)

celery_app.conf.update(
    timezone="Asia/Kolkata",
    enable_utc=False,
    broker_connection_retry_on_startup=True,
    task_track_started=True,
    task_default_queue="email",
    result_expires=3600,
)

# Schedule for batch jobs
celery_app.conf.beat_schedule = {
    # Keep persisted appointment statuses aligned with elapsed time.
    "sync-appointment-statuses": {
        "task": "tasks.sync_appointment_statuses_task",
        "schedule": 60.0,
    },
    # Send doctor schedules everyday at 6:00 PM for the next day's appointments
    "send-doctor-schedules-daily": {
        "task": "tasks.send_doctor_schedules_task",
        "schedule": crontab(hour=18, minute=0),
    },
    # Send one reminder within the 15-minute window before an appointment.
    "send-pre-appointment-reminders": {
        "task": "tasks.send_today_reminders_task",
        "schedule": 60.0,
    }
}
