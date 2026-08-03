from src.common.utils import date_utils
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
