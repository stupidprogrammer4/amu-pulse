from collections import defaultdict

from src.common.utils import date_utils
from src.modules.chart.ticker.app.helpers import ChartBuilder
from src.modules.chart.ticker.domain.enums import ChartType
from src.modules.chart.ticker.domain.models import (
    PriceTickerModel,
    SourcePriceTickerModel,
)
from src.modules.chart.ticker.domain.results import (
    PriceTickerResult,
    SingleSourcePriceResult,
    SourcePriceResult,
)
from src.modules.chart.ticker.domain.schemas import (
    PointOutput,
    SourceChartOutput,
)
from src.modules.chart.ticker.infra.repository import (
    PriceTickerRepository,
    SourcePriceTickerRepository,
)
from src.modules.price.assets.interfaces import IAssetMetaService
from src.modules.price.calculator.interfaces import (
    ICacheReaderService as IPriceCacheReaderService,
)
from src.modules.price.engine.interfaces import (
    ICacheReaderService as IReadingCacheReaderService,
)
from src.modules.price.sources.domain.enums import SourceCode
from src.modules.price.sources.interfaces import (
    ISourceMetaService,
    ISourceService,
)


class PriceSnapshotService:
    def __init__(
        self,
        repo: PriceTickerRepository,
        prices: IPriceCacheReaderService,
    ) -> None:
        self.repo = repo
        self.prices = prices

    async def snapshot_all(self) -> bool:
        """
        Desc: Write down what every asset is priced at right now.
        Returns:
            return (bool): Whether anything was written.
        """
        priced = await self.prices.get_all_prices()
        rows = [
            PriceTickerModel(
                asset_id=price.asset_id,
                price=price.price,
                timestamp=int(price.priced_at.timestamp()),
            )
            for price in priced
        ]
        if rows:
            await self.repo.bulk_create(rows)
        return bool(rows)


class SourcePriceSnapshotService:
    def __init__(
        self,
        repo: SourcePriceTickerRepository,
        readings: IReadingCacheReaderService,
    ) -> None:
        self.repo = repo
        self.readings = readings

    async def snapshot_all(self) -> bool:
        """
        Desc: Write down what every source last quoted, under the line it
        was quoted for.
        Returns:
            return (bool): Whether anything was written.
        """
        board = await self.readings.get_all()
        rows = [
            SourcePriceTickerModel(
                symbol_id=reading.symbol_id,
                source_id=reading.source_id,
                price=reading.price,
                timestamp=int(reading.priced_at.timestamp()),
            )
            for readings in board.values()
            for reading in readings
        ]
        if rows:
            await self.repo.bulk_create(rows)
        return bool(rows)


class PriceTickerService:
    def __init__(
        self,
        repo: PriceTickerRepository,
        meta: IAssetMetaService,
    ) -> None:
        self.repo = repo
        self.meta = meta
        self.builder = ChartBuilder()

    async def get_chart(
        self,
        asset_id: int,
        type: ChartType,
    ) -> PriceTickerResult:
        """
        Desc: Draw one asset's chart, and say how far it moved over it.
        Args:
            asset_id (int): ID of the asset being charted.
            type (ChartType): The chart to draw.
        Returns:
            return (PriceTickerResult): The chart and the asset it is of.
        """
        now = int(date_utils.utc_now().timestamp())
        rows = await self.repo.get_chart(asset_id, type, now)
        data = self.builder.build(type, rows, now)
        meta = await self.meta.build(list({row.asset_id for row in rows}))
        return PriceTickerResult(data=data, meta=meta)


class SourcePriceTickerService:
    def __init__(
        self,
        repo: SourcePriceTickerRepository,
        sources: ISourceService,
        meta: ISourceMetaService,
    ) -> None:
        self.repo = repo
        self.sources = sources
        self.meta = meta
        self.builder = ChartBuilder()

    async def get_chart_by_symbol(
        self,
        symbol_id: int,
        type: ChartType,
    ) -> SourcePriceResult:
        """
        Desc: Draw one line as every source that quotes it saw it.
        Args:
            symbol_id (int): ID of the line being charted.
            type (ChartType): The chart to draw.
        Returns:
            return (SourcePriceResult): One series per source, and the
                sources and line they are of.
        """
        now = int(date_utils.utc_now().timestamp())
        rows = await self.repo.get_chart_by_symbol(symbol_id, type, now)
        quoting = {row.source_id for row in rows}
        sources = await self.sources.get_by_ids(list(quoting))
        codes = {source.id: SourceCode(source.code) for source in sources}
        quoted: dict[SourceCode, list[PointOutput]] = defaultdict(list)
        for row in rows:
            code = codes.get(row.source_id)
            if code is not None:
                quoted[code].append(
                    PointOutput(price=row.price, timestamp=row.timestamp)
                )
        data = SourceChartOutput(
            type=type,
            points=[],
            from_timestamp=now - type.span,
            to_timestamp=now,
            source_points=quoted,
        )
        meta = await self.meta.build_by_sources(
            sources, list({row.symbol_id for row in rows})
        )
        return SourcePriceResult(data=data, meta=meta)

    async def get_source_chart_by_symbol(
        self,
        source_id: int,
        symbol_id: int,
        type: ChartType,
    ) -> SingleSourcePriceResult:
        """
        Desc: Draw one line as one source saw it, and say how far it moved.
        Args:
            source_id (int): ID of the source that quoted it.
            symbol_id (int): ID of the line being charted.
            type (ChartType): The chart to draw.
        Returns:
            return (SingleSourcePriceResult): The chart, and the source
                and line it is of.
        """
        now = int(date_utils.utc_now().timestamp())
        rows = await self.repo.get_chart(source_id, symbol_id, type, now)
        charted = [source_id] if rows else []
        data = self.builder.build(type, rows, now)
        meta = await self.meta.build(
            charted, list({row.symbol_id for row in rows})
        )
        return SingleSourcePriceResult(data=data, meta=meta)
