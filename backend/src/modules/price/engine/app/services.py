import asyncio
from collections import defaultdict
from typing import Awaitable, Sequence

from dishka import AsyncContainer

from src.common.utils import date_utils
from src.modules.chart.candle.interfaces import ISourceWindowService
from src.modules.price.assets.domain.enums import AssetCode
from src.modules.price.engine.app.helpers import (
    GlobalMarketPriceHelper,
    IranMarketPriceHelper,
    SupplierMarketPriceHelper,
)
from src.modules.price.engine.domain.context import CFGContext
from src.modules.price.engine.domain.quotes import (
    BubbleQuote,
    ErrorQuote,
    GlobalSourceQuote,
    IranSourceQuote,
    SourceQuote,
    SupplierSourceQuote,
)
from src.modules.price.engine.domain.results import (
    SourceBubbleResult,
    SourcePriceResult,
)
from src.modules.price.engine.infra.cache import (
    BubbleSourceCache,
    SourcePriceCache,
)
from src.modules.price.engine.infra.gateways.bubble import BUBBLE_FETCHERS
from src.modules.price.engine.infra.gateways.global_market import (
    GLOBAL_FETCHERS,
)
from src.modules.price.engine.infra.gateways.iran_market import IRAN_FETCHERS
from src.modules.price.engine.infra.gateways.supplier import SUPPLIER_FETCHERS
from src.modules.price.engine.infra.readers import (
    AssetReader,
    SourceReader,
    SymbolReader,
)
from src.modules.price.engine.interfaces import (
    ICacheFlusherService,
    ICFGReaderService,
    ICrawlerService,
    IPersistFlusherService,
)
from src.modules.price.sources.domain.errors import SourceErrorInfo
from src.modules.price.sources.interfaces import ISourceErrorService
from src.modules.price.symbols.domain.enums import SymbolCode


class CFGReaderService:
    def __init__(
        self,
        assets: AssetReader,
        symbols: SymbolReader,
        sources: SourceReader,
    ) -> None:
        """
        Desc: Build the service with the readers it reads through.
        Args:
            assets (AssetReader): Reader over the assets module's tables.
            symbols (SymbolReader): Reader over the symbols module's tables.
            sources (SourceReader): Reader over the sources module's tables.
        """
        self.assets = assets
        self.symbols = symbols
        self.sources = sources

    async def read_context(self) -> CFGContext:
        """
        Desc: Read what a crawl needs: every source, and the ids a quoted
        code maps to.
        Returns:
            return (CFGContext): The sources to call, and the symbols and
                assets to attribute their quotes to.
        """
        sources = await self.sources.read_all()
        symbols = await self.symbols.read_refs()
        assets = await self.assets.read_refs()
        context = CFGContext(sources=sources, symbols=symbols, assets=assets)
        return context


class CrawlerService:
    async def crawl(
        self,
        cfg: CFGContext,
    ) -> tuple[SourceQuote, SourceQuote]:
        """
        Desc: Call every source that has a fetcher, all at once, and split
        what answered from what failed.
        Args:
            cfg (CFGContext): The sources to call, with their configs.
        Returns:
            return (tuple[SourceQuote, SourceQuote]): The answered quotes,
                then the failed ones.
        """
        suppliers: list[Awaitable[Sequence[SupplierSourceQuote]]] = []
        irans: list[Awaitable[Sequence[IranSourceQuote]]] = []
        globals_: list[Awaitable[Sequence[GlobalSourceQuote]]] = []
        bubbles: list[Awaitable[Sequence[BubbleQuote]]] = []
        for source in cfg.sources:
            headers = source.cfg.headers_credentials
            timeout = source.cfg.timeout
            supplier_cls = SUPPLIER_FETCHERS.get(source.code)
            if supplier_cls is not None:
                suppliers.append(supplier_cls(headers, timeout).fetch())
            iran_cls = IRAN_FETCHERS.get(source.code)
            if iran_cls is not None:
                irans.append(iran_cls(headers, timeout).fetch())
            global_cls = GLOBAL_FETCHERS.get(source.code)
            if global_cls is not None:
                globals_.append(global_cls(headers, timeout).fetch())
            bubble_cls = BUBBLE_FETCHERS.get(source.code)
            if bubble_cls is not None:
                bubbles.append(bubble_cls(headers, timeout).fetch())

        (
            supplier_rows,
            iran_rows,
            global_rows,
            bubble_rows,
        ) = await asyncio.gather(
            asyncio.gather(*suppliers),
            asyncio.gather(*irans),
            asyncio.gather(*globals_),
            asyncio.gather(*bubbles),
        )
        supplied = [q for rows in supplier_rows for q in rows]
        iraned = [q for rows in iran_rows for q in rows]
        worlded = [q for rows in global_rows for q in rows]
        bubbled = [q for rows in bubble_rows for q in rows]
        answered = SourceQuote(
            suppliers=[q for q in supplied if q.error is None],
            irans=[q for q in iraned if q.error is None],
            globals=[q for q in worlded if q.error is None],
            bubbles=[q for q in bubbled if q.error is None],
        )
        failed = SourceQuote(
            suppliers=[q for q in supplied if q.error is not None],
            irans=[q for q in iraned if q.error is not None],
            globals=[q for q in worlded if q.error is not None],
            bubbles=[q for q in bubbled if q.error is not None],
        )
        return answered, failed


class CacheFlusherService:
    def __init__(
        self,
        prices: SourcePriceCache,
        source_bubbles: BubbleSourceCache,
        windows: ISourceWindowService,
    ) -> None:
        """
        Desc: Build the service with the caches it writes to.
        Args:
            prices (SourcePriceCache): Where each source's reading lands.
            source_bubbles (BubbleSourceCache): Where each source's raw
                premium lands.
            windows (ISourceWindowService): The open candle each reading is
                folded into.
        """
        self.prices = prices
        self.source_bubbles = source_bubbles
        self.windows = windows
        self.irans = IranMarketPriceHelper()
        self.suppliers = SupplierMarketPriceHelper()
        self.worlds = GlobalMarketPriceHelper()

    async def flush_results(
        self,
        cfg: CFGContext,
        quotes: SourceQuote,
    ) -> int:
        """
        Desc: Cache every quote under the symbol it was read for, and every
        premium under its asset.
        Args:
            cfg (CFGContext): What the crawl ran against, holding the ids
                the quotes have to be attributed to.
            quotes (SourceQuote): What the crawl came back with.
        Returns:
            return (int): How many readings were cached.
        """
        source_ids = {source.code: source.id for source in cfg.sources}
        symbol_ids = {symbol.code: symbol.id for symbol in cfg.symbols}
        asset_ids = {asset.code: asset.id for asset in cfg.assets}
        codes = {id: code for code, id in symbol_ids.items()}

        built = [
            *self.irans.build(symbol_ids, source_ids, quotes.irans),
            *self.suppliers.build(symbol_ids, source_ids, quotes.suppliers),
            *self.worlds.build(symbol_ids, source_ids, quotes.globals),
        ]
        readings: dict[SymbolCode, list[SourcePriceResult]] = defaultdict(list)
        for reading in built:
            readings[codes[reading.symbol_id]].append(reading)

        premiums: dict[AssetCode, list[SourceBubbleResult]] = defaultdict(list)
        for bubble in quotes.bubbles:
            source_id = source_ids.get(bubble.code)
            asset_id = asset_ids.get(bubble.asset)
            if source_id is None or asset_id is None:
                continue
            premiums[bubble.asset].append(
                SourceBubbleResult(
                    source_id=source_id,
                    asset_id=asset_id,
                    amount=bubble.amount,
                    priced_at=date_utils.utc_now(),
                )
            )

        if readings:
            await self.prices.set_many(readings)
            await self.windows.update_window(readings)
        if premiums:
            await self.source_bubbles.set_many(premiums)
        return sum(len(rows) for rows in readings.values())


class CacheReaderService:
    def __init__(
        self,
        prices: SourcePriceCache,
        source_bubbles: BubbleSourceCache,
    ) -> None:
        """
        Desc: Build the service with the caches it reads from.
        Args:
            prices (SourcePriceCache): Where each source's reading lands.
            source_bubbles (BubbleSourceCache): Where each source's raw
                premium lands.
        """
        self.prices = prices
        self.source_bubbles = source_bubbles

    async def get_by_symbol(
        self,
        symbol: SymbolCode,
    ) -> Sequence[SourcePriceResult]:
        """
        Desc: Read what every source last quoted for one line.
        Args:
            symbol (SymbolCode): The line to read.
        Returns:
            return (Sequence[SourcePriceResult]): The readings, empty when
                no crawl has cached that line yet.
        """
        readings = await self.prices.get(symbol)
        return readings or []

    async def get_many_by_symbols(
        self,
        symbols: Sequence[SymbolCode],
    ) -> dict[SymbolCode, Sequence[SourcePriceResult]]:
        """
        Desc: Read what every source last quoted for several lines.
        Args:
            symbols (Sequence[SymbolCode]): The lines to read.
        Returns:
            return (dict[SymbolCode, Sequence[SourcePriceResult]]): The
                readings of each line that has any.
        """
        readings = await self.prices.get_many(symbols)
        return {code: rows for code, rows in readings.items()}

    async def get_all(
        self,
    ) -> dict[SymbolCode, Sequence[SourcePriceResult]]:
        """
        Desc: Read the whole board the last crawl left behind.
        Returns:
            return (dict[SymbolCode, Sequence[SourcePriceResult]]): Every
                line that has readings.
        """
        readings = await self.prices.get_all()
        return {code: rows for code, rows in readings.items()}

    async def get_bubbles_by_asset(
        self,
        code: AssetCode,
    ) -> Sequence[SourceBubbleResult]:
        """
        Desc: Read what every source last published as one asset's premium.
        Args:
            code (AssetCode): The asset to read.
        Returns:
            return (Sequence[SourceBubbleResult]): The premiums, empty when
                no crawl has cached one for that asset yet.
        """
        premiums = await self.source_bubbles.get(code)
        return premiums or []

    async def get_all_bubbles(
        self,
    ) -> dict[AssetCode, Sequence[SourceBubbleResult]]:
        """
        Desc: Read every premium the last crawl left behind.
        Returns:
            return (dict[AssetCode, Sequence[SourceBubbleResult]]): Every
                asset a source published a premium for.
        """
        premiums = await self.source_bubbles.get_all()
        return {code: rows for code, rows in premiums.items()}


class PersistFlusherService:
    def __init__(self, errors: ISourceErrorService) -> None:
        """
        Desc: Build the service with the source service it writes through.
        Args:
            errors (ISourceErrorService): Where a source's failure is kept.
        """
        self.errors = errors

    def _as_info(self, error: ErrorQuote) -> SourceErrorInfo:
        """
        Desc: Turn what a gateway reported into what a source row stores.
        Args:
            error (ErrorQuote): What the fetcher came back with.
        Returns:
            return (SourceErrorInfo): The row payload.
        """
        info = SourceErrorInfo(kind=error.error_type, message=error.message)
        if error.http_error is not None:
            info["status_code"] = int(error.http_error.status_code)
            info["raw_content"] = error.http_error.raw_content
        return info

    async def flush_errors(
        self,
        cfg: CFGContext,
        quotes: SourceQuote,
    ) -> int:
        """
        Desc: Stamp every source that failed, and clear the error every
        other crawled source carried from the last run.
        Args:
            cfg (CFGContext): What the crawl ran against.
            quotes (SourceQuote): The quotes that came back failed.
        Returns:
            return (int): How many sources were stamped.
        """
        source_ids = {source.code: source.id for source in cfg.sources}
        # a source without a fetcher was never called, so it is not judged
        called = {
            *SUPPLIER_FETCHERS,
            *IRAN_FETCHERS,
            *GLOBAL_FETCHERS,
            *BUBBLE_FETCHERS,
        }
        errors: dict[int, SourceErrorInfo | None] = {
            id: None for code, id in source_ids.items() if code in called
        }
        rows = (
            list(quotes.irans)
            + list(quotes.suppliers)
            + list(quotes.globals)
            + list(quotes.bubbles)
        )
        for row in rows:
            source_id = source_ids.get(row.code)
            if source_id is None or row.error is None:
                continue
            errors[source_id] = self._as_info(row.error)
        if errors:
            await self.errors.apply_errors(errors)
        return len(errors)


class RunnerService:
    def __init__(self, container: AsyncContainer) -> None:
        """
        Desc: Build the service with the container it opens its scopes on.
        Args:
            container (AsyncContainer): The application container.
        """
        self.container = container

    async def run(self) -> bool:
        """
        Desc: Read the config, crawl every source, then write what came
        back, holding a database connection only for the two db phases.
        Returns:
            return (bool): Whether anything was cached.
        """
        async with self.container() as scope:
            reader = await scope.get(ICFGReaderService)
            cfg = await reader.read_context()

        crawler = await self.container.get(ICrawlerService)
        answered, failed = await crawler.crawl(cfg)

        flusher = await self.container.get(ICacheFlusherService)
        saved = await flusher.flush_results(cfg, answered)

        async with self.container() as scope:
            persist = await scope.get(IPersistFlusherService)
            await persist.flush_errors(cfg, failed)
        return saved > 0
