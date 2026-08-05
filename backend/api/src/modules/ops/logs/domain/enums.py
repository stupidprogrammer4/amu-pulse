from enum import StrEnum


class LogLevel(StrEnum):
    # lowercase, because that is how JSONFormatter writes log.level
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
