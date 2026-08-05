from src.common.utils import date_utils
from src.modules.chart.candle.domain.dtos import ParamDTO
from src.modules.chart.candle.domain.enums import TimeFrame


class WindowClock:
    # prices are folded into the finest candle; the coarser ones are
    # rolled up out of it
    timeframe = TimeFrame.FIVE_MINUTE

    def opened_now(self) -> int:
        """
        Desc: Read when the window prices are folded into opened at.
        Returns:
            return (int): The moment it opened, in whole seconds.
        """
        stamp = int(date_utils.utc_now().timestamp())
        opened = self.timeframe.opened_at(stamp)
        return opened

    def last_closed(self) -> int:
        """
        Desc: Read when the window that has just closed opened at.
        Returns:
            return (int): The moment it opened, in whole seconds.
        """
        closed = self.opened_now() - self.timeframe.seconds
        return closed


class ChartWindow:
    # a chart is drawn over a span shorter than a year
    max_days = 370

    def days(self, param: ParamDTO) -> float:
        """
        Desc: Read how many days a chart's span covers.
        Args:
            param (ParamDTO): The span the chart is asked for.
        Returns:
            return (float): The days between the two moments.
        """
        span = param.to_datetime - param.from_datetime
        return span.total_seconds() / TimeFrame.DAILY.seconds

    def timeframe(self, days: float) -> TimeFrame:
        """
        Desc: Read how fine the candles of a span that long are cut.
        Args:
            days (float): How many days the chart covers.
        Returns:
            return (TimeFrame): The timeframe the chart is drawn on.
        """
        picked = TimeFrame.DAILY
        if days <= 1:
            picked = TimeFrame.FIVE_MINUTE
        elif days <= 7:
            picked = TimeFrame.HOURLY
        elif days <= 60:
            picked = TimeFrame.FIVE_HOURLY
        return picked
