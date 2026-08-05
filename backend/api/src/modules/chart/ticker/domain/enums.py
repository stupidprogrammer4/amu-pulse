from enum import StrEnum


class ChartType(StrEnum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    SIX_MONTHLY = "six_monthly"
    YEARLY = "yearly"

    @property
    def step(self) -> int:
        """
        Desc: How far apart two points of this chart sit, in seconds.
        Returns:
            return (int): The distance between points.
        """
        return {
            ChartType.DAILY: 5 * 60,
            ChartType.WEEKLY: 30 * 60,
            ChartType.MONTHLY: 2 * 60 * 60,
            ChartType.SIX_MONTHLY: 12 * 60 * 60,
            ChartType.YEARLY: 24 * 60 * 60,
        }[self]

    @property
    def span(self) -> int:
        """
        Desc: How far back this chart reaches, in seconds.
        Returns:
            return (int): The window the points are read from.
        """
        day = 24 * 60 * 60
        return {
            ChartType.DAILY: day,
            ChartType.WEEKLY: 7 * day,
            ChartType.MONTHLY: 30 * day,
            ChartType.SIX_MONTHLY: 180 * day,
            ChartType.YEARLY: 365 * day,
        }[self]
