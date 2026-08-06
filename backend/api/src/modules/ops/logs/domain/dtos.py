from datetime import datetime

from src.common.bases.dtos import BaseDTO
from src.common.types import PageType, PerPageType, ValueType
from src.modules.ops.logs.domain.enums import LogLevel


class LogSearch(BaseDTO):
    q: ValueType | None = None
    levels: list[LogLevel] | None = None
    loggers: list[str] | None = None
    containers: list[str] | None = None
    request_id: str | None = None
    from_time: datetime | None = None
    to_time: datetime | None = None
    page: PageType = 1
    per_page: PerPageType = 20


class LogChartSearch(BaseDTO):
    container: str
    level: LogLevel | None = None
