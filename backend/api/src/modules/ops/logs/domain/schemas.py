from datetime import datetime

from pydantic import Field

from src.common.bases.schemas import BaseMeta, BaseOutput
from src.modules.ops.logs.domain.enums import LogBucket


class OriginFileOut(BaseOutput):
    name: str | None = None
    line: int | None = None


class OriginOut(BaseOutput):
    function: str | None = None
    file: OriginFileOut | None = None


class LogDetailOut(BaseOutput):
    level: str | None = None
    logger: str | None = None
    origin: OriginOut | None = None


class ErrorOut(BaseOutput):
    type: str | None = None
    message: str | None = None
    stack_trace: str | None = None


class NamedOut(BaseOutput):
    name: str | None = None


class LogOut(BaseOutput):
    timestamp: datetime = Field(validation_alias="@timestamp")
    message: str | None = None
    request_id: str | None = None
    stream: str | None = None
    log: LogDetailOut | None = None
    error: ErrorOut | None = None
    service: NamedOut | None = None
    container: NamedOut | None = None


class LogMeta(BaseMeta):
    levels: dict[str, int]
    loggers: dict[str, int]
    containers: dict[str, int]


class LogPointOut(BaseOutput):
    count: int
    timestamp: datetime


class LogChartOut(BaseOutput):
    bucket: LogBucket
    points: list[LogPointOut]
    min: int
    max: int
    mean: float


class LogChartMeta(BaseMeta):
    levels: list[str]
    containers: list[str]
    buckets: list[LogBucket]
