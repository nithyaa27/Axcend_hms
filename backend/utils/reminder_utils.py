from datetime import datetime

from extensions import db
from models.models import ReminderSettings


DEFAULT_DAILY_TIME = "09:00"
DEFAULT_MONTHLY_TIME = "09:00"
DEFAULT_MONTHLY_DAY = 1


def get_or_create_reminder_settings():
    settings = db.session.get(ReminderSettings, 1)
    if settings:
        return settings

    settings = ReminderSettings(
        id=1,
        daily_enabled=False,
        daily_time=DEFAULT_DAILY_TIME,
        monthly_enabled=False,
        monthly_day=DEFAULT_MONTHLY_DAY,
        monthly_time=DEFAULT_MONTHLY_TIME,
    )
    db.session.add(settings)
    db.session.commit()
    return settings


def serialize_reminder_settings(settings):
    return {
        "daily": {
            "enabled": bool(settings.daily_enabled),
            "time": settings.daily_time or DEFAULT_DAILY_TIME,
        },
        "monthly": {
            "enabled": bool(settings.monthly_enabled),
            "day": int(settings.monthly_day or DEFAULT_MONTHLY_DAY),
            "time": settings.monthly_time or DEFAULT_MONTHLY_TIME,
        },
    }


def month_period(value=None):
    current = value or datetime.now()
    return current.strftime("%Y-%m")
