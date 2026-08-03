from dataclasses import dataclass

from src.modules.chart.ticker.domain.schemas import (
    ChartOutput,
    SourceChartOutput,
)
from src.modules.price.assets.domain.schemas import AssetMeta
from src.modules.price.sources.domain.schemas import SourceMeta


@dataclass
class PriceTickerResult:
    data: ChartOutput
    meta: AssetMeta


@dataclass
class SourcePriceResult:
    data: SourceChartOutput
    meta: SourceMeta


@dataclass
class SingleSourcePriceResult:
    data: ChartOutput
    meta: SourceMeta
