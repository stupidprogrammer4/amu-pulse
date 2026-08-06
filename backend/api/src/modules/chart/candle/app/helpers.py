from src.common.utils import date_utils
from src.modules.chart.candle.domain.dtos import ParamDTO
from src.modules.chart.candle.domain.enums import TimeFrame


class WindowClock:
    timeframe = TimeFrame.FIVE_MINUTE

    def opened_now(self) -> int:
        stamp = int(date_utils.utc_now().timestamp())
        opened = self.timeframe.opened_at(stamp)
        return opened

    def last_closed(self) -> int:
        closed = self.opened_now() - self.timeframe.seconds
        return closed


class ChartWindow:
    max_days = 370

    def days(self, param: ParamDTO) -> float:
        span = param.to_datetime - param.from_datetime
        return span.total_seconds() / TimeFrame.DAILY.seconds

    def timeframe(self, days: float) -> TimeFrame:
        picked = TimeFrame.DAILY
        if days <= 1:
            picked = TimeFrame.FIVE_MINUTE
        elif days <= 7:
            picked = TimeFrame.HOURLY
        elif days <= 60:
            picked = TimeFrame.FIVE_HOURLY
        return picked
