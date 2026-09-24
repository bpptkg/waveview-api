from datetime import datetime, timezone
from zoneinfo import ZoneInfo

# BMA list filters in this repo (see BulletinImporter) use Asia/Jakarta wall
# time with no offset. WaveView stores event.time in UTC.
BMA_ZONE = ZoneInfo("Asia/Jakarta")
BMA_TIME_FORMAT = "%Y-%m-%d %H:%M:%S"


def as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def format_bma_time(value: datetime) -> str:
    """Format an instant as naive Asia/Jakarta wall time for BMA query params."""
    return as_utc(value).astimezone(BMA_ZONE).strftime(BMA_TIME_FORMAT)


def parse_bma_time(value: str) -> datetime:
    """
    Parse a BMA timestamp into UTC.

    Offsets and a trailing ``Z`` are honored. Naive values are Asia/Jakarta,
    matching :func:`format_bma_time`.
    """
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        parsed = datetime.strptime(text, BMA_TIME_FORMAT)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=BMA_ZONE)
    return parsed.astimezone(timezone.utc)
