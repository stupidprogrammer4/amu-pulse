from typing import Protocol

from src.modules.price.sources.domain.dtos import SourceCreate, SourceUpdate
from src.modules.price.sources.domain.models import SourceModel


class ISourceService(Protocol):
    async def create(self, data: SourceCreate) -> SourceModel: ...

    async def update(self, id: int, data: SourceUpdate) -> SourceModel: ...

    async def get_by_id(self, id: int) -> SourceModel: ...

    async def remove(self, id: int) -> SourceModel: ...
