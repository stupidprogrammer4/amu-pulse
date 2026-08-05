from typing import Sequence

from sqlmodel import col, select

from src.infra.postgres.repository.base import PGTimestampIDRepository
from src.modules.chart.candle.domain.enums import TimeFrame
from src.modules.chart.candle.domain.models import (
    CandleModel,
    SourceCandleModel,
)


class CandleRepository(PGTimestampIDRepository[CandleModel]):
    async def bulk_upsert(
        self,
        candles: Sequence[CandleModel],
    ) -> Sequence[CandleModel]:
        """
        Desc: Write candles down, rewriting the ones already written.
        Args:
            candles (Sequence[CandleModel]): The candles to write.
        Returns:
            return (Sequence[CandleModel]): The written candles.
        """
        stmt = self._upsert_stmt(
            candles,
            [
                col(CandleModel.asset_id),
                col(CandleModel.timeframe),
                col(CandleModel.st_ts),
            ],
        )
        result = await self.session.execute(stmt)
        rows = result.scalars().all()
        return rows

    async def get_by_timeframe(
        self,
        asset_id: int,
        timeframe: TimeFrame,
        from_ts: int,
        to_ts: int,
    ) -> Sequence[CandleModel]:
        """
        Desc: Read one asset's candles of one timeframe over a range.
        Args:
            asset_id (int): ID of the asset being charted.
            timeframe (TimeFrame): The timeframe the candles are cut on.
            from_ts (int): The moment the range opens at, included.
            to_ts (int): The moment the range closes at, excluded.
        Returns:
            return (Sequence[CandleModel]): The candles, oldest first.
        """
        stamp = col(CandleModel.st_ts)
        stmt = (
            select(CandleModel)
            .where(
                col(CandleModel.asset_id) == asset_id,
                col(CandleModel.timeframe) == timeframe,
                stamp >= from_ts,
                stamp < to_ts,
            )
            .order_by(stamp)
        )
        result = await self.session.execute(stmt)
        rows = result.scalars().all()
        return rows

    async def get_all_by_timeframe(
        self,
        timeframe: TimeFrame,
        from_ts: int,
        to_ts: int,
    ) -> Sequence[CandleModel]:
        """
        Desc: Read every asset's candles of one timeframe over a range.
        Args:
            timeframe (TimeFrame): The timeframe the candles are cut on.
            from_ts (int): The moment the range opens at, included.
            to_ts (int): The moment the range closes at, excluded.
        Returns:
            return (Sequence[CandleModel]): The candles, grouped by asset,
                oldest first within each.
        """
        stamp = col(CandleModel.st_ts)
        asset = col(CandleModel.asset_id)
        stmt = (
            select(CandleModel)
            .where(
                col(CandleModel.timeframe) == timeframe,
                stamp >= from_ts,
                stamp < to_ts,
            )
            .order_by(asset, stamp)
        )
        result = await self.session.execute(stmt)
        rows = result.scalars().all()
        return rows


class SourceCandleRepository(PGTimestampIDRepository[SourceCandleModel]):
    async def bulk_upsert(
        self,
        candles: Sequence[SourceCandleModel],
    ) -> Sequence[SourceCandleModel]:
        """
        Desc: Write source candles down, rewriting the written ones.
        Args:
            candles (Sequence[SourceCandleModel]): The candles to write.
        Returns:
            return (Sequence[SourceCandleModel]): The written candles.
        """
        stmt = self._upsert_stmt(
            candles,
            [
                col(SourceCandleModel.symbol_id),
                col(SourceCandleModel.source_id),
                col(SourceCandleModel.timeframe),
                col(SourceCandleModel.st_ts),
            ],
        )
        result = await self.session.execute(stmt)
        rows = result.scalars().all()
        return rows

    async def get_by_timeframe(
        self,
        source_id: int,
        symbol_id: int,
        timeframe: TimeFrame,
        from_ts: int,
        to_ts: int,
    ) -> Sequence[SourceCandleModel]:
        """
        Desc: Read what one source quoted one line at, candle by candle.
        Args:
            source_id (int): ID of the source that quoted it.
            symbol_id (int): ID of the line being charted.
            timeframe (TimeFrame): The timeframe the candles are cut on.
            from_ts (int): The moment the range opens at, included.
            to_ts (int): The moment the range closes at, excluded.
        Returns:
            return (Sequence[SourceCandleModel]): The candles, oldest
                first.
        """
        stamp = col(SourceCandleModel.st_ts)
        stmt = (
            select(SourceCandleModel)
            .where(
                col(SourceCandleModel.source_id) == source_id,
                col(SourceCandleModel.symbol_id) == symbol_id,
                col(SourceCandleModel.timeframe) == timeframe,
                stamp >= from_ts,
                stamp < to_ts,
            )
            .order_by(stamp)
        )
        result = await self.session.execute(stmt)
        rows = result.scalars().all()
        return rows

    async def get_all_by_timeframe(
        self,
        timeframe: TimeFrame,
        from_ts: int,
        to_ts: int,
    ) -> Sequence[SourceCandleModel]:
        """
        Desc: Read every source's candles of one timeframe over a range.
        Args:
            timeframe (TimeFrame): The timeframe the candles are cut on.
            from_ts (int): The moment the range opens at, included.
            to_ts (int): The moment the range closes at, excluded.
        Returns:
            return (Sequence[SourceCandleModel]): The candles, grouped by
                source and line, oldest first within each.
        """
        stamp = col(SourceCandleModel.st_ts)
        source = col(SourceCandleModel.source_id)
        symbol = col(SourceCandleModel.symbol_id)
        stmt = (
            select(SourceCandleModel)
            .where(
                col(SourceCandleModel.timeframe) == timeframe,
                stamp >= from_ts,
                stamp < to_ts,
            )
            .order_by(source, symbol, stamp)
        )
        result = await self.session.execute(stmt)
        rows = result.scalars().all()
        return rows
