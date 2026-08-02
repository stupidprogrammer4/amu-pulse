from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Mapping, Sequence, cast

import pytest

from src.common.errors.exceptions import NotFoundException
from src.infra.redis.client import RedisClient
from src.modules.price.assets.domain.enums import AggregationType, AssetCode
from src.modules.price.assets.domain.models import AssetConfigModel
from src.modules.price.calculator.app.services import CalculatorService
from src.modules.price.calculator.domain.context import (
    AssetContext,
    SwitchOrderContext,
    SymbolContext,
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
    SourceReader,
    SwitchOrderReader,
    SymbolReader,
)
from src.modules.price.engine.domain.results import SourcePriceResult
from src.modules.price.engine.interfaces import ICacheReaderService
from src.modules.price.sources.domain.enums import SourceSwitch
from src.modules.price.symbols.domain.enums import CurrencyType, SymbolCode
from tests.unit.calculator.test_asset_price_cache import _FakeRedis

_at = datetime(2026, 8, 1, 12, 0, tzinfo=UTC)

# who quotes what: iran quotes the gram and the dollar, the supplier the
# mazane, the world the ounce
_iran_source = 1
_supplier_source = 2
_world_source = 3

# the lines each asset is quoted through
_gram_symbol = 10
_mazane_symbol = 11
_ounce_symbol = 12
_dollar_symbol = 13


def _asset(
    asset_id: int = 1,
    code: AssetCode = AssetCode.GOLD18,
    agg: AggregationType = AggregationType.MEDIAN,
) -> AssetContext:
    """
    Desc: Build an asset context priced by the given rule.
    Args:
        asset_id (int): ID of the asset.
        code (AssetCode): Code of the asset.
        agg (AggregationType): The rule its readings are folded by.
    Returns:
        return (AssetContext): The context the service prices.
    """
    config = AssetConfigModel(
        asset_id=asset_id,
        scheduler_on=True,
        scheduler_seconds=60,
        agg_type=agg,
    )
    return AssetContext(code=code, asset_id=asset_id, config=config)


def _reading(
    buying: int,
    selling: int,
    source_id: int,
    symbol_id: int,
    currency: CurrencyType = CurrencyType.RIAL,
) -> SourcePriceResult:
    """
    Desc: Build one source reading, mid priced like the crawl caches it.
    Args:
        buying (int): The buying side, in the currency's own unit.
        selling (int): The selling side, in the currency's own unit.
        source_id (int): ID of the source that quoted it.
        symbol_id (int): ID of the line it was quoted for.
        currency (CurrencyType): What the two sides are counted in.
    Returns:
        return (SourcePriceResult): The reading.
    """
    price = round((buying + selling) / 2)
    return SourcePriceResult(
        source_id=source_id,
        symbol_id=symbol_id,
        currency=currency,
        buy_price=buying,
        sell_price=selling,
        price=price,
        buy_spread=price - buying,
        sell_spread=selling - price,
        buy_spread_rate=(price - buying) / price,
        sell_spread_rate=(selling - price) / price,
        priced_at=_at,
    )


class _FakeAssetReader:
    """The asset reads the service makes, over a list of contexts."""

    def __init__(self, assets: Sequence[AssetContext]) -> None:
        self.assets = assets

    async def get_all_config(
        self, excludes: Sequence[AssetCode] = ()
    ) -> Sequence[AssetContext]:
        return [a for a in self.assets if a.code not in excludes]

    async def get_id_by_code(self, code: AssetCode) -> int | None:
        found = None
        for asset in self.assets:
            if asset.code is code:
                found = asset.asset_id
        return found

    async def get_asset_config(self, asset_id: int) -> AssetContext | None:
        found = None
        for asset in self.assets:
            if asset.asset_id == asset_id:
                found = asset
        return found


class _FakeSymbolReader:
    """The symbol reads the service makes, over a list of contexts."""

    def __init__(self, symbols: Sequence[SymbolContext]) -> None:
        self.symbols = symbols

    async def get_all(
        self, excludes: Sequence[AssetCode] = ()
    ) -> Sequence[SymbolContext]:
        return [s for s in self.symbols if s.code not in excludes]

    async def get_symbols_of_asset(
        self, asset_id: int
    ) -> Sequence[SymbolContext]:
        return [s for s in self.symbols if s.asset_id == asset_id]


class _FakeSwitchOrderReader:
    """The order reads the service makes, over a list of rows."""

    def __init__(self, orders: Sequence[SwitchOrderContext]) -> None:
        self.orders = orders

    async def get_all(
        self, excludes: Sequence[AssetCode] = ()
    ) -> Sequence[SwitchOrderContext]:
        return [o for o in self.orders if o.code not in excludes]

    async def get_switch_order(
        self, asset_id: int
    ) -> Sequence[SwitchOrderContext]:
        return [o for o in self.orders if o.asset_id == asset_id]


class _FakeSourceReader:
    """Which market each source feeds."""

    def __init__(self, switches: Sequence[tuple[int, SourceSwitch]]) -> None:
        self.switches = switches

    async def get_source_switches(
        self,
    ) -> Sequence[tuple[int, SourceSwitch]]:
        return self.switches


class _FakeCacheReader:
    """The reading side of the engine's cache reader, over a dict."""

    def __init__(
        self,
        readings: Mapping[SymbolCode, Sequence[SourcePriceResult]],
    ) -> None:
        self.readings = readings

    async def get_all(
        self,
    ) -> dict[SymbolCode, Sequence[SourcePriceResult]]:
        return dict(self.readings)

    async def get_many_by_symbols(
        self, symbols: Sequence[SymbolCode]
    ) -> dict[SymbolCode, Sequence[SourcePriceResult]]:
        return {
            code: rows
            for code, rows in self.readings.items()
            if code in set(symbols)
        }


def _symbols() -> Sequence[SymbolContext]:
    """
    Desc: Build the lines gold and the dollar are quoted through.
    Returns:
        return (Sequence[SymbolContext]): The four lines.
    """
    return [
        SymbolContext(
            id=_gram_symbol,
            code=AssetCode.GOLD18,
            symbol=SymbolCode.GOLD18_GRAM,
            asset_id=1,
        ),
        SymbolContext(
            id=_mazane_symbol,
            code=AssetCode.GOLD18,
            symbol=SymbolCode.GOLD18_MAZANE,
            asset_id=1,
        ),
        SymbolContext(
            id=_ounce_symbol,
            code=AssetCode.GOLD18,
            symbol=SymbolCode.XAU_OUNCE,
            asset_id=1,
        ),
        SymbolContext(
            id=_dollar_symbol,
            code=AssetCode.USD,
            symbol=SymbolCode.USD_RIAL,
            asset_id=2,
        ),
    ]


def _order(
    asset_id: int,
    switches: Sequence[SourceSwitch],
    code: AssetCode = AssetCode.GOLD18,
) -> Sequence[SwitchOrderContext]:
    """
    Desc: Build an asset's pricing order out of the markets given.
    Args:
        asset_id (int): ID of the asset the order belongs to.
        switches (Sequence[SourceSwitch]): The markets, first tried first.
        code (AssetCode): Code of the asset.
    Returns:
        return (Sequence[SwitchOrderContext]): The order rows.
    """
    return [
        SwitchOrderContext(
            code=code, asset_id=asset_id, switch=switch, order=index
        )
        for index, switch in enumerate(switches)
    ]


async def _service(
    assets: Sequence[AssetContext],
    orders: Sequence[SwitchOrderContext],
    readings: Mapping[SymbolCode, Sequence[SourcePriceResult]],
    bubbles: Mapping[AssetCode, BubbleResult] | None = None,
    dollar: int = 0,
) -> tuple[CalculatorService, AssetPriceCache]:
    """
    Desc: Build the service over fake reads and caches on a fake Redis.
    Args:
        assets (Sequence[AssetContext]): The assets that exist.
        orders (Sequence[SwitchOrderContext]): Their pricing orders.
        readings (Mapping[SymbolCode, Sequence[SourcePriceResult]]): What
            the crawl cached for each line.
        bubbles (Mapping[AssetCode, BubbleResult] | None): The settled
            premiums, if any.
        dollar (int): The dollar price already cached, zero for none.
    Returns:
        return (tuple[CalculatorService, AssetPriceCache]): The service and
            the cache it prices into.
    """
    client = cast(RedisClient, SimpleNamespace(client=_FakeRedis()))
    prices = AssetPriceCache(client)
    premiums = BubbleCache(client)
    if bubbles:
        await premiums.set_many(bubbles)
    if dollar:
        await prices.set(
            AssetCode.USD,
            _priced(asset_id=2, price=dollar),
        )
    switches = [
        (_iran_source, SourceSwitch.IRAN_MARKET),
        (_supplier_source, SourceSwitch.SUPPLIER),
        (_world_source, SourceSwitch.GLOBAL_MARKET),
    ]
    service = CalculatorService(
        cast(AssetReader, _FakeAssetReader(assets)),
        cast(SymbolReader, _FakeSymbolReader(_symbols())),
        cast(SwitchOrderReader, _FakeSwitchOrderReader(orders)),
        cast(SourceReader, _FakeSourceReader(switches)),
        cast(ICacheReaderService, _FakeCacheReader(readings)),
        premiums,
        prices,
    )
    return service, prices


def _priced(asset_id: int, price: int) -> AssetPriceResult:
    """
    Desc: Build an already cached asset price.
    Args:
        asset_id (int): ID of the asset it belongs to.
        price (int): The mid price in rial.
    Returns:
        return (AssetPriceResult): The cached price.
    """
    return AssetPriceResult(
        asset_id=asset_id,
        buy_price=price,
        sell_price=price,
        price=price,
        buy_spread=0,
        sell_spread=0,
        buy_spread_rate=0.0,
        sell_spread_rate=0.0,
        priced_at=_at,
    )


class TestCalculateOne:
    async def test_the_first_market_of_the_order_prices_the_asset(
        self,
    ) -> None:
        service, cache = await _service(
            [_asset()],
            _order(1, [SourceSwitch.IRAN_MARKET, SourceSwitch.SUPPLIER]),
            {
                SymbolCode.GOLD18_GRAM: [
                    _reading(
                        100_000_000, 101_000_000, _iran_source, _gram_symbol
                    )
                ],
                SymbolCode.GOLD18_MAZANE: [
                    _reading(
                        4_331_802, 4_331_802, _supplier_source, _mazane_symbol
                    )
                ],
            },
        )

        price = await service.calculate(1)
        found = await cache.get(AssetCode.GOLD18)

        assert price == 100_500_000
        assert found is not None
        assert found.asset_id == 1

    async def test_it_falls_through_to_the_next_market(self) -> None:
        # the iranian sources went quiet, so the suppliers price it
        service, _ = await _service(
            [_asset()],
            _order(1, [SourceSwitch.IRAN_MARKET, SourceSwitch.SUPPLIER]),
            {
                SymbolCode.GOLD18_MAZANE: [
                    _reading(
                        4_331_802, 4_331_802, _supplier_source, _mazane_symbol
                    )
                ]
            },
        )

        price = await service.calculate(1)

        assert price == 1_000_000

    async def test_a_market_off_the_order_never_prices(self) -> None:
        # only the suppliers are switched on, and only iran has readings
        service, cache = await _service(
            [_asset()],
            _order(1, [SourceSwitch.SUPPLIER]),
            {
                SymbolCode.GOLD18_GRAM: [
                    _reading(
                        100_000_000, 101_000_000, _iran_source, _gram_symbol
                    )
                ]
            },
        )

        price = await service.calculate(1)

        assert price == 0
        assert await cache.get(AssetCode.GOLD18) is None

    async def test_an_asset_with_no_market_switched_on(self) -> None:
        service, _ = await _service(
            [_asset()],
            [],
            {
                SymbolCode.GOLD18_GRAM: [
                    _reading(
                        100_000_000, 101_000_000, _iran_source, _gram_symbol
                    )
                ]
            },
        )

        price = await service.calculate(1)

        assert price == 0

    async def test_the_world_prices_it_off_the_dollar_and_the_premium(
        self,
    ) -> None:
        service, _ = await _service(
            [_asset()],
            _order(1, [SourceSwitch.GLOBAL_MARKET]),
            {
                SymbolCode.XAU_OUNCE: [
                    _reading(
                        400_000,
                        400_000,
                        _world_source,
                        _ounce_symbol,
                        CurrencyType.USD,
                    )
                ]
            },
            bubbles={
                AssetCode.GOLD18: BubbleResult(
                    asset_id=1, amount=5_000_000, priced_at=_at
                )
            },
            dollar=1_000_000,
        )

        price = await service.calculate(1)

        assert price == 101_452_240

    async def test_without_a_cached_dollar_the_world_cannot_price(
        self,
    ) -> None:
        service, _ = await _service(
            [_asset()],
            _order(1, [SourceSwitch.GLOBAL_MARKET]),
            {
                SymbolCode.XAU_OUNCE: [
                    _reading(
                        400_000,
                        400_000,
                        _world_source,
                        _ounce_symbol,
                        CurrencyType.USD,
                    )
                ]
            },
        )

        price = await service.calculate(1)

        assert price == 0

    async def test_a_supplier_reading_never_reaches_the_iran_fold(
        self,
    ) -> None:
        # a mazane folded as a gram would price gold at a quarter of itself
        service, _ = await _service(
            [_asset()],
            _order(1, [SourceSwitch.IRAN_MARKET]),
            {
                SymbolCode.GOLD18_MAZANE: [
                    _reading(
                        4_331_802, 4_331_802, _supplier_source, _mazane_symbol
                    )
                ]
            },
        )

        price = await service.calculate(1)

        assert price == 0

    async def test_an_asset_that_does_not_exist(self) -> None:
        service, _ = await _service([_asset()], [], {})

        with pytest.raises(NotFoundException):
            await service.calculate(9999)


class TestCalculateUsd:
    async def test_it_prices_the_dollar_without_being_told_its_id(
        self,
    ) -> None:
        service, cache = await _service(
            [_asset(asset_id=2, code=AssetCode.USD)],
            _order(2, [SourceSwitch.IRAN_MARKET], code=AssetCode.USD),
            {
                SymbolCode.USD_RIAL: [
                    _reading(
                        1_900_000, 1_910_000, _iran_source, _dollar_symbol
                    )
                ]
            },
        )

        price = await service.calculate_usd()
        found = await cache.get(AssetCode.USD)

        assert price == 1_905_000
        assert found is not None
        assert found.asset_id == 2

    async def test_a_dollar_nobody_quoted(self) -> None:
        service, _ = await _service(
            [_asset(asset_id=2, code=AssetCode.USD)],
            _order(2, [SourceSwitch.IRAN_MARKET], code=AssetCode.USD),
            {},
        )

        price = await service.calculate_usd()

        assert price == 0

    async def test_no_dollar_asset_at_all(self) -> None:
        service, _ = await _service([_asset()], [], {})

        with pytest.raises(NotFoundException):
            await service.calculate_usd()


class TestCalculateAll:
    async def test_the_sweep_leaves_the_dollar_to_its_own_route(self) -> None:
        gold = _asset(asset_id=1)
        dollar = _asset(asset_id=2, code=AssetCode.USD)
        orders = [
            *_order(1, [SourceSwitch.SUPPLIER, SourceSwitch.IRAN_MARKET]),
            *_order(2, [SourceSwitch.IRAN_MARKET], code=AssetCode.USD),
        ]
        service, cache = await _service(
            [gold, dollar],
            orders,
            {
                SymbolCode.GOLD18_MAZANE: [
                    _reading(
                        4_331_802, 4_331_802, _supplier_source, _mazane_symbol
                    )
                ],
                SymbolCode.USD_RIAL: [
                    _reading(
                        1_900_000, 1_910_000, _iran_source, _dollar_symbol
                    )
                ],
            },
        )

        priced = await service.calculate_all()
        found = await cache.get_all()

        assert priced == 1
        assert {code: r.price for code, r in found.items()} == {
            AssetCode.GOLD18: 1_000_000
        }

    async def test_each_asset_walks_its_own_order(self) -> None:
        # the suppliers come first, so the gram reading never gets a turn
        service, cache = await _service(
            [_asset(asset_id=1)],
            _order(1, [SourceSwitch.SUPPLIER, SourceSwitch.IRAN_MARKET]),
            {
                SymbolCode.GOLD18_GRAM: [
                    _reading(
                        100_000_000, 101_000_000, _iran_source, _gram_symbol
                    )
                ],
                SymbolCode.GOLD18_MAZANE: [
                    _reading(
                        4_331_802, 4_331_802, _supplier_source, _mazane_symbol
                    )
                ],
            },
        )

        priced = await service.calculate_all()
        found = await cache.get(AssetCode.GOLD18)

        assert priced == 1
        assert found is not None
        assert found.price == 1_000_000

    async def test_one_asset_s_readings_never_price_another(self) -> None:
        # only the dollar was quoted, and the dollar is not in the sweep
        service, cache = await _service(
            [_asset(asset_id=1), _asset(asset_id=2, code=AssetCode.USD)],
            [
                *_order(1, [SourceSwitch.IRAN_MARKET]),
                *_order(2, [SourceSwitch.IRAN_MARKET], code=AssetCode.USD),
            ],
            {
                SymbolCode.USD_RIAL: [
                    _reading(
                        1_900_000, 1_910_000, _iran_source, _dollar_symbol
                    )
                ]
            },
        )

        priced = await service.calculate_all()

        assert priced == 0
        assert await cache.get_all() == {}

    async def test_an_asset_with_no_market_switched_on_is_skipped(
        self,
    ) -> None:
        service, cache = await _service(
            [_asset(asset_id=1)],
            [],
            {
                SymbolCode.GOLD18_GRAM: [
                    _reading(
                        100_000_000, 101_000_000, _iran_source, _gram_symbol
                    )
                ]
            },
        )

        priced = await service.calculate_all()

        assert priced == 0
        assert await cache.get_all() == {}

    async def test_a_sweep_with_nothing_cached_writes_nothing(self) -> None:
        service, cache = await _service(
            [_asset()], _order(1, [SourceSwitch.IRAN_MARKET]), {}
        )

        priced = await service.calculate_all()

        assert priced == 0
        assert await cache.get_all() == {}

    async def test_the_sweep_prices_gold_off_the_dollar_route_left(
        self,
    ) -> None:
        # whatever the dollar route last cached is the rate world parity
        # is read at
        service, cache = await _service(
            [_asset()],
            _order(1, [SourceSwitch.GLOBAL_MARKET]),
            {
                SymbolCode.XAU_OUNCE: [
                    _reading(
                        400_000,
                        400_000,
                        _world_source,
                        _ounce_symbol,
                        CurrencyType.USD,
                    )
                ]
            },
            dollar=1_931_900,
        )

        priced = await service.calculate_all()
        found = await cache.get(AssetCode.GOLD18)

        assert priced == 1
        assert found is not None
        assert found.price == 186_336_080

    async def test_the_sweep_gives_each_asset_its_own_premium(self) -> None:
        service, cache = await _service(
            [_asset()],
            _order(1, [SourceSwitch.GLOBAL_MARKET]),
            {
                SymbolCode.XAU_OUNCE: [
                    _reading(
                        400_000,
                        400_000,
                        _world_source,
                        _ounce_symbol,
                        CurrencyType.USD,
                    )
                ]
            },
            bubbles={
                AssetCode.GOLD18: BubbleResult(
                    asset_id=1, amount=5_000_000, priced_at=_at
                ),
                AssetCode.USD: BubbleResult(
                    asset_id=2, amount=99_000_000, priced_at=_at
                ),
            },
            dollar=1_000_000,
        )

        await service.calculate_all()
        found = await cache.get(AssetCode.GOLD18)

        assert found is not None
        assert found.price == 101_452_240
