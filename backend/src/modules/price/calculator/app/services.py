from collections import defaultdict
from typing import Mapping, Sequence

from taskiq import ScheduledTask, ScheduleSource

from src.common.errors.exceptions import NotFoundException
from src.core import resources
from src.modules.price.assets.domain.enums import AssetCode
from src.modules.price.calculator.app.helpers import (
    Aggregator,
    GlobalMarketCalculator,
    IranMarketCalculator,
    SupplierCalculator,
)
from src.modules.price.calculator.domain.context import (
    AssetContext,
    BubbleContext,
    SwitchOrderContext,
)
from src.modules.price.calculator.domain.results import (
    AssetPriceResult,
    BubbleResult,
)
from src.modules.price.calculator.infra.cache import (
    AssetPriceCache,
    BubbleCache,
)
from src.modules.price.calculator.infra.readers import (
    AssetReader,
    BubbleReader,
    SourceReader,
    SwitchOrderReader,
    SymbolReader,
)
from src.modules.price.engine.domain.results import (
    SourceBubbleResult,
    SourcePriceResult,
)
from src.modules.price.engine.interfaces import ICacheReaderService
from src.modules.price.sources.domain.enums import SourceSwitch


class BubbleCalculatorService:
    def __init__(
        self,
        bubbles: BubbleReader,
        published: ICacheReaderService,
        cache: BubbleCache,
    ) -> None:
        """
        Desc: Build the service with what it settles premiums out of.
        Args:
            bubbles (BubbleReader): Reader over the bubbles module's tables.
            published (ICacheReaderService): Where the crawl left what each
                source published.
            cache (BubbleCache): Where the settled premium lands.
        """
        self.bubbles = bubbles
        self.published = published
        self.cache = cache
        self.aggregator = Aggregator()

    def _settled(
        self,
        bubble: BubbleContext,
        published: Sequence[SourceBubbleResult],
    ) -> BubbleResult | None:
        """
        Desc: Fold every published premium of one asset into a settled one.
        Args:
            bubble (BubbleContext): The bubble being settled, with the rule
                its publishers are folded by.
            published (Sequence[SourceBubbleResult]): What each source
                published for that asset.
        Returns:
            return (BubbleResult | None): The settled premium, or None when
                nobody published one.
        """
        result = None
        if published:
            amount = self.aggregator.pick(
                [row.amount for row in published],
                bubble.config.agg_type,
            )
            result = BubbleResult(
                asset_id=published[0].asset_id,
                amount=amount,
                priced_at=max(row.priced_at for row in published),
            )
        return result

    async def calculate(self, bubble_id: int) -> int:
        """
        Desc: Settle one bubble out of what its publishers last said.
        Args:
            bubble_id (int): ID of the bubble to settle.
        Returns:
            return (int): The settled premium in rial, signed, and zero
                when nobody published one.
        """
        bubble = await self.bubbles.get_bubble_config(bubble_id)
        if bubble is None:
            raise NotFoundException(
                identifier="id",
                identifier_value=bubble_id,
                message=f"Cannot find Bubble by id with value {bubble_id}",
                message_code=resources.NOT_FOUND_ERROR,
                entity="Bubble",
            )
        published = await self.published.get_bubbles_by_asset(bubble.code)
        result = self._settled(bubble, published)
        amount = 0
        if result is not None:
            await self.cache.set(bubble.code, result)
            amount = result.amount
        return amount

    async def calculate_all(self) -> int:
        """
        Desc: Settle every bubble out of what its publishers last said.
        Returns:
            return (int): How many bubbles were settled.
        """
        bubbles = await self.bubbles.get_all()
        published = await self.published.get_all_bubbles()
        settled: dict[AssetCode, BubbleResult] = {}
        for bubble in bubbles:
            result = self._settled(bubble, published.get(bubble.code, ()))
            if result is not None:
                settled[bubble.code] = result
        if settled:
            await self.cache.set_many(settled)
        return len(settled)


class CalculatorService:
    # the dollar is priced on its own route, before a sweep reads its rate
    excludes = (AssetCode.USD,)

    def __init__(
        self,
        assets: AssetReader,
        symbols: SymbolReader,
        orders: SwitchOrderReader,
        sources: SourceReader,
        readings: ICacheReaderService,
        bubbles: BubbleCache,
        prices: AssetPriceCache,
    ) -> None:
        """
        Desc: Build the service with what it prices out of and writes to.
        Args:
            assets (AssetReader): Reader over the assets module's tables.
            symbols (SymbolReader): Reader over the symbols module's tables.
            orders (SwitchOrderReader): Reader of the markets an asset is
                priced from, in order.
            sources (SourceReader): Reader of which market each source
                feeds.
            readings (ICacheReaderService): Where the crawl left what each
                source quoted.
            bubbles (BubbleCache): Where the settled premiums live.
            prices (AssetPriceCache): Where the asset's price lands, and
                where the dollar rate is read from.
        """
        self.assets = assets
        self.symbols = symbols
        self.orders = orders
        self.sources = sources
        self.readings = readings
        self.bubbles = bubbles
        self.prices = prices
        self.iran = IranMarketCalculator()
        self.supplier = SupplierCalculator()
        self.world = GlobalMarketCalculator()

    def _priced(
        self,
        asset: AssetContext,
        order: Sequence[SwitchOrderContext],
        markets: Mapping[SourceSwitch, Sequence[SourcePriceResult]],
        bubble: BubbleResult | None,
        usd_price: int,
    ) -> AssetPriceResult | None:
        """
        Desc: Walk an asset's markets and take the first price it gets.
        Args:
            asset (AssetContext): The asset being priced.
            order (Sequence[SwitchOrderContext]): Its markets, the one
                tried first at the front.
            markets (Mapping[SourceSwitch, Sequence[SourcePriceResult]]):
                Its readings, split by the market they were quoted in.
            bubble (BubbleResult | None): Its settled premium, if any.
            usd_price (int): What one dollar costs, in rial.
        Returns:
            return (AssetPriceResult | None): The asset's price, or None
                when no market of its own could price it.
        """
        result = None
        for row in order:
            rows = markets.get(row.switch, ())
            if row.switch is SourceSwitch.IRAN_MARKET:
                result = self.iran.calculate(asset, rows)
            elif row.switch is SourceSwitch.SUPPLIER:
                result = self.supplier.calculate(asset, rows)
            elif row.switch is SourceSwitch.GLOBAL_MARKET:
                result = self.world.calculate(usd_price, bubble, asset, rows)
            if result is not None:
                break
        return result

    async def calculate(self, asset_id: int) -> int:
        """
        Desc: Price one asset from the first of its markets that answers.
        Args:
            asset_id (int): ID of the asset to price.
        Returns:
            return (int): The asset's price in rial, and zero when no
                market of its own could price it.
        """
        asset = await self.assets.get_asset_config(asset_id)
        if asset is None:
            raise NotFoundException(
                identifier="id",
                identifier_value=asset_id,
                message=f"Cannot find Asset by id with value {asset_id}",
                message_code=resources.NOT_FOUND_ERROR,
                entity="Asset",
            )
        symbols = await self.symbols.get_symbols_of_asset(asset_id)
        order = await self.orders.get_switch_order(asset_id)
        switches = dict(await self.sources.get_source_switches())
        codes = [symbol.symbol for symbol in symbols]
        readings = await self.readings.get_many_by_symbols(codes)
        # both are read before a single market is tried, so the world has
        # what it needs the moment its turn comes
        bubble = await self.bubbles.get(asset.code)
        dollar = await self.prices.get(AssetCode.USD)
        usd_price = 0 if dollar is None else dollar.price

        markets: dict[SourceSwitch, list[SourcePriceResult]] = defaultdict(
            list
        )
        flatten_readings = [row for rows in readings.values() for row in rows]
        for row in flatten_readings:
            switch = switches.get(row.source_id)
            if switch is not None:
                markets[switch].append(row)

        result = self._priced(asset, order, markets, bubble, usd_price)
        price = 0
        if result is not None:
            await self.prices.set(asset.code, result)
            price = result.price
        return price

    async def calculate_usd(self) -> int:
        """
        Desc: Price the dollar on its own, the rate a sweep reads world
        parity at.
        Returns:
            return (int): The dollar's price in rial, and zero when no
                market of its own could price it.
        """
        asset_id = await self.assets.get_id_by_code(AssetCode.USD)
        if asset_id is None:
            raise NotFoundException(
                identifier="code",
                identifier_value=AssetCode.USD.value,
                message=(
                    f"Cannot find Asset by code with value "
                    f"{AssetCode.USD.value}"
                ),
                message_code=resources.NOT_FOUND_ERROR,
                entity="Asset",
            )
        price = await self.calculate(asset_id)
        return price

    async def calculate_all(self) -> int:
        """
        Desc: Price every asset but the dollar, each from the first of its
        markets that answers.
        Returns:
            return (int): How many assets were priced.
        """
        assets = await self.assets.get_all_config(self.excludes)
        symbols = await self.symbols.get_all(self.excludes)
        orders = await self.orders.get_all(self.excludes)
        switches = dict(await self.sources.get_source_switches())
        readings = await self.readings.get_all()
        # both are read before a single market is tried, so the world has
        # what it needs the moment its turn comes
        bubbles = await self.bubbles.get_all()
        dollar = await self.prices.get(AssetCode.USD)
        usd_price = 0 if dollar is None else dollar.price

        ordered: dict[int, list[SwitchOrderContext]] = defaultdict(list)
        for row in orders:
            ordered[row.asset_id].append(row)

        markets: dict[int, dict[SourceSwitch, list[SourcePriceResult]]] = (
            defaultdict(lambda: defaultdict(list))
        )
        symbol_dict = {symbol.id: symbol for symbol in symbols}
        flattend_readings = [row for rows in readings.values() for row in rows]
        for row in flattend_readings:
            symbol = symbol_dict.get(row.symbol_id)
            if symbol is not None:
                switch = switches.get(row.source_id)
                if switch is not None:
                    markets[symbol.asset_id][switch].append(row)

        priced: dict[AssetCode, AssetPriceResult] = {}
        for asset in assets:
            result = self._priced(
                asset,
                ordered.get(asset.asset_id, ()),
                markets.get(asset.asset_id, {}),
                bubbles.get(asset.code),
                usd_price,
            )
            if result is not None:
                priced[asset.code] = result
        if priced:
            await self.prices.set_many(priced)
        return len(priced)


class CacheReaderService:
    def __init__(
        self,
        prices: AssetPriceCache,
        bubbles: BubbleCache,
    ) -> None:
        """
        Desc: Build the service with the caches it reads from.
        Args:
            prices (AssetPriceCache): Where each asset's price lands.
            bubbles (BubbleCache): Where each settled premium lands.
        """
        self.prices = prices
        self.bubbles = bubbles

    async def get_price(
        self,
        asset_code: AssetCode,
    ) -> AssetPriceResult | None:
        """
        Desc: Read what one asset was last priced at.
        Args:
            asset_code (AssetCode): The asset to read.
        Returns:
            return (AssetPriceResult | None): Its price, or None when it
                has not been priced yet.
        """
        found = await self.prices.get(asset_code)
        return found

    async def get_bubble_amount(
        self,
        bubble_code: AssetCode,
    ) -> BubbleResult | None:
        """
        Desc: Read one asset's last settled premium.
        Args:
            bubble_code (AssetCode): The asset whose premium to read.
        Returns:
            return (BubbleResult | None): Its premium, or None when none
                has been settled yet.
        """
        found = await self.bubbles.get(bubble_code)
        return found

    async def get_all_bubble_amounts(self) -> Sequence[BubbleResult]:
        """
        Desc: Read every premium that has been settled.
        Returns:
            return (Sequence[BubbleResult]): The settled premiums, empty
                when none has been.
        """
        found = await self.bubbles.get_all()
        return list(found.values())

    async def get_all_prices(self) -> Sequence[AssetPriceResult]:
        """
        Desc: Read the price of every asset that has one.
        Returns:
            return (Sequence[AssetPriceResult]): The prices, empty when
                nothing has been priced yet.
        """
        found = await self.prices.get_all()
        return list(found.values())


class SchedulerService:
    # the task a schedule fires, and the queue it fires it on
    task_name = "calculator.calculate_asset"
    queue_name = "calculator_queue"
    prefix = "calculator:asset:"
    # the dollar runs on a period of its own that no config can move
    fixed = (AssetCode.USD,)

    def __init__(
        self,
        assets: AssetReader,
        source: ScheduleSource,
    ) -> None:
        """
        Desc: Build the service with the config it reads and the schedules
        it writes.
        Args:
            assets (AssetReader): Reader over the assets module's tables.
            source (ScheduleSource): Where the running schedules live.
        """
        self.assets = assets
        self.source = source

    async def sync(self, asset_id: int) -> bool:
        """
        Desc: Give a switched-on asset a schedule of its own period, and
        take it away from one that is switched off or gone.
        Args:
            asset_id (int): ID of the asset whose config was written.
        Returns:
            return (bool): Whether the asset is scheduled now.
        """
        asset = await self.assets.get_asset_config(asset_id)
        schedule_id = f"{self.prefix}{asset_id}"
        # a changed period is a different schedule, so whatever was there
        # goes before the new one is written
        await self.source.delete_schedule(schedule_id)
        scheduled = False
        if (
            asset is not None
            and asset.config.scheduler_on
            and asset.code not in self.fixed
        ):
            await self.source.add_schedule(
                ScheduledTask(
                    task_name=self.task_name,
                    labels={"queue_name": self.queue_name},
                    args=[],
                    kwargs={"asset_id": asset_id},
                    schedule_id=schedule_id,
                    interval=asset.config.scheduler_seconds,
                )
            )
            scheduled = True
        return scheduled
