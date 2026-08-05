from datetime import datetime

from src.common.bases.dtos import BaseDTO
from src.common.types import PageType, PerPageType, ValueType
from src.modules.ops.logs.domain.enums import LogLevel


class LogSearch(BaseDTO):
    # free text over the message
    q: ValueType | None = None
    # lists, so the front end can offer each of these as checkboxes
    levels: list[LogLevel] | None = None
    # the loggers that wrote the line: "app", "uvicorn.access", "taskiq.*"
    loggers: list[str] | None = None
    # which containers wrote it: amu-pulse-api-1, -worker-1, -scheduler-1
    containers: list[str] | None = None
    # one HTTP request or one task execution, end to end
    request_id: str | None = None
    from_time: datetime | None = None
    to_time: datetime | None = None
    page: PageType = 1
    per_page: PerPageType = 20
