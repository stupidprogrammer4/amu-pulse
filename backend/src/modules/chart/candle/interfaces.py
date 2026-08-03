from typing import Mapping, Protocol, Sequence

from src.modules.chart.candle.domain.dtos import ParamDTO, SourceParamDTO
from src.modules.chart.candle.domain.enums import TimeFrame
from src.modules.price.assets.domain.enums import AssetCode
from src.modules.price.calculator.domain.results import AssetPriceResult
from src.modules.price.engine.domain.results import SourcePriceResult
from src.modules.price.symbols.domain.enums import SymbolCode


class IWindowService(Protocol):
    async def update_window(
        self, code: AssetCode, cached_prices: AssetPriceResult
    ) -> bool: ...

    async def update_windows(
        self, cached_prices: dict[AssetCode, AssetPriceResult]
    ) -> int: ...


class ISourceWindowService(Protocol):
    async def update_window(
        self, cached_prices: Mapping[SymbolCode, Sequence[SourcePriceResult]]
    ) -> int: ...


class ISourceCandleService(Protocol):
    async def build_timeframe_from_rolled(self, tf: TimeFrame) -> int: ...

    async def build_from_cache(self) -> int: ...

    async def get_candle(self, source_id: int, param: SourceParamDTO): ...


class ICandleService(Protocol):
    async def build_timeframe_from_rolled(self, tf: TimeFrame) -> int: ...

    async def build_from_cache(self) -> int: ...

    async def get_candle(self, param: ParamDTO): ...
