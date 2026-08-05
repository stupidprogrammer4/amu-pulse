from enum import StrEnum


class TimeFrame(StrEnum):
    FIVE_MINUTE = "5m"
    HOURLY = "1h"
    FIVE_HOURLY = "5h"
    DAILY = "1d"

    @property
    def seconds(self) -> int:
        """
        Desc: How long one candle of this timeframe lasts, in seconds.
        Returns:
            return (int): The length of the candle.
        """
        return {
            TimeFrame.FIVE_MINUTE: 5 * 60,
            TimeFrame.HOURLY: 60 * 60,
            TimeFrame.FIVE_HOURLY: 5 * 60 * 60,
            TimeFrame.DAILY: 24 * 60 * 60,
        }[self]

    @property
    def rolled_from(self) -> "TimeFrame | None":
        """
        Desc: Read the finer candle this one is built out of.
        Returns:
            return (TimeFrame | None): The finer timeframe, or None for
                the one the prices themselves are folded into.
        """
        return {
            TimeFrame.FIVE_MINUTE: None,
            TimeFrame.HOURLY: TimeFrame.FIVE_MINUTE,
            TimeFrame.FIVE_HOURLY: TimeFrame.HOURLY,
            # a day is not a whole number of five hour candles, so it is
            # rolled from the hourly one
            TimeFrame.DAILY: TimeFrame.HOURLY,
        }[self]

    def opened_at(self, timestamp: int) -> int:
        """
        Desc: Read the moment the candle a timestamp falls in opened at.
        Args:
            timestamp (int): The moment a price was read at.
        Returns:
            return (int): When that candle opened, in whole seconds.
        """
        # every candle is cut on Tehran's clock, so a day is a day here
        # and an hour lands half past the UTC one. the country keeps no
        # daylight saving, so this offset holds all year
        offset = 3 * 60 * 60 + 30 * 60
        opened = (timestamp + offset) // self.seconds
        return opened * self.seconds - offset
