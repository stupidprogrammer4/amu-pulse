from collections import defaultdict
from typing import Sequence

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
    AssetMetaOutput,
    ChartMeta,
    PointOutput,
    SourceChartMeta,
    SourceChartOutput,
    SourceMetaOutput,
    SymbolMetaOutput,
)
from src.modules.chart.ticker.infra.repository import (
    PriceTickerRepository,
    SourcePriceTickerRepository,
)
from src.modules.chart.ticker.interfaces import IMetaService
from src.modules.price.assets.interfaces import IAssetService
from src.modules.price.calculator.interfaces import (
    ICacheReaderService as IPriceCacheReaderService,
)
from src.modules.price.engine.interfaces import (
    ICacheReaderService as IReadingCacheReaderService,
)
from src.modules.price.sources.domain.enums import SourceCode
from src.modules.price.sources.domain.models import SourceModel
from src.modules.price.sources.interfaces import ISourceService
from src.modules.price.symbols.interfaces import ISymbolService


class PriceSnapshotService:
    def __init__(
        self,
        repo: PriceTickerRepository,
        prices: IPriceCacheReaderService,
    ) -> None:
        """
        Desc: Build the service with what it snapshots and where it lands.
        Args:
            repo (PriceTickerRepository): The price ticker repository.
            prices (IPriceCacheReaderService): Where each asset's price
                lives.
        """
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
        """
        Desc: Build the service with what it snapshots and where it lands.
        Args:
            repo (SourcePriceTickerRepository): The source ticker
                repository.
            readings (IReadingCacheReaderService): Where each source's
                reading lives.
        """
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


class MetaService:
    def __init__(
        self,
        assets: IAssetService,
        symbols: ISymbolService,
    ) -> None:
        """
        Desc: Build the service with what it names the charted lines by.
        Args:
            assets (IAssetService): Where an asset's name and colour live.
            symbols (ISymbolService): Where a line's name and colour live.
        """
        self.assets = assets
        self.symbols = symbols

    async def build_asset(
        self,
        points: Sequence[PriceTickerModel],
    ) -> ChartMeta:
        """
        Desc: Name the assets a set of points was drawn from.
        Args:
            points (Sequence[PriceTickerModel]): The points being charted.
        Returns:
            return (ChartMeta): One entry per asset the points belong to.
        """
        charted = {point.asset_id for point in points}
        assets = await self.assets.get_by_ids(list(charted))
        return ChartMeta(
            assets=[
                AssetMetaOutput(
                    id=asset.id,
                    code=asset.code,
                    title=asset.title,
                    primary_color=asset.primary_color,
                )
                for asset in assets
            ]
        )

    async def build_source(
        self,
        points: Sequence[SourcePriceTickerModel],
        sources: Sequence[SourceModel],
    ) -> SourceChartMeta:
        """
        Desc: Name the sources and lines a set of points was drawn from.
        Args:
            points (Sequence[SourcePriceTickerModel]): The points being
                charted.
            sources (Sequence[SourceModel]): The sources already read.
            symbols.
        Returns:
            return (SourceChartMeta): One entry per source and per line
                the points belong to.
        """
        lines = {point.symbol_id for point in points}
        symbols = await self.symbols.get_by_ids(list(lines))
        return SourceChartMeta(
            sources=[
                SourceMetaOutput(
                    id=source.id,
                    code=source.code,
                    title=source.title,
                    primary_color=source.primary_color,
                )
                for source in sources
            ],
            symbols=[
                SymbolMetaOutput(
                    id=symbol.id,
                    code=symbol.code,
                    title=symbol.title,
                    primary_color=symbol.primary_color,
                )
                for symbol in symbols
            ],
        )


class PriceTickerService:
    def __init__(
        self,
        repo: PriceTickerRepository,
        meta: IMetaService,
    ) -> None:
        """
        Desc: Build the service with the points it draws and what names
        them.
        Args:
            repo (PriceTickerRepository): The price ticker repository.
            meta (IMetaService): What the charted asset is named by.
        """
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
        meta = await self.meta.build_asset(rows)
        return PriceTickerResult(data=data, meta=meta)


class SourcePriceTickerService:
    def __init__(
        self,
        repo: SourcePriceTickerRepository,
        sources: ISourceService,
        meta: IMetaService,
    ) -> None:
        """
        Desc: Build the service with the points it draws and what names
        them.
        Args:
            repo (SourcePriceTickerRepository): The source ticker
                repository.
            sources (ISourceService): Which code each source carries.
            meta (IMetaService): What the charted source and line are
                named by.
        """
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
            # a point of a source that has since been dropped
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
        meta = await self.meta.build_source(rows, sources)
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
        quoting = [source_id] if rows else []
        sources = await self.sources.get_by_ids(quoting)
        data = self.builder.build(type, rows, now)
        meta = await self.meta.build_source(rows, sources)
        return SingleSourcePriceResult(data=data, meta=meta)
