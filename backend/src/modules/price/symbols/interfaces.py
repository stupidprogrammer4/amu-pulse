from typing import Protocol, Sequence

from src.modules.price.symbols.domain.dtos import SymbolCreate, SymbolUpdate
from src.modules.price.symbols.domain.models import SymbolModel


class ISymbolService(Protocol):
    async def create(self, data: SymbolCreate) -> SymbolModel: ...

    async def update(self, id: int, data: SymbolUpdate) -> SymbolModel: ...

    async def get_by_id(self, id: int) -> SymbolModel: ...

    async def get_all(self) -> Sequence[SymbolModel]: ...

    async def get_by_asset_id(
        self,
        asset_id: int,
    ) -> Sequence[SymbolModel]: ...

    async def remove(self, id: int) -> SymbolModel: ...
