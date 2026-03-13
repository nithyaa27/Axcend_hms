from datetime import datetime
from zoneinfo import ZoneInfo


APP_TIMEZONE = ZoneInfo("Asia/Kolkata")


def local_now():
    """Return app-local current time as a naive datetime for DB comparisons."""
    return datetime.now(APP_TIMEZONE).replace(tzinfo=None)
