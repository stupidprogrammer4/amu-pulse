from __future__ import annotations

from dataclasses import dataclass, field
from typing import Generic, Sequence, TypeVar

T = TypeVar("T")
E = TypeVar("E")


@dataclass(frozen=True, slots=True)
class BatchResultType(Generic[T, E]):
    items: Sequence[T]
    errors: Sequence[E]
    item_ids: set[int] = field(default_factory=set)


@dataclass(frozen=True, slots=True)
class PagedType(Generic[T]):
    items: Sequence[T]
    total_items: int
