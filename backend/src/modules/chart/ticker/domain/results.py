from dataclasses import dataclass

from src.modules.chart.ticker.domain.schemas import (
    ChartMeta,
    ChartOutput,
    SourceChartMeta,
    SourceChartOutput,
)


@dataclass
class PriceTickerResult:
    data: ChartOutput
    meta: ChartMeta


@dataclass
class SourcePriceResult:
    data: SourceChartOutput
    meta: SourceChartMeta


@dataclass
class SingleSourcePriceResult:
    data: ChartOutput
    meta: SourceChartMeta
