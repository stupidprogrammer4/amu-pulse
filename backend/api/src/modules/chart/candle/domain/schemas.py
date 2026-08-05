from src.common.bases.schemas import BaseOutput
from src.modules.chart.candle.domain.enums import TimeFrame


class CandleOut(BaseOutput):
    open: int
    high: int
    low: int
    close: int
    st_ts: int
    en_ts: int


class CandleChartOut(BaseOutput):
    timeframe: TimeFrame
    candles: list[CandleOut]
    from_timestamp: int
    to_timestamp: int
