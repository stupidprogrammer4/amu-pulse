from dataclasses import dataclass

from src.modules.chart.candle.domain.schemas import CandleChartOut
from src.modules.price.assets.domain.schemas import AssetMeta
from src.modules.price.sources.domain.schemas import SourceMeta


@dataclass
class CandleResult:
    data: CandleChartOut
    meta: AssetMeta


@dataclass
class SourceCandleResult:
    data: CandleChartOut
    meta: SourceMeta
