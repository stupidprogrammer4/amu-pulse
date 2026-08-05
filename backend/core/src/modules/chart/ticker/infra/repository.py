from typing import Sequence

from sqlmodel import col, select

from src.infra.postgres.repository.base import PGTimestampIDRepository
from src.modules.chart.ticker.domain.enums import ChartType
from src.modules.chart.ticker.domain.models import (
    PriceTickerModel,
    SourcePriceTickerModel,
)


class PriceTickerRepository(PGTimestampIDRepository[PriceTickerModel]):
    async def get_chart(
        self, asset_id: int, type: ChartType, now: int
    ) -> Sequence[PriceTickerModel]:
        """
        Desc: Read one asset's points over a chart's window, the last of
        each step.
        Args:
            asset_id (int): ID of the asset being charted.
            type (ChartType): The chart, which sets the step and window.
            now (int): The moment the window is measured back from.
        Returns:
            return (Sequence[PriceTickerModel]): The points, oldest first.
        """
        since = now - type.span
        # the snapshots are finer than every chart but the daily one, so
        # each step keeps its last point and drops the rest. the step is
        # the stamp minus its remainder: dividing would ask postgres for a
        # numeric, and every point would land in a step of its own
        stamp = col(PriceTickerModel.timestamp)
        bucket = stamp - stamp % type.step
        stmt = (
            select(PriceTickerModel)
            .distinct(bucket)
            .where(
                col(PriceTickerModel.asset_id) == asset_id,
                col(PriceTickerModel.timestamp) >= since,
            )
            .order_by(bucket, col(PriceTickerModel.timestamp).desc())
        )
        result = await self.session.execute(stmt)
        rows = result.scalars().all()
        return rows


class SourcePriceTickerRepository(
    PGTimestampIDRepository[SourcePriceTickerModel]
):
    async def get_chart(
        self,
        source_id: int,
        symbol_id: int,
        type: ChartType,
        now: int,
    ) -> Sequence[SourcePriceTickerModel]:
        """
        Desc: Read what one source quoted one line at over a chart's
        window, the last of each step.
        Args:
            source_id (int): ID of the source that quoted it.
            symbol_id (int): ID of the line being charted.
            type (ChartType): The chart, which sets the step and window.
            now (int): The moment the window is measured back from.
        Returns:
            return (Sequence[SourcePriceTickerModel]): The points, oldest
                first.
        """
        since = now - type.span
        stamp = col(SourcePriceTickerModel.timestamp)
        bucket = stamp - stamp % type.step
        stmt = (
            select(SourcePriceTickerModel)
            .distinct(bucket)
            .where(
                col(SourcePriceTickerModel.source_id) == source_id,
                col(SourcePriceTickerModel.symbol_id) == symbol_id,
                stamp >= since,
            )
            .order_by(bucket, stamp.desc())
        )
        result = await self.session.execute(stmt)
        rows = result.scalars().all()
        return rows

    async def get_chart_by_symbol(
        self,
        symbol_id: int,
        type: ChartType,
        now: int,
    ) -> Sequence[SourcePriceTickerModel]:
        """
        Desc: Read what every source quoted one line at over a chart's
        window, the last of each step of each source.
        Args:
            symbol_id (int): ID of the line being charted.
            type (ChartType): The chart, which sets the step and window.
            now (int): The moment the window is measured back from.
        Returns:
            return (Sequence[SourcePriceTickerModel]): The points, grouped
                by source, oldest first within each.
        """
        since = now - type.span
        stamp = col(SourcePriceTickerModel.timestamp)
        bucket = stamp - stamp % type.step
        source = col(SourcePriceTickerModel.source_id)
        stmt = (
            select(SourcePriceTickerModel)
            .distinct(source, bucket)
            .where(
                col(SourcePriceTickerModel.symbol_id) == symbol_id,
                stamp >= since,
            )
            .order_by(source, bucket, stamp.desc())
        )
        result = await self.session.execute(stmt)
        rows = result.scalars().all()
        return rows
