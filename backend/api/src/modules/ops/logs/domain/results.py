from collections.abc import Sequence
from dataclasses import dataclass, field

from src.modules.ops.logs.domain.documents import LogDocument
from src.modules.ops.logs.domain.schemas import LogMeta, LogOut


@dataclass(frozen=True, slots=True)
class LogPageType:

    items: Sequence[LogDocument]
    total_items: int
    levels: dict[str, int] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class LogSearchResult:

    data: list[LogOut]
    meta: LogMeta
