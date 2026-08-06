from datetime import timedelta
from enum import StrEnum


class LogBucket(StrEnum):
    FIVE_MINUTE = "5m"
    HOURLY = "1h"
    FIVE_HOURLY = "5h"
    DAILY = "1d"

    @property
    def span(self) -> timedelta:
        return {
            LogBucket.FIVE_MINUTE: timedelta(days=1),
            LogBucket.HOURLY: timedelta(days=7),
            LogBucket.FIVE_HOURLY: timedelta(days=30),
            LogBucket.DAILY: timedelta(days=180),
        }[self]


class LogLevel(StrEnum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
