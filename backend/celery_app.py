import os
import importlib.util
from pathlib import Path

from celery import Celery

from app import app

BACKEND_DIR = Path(__file__).resolve().parent


def _load_run_scheduled_reminders():
    module_path = BACKEND_DIR / "reminder_tasks.py"
    spec = importlib.util.spec_from_file_location("backend_reminder_tasks", module_path)
    if spec is None or spec.loader is None:
        raise ModuleNotFoundError(f"Unable to load reminder tasks from {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.run_scheduled_reminders


def _make_celery(flask_app):
    celery = Celery(
        flask_app.import_name,
        broker=os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0"),
        backend=os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/1"),
    )
    celery.conf.update(
        timezone=os.getenv("CELERY_TIMEZONE", "Asia/Kolkata"),
        beat_schedule={
            "run-reminder-dispatch-every-minute": {
                "task": "reminders.dispatch",
                "schedule": 1,
            }
        },
    )

    class FlaskContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with flask_app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = FlaskContextTask
    return celery


celery_app = _make_celery(app)


@celery_app.task(name="reminders.dispatch")
def dispatch_reminders():
    run_scheduled_reminders = _load_run_scheduled_reminders()
    return run_scheduled_reminders()
