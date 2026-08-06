from dataclasses import dataclass, field
from datetime import datetime
from typing import Sequence

from src.modules.ops.logs.domain.documents import LogDocument


@dataclass(frozen=True, slots=True)
class LogPageType:

    items: Sequence[LogDocument]
    total_items: int
    levels: dict[str, int] = field(default_factory=dict)
    loggers: dict[str, int] = field(default_factory=dict)
    containers: dict[str, int] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class PointType:
    count: int
    timestamp: datetime

@dataclass(frozen=True, slots=True)
class LogChartType:
    points: Sequence[PointType]
    min: int
    max: int
    mean: float
    levels: Sequence[str]
    containers: Sequence[str] = ()
