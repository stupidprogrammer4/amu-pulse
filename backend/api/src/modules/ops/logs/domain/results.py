from dataclasses import dataclass

from src.modules.ops.logs.domain.schemas import (
    LogChartMeta,
    LogChartOut,
    LogMeta,
    LogOut,
)


@dataclass(frozen=True, slots=True)
class LogSearchResult:

    data: list[LogOut]
    meta: LogMeta


@dataclass(frozen=True, slots=True)
class LogChartResult:

    data: LogChartOut
    meta: LogChartMeta
