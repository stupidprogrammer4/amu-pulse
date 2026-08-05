from typing import Mapping, Sequence

from src.common.errors.exceptions import ValidationException
from src.modules.chart.candle.app.helpers import ChartWindow, WindowClock
from src.modules.chart.candle.config import resources
from src.modules.chart.candle.domain.dtos import ParamDTO, SourceParamDTO
from src.modules.chart.candle.domain.enums import TimeFrame
from src.modules.chart.candle.domain.models import (
    CandleModel,
    SourceCandleModel,
)
from src.modules.chart.candle.domain.results import (
    CandleResult,
    SourceCandleResult,
)
from src.modules.chart.candle.domain.schemas import (
    CandleChartOut,
    CandleOut,
)
from src.modules.chart.candle.domain.windows import (
    AssetPriceWindow,
    SourcePriceWindow,
)
from src.modules.chart.candle.infra.cache import (
    AssetWindowCache,
    SourceWindowCache,
)
from src.modules.chart.candle.infra.repository import (
    CandleRepository,
    SourceCandleRepository,
)
from src.modules.price.assets.domain.enums import AssetCode
from src.modules.price.assets.interfaces import IAssetMetaService
from src.modules.price.calculator.domain.results import AssetPriceResult
from src.modules.price.engine.domain.results import SourcePriceResult
from src.modules.price.sources.interfaces import ISourceMetaService
from src.modules.price.symbols.domain.enums import SymbolCode


class WindowService:
    def __init__(self, cache: AssetWindowCache) -> None:
        """
        Desc: Build the service with the window each price is folded into.
        Args:
            cache (AssetWindowCache): Where the open window lives.
        """
        self.cache = cache
        self.clock = WindowClock()

    def _folded(
        self,
        standing: AssetPriceWindow | None,
        priced: AssetPriceResult,
    ) -> AssetPriceWindow:
        """
        Desc: Take a price into the open window, opening one when it is the
        first price of that window.
        Args:
            standing (AssetPriceWindow | None): The window as it stands, or
                None when nothing has been folded into it yet.
            priced (AssetPriceResult): What the asset was last priced at.
        Returns:
            return (AssetPriceWindow): The window with that price in it.
        """
        window = AssetPriceWindow.opened(priced.asset_id, priced.price)
        if standing is not None:
            window = standing.folded(priced.price)
        return window

    async def update_window(
        self,
        code: AssetCode,
        cached_prices: AssetPriceResult,
    ) -> bool:
        """
        Desc: Fold what one asset is priced at into the open window.
        Args:
            code (AssetCode): The asset that was priced.
            cached_prices (AssetPriceResult): What it was priced at.
        Returns:
            return (bool): Whether the price was folded in.
        """
        opened = self.clock.opened_now()
        standing = await self.cache.get(opened, code)
        window = self._folded(standing, cached_prices)
        await self.cache.set(opened, code, window)
        return True

    async def update_windows(
        self,
        cached_prices: dict[AssetCode, AssetPriceResult],
    ) -> int:
        """
        Desc: Fold what every asset is priced at into the open window.
        Args:
            cached_prices (dict[AssetCode, AssetPriceResult]): What each
                asset was priced at.
        Returns:
            return (int): How many prices were folded in.
        """
        opened = self.clock.opened_now()
        folded: dict[AssetCode, AssetPriceWindow] = {}
        if cached_prices:
            standing = await self.cache.get_many(opened, list(cached_prices))
            folded = {
                code: self._folded(standing.get(code), price)
                for code, price in cached_prices.items()
            }
            await self.cache.set_many(opened, folded)
        return len(folded)


class SourceWindowService:
    def __init__(self, cache: SourceWindowCache) -> None:
        """
        Desc: Build the service with the window each reading is folded
        into.
        Args:
            cache (SourceWindowCache): Where the open window lives.
        """
        self.cache = cache
        self.clock = WindowClock()

    def _folded(
        self,
        standing: Sequence[SourcePriceWindow],
        quoted: Sequence[SourcePriceResult],
    ) -> list[SourcePriceWindow]:
        """
        Desc: Take a line's readings into the open window, one window per
        source that quoted it.
        Args:
            standing (Sequence[SourcePriceWindow]): The line's windows as
                they stand, empty when nothing has been folded in yet.
            quoted (Sequence[SourcePriceResult]): What each source quoted
                that line at.
        Returns:
            return (list[SourcePriceWindow]): The line's windows with those
                readings in them.
        """
        windows = {window.source_id: window for window in standing}
        for row in quoted:
            # a window opened on the reading folds it back as a no-op, so
            # the first reading of a source needs no branch of its own
            window = windows.get(
                row.source_id,
                SourcePriceWindow.opened(
                    row.source_id, row.symbol_id, row.price
                ),
            )
            windows[row.source_id] = window.folded(row.price)
        return list(windows.values())

    async def update_window(
        self,
        cached_prices: Mapping[SymbolCode, Sequence[SourcePriceResult]],
    ) -> int:
        """
        Desc: Fold what every source quoted into the open window, line by
        line.
        Args:
            cached_prices (Mapping[SymbolCode, Sequence[SourcePriceResult]]):
                What each line was quoted at, by every source quoting it.
        Returns:
            return (int): How many readings were folded in.
        """
        opened = self.clock.opened_now()
        folded = 0
        if cached_prices:
            standing = await self.cache.get_many(opened, list(cached_prices))
            windows = {
                code: self._folded(standing.get(code, ()), quoted)
                for code, quoted in cached_prices.items()
            }
            await self.cache.set_many(opened, windows)
            folded = sum(len(quoted) for quoted in cached_prices.values())
        return folded


class CandleService:
    def __init__(
        self,
        repo: CandleRepository,
        cache: AssetWindowCache,
        meta: IAssetMetaService,
    ) -> None:
        """
        Desc: Build the service with the candles it writes, the windows it
        writes them out of and what names the asset they are of.
        Args:
            repo (CandleRepository): The candle repository.
            cache (AssetWindowCache): Where the open window lives.
            meta (IAssetMetaService): What the charted asset is named by.
        """
        self.repo = repo
        self.cache = cache
        self.clock = WindowClock()
        self.window = ChartWindow()
        self.meta = meta

    async def build_from_cache(self) -> int:
        """
        Desc: Write down the window that has just closed, one candle per
        asset priced in it.
        Returns:
            return (int): How many candles were written.
        """
        closed = self.clock.last_closed()
        length = self.clock.timeframe.seconds
        windows = await self.cache.get_all(closed)
        rows = [
            CandleModel(
                asset_id=window.asset_id,
                timeframe=self.clock.timeframe,
                open=window.open,
                high=window.high,
                low=window.low,
                close=window.close,
                st_ts=closed,
                en_ts=closed + length,
            )
            for window in windows.values()
        ]
        if rows:
            await self.repo.bulk_upsert(rows)
            await self.cache.remove(closed)
        return len(rows)

    async def build_timeframe_from_rolled(self, tf: TimeFrame) -> int:
        """
        Desc: Roll one timeframe up out of the finer candles it is built
        from, over the window the last written candle falls in.
        Args:
            tf (TimeFrame): The timeframe to roll up.
        Returns:
            return (int): How many candles were written.
        """
        finer = tf.rolled_from
        built = 0
        if finer is not None:
            st_ts = tf.opened_at(self.clock.last_closed())
            en_ts = st_ts + tf.seconds
            candles = await self.repo.get_all_by_timeframe(finer, st_ts, en_ts)
            # the rows come by asset, oldest first: the first opens the
            # candle and every one after it stretches the same one
            folded: dict[int, CandleModel] = {}
            for row in candles:
                standing = folded.get(row.asset_id)
                if standing is None:
                    folded[row.asset_id] = CandleModel(
                        asset_id=row.asset_id,
                        timeframe=tf,
                        open=row.open,
                        high=row.high,
                        low=row.low,
                        close=row.close,
                        st_ts=st_ts,
                        en_ts=en_ts,
                    )
                else:
                    standing.high = max(standing.high, row.high)
                    standing.low = min(standing.low, row.low)
                    standing.close = row.close
            if folded:
                await self.repo.bulk_upsert(list(folded.values()))
                built = len(folded)
        return built

    def _check_span(self, days: float) -> None:
        """
        Desc: Turn away a chart asked for over too long a span.
        Args:
            days (float): How many days the chart covers.
        """
        if days <= 0:
            raise ValidationException(
                message="A chart ends after it begins",
                message_code=resources.CHART_SPAN_BACKWARDS,
                loc=["query", "to_datetime"],
                input=days,
            )
        if days >= self.window.max_days:
            raise ValidationException(
                message=(
                    f"A chart spans fewer than {self.window.max_days} days"
                ),
                message_code=resources.CHART_SPAN_TOO_LONG,
                loc=["query", "to_datetime"],
                input=days,
            )

    async def get_candle(
        self,
        asset_id: int,
        param: ParamDTO,
    ) -> CandleResult:
        """
        Desc: Draw one asset's candles over the span it is asked for.
        Args:
            asset_id (int): ID of the asset being charted.
            param (ParamDTO): The span the chart is asked for.
        Returns:
            return (CandleResult): The chart and the asset it is of.
        """
        days = self.window.days(param)
        self._check_span(days)
        timeframe = self.window.timeframe(days)
        from_ts = int(param.from_datetime.timestamp())
        to_ts = int(param.to_datetime.timestamp())
        rows = await self.repo.get_by_timeframe(
            asset_id, timeframe, from_ts, to_ts
        )
        chart = CandleChartOut(
            timeframe=timeframe,
            candles=CandleOut.from_objs(rows),
            from_timestamp=from_ts,
            to_timestamp=to_ts,
        )
        charted = [asset_id] if rows else []
        meta = await self.meta.build(charted)
        result = CandleResult(data=chart, meta=meta)
        return result


class SourceCandleService:
    def __init__(
        self,
        repo: SourceCandleRepository,
        cache: SourceWindowCache,
        meta: ISourceMetaService,
    ) -> None:
        """
        Desc: Build the service with the candles it writes, the windows it
        writes them out of and what names the source they are of.
        Args:
            repo (SourceCandleRepository): The source candle repository.
            cache (SourceWindowCache): Where the open window lives.
            meta (ISourceMetaService): What the charted source and line are
                named by.
        """
        self.repo = repo
        self.cache = cache
        self.clock = WindowClock()
        self.window = ChartWindow()
        self.meta = meta

    async def build_from_cache(self) -> int:
        """
        Desc: Write down the window that has just closed, one candle per
        source and line quoted in it.
        Returns:
            return (int): How many candles were written.
        """
        closed = self.clock.last_closed()
        length = self.clock.timeframe.seconds
        quoted = await self.cache.get_all(closed)
        rows = [
            SourceCandleModel(
                source_id=window.source_id,
                symbol_id=window.symbol_id,
                timeframe=self.clock.timeframe,
                open=window.open,
                high=window.high,
                low=window.low,
                close=window.close,
                st_ts=closed,
                en_ts=closed + length,
            )
            for windows in quoted.values()
            for window in windows
        ]
        if rows:
            await self.repo.bulk_upsert(rows)
            await self.cache.remove(closed)
        return len(rows)

    async def build_timeframe_from_rolled(self, tf: TimeFrame) -> int:
        """
        Desc: Roll one timeframe up out of the finer candles it is built
        from, over the window the last written candle falls in.
        Args:
            tf (TimeFrame): The timeframe to roll up.
        Returns:
            return (int): How many candles were written.
        """
        finer = tf.rolled_from
        built = 0
        if finer is not None:
            st_ts = tf.opened_at(self.clock.last_closed())
            en_ts = st_ts + tf.seconds
            candles = await self.repo.get_all_by_timeframe(finer, st_ts, en_ts)
            # the rows come by source and line, oldest first: the first
            # opens the candle and every one after it stretches the same
            folded: dict[tuple[int, int], SourceCandleModel] = {}
            for row in candles:
                key = (row.source_id, row.symbol_id)
                standing = folded.get(key)
                if standing is None:
                    folded[key] = SourceCandleModel(
                        source_id=row.source_id,
                        symbol_id=row.symbol_id,
                        timeframe=tf,
                        open=row.open,
                        high=row.high,
                        low=row.low,
                        close=row.close,
                        st_ts=st_ts,
                        en_ts=en_ts,
                    )
                else:
                    standing.high = max(standing.high, row.high)
                    standing.low = min(standing.low, row.low)
                    standing.close = row.close
            if folded:
                await self.repo.bulk_upsert(list(folded.values()))
                built = len(folded)
        return built

    def _check_span(self, days: float) -> None:
        """
        Desc: Turn away a chart asked for over too long a span.
        Args:
            days (float): How many days the chart covers.
        """
        if days <= 0:
            raise ValidationException(
                message="A chart ends after it begins",
                message_code=resources.CHART_SPAN_BACKWARDS,
                loc=["query", "to_datetime"],
                input=days,
            )
        if days >= self.window.max_days:
            raise ValidationException(
                message=(
                    f"A chart spans fewer than {self.window.max_days} days"
                ),
                message_code=resources.CHART_SPAN_TOO_LONG,
                loc=["query", "to_datetime"],
                input=days,
            )

    async def get_candle(
        self,
        source_id: int,
        param: SourceParamDTO,
    ) -> SourceCandleResult:
        """
        Desc: Draw what one source quoted one line at, candle by candle,
        over the span it is asked for.
        Args:
            source_id (int): ID of the source that quoted it.
            param (SourceParamDTO): The line and the span the chart is
                asked for.
        Returns:
            return (SourceCandleResult): The chart, and the source and line
                it is of.
        """
        days = self.window.days(param)
        self._check_span(days)
        timeframe = self.window.timeframe(days)
        from_ts = int(param.from_datetime.timestamp())
        to_ts = int(param.to_datetime.timestamp())
        rows = await self.repo.get_by_timeframe(
            source_id, param.symbol_id, timeframe, from_ts, to_ts
        )
        chart = CandleChartOut(
            timeframe=timeframe,
            candles=CandleOut.from_objs(rows),
            from_timestamp=from_ts,
            to_timestamp=to_ts,
        )
        charted = [source_id] if rows else []
        meta = await self.meta.build(charted, [param.symbol_id])
        result = SourceCandleResult(data=chart, meta=meta)
        return result
