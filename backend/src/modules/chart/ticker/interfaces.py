from typing import Protocol, Sequence

from src.modules.chart.ticker.domain.enums import ChartType
from src.modules.chart.ticker.domain.models import (
    PriceTickerModel,
    SourcePriceTickerModel,
)
from src.modules.chart.ticker.domain.results import (
    PriceTickerResult,
    SingleSourcePriceResult,
    SourcePriceResult,
)
from src.modules.chart.ticker.domain.schemas import (
    ChartMeta,
    SourceChartMeta,
)
from src.modules.price.sources.domain.models import SourceModel


class IPriceTickerService(Protocol):
    async def get_chart(
        self, asset_id: int, type: ChartType
    ) -> PriceTickerResult: ...


class ISourcePriceTickerService(Protocol):
    async def get_chart_by_symbol(
        self, symbol_id: int, type: ChartType
    ) -> SourcePriceResult: ...

    async def get_source_chart_by_symbol(
        self, source_id: int, symbol_id: int, type: ChartType
    ) -> SingleSourcePriceResult: ...


class IPriceSnapshotService(Protocol):
    async def snapshot_all(self) -> bool: ...


class ISourcePriceSnapshotService(Protocol):
    async def snapshot_all(self) -> bool: ...


class IMetaService(Protocol):
    async def build_source(
        self,
        points: Sequence[SourcePriceTickerModel],
        sources: Sequence[SourceModel],
    ) -> SourceChartMeta: ...

    async def build_asset(
        self, points: Sequence[PriceTickerModel]
    ) -> ChartMeta: ...
