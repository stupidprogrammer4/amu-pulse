from typing import Mapping, Protocol, Sequence

from src.common.bases.results import PagedType
from src.modules.price.sources.domain.dtos import (
    SourceConfigUpdate,
    SourceCreate,
    SourceSearch,
    SourceUpdate,
)
from src.modules.price.sources.domain.enums import SourceSwitch
from src.modules.price.sources.domain.errors import SourceErrorInfo
from src.modules.price.sources.domain.models import (
    SourceConfigModel,
    SourceModel,
)
from src.modules.price.sources.domain.schemas import SourceMeta
from src.modules.price.symbols.domain.models import SymbolModel


class ISourceConfigService(Protocol):
    async def create_default(self, source_id: int) -> SourceConfigModel: ...

    async def update(
        self,
        source_id: int,
        data: SourceConfigUpdate,
    ) -> SourceConfigModel: ...

    async def get_by_source_id(self, source_id: int) -> SourceConfigModel: ...

    async def get_all(self) -> Sequence[SourceConfigModel]: ...


class ISourceService(Protocol):
    async def create(self, data: SourceCreate) -> SourceModel: ...

    async def update(self, id: int, data: SourceUpdate) -> SourceModel: ...

    async def get_by_id(self, id: int) -> SourceModel: ...

    async def get_by_ids(self, ids: list[int]) -> Sequence[SourceModel]: ...

    async def get_all(self) -> Sequence[SourceModel]: ...

    async def get_page(self, data: SourceSearch) -> PagedType[SourceModel]: ...

    async def get_all_with_config(self) -> Sequence[SourceModel]: ...

    async def get_by_switch_with_config(
        self,
        switch: SourceSwitch,
    ) -> Sequence[SourceModel]: ...

    async def mark_failed(
        self,
        id: int,
        error: SourceErrorInfo,
    ) -> SourceModel: ...

    async def clear_error(self, id: int) -> SourceModel: ...

    async def remove(self, id: int) -> SourceModel: ...


class ISourceErrorService(Protocol):
    async def apply_errors(
        self,
        errors: Mapping[int, SourceErrorInfo | None],
    ) -> Sequence[SourceModel]: ...


class ISourceMetaService(Protocol):
    async def build(
        self,
        source_ids: Sequence[int],
        symbol_ids: Sequence[int],
    ) -> SourceMeta: ...

    async def build_by_sources(
        self,
        sources: Sequence[SourceModel],
        symbol_ids: Sequence[int],
    ) -> SourceMeta: ...

    async def build_by_symbols(
        self,
        source_ids: Sequence[int],
        symbols: Sequence[SymbolModel],
    ) -> SourceMeta: ...
