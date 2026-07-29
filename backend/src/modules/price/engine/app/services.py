import asyncio
from collections import defaultdict
from typing import Awaitable, Sequence

from src.common.constants import MAZANE_FACTOR
from src.common.utils import currency_utils
from src.modules.price.assets.domain.enums import AssetCode
from src.modules.price.engine.domain.context import CFGContext
from src.modules.price.engine.domain.quotes import (
    BubbleQuote,
    GlobalSourceQuote,
    IranSourceQuote,
    SourceQuote,
    SupplierSourceQuote,
)
from src.modules.price.engine.domain.results import (
    SourcePriceResult,
    SupplierComputation,
)
from src.modules.price.engine.infra.cache import SourcePriceCache
from src.modules.price.engine.infra.gateways.bubble import BUBBLE_FETCHERS
from src.modules.price.engine.infra.gateways.global_market import (
    GLOBAL_FETCHERS,
)
from src.modules.price.engine.infra.gateways.iran_market import IRAN_FETCHERS
from src.modules.price.engine.infra.gateways.supplier import SUPPLIER_FETCHERS
from src.modules.price.engine.infra.readers import AssetReader, SourceReader


class PricingEngineService:
    def __init__(
        self,
        assets: AssetReader,
        sources: SourceReader,
        prices: SourcePriceCache,
    ) -> None:
        """
        Desc: Build the service with the readers it crawls from and the
        cache it writes to.
        Args:
            assets (AssetReader): Reader over the assets module's tables.
            sources (SourceReader): Reader over the sources module's tables.
            prices (SourcePriceCache): Where each source's reading lands.
        """
        self.assets = assets
        self.sources = sources
        self.prices = prices

    async def _fetch_all_db(self) -> CFGContext:
        """
        Desc: Read what the crawl needs: every source, and the asset ids a
        quoted code maps to.
        Returns:
            return (CFGContext): The sources to call and the assets to
                attribute their quotes to.
        """
        sources = await self.sources.read_all()
        refs = await self.assets.read_refs()
        context = CFGContext(sources=sources, assets=refs)
        return context

    async def _fetch_all_http(self, context: CFGContext) -> SourceQuote:
        """
        Desc: Call every source that has a fetcher, all at once.
        Args:
            context (CFGContext): The sources to call, with their configs.
        Returns:
            return (SourceQuote): Every quote the crawl came back with,
                split by the family that produced it.
        """
        suppliers: list[Awaitable[Sequence[SupplierSourceQuote]]] = []
        irans: list[Awaitable[Sequence[IranSourceQuote]]] = []
        globals_: list[Awaitable[Sequence[GlobalSourceQuote]]] = []
        bubbles: list[Awaitable[Sequence[BubbleQuote]]] = []
        for source in context.sources:
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
        quote = SourceQuote(
            suppliers=[q for rows in supplier_rows for q in rows],
            irans=[q for rows in iran_rows for q in rows],
            globals=[q for rows in global_rows for q in rows],
            bubbles=[q for rows in bubble_rows for q in rows],
        )
        return quote

    async def _save_all(
        self,
        context: CFGContext,
        quote: SourceQuote,
    ) -> int:
        """
        Desc: Price every rial quote the crawl produced and cache it under
        the asset it belongs to.
        Args:
            context (CFGContext): What the crawl ran against, holding the
                ids the quotes have to be attributed to.
            quote (SourceQuote): What the crawl came back with.
        Returns:
            return (int): How many readings were cached.
        """
        source_ids = {source.code: source.id for source in context.sources}
        asset_ids = {asset.code: asset.id for asset in context.assets}
        readings: dict[AssetCode, list[SourcePriceResult]] = defaultdict(list)

        for row in quote.irans:
            source_id = source_ids.get(row.code)
            asset_id = asset_ids.get(row.asset)
            if row.error is not None or source_id is None or asset_id is None:
                continue
            readings[row.asset].append(
                SourcePriceResult.from_sides(
                    source_id=source_id,
                    asset_id=asset_id,
                    selling=row.selling,
                    buying=row.buying,
                )
            )

        for row in quote.suppliers:
            source_id = source_ids.get(row.code)
            asset_id = asset_ids.get(row.asset)
            if row.error is not None or source_id is None or asset_id is None:
                continue
            selling = currency_utils.from_mazane(row.selling)
            buying = currency_utils.from_mazane(row.buying)
            readings[row.asset].append(
                SourcePriceResult.from_sides(
                    source_id=source_id,
                    asset_id=asset_id,
                    selling=selling,
                    buying=buying,
                    computation=SupplierComputation(
                        selling_mazane=row.selling,
                        buying_mazane=row.buying,
                        mazane_factor=MAZANE_FACTOR,
                        final_price=round((selling + buying) / 2),
                    ),
                )
            )

        await self.prices.set_many(readings)
        return sum(len(rows) for rows in readings.values())

    async def run(self) -> int:
        """
        Desc: Crawl every source once and cache what they quoted.
        Returns:
            return (int): How many readings were cached.
        """
        context = await self._fetch_all_db()
        quote = await self._fetch_all_http(context)
        saved = await self._save_all(context, quote)
        return saved
