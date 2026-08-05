from collections.abc import Sequence
from dataclasses import dataclass, field

from src.modules.ops.logs.domain.documents import LogDocument
from src.modules.ops.logs.domain.schemas import LogMeta, LogOut


@dataclass(frozen=True, slots=True)
class LogPageType:
    """What the repository read: the documents themselves."""

    items: Sequence[LogDocument]
    total_items: int
    # level -> count over everything the filter matched, not just this page
    levels: dict[str, int] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class LogSearchResult:
    """What the service returns: the page already shaped for the wire."""

    data: list[LogOut]
    meta: LogMeta
