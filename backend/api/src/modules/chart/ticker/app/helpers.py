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
        points = self.points(rows)
        prices = [point.price for point in points]
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
