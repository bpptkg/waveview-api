from datetime import datetime


def to_timestamp(dt: datetime) -> int:
    return int(dt.timestamp())


def from_timestamp(ts: int) -> datetime:
    return datetime.fromtimestamp(ts)


def to_iso(dt: datetime) -> str:
    return dt.isoformat()


def from_iso(iso: str) -> datetime:
    return datetime.fromisoformat(iso)


def to_milliseconds(dt: datetime) -> int:
    return int(dt.timestamp() * 1_000)


def from_milliseconds(ms: int) -> datetime:
    return datetime.fromtimestamp(ms / 1_000)


def to_microseconds(dt: datetime) -> int:
    return int(dt.timestamp() * 1_000_000)


def from_microseconds(us: int) -> datetime:
    return datetime.fromtimestamp(us / 1_000_000)


def to_nanoseconds(dt: datetime) -> int:
    return int(dt.timestamp() * 1_000_000_000)


def from_nanoseconds(ns: int) -> datetime:
    return datetime.fromtimestamp(ns / 1_000_000_000)
