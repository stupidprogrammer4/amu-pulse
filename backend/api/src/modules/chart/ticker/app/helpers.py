from typing import Protocol, Sequence

from src.modules.chart.ticker.domain.enums import ChartType
from src.modules.chart.ticker.domain.schemas import ChartOutput, PointOutput


class PricedPoint(Protocol):
    price: int
    timestamp: int


class ChartBuilder:
    def points(
        self,
        rows: Sequence[PricedPoint],
    ) -> list[PointOutput]:
        """
        Desc: Turn the rows a chart is drawn from into its points.
        Args:
            rows (Sequence[PricedPoint]): The rows, oldest first.
        Returns:
            return (list[PointOutput]): The points, oldest first.
        """
        return [
            PointOutput(price=row.price, timestamp=row.timestamp)
            for row in rows
        ]

    def build(
        self,
        type: ChartType,
        rows: Sequence[PricedPoint],
        now: int,
    ) -> ChartOutput:
        """
        Desc: Draw one series, and say how far it moved over its window.
        Args:
            type (ChartType): The chart being drawn.
            rows (Sequence[PricedPoint]): The rows, oldest first.
            now (int): The moment the window is measured back from.
        Returns:
            return (ChartOutput): The points, their extremes and the move
                from the first of them to the last.
        """
        points = self.points(rows)
        prices = [point.price for point in points]
        # what the chart is worth reading for: where it started against
        # where it ended up, as a share of where it started
        opening = prices[0] if prices else 0
        closing = prices[-1] if prices else 0
        divisor = opening or 1
        return ChartOutput(
            type=type,
            points=points,
            from_timestamp=now - type.span,
            to_timestamp=now,
            max=max(prices, default=0),
            min=min(prices, default=0),
            mean=round(sum(prices) / len(prices)) if prices else 0,
            change_rate=(closing - opening) / divisor,
        )
