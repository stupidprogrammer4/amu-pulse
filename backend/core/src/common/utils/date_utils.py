from __future__ import annotations

from datetime import UTC, datetime, tzinfo
from zoneinfo import ZoneInfo

import jdatetime

DEFAULT_JALALI_FORMAT = "%Y/%m/%d %H:%M:%S"


def _zone(tz: str | tzinfo) -> tzinfo:
    return tz if isinstance(tz, tzinfo) else ZoneInfo(tz)


def utc_now() -> datetime:
    return datetime.now(UTC)


def ensure_aware(dt: datetime, tz: str | tzinfo = UTC) -> datetime:
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=_zone(tz))


def convert_tz(
    dt: datetime, tz: str | tzinfo, *, assume: str | tzinfo = UTC
) -> datetime:
    return ensure_aware(dt, assume).astimezone(_zone(tz))


def to_utc(dt: datetime, *, assume: str | tzinfo = UTC) -> datetime:
    return ensure_aware(dt, assume).astimezone(UTC)


def from_db(dt: datetime, tz: str | tzinfo) -> datetime:
    return ensure_aware(dt, UTC).astimezone(_zone(tz))


def to_db(dt: datetime, *, assume: str | tzinfo) -> datetime:
    return to_utc(dt, assume=assume)


def to_jalali(
    dt: datetime, tz: str | tzinfo | None = None
) -> jdatetime.datetime:
    aware = ensure_aware(dt, UTC)
    if tz is not None:
        aware = aware.astimezone(_zone(tz))
    return jdatetime.datetime.fromgregorian(datetime=aware)


def from_jalali(jdt: jdatetime.datetime, *, as_utc: bool = True) -> datetime:
    greg = jdt.togregorian()
    if as_utc and greg.tzinfo is not None:
        greg = greg.astimezone(UTC)
    return greg


def format_jalali(
    dt: datetime,
    fmt: str = DEFAULT_JALALI_FORMAT,
    tz: str | tzinfo | None = None,
) -> str:
    return to_jalali(dt, tz).strftime(fmt)


def parse_jalali(
    value: str,
    fmt: str = DEFAULT_JALALI_FORMAT,
    *,
    tz: str | tzinfo | None = None,
    as_utc: bool = True,
) -> datetime:
    parsed = jdatetime.datetime.strptime(value, fmt).togregorian()
    if tz is not None:
        parsed = parsed.replace(tzinfo=_zone(tz))
        if as_utc:
            parsed = parsed.astimezone(UTC)
    return parsed
